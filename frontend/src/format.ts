export const formatPercent = (value: number) => `${value.toFixed(2)}%`;
export const localTime = (iso: string) => new Date(iso).toLocaleString();
