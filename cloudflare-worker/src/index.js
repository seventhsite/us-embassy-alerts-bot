/**
 * Cloudflare Worker — RSS Proxy for US Embassy Alert Bot.
 *
 * Proxies RSS feed requests to *.usembassy.gov bypassing CloudFront WAF
 * which blocks datacenter IPs. Cloudflare Worker IPs are whitelisted by CloudFront.
 *
 * Usage: GET /?url=https://rs.usembassy.gov/category/alert/feed/
 * Auth:  X-Proxy-Key header must match the PROXY_KEY environment variable.
 */

export default {
	async fetch(request, env) {
		// CORS preflight
		if (request.method === "OPTIONS") {
			return new Response(null, { status: 204 });
		}

		// Only allow GET
		if (request.method !== "GET") {
			return jsonError("Method not allowed", 405);
		}

		// Validate API key
		const proxyKey = request.headers.get("X-Proxy-Key");
		if (!env.PROXY_KEY || proxyKey !== env.PROXY_KEY) {
			return jsonError("Unauthorized", 401);
		}

		// Get target URL
		const url = new URL(request.url);
		const targetUrl = url.searchParams.get("url");

		if (!targetUrl) {
			return jsonError("Missing 'url' query parameter", 400);
		}

		// Only allow *.usembassy.gov domains
		let targetHost;
		try {
			targetHost = new URL(targetUrl).hostname;
		} catch {
			return jsonError("Invalid URL", 400);
		}

		if (!targetHost.endsWith(".usembassy.gov")) {
			return jsonError("Only *.usembassy.gov domains are allowed", 403);
		}

		// Fetch the target URL
		try {
			const response = await fetch(targetUrl, {
				headers: {
					"User-Agent":
						"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
					Accept:
						"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
					"Accept-Language": "en-US,en;q=0.9",
				},
				cf: {
					// Cache the response for 5 minutes on Cloudflare edge
					cacheTtl: 300,
					cacheEverything: true,
				},
			});

			const body = await response.text();

			return new Response(body, {
				status: response.status,
				headers: {
					"Content-Type":
						response.headers.get("Content-Type") || "application/xml",
					"X-Proxied-Status": response.status.toString(),
				},
			});
		} catch (err) {
			return jsonError(`Fetch error: ${err.message}`, 502);
		}
	},
};

function jsonError(message, status) {
	return new Response(JSON.stringify({ error: message }), {
		status,
		headers: { "Content-Type": "application/json" },
	});
}
