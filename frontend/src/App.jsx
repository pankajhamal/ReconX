import { useEffect, useState } from "react";
import { getBatches, getSummary } from "./api";
import Charts from "./components/Charts";
import ResultsTable from "./components/ResultsTable";
import SummaryCards from "./components/SummaryCards";
import UploadPanel from "./components/UploadPanel";

export default function App() {
  const [batches, setBatches] = useState([]);
  const [batchId, setBatchId] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  // Load the list of batches and show the newest one.
  function loadBatches(selectId) {
    getBatches()
      .then((list) => {
        setBatches(list);
        setBatchId(selectId ?? list[0]?.id ?? null);
      })
      .catch(() => setError("Cannot reach the API. Is the backend running?"));
  }

  useEffect(() => loadBatches(), []);

  // Load the summary whenever another batch is selected.
  useEffect(() => {
    if (batchId) getSummary(batchId).then(setSummary);
  }, [batchId]);

  return (
    <main>
      <header>
        <h1>ReconX</h1>
        <p>Financial reconciliation & payment failure detection</p>
      </header>

      {error && <p className="error">{error}</p>}

      <UploadPanel onReconciled={loadBatches} />

      {batchId && summary && (
        <>
          <section className="panel">
            <div className="table-header">
              <h2>2. Results</h2>
              <select value={batchId} onChange={(e) => setBatchId(Number(e.target.value))}>
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>
                    Batch #{b.id} — {new Date(b.created_at).toLocaleString()}
                  </option>
                ))}
              </select>
            </div>
            <SummaryCards summary={summary} />
            <Charts summary={summary} />
          </section>
          <ResultsTable batchId={batchId} />
        </>
      )}
    </main>
  );
}
