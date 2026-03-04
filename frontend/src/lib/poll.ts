export async function poll<T>(
  fn: () => Promise<T>,
  isDone: (x: T) => boolean,
  {
    intervalMs = 1000,
    timeoutMs = 5 * 60 * 1000,
  }: { intervalMs?: number; timeoutMs?: number } = {}
): Promise<T> {
  const start = Date.now();
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const value = await fn();
    if (isDone(value)) return value;

    if (Date.now() - start > timeoutMs) {
      throw new Error("Polling timed out.");
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}