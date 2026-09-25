// Small helper to open the user's default email client (mailto:) with a
// pre-addressed, pre-filled message. Used by the Students, Counselors and
// Appointments pages so their "Mail" actions go straight to a real email
// instead of an in-app compose page.

export interface MailOptions {
  /** One or more recipient addresses. */
  to: string | Array<string | null | undefined>;
  /** Optional CC recipients. */
  cc?: string | Array<string | null | undefined>;
  subject?: string;
  body?: string;
}

function joinAddresses(
  value?: string | Array<string | null | undefined>,
): string {
  if (!value) return "";
  const list = Array.isArray(value) ? value : [value];
  return list
    .map((a) => (a ?? "").trim())
    .filter((a) => a.length > 0)
    .join(",");
}

/** Build a valid `mailto:` URL with encoded subject/body/cc. */
export function buildMailtoUrl({ to, cc, subject, body }: MailOptions): string {
  const toStr = joinAddresses(to);
  const params: string[] = [];

  const ccStr = joinAddresses(cc);
  if (ccStr) params.push(`cc=${encodeURIComponent(ccStr)}`);
  if (subject) params.push(`subject=${encodeURIComponent(subject)}`);
  if (body) params.push(`body=${encodeURIComponent(body)}`);

  return `mailto:${toStr}${params.length ? `?${params.join("&")}` : ""}`;
}

/**
 * Open the default mail client for the given message.
 * Returns false (and does nothing) when there is no recipient address,
 * so callers can show a helpful message.
 */
export function openMailClient(options: MailOptions): boolean {
  if (!joinAddresses(options.to)) return false;
  window.location.href = buildMailtoUrl(options);
  return true;
}
