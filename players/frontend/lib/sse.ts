// Minimal Server-Sent Events parser over a fetch ReadableStream.
// Handles multi-chunk buffering, CRLF/LF line endings, multi-line `data:`
// fields (joined with newlines per the SSE spec), and comment lines.

export interface SSEMessage {
  event: string;
  data: string;
}

function parseBlock(raw: string): SSEMessage | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split(/\r?\n/)) {
    if (!line || line.startsWith(":")) continue; // comment / blank
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "event") event = value;
    else if (field === "data") dataLines.push(value);
  }
  if (dataLines.length === 0 && event === "message") return null;
  return { event, data: dataLines.join("\n") };
}

/**
 * Async-iterate SSE messages from a streaming Response body.
 * Events are delimited by a blank line; chunks may split events arbitrarily.
 */
export async function* readSSE(
  body: ReadableStream<Uint8Array>
): AsyncGenerator<SSEMessage> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const drain = function* (final: boolean): Generator<SSEMessage> {
    // Events are separated by a blank line (\n\n or \r\n\r\n).
    for (;;) {
      const match = /\r?\n\r?\n/.exec(buffer);
      if (!match) break;
      const raw = buffer.slice(0, match.index);
      buffer = buffer.slice(match.index + match[0].length);
      const msg = parseBlock(raw);
      if (msg) yield msg;
    }
    if (final && buffer.trim()) {
      const msg = parseBlock(buffer);
      buffer = "";
      if (msg) yield msg;
    }
  };

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      yield* drain(false);
    }
    buffer += decoder.decode();
    yield* drain(true);
  } finally {
    reader.releaseLock();
  }
}

/** Parse a `data:` payload as JSON, returning null on failure. */
export function parseData<T>(msg: SSEMessage): T | null {
  try {
    return JSON.parse(msg.data) as T;
  } catch {
    return null;
  }
}
