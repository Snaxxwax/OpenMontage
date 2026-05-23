export const cardStyle = {
  border: "2px solid color-mix(in srgb, var(--accent) 72%, white 12%)",
  background: "rgba(3, 9, 15, 0.78)",
  boxShadow: "0 20px 60px rgba(0,0,0,0.36), inset 0 0 0 1px rgba(255,255,255,0.05)",
  borderRadius: 26,
};

export const labelStyle = {
  color: "var(--accent)",
  letterSpacing: 7,
  textTransform: "uppercase" as const,
  fontSize: 24,
  fontWeight: 800,
};

export function valueText(value: unknown, fallback = ""): string {
  return typeof value === "string" || typeof value === "number" ? String(value) : fallback;
}
