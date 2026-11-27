import { useEffect, useState } from "react";
import { getResults, reportUrl } from "../api";
import { CATEGORIES, PAYMENT_OUTCOMES, formatNPR } from "../format";

const EMPTY_FILTERS = { reference: "", category: "", payment_outcome: "", transaction_date: "" };

export default function ResultsTable({ batchId }) {
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  // Reload whenever the batch or a filter changes.
  useEffect(() => {
    getResults(batchId, filters)
      .then((rows) => {
        setResults(rows);
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [batchId, filters]);

  function setFilter(name, value) {
    setFilters({ ...filters, [name]: value });
  }

  return (
    <section className="panel">
      <div className="table-header">
        <h2>Transactions ({results.length})</h2>
        <a className="button" href={reportUrl(batchId)}>Download CSV report</a>
      </div>

      <div className="filters">
        <input
          placeholder="Reference, e.g. TXN-1005"
          value={filters.reference}
          onChange={(e) => setFilter("reference", e.target.value)}
        />
        <select value={filters.category} onChange={(e) => setFilter("category", e.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
        </select>
        <select value={filters.payment_outcome} onChange={(e) => setFilter("payment_outcome", e.target.value)}>
          <option value="">All payment outcomes</option>
          {PAYMENT_OUTCOMES.map((o) => <option key={o}>{o}</option>)}
        </select>
        <input
          type="date"
          value={filters.transaction_date}
          onChange={(e) => setFilter("transaction_date", e.target.value)}
        />
        <button onClick={() => setFilters(EMPTY_FILTERS)}>Clear</button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Reference</th>
              <th>Date</th>
              <th>Internal amount</th>
              <th>Provider amount</th>
              <th>Difference</th>
              <th>Internal status</th>
              <th>Provider status</th>
              <th>Reconciliation</th>
              <th>Payment outcome</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.reference}>
                <td>{r.reference}</td>
                <td>{r.transaction_date?.slice(0, 10)}</td>
                <td>{formatNPR(r.internal_amount)}</td>
                <td>{formatNPR(r.provider_amount)}</td>
                <td>{r.amount_difference ? formatNPR(r.amount_difference) : ""}</td>
                <td>{r.internal_status || "—"}</td>
                <td>{r.provider_status || "—"}</td>
                <td>
                  {r.category.split(";").map((flag) => (
                    <span key={flag} className={`tag ${flag}`}>{flag}</span>
                  ))}
                </td>
                <td><span className={`tag ${r.payment_outcome}`}>{r.payment_outcome}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
