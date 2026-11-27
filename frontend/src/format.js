// Amounts from the API are in paisa (100 paisa = NPR 1).
export function formatNPR(paisa) {
  if (paisa === null || paisa === undefined) return "—";
  const rupees = paisa / 100;
  return "NPR " + rupees.toLocaleString("en-IN", { minimumFractionDigits: 2 });
}

export const CATEGORIES = [
  "MATCHED",
  "PENDING",
  "AMOUNT_MISMATCH",
  "STATUS_MISMATCH",
  "CURRENCY_MISMATCH",
  "MISSING_PROVIDER",
  "MISSING_INTERNAL",
  "DUPLICATE",
];

export const PAYMENT_OUTCOMES = ["SUCCESS", "FAILED", "PENDING", "NEEDS_INVESTIGATION"];
