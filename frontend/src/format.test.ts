import { describe, expect, it } from 'vitest';
import { formatPercent } from './format';
describe('formatPercent', () => {
  it('preserves the distinction-friendly precision used by the summary', () => expect(formatPercent(73.421)).toBe('73.42%'));
});
