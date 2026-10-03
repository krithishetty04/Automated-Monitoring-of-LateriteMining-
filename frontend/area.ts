const HECTARES_TO_ACRES = 2.4710538146717;
export const PERMITTED_AREA_ACRES = 1.8;

export function hectaresToAcres(value: number): number {
  return value * HECTARES_TO_ACRES;
}

export function formatAcres(value: number | null | undefined, decimals = 2): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return formatAcresValue(hectaresToAcres(value), decimals);
}

export function formatAcresValue(value: number, decimals = 2): string {
  return `${value.toFixed(decimals)} ac`;
}

export function formatAreaText(text: string): string {
  return text.replace(/(\d+(?:\.\d+)?)\s*ha\b/gi, (_, hectares: string) =>
    formatAcres(Number(hectares), 3),
  );
}
