"""
Database layer using aiosqlite.

Handles users, subscriptions, and seen-alert tracking.
"""

import logging
from datetime import datetime, timezone

import aiosqlite

from bot.config import DB_PATH

logger = logging.getLogger(__name__)

_db: aiosqlite.Connection | None = None


async def init_db() -> None:
    """Initialize the database connection and create tables if needed."""
    global _db
    _db = await aiosqlite.connect(DB_PATH)
    _db.row_factory = aiosqlite.Row

    await _db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            country_code TEXT    NOT NULL,
            created_at   TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, country_code)
        );

        CREATE TABLE IF NOT EXISTS seen_alerts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            alert_guid   TEXT NOT NULL,
            title        TEXT,
            link         TEXT,
            pub_date     TEXT,
            created_at   TEXT DEFAULT (datetime('now')),
            UNIQUE(country_code, alert_guid)
        );

        CREATE INDEX IF NOT EXISTS idx_subs_user
            ON subscriptions(user_id);
        CREATE INDEX IF NOT EXISTS idx_subs_country
            ON subscriptions(country_code);
        CREATE INDEX IF NOT EXISTS idx_seen_country_guid
            ON seen_alerts(country_code, alert_guid);
    """)
    await _db.commit()
    logger.info("Database initialized at %s", DB_PATH)


async def close_db() -> None:
    """Close the database connection."""
    global _db
    if _db:
        await _db.close()
        _db = None
        logger.info("Database connection closed")


# ── User operations ──────────────────────────────────────────────────


async def upsert_user(
    user_id: int, username: str | None, first_name: str | None
) -> None:
    """Create or update a user record."""
    assert _db is not None
    await _db.execute(
        """
        INSERT INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username   = excluded.username,
            first_name = excluded.first_name
        """,
        (user_id, username, first_name),
    )
    await _db.commit()


# ── Subscription operations ─────────────────────────────────────────


async def get_user_subscriptions(user_id: int) -> list[str]:
    """Return a list of country codes the user is subscribed to."""
    assert _db is not None
    cursor = await _db.execute(
        "SELECT country_code FROM subscriptions WHERE user_id = ? ORDER BY country_code",
        (user_id,),
    )
    rows = await cursor.fetchall()
    return [row["country_code"] for row in rows]


async def get_subscription_count(user_id: int) -> int:
    """Return the number of active subscriptions for a user."""
    assert _db is not None
    cursor = await _db.execute(
        "SELECT COUNT(*) as cnt FROM subscriptions WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    return row["cnt"] if row else 0


async def add_subscription(user_id: int, country_code: str) -> bool:
    """
    Subscribe a user to a country.

    Returns True if newly subscribed, False if already subscribed.
    """
    assert _db is not None
    try:
        await _db.execute(
            "INSERT INTO subscriptions (user_id, country_code) VALUES (?, ?)",
            (user_id, country_code),
        )
        await _db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False


async def remove_subscription(user_id: int, country_code: str) -> bool:
    """
    Unsubscribe a user from a country.

    Returns True if removed, False if was not subscribed.
    """
    assert _db is not None
    cursor = await _db.execute(
        "DELETE FROM subscriptions WHERE user_id = ? AND country_code = ?",
        (user_id, country_code),
    )
    await _db.commit()
    return cursor.rowcount > 0


async def get_subscribers_for_country(country_code: str) -> list[int]:
    """Return a list of user IDs subscribed to a given country."""
    assert _db is not None
    cursor = await _db.execute(
        "SELECT user_id FROM subscriptions WHERE country_code = ?",
        (country_code,),
    )
    rows = await cursor.fetchall()
    return [row["user_id"] for row in rows]


async def get_all_subscribed_countries() -> list[str]:
    """Return distinct country codes that have at least one subscriber."""
    assert _db is not None
    cursor = await _db.execute(
        "SELECT DISTINCT country_code FROM subscriptions ORDER BY country_code"
    )
    rows = await cursor.fetchall()
    return [row["country_code"] for row in rows]


# ── Seen alerts operations ──────────────────────────────────────────


async def is_alert_seen(country_code: str, alert_guid: str) -> bool:
    """Check if an alert has already been processed."""
    assert _db is not None
    cursor = await _db.execute(
        "SELECT 1 FROM seen_alerts WHERE country_code = ? AND alert_guid = ?",
        (country_code, alert_guid),
    )
    return await cursor.fetchone() is not None


async def mark_alert_seen(
    country_code: str,
    alert_guid: str,
    title: str | None = None,
    link: str | None = None,
    pub_date: str | None = None,
) -> bool:
    """
    Mark an alert as seen.

    Returns True if newly inserted, False if already existed.
    """
    assert _db is not None
    try:
        await _db.execute(
            """
            INSERT INTO seen_alerts (country_code, alert_guid, title, link, pub_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (country_code, alert_guid, title, link, pub_date),
        )
        await _db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False


async def get_recent_alerts(
    country_code: str, limit: int = 5
) -> list[dict[str, str | None]]:
    """Return the most recent seen alerts for a country."""
    assert _db is not None
    cursor = await _db.execute(
        """
        SELECT title, link, pub_date
        FROM seen_alerts
        WHERE country_code = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (country_code, limit),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def cleanup_old_alerts(days: int = 90) -> int:
    """Remove alerts older than the specified number of days."""
    assert _db is not None
    cutoff = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    cursor = await _db.execute(
        """
        DELETE FROM seen_alerts
        WHERE created_at < datetime(?, '-' || ? || ' days')
        """,
        (cutoff, days),
    )
    await _db.commit()
    return cursor.rowcount
