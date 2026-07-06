from prometheus_client import Counter, Histogram

AI_TOKEN_USAGE_TOTAL = Counter(
    "ai_token_usage_total",
    "Total number of tokens used by AI models",
    ["model", "operation", "token_type"] # e.g. prompt, completion, total
)

AI_API_COST_TOTAL = Counter(
    "ai_api_cost_total",
    "Total estimated API cost in USD",
    ["model", "operation"]
)

AI_REQUEST_LATENCY_SECONDS = Histogram(
    "ai_request_latency_seconds",
    "Latency of requests to AI models",
    ["model", "operation"]
)
