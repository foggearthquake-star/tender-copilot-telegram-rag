type Bucket = {
  count: number;
  resetAt: number;
};

const WINDOW_MS = 15 * 60 * 1000;
const MAX_REQUESTS = 5;
const buckets = new Map<string, Bucket>();

export function checkRateLimit(ip: string) {
  const now = Date.now();
  const entry = buckets.get(ip);

  if (!entry || entry.resetAt < now) {
    buckets.set(ip, {
      count: 1,
      resetAt: now + WINDOW_MS,
    });
    return { ok: true, remaining: MAX_REQUESTS - 1 };
  }

  if (entry.count >= MAX_REQUESTS) {
    return { ok: false, remaining: 0, retryAfterMs: entry.resetAt - now };
  }

  entry.count += 1;
  return { ok: true, remaining: MAX_REQUESTS - entry.count };
}
