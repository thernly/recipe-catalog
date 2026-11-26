import { formatQuantityUnit } from "#lib/api/shopping-lists.js";
import type { ParsedIngredient } from "#lib/types/index.js";

const UNICODE_FRACTIONS: Record<string, string> = {
  "½": "1/2",
  "⅓": "1/3",
  "⅔": "2/3",
  "¼": "1/4",
  "¾": "3/4",
  "⅛": "1/8",
};
const NUM = String.raw`\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?`;
// "2", "1 1/2", "3/4", "0.5", and ranges: "2-3", "2 to 3"
const LEADING_AMOUNT = new RegExp(
  String.raw`^(${NUM})(?:(\s*(?:-|–|to)\s*)(${NUM}))?`,
);

function toNumber(text: string): number {
  return text
    .trim()
    .split(/\s+/)
    .reduce((sum, part) => {
      const [top, bottom] = part.split("/");
      return sum + (bottom ? Number(top) / Number(bottom) : Number(top));
    }, 0);
}

/** 3, "1 1/2", "2/3"; decimals for amounts written as decimals and for large ones (62.5g). */
function formatAmount(value: number, asDecimal: boolean): string {
  const decimal = String(Math.round(value * 100) / 100);
  if (Number.isInteger(value) || asDecimal || value >= 20) return decimal;
  for (let bottom = 2; bottom <= 16; bottom++) {
    const top = Math.round(value * bottom);
    if (top > 0 && Math.abs(top / bottom - value) < 0.01) {
      const whole = Math.floor(top / bottom);
      const rest = top % bottom;
      return whole ? `${whole} ${rest}/${bottom}` : `${rest}/${bottom}`;
    }
  }
  return decimal;
}

/**
 * An ingredient line with its leading amount multiplied by `factor`; the rest of the
 * line is kept as written.
 *
 * ponytail: only the amount the line starts with is scaled. Amounts later in the line
 * ("2/3 cup (142g) sugar", "juice of 2 lemons") stay as written; the page says so.
 */
export function scaleIngredient(
  raw: string,
  factor: number,
  parsed?: ParsedIngredient,
): string {
  if (factor === 1 || parsed?.header) return raw;
  // "1½ cups" -> "1 1/2 cups"
  const text = raw
    .trim()
    .replace(/[½⅓⅔¼¾⅛]/g, (char) => ` ${UNICODE_FRACTIONS[char]}`)
    .trimStart();
  const match = LEADING_AMOUNT.exec(text);
  if (!match) return raw;

  const [whole, low, separator, high] = match;
  const scaled = (amount: string) =>
    formatAmount(toNumber(amount) * factor, amount.includes("."));
  const last = scaled(high ?? low);
  let rest = text.slice(whole.length);

  // "1 cup" x2 -> "2 cups". Units are stored spelled out and singular, so an
  // abbreviation in the line ("tbsp", "g") never matches and stays as written.
  const unit = parsed?.unit;
  const word = /^(\s*)([A-Za-z]+)\b/.exec(rest);
  if (unit && word) {
    const forms = ["1", "2"].map((n) => formatQuantityUnit(n, unit).slice(2));
    if (forms.includes(word[2].toLowerCase())) {
      const agreed = formatQuantityUnit(last, unit).slice(last.length + 1);
      rest = word[1] + agreed + rest.slice(word[0].length);
    }
  }

  const amount = high ? `${scaled(low)}${separator}${last}` : last;
  return amount + rest;
}
