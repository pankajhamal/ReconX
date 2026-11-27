import { formatNPR } from "../format";

export default function SummaryCards({ summary }) {
  const cards = [
    { label: "Internal transactions", value: summary.internal_transactions },
    { label: "Provider transactions", value: summary.provider_transactions },
    { label: "Matched", value: summary.matched },
    { label: "Discrepancies", value: summary.discrepancies, warn: true },
    { label: "Failed payments", value: summary.failed_payments, warn: true },
    { label: "Pending payments", value: summary.pending },
    { label: "Amount at risk", value: formatNPR(summary.total_amount_at_risk), warn: true },
  ];

  return (
    <div className="cards">
      {cards.map((card) => (
        <div key={card.label} className={card.warn ? "card warn" : "card"}>
          <div className="card-value">{card.value}</div>
          <div className="card-label">{card.label}</div>
        </div>
      ))}
    </div>
  );
}
