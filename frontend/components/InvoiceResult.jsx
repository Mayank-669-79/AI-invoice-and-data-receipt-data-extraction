const FIELD_LABELS = {
  vendor_name: "Vendor", vendor_address: "Vendor address", vendor_gstin: "Vendor tax ID",
  customer_name: "Customer", customer_address: "Customer address", customer_gstin: "Customer tax ID",
  invoice_number: "Invoice number", invoice_date: "Invoice date", due_date: "Due date",
  subtotal: "Subtotal", tax_amount: "Tax", total_amount: "Total", currency: "Currency",
  payment_terms: "Payment terms", description: "Description",
};

export default function InvoiceResult({ result, prompts }) {
  if (!result) return null;
  return (
    <section className="results-area">
      <div className="result-heading"><div><p className="eyebrow">EXTRACTION COMPLETE · {result.extraction_method}</p><h2>Review extracted data</h2></div><div className="result-chips"><span className="prompt-chip">{result.provider} · {result.model}</span><span className="prompt-chip">{prompts.find((prompt) => prompt.id === result.prompt_version)?.name || result.prompt_version}</span></div></div>
      <div className="review-note">AI extraction can be wrong. Verify every value against the original before accounting use.</div>
      {result.warnings?.length > 0 && <div className="warning-list"><strong>Review flags ({result.warnings.length})</strong>{result.warnings.map((warning, index) => <p key={`${warning.code}-${index}`}><span>!</span>{warning.message}</p>)}</div>}
      <div className="data-card"><div className="card-label">INVOICE DETAILS</div><div className="field-grid">{Object.entries(FIELD_LABELS).map(([key, label]) => <div className="field" key={key}><small>{label}</small><strong>{result.invoice_data?.[key] ?? <em>Not identified</em>}</strong></div>)}</div>
        <div className="card-label items-label">LINE ITEMS</div>
        {result.invoice_data?.items?.length ? <div className="table-wrap"><table><thead><tr><th>Description</th><th>Qty</th><th>Unit price</th><th>Amount</th></tr></thead><tbody>{result.invoice_data.items.map((item, index) => <tr key={index}><td>{item.description || "—"}</td><td>{item.quantity ?? "—"}</td><td>{item.unit_price ?? "—"}</td><td>{item.amount ?? "—"}</td></tr>)}</tbody></table></div> : <p className="empty-items">No line items identified.</p>}
      </div>
      <details className="source-details"><summary>Source text and structured JSON</summary><h3>Extracted source text</h3><pre>{result.extracted_text}</pre><h3>JSON response</h3><pre>{JSON.stringify(result.invoice_data, null, 2)}</pre></details>
    </section>
  );
}
