#!/bin/bash
#
# Updates runtime components of the bot:
#   1. Pulls the latest base image (FROM in Dockerfile) and rebuilds the bot image.
#   2. If the image changed, recreates the container and waits for it to become
#      healthy; on failure rolls back to the previous image.
#   3. Reports pinned packages from requirements.txt that have newer releases.
#      requirements.txt is managed in the repo (CI overwrites local changes),
#      so pins are only reported, not bumped.
#   4. Reports when the latest Python (python:3-slim) is newer than the one in
#      Dockerfile and all pinned packages install on it. Dependencies often lag
#      behind a new Python minor, so FROM is bumped in the repo, not here.
#
# Code itself is deployed by GitHub Actions (.github/workflows/deploy.yml).
#
# Notifications go to a separate monitoring Telegram bot: MONITORING_BOT_TOKEN
# and MONITORING_CHAT_ID in .env. Only these two variables are read from .env —
# TELEGRAM_BOT_TOKEN there belongs to the alerts bot itself. A message is sent
# only when something changed or failed; errors also go to stderr.
#
# Usage: ./update.sh [--force]
#   --force  rebuild without cache and recreate the container even if unchanged
#
# Cron example (weekly, Monday 05:45; stderr is left for cron mail):
#   45 5 * * 1 /path/to/deploy/update.sh >/dev/null

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
STATE_DIR="$PROJECT_DIR/data"
OUTDATED_STATE="$STATE_DIR/.outdated-packages"
PYTHON_STATE="$STATE_DIR/.latest-python"
LATEST_BASE="python:3-slim"
LOCK_FILE="$STATE_DIR/.update.lock"
SERVICE="bot"
CONTAINER="usembassy-alerts-bot"
HEALTH_TIMEOUT=180
LOG_TAG="usembassy-alerts-update"
HOST="$(hostname -s)"

FORCE=false
[ "${1:-}" = "--force" ] && FORCE=true

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# Logging function for systemd journal
log_info() {
    echo "INFO: $1" | systemd-cat -t "$LOG_TAG" -p info 2>/dev/null || true
    echo "INFO: $1"
}

log_error() {
    echo "ERROR: $1" | systemd-cat -t "$LOG_TAG" -p err 2>/dev/null || true
    echo "ERROR: $1" >&2
}

log_warning() {
    echo "WARNING: $1" | systemd-cat -t "$LOG_TAG" -p warning 2>/dev/null || true
    echo "WARNING: $1"
}

# Reads a single variable from .env without sourcing the whole file
read_env_var() {
    [ -f "$ENV_FILE" ] || return 0
    grep -E "^$1=" "$ENV_FILE" | tail -n1 | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//' || true
}

html_escape() {
    sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'
}

MONITORING_BOT_TOKEN="${MONITORING_BOT_TOKEN:-$(read_env_var MONITORING_BOT_TOKEN)}"
MONITORING_CHAT_ID="${MONITORING_CHAT_ID:-$(read_env_var MONITORING_CHAT_ID)}"

# Sends a message to the monitoring Telegram bot. Level: ok | warning | error
send_notification() {
    local message="$1"
    local level="${2:-ok}"

    if [ -z "$MONITORING_BOT_TOKEN" ] || [ -z "$MONITORING_CHAT_ID" ]; then
        log_warning "MONITORING_BOT_TOKEN/MONITORING_CHAT_ID not set. Skipping notification."
        return 0
    fi

    local emoji="🚀"
    case "$level" in
        warning) emoji="⚠️" ;;
        error) emoji="❌" ;;
    esac

    local text
    text="$emoji <b>US Embassy Alerts</b> · <code>$HOST</code>"$'\n\n'"$message"
    # Telegram limit is 4096 chars
    text="${text:0:4000}"

    local response_file="$TMP_DIR/telegram_response.txt"
    local http_code
    if ! http_code=$(curl -sS -o "$response_file" -w '%{http_code}' \
        --connect-timeout 10 --max-time 30 \
        --data-urlencode "chat_id=$MONITORING_CHAT_ID" \
        --data-urlencode "text=$text" \
        -d "parse_mode=HTML" \
        -d "disable_web_page_preview=true" \
        "https://api.telegram.org/bot$MONITORING_BOT_TOKEN/sendMessage"); then
        log_error "Failed to send Telegram notification (curl failed)"
        return 0
    fi

    if [ "$http_code" = "200" ]; then
        log_info "Telegram notification sent"
    else
        log_error "Failed to send Telegram notification (HTTP $http_code): $(cat "$response_file")"
    fi
}

# Logs, notifies and exits. Second argument is optional details (e.g. log tail)
fail() {
    local reason="$1"
    local details="${2:-}"
    trap - ERR
    log_error "$reason"
    local message="<b>Update FAILED</b>"$'\n'"$(html_escape <<<"$reason")"
    if [ -n "$details" ]; then
        message+=$'\n\n'"<pre>$(tail -c 2500 <<<"$details" | html_escape)</pre>"
    fi
    send_notification "$message" error
    exit 1
}

CURRENT_STEP="init"
error_handler() {
    local exit_code=$?
    local line_number=$1
    fail "Unexpected error at line $line_number (step: $CURRENT_STEP, exit code $exit_code)"
}
trap 'error_handler $LINENO' ERR

short_id() {
    local id="${1#sha256:}"
    echo "${id:0:12}"
}

image_id() {
    docker image inspect -f '{{.Id}}' "$1" 2>/dev/null || echo "none"
}

container_image_id() {
    docker inspect -f '{{.Image}}' "$CONTAINER" 2>/dev/null || echo "none"
}

# Waits until the container reports healthy. Returns 1 on timeout or crash.
wait_healthy() {
    local deadline=$((SECONDS + HEALTH_TIMEOUT))
    local state health
    while [ "$SECONDS" -lt "$deadline" ]; do
        state=$(docker inspect -f '{{.State.Status}}' "$CONTAINER" 2>/dev/null || echo "not_found")
        health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$CONTAINER" 2>/dev/null || echo "none")
        case "$state/$health" in
            running/healthy | running/none) return 0 ;;
            running/*) ;;
            *) log_error "Container state: $state"; return 1 ;;
        esac
        sleep 5
    done
    log_error "Container did not become healthy within ${HEALTH_TIMEOUT}s (health: $health)"
    return 1
}

# --- Main ---

cd "$PROJECT_DIR"

mkdir -p "$STATE_DIR"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    log_warning "Another update is already running. Exiting."
    exit 0
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose)
else
    fail "Neither 'docker compose' nor docker-compose found"
fi

IMAGE="$("${COMPOSE[@]}" config --images | head -n1)"
IMAGE="${IMAGE%:latest}"
BASE_IMAGE="$(awk 'toupper($1) == "FROM" { print $2; exit }' Dockerfile)"
[ -n "$IMAGE" ] || fail "Cannot determine image name from compose config"
[ -n "$BASE_IMAGE" ] || fail "Cannot determine base image from Dockerfile"

log_info "Starting update (image: $IMAGE, base: $BASE_IMAGE, force: $FORCE)"

# 1. Base image
CURRENT_STEP="pull $BASE_IMAGE"
old_base=$(image_id "$BASE_IMAGE")
if ! pull_log=$(docker pull "$BASE_IMAGE" 2>&1); then
    fail "Failed to pull base image $BASE_IMAGE" "$pull_log"
fi
new_base=$(image_id "$BASE_IMAGE")
if [ "$old_base" != "$new_base" ]; then
    log_info "Base image updated: $(short_id "$old_base") -> $(short_id "$new_base")"
fi

# 2. Rebuild bot image, keep the current one for rollback
CURRENT_STEP="build $IMAGE"
running_image=$(container_image_id)
if [ "$running_image" != "none" ]; then
    docker tag "$running_image" "$IMAGE:rollback"
fi

build_args=()
if $FORCE; then
    build_args+=(--no-cache)
fi
log_info "Building image"
if ! build_log=$("${COMPOSE[@]}" build "${build_args[@]}" "$SERVICE" 2>&1); then
    fail "Docker build failed" "$build_log"
fi
new_image=$(image_id "$IMAGE")

# 3. Restart if the running container is not on the fresh image
if [ "$running_image" = "$new_image" ] && ! $FORCE; then
    log_info "Image unchanged ($(short_id "$new_image")), container is up to date"
else
    CURRENT_STEP="restart container"
    log_info "Recreating container: $(short_id "$running_image") -> $(short_id "$new_image")"
    if ! up_log=$("${COMPOSE[@]}" up -d --force-recreate "$SERVICE" 2>&1) || ! wait_healthy; then
        logs=$(docker logs --tail 20 "$CONTAINER" 2>&1 || true)
        rollback_status="no previous image to roll back to"
        if [ "$running_image" != "none" ]; then
            log_warning "Rolling back to $(short_id "$running_image")"
            docker tag "$IMAGE:rollback" "$IMAGE:latest"
            if "${COMPOSE[@]}" up -d --force-recreate "$SERVICE" >/dev/null 2>&1 && wait_healthy; then
                rollback_status="rolled back to $(short_id "$running_image"), bot is running"
            else
                rollback_status="ROLLBACK FAILED, bot is down"
            fi
        fi
        fail "New image $(short_id "$new_image") failed to start; $rollback_status" "${up_log:-}"$'\n'"$logs"
    fi

    python_version=$(docker exec "$CONTAINER" python -V 2>&1 || echo "unknown")
    message="<b>Bot updated</b>"$'\n'
    message+="🐳 Image: <code>$(short_id "$running_image")</code> → <code>$(short_id "$new_image")</code>"$'\n'
    if [ "$old_base" != "$new_base" ]; then
        message+="📦 Base <code>$BASE_IMAGE</code>: <code>$(short_id "$old_base")</code> → <code>$(short_id "$new_base")</code>"$'\n'
    fi
    message+="🐍 $(html_escape <<<"$python_version")"$'\n'
    message+="✅ Container is healthy"
    send_notification "$message"
    log_info "Container recreated and healthy"
fi

CURRENT_STEP="cleanup"
docker image prune -f >/dev/null

# 4. Report outdated pinned packages (only when the list changes)
CURRENT_STEP="check outdated packages"
check_script='
import json, re, subprocess
norm = lambda n: re.sub(r"[-_.]+", "-", n).lower()
pins = set()
for line in open("requirements.txt"):
    m = re.match(r"\s*([A-Za-z0-9_.-]+)\s*==", line)
    if m:
        pins.add(norm(m[1]))
out = subprocess.run(
    ["pip", "list", "--outdated", "--format=json", "--disable-pip-version-check"],
    capture_output=True, text=True, check=True,
).stdout
for p in sorted(json.loads(out), key=lambda p: p["name"].lower()):
    if norm(p["name"]) in pins:
        print(p["name"], p["version"], "→", p["latest_version"])
'
if outdated=$(docker run --rm --entrypoint python "$IMAGE" -c "$check_script" 2>"$TMP_DIR/outdated.err"); then
    previous=$(cat "$OUTDATED_STATE" 2>/dev/null || true)
    if [ "$outdated" != "$previous" ]; then
        if [ -n "$outdated" ]; then
            log_info "Outdated packages: $(tr '\n' ';' <<<"$outdated")"
            send_notification "<b>Package updates available</b>"$'\n'"<pre>$(html_escape <<<"$outdated")</pre>"$'\n'"Bump pins in <code>requirements.txt</code> in the repo." warning
        fi
        printf '%s' "$outdated" >"$OUTDATED_STATE"
    else
        log_info "Outdated packages unchanged since last check"
    fi
else
    log_warning "Failed to check outdated packages: $(cat "$TMP_DIR/outdated.err")"
    send_notification "<b>Failed to check outdated packages</b>"$'\n'"<pre>$(tail -c 1500 "$TMP_DIR/outdated.err" | html_escape)</pre>" warning
fi

# 5. Check whether the latest Python minor is supported by pinned packages
CURRENT_STEP="check latest python"
python_minor() {
    docker run --rm --entrypoint python "$1" -c 'import sys; print("%d.%d" % sys.version_info[:2])'
}
if ! latest_log=$(docker pull "$LATEST_BASE" 2>&1); then
    log_warning "Failed to pull $LATEST_BASE: $latest_log"
else
    current_py=$(python_minor "$BASE_IMAGE")
    latest_py=$(python_minor "$LATEST_BASE")
    if [ "$current_py" = "$latest_py" ]; then
        status="current"
    elif docker run --rm -v "$PROJECT_DIR/requirements.txt:/tmp/requirements.txt:ro" "$LATEST_BASE" \
        pip install --dry-run --quiet --no-cache-dir --disable-pip-version-check \
        --root-user-action=ignore -r /tmp/requirements.txt >"$TMP_DIR/latest-python.log" 2>&1; then
        status="supported $latest_py"
    else
        status="unsupported $latest_py"
    fi
    previous=$(cat "$PYTHON_STATE" 2>/dev/null || true)
    log_info "Python in Dockerfile: $current_py, latest: $latest_py ($status)"
    if [ "$status" != "$previous" ]; then
        if [ "${status%% *}" = "supported" ]; then
            send_notification "<b>Python $latest_py is supported by all pinned packages</b>"$'\n'"Bump <code>FROM python:$current_py-slim</code> in <code>Dockerfile</code> in the repo." warning
        fi
        printf '%s' "$status" >"$PYTHON_STATE"
    fi
fi

log_info "Update completed"
