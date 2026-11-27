import { useState } from "react";
import { runReconciliation, uploadFile } from "../api";

// Upload the two CSV files, then run reconciliation.
export default function UploadPanel({ onReconciled }) {
  const [internalFile, setInternalFile] = useState(null);
  const [providerFile, setProviderFile] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleRun() {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      if (internalFile) {
        const result = await uploadFile("internal", internalFile);
        setMessage(`Internal: ${result.inserted} new rows. `);
      }
      if (providerFile) {
        const result = await uploadFile("provider", providerFile);
        setMessage((text) => text + `Provider: ${result.inserted} new rows. `);
      }
      const summary = await runReconciliation();
      setMessage((text) => text + `Reconciliation batch #${summary.batch_id} finished.`);
      onReconciled(summary.batch_id);
    } catch (err) {
      setError(err.message);
    }
    setBusy(false);
  }

  return (
    <section className="panel">
      <h2>1. Upload and reconcile</h2>
      <div className="upload-row">
        <label>
          Internal transactions CSV
          <input type="file" accept=".csv" onChange={(e) => setInternalFile(e.target.files[0])} />
        </label>
        <label>
          Provider transactions CSV
          <input type="file" accept=".csv" onChange={(e) => setProviderFile(e.target.files[0])} />
        </label>
        <button onClick={handleRun} disabled={busy}>
          {busy ? "Working..." : "Upload & run reconciliation"}
        </button>
      </div>
      <p className="hint">You can also run it without new files to reconcile the data already uploaded.</p>
      {message && <p className="success">{message}</p>}
      {error && <pre className="error">{error}</pre>}
    </section>
  );
}
