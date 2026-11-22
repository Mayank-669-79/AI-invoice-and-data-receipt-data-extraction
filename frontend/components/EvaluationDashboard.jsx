const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function EvaluationDashboard({ evaluation }) {
  return (
    <section className="workspace-card evaluation-card">
      <div className="section-top"><div><span className="step">02</span><div><h2>Measured pilot results</h2><p>All prompts use the same fixed synthetic cases and selected experiment provider.</p></div></div></div>
      {!evaluation?.available ? <div className="empty-evaluation"><div className="empty-mark">◎</div><h3>No experiment results yet</h3><p>Run the six-prompt experiment to generate measured results. By default it makes 300 provider requests (six prompts × 50 examples) and may consume API quota or incur charges.</p><code>python -m experiments.experiment_runner</code><small>Results are synthetic pilot evidence, not generalizable research conclusions.</small></div> : <>
        <div className="evaluation-summary"><span>{evaluation.sample_count} synthetic cases</span><span>Provider/model: {evaluation.provider} · {evaluation.model}</span><span>Dataset: {evaluation.dataset}</span></div>
        <div className="table-wrap"><table><thead><tr><th>Prompt</th><th>Field match</th><th>Record exact</th><th>Item exact</th><th>Valid JSON</th><th>Missing handling</th><th>Unsupported values*</th><th>Latency</th><th>Tokens (in/out)</th></tr></thead><tbody>{evaluation.prompts?.map((prompt) => <tr key={prompt.prompt_id}><td><strong>{prompt.name}</strong></td><td>{percent(prompt.field_accuracy, 1)}</td><td>{percent(prompt.exact_record_accuracy, 0)}</td><td>{percent(prompt.line_item_exact_accuracy, 0)}</td><td>{percent(prompt.valid_json_rate, 0)}</td><td>{percent(prompt.missing_field_handling_accuracy, 0)}</td><td>{percent(prompt.unsupported_field_rate, 1)}</td><td>{Number(prompt.mean_latency_seconds || 0).toFixed(2)} s</td><td>{prompt.input_tokens ?? "—"} / {prompt.output_tokens ?? "—"}</td></tr>)}</tbody></table></div>
        <p className="eval-notice">{evaluation.notice} Unsupported-field rate is a proxy computed from labels absent in ground truth; it is not a fully adjudicated hallucination rate.</p>
        <div className="chart-grid">{[["field_accuracy.png", "Field-level accuracy"], ["record_accuracy.png", "Exact-record accuracy"], ["item_accuracy.png", "Exact line-item match"], ["json_validity.png", "Schema-valid response rate"], ["missing_field_handling.png", "Missing-field handling"], ["unsupported_field_rate.png", "Unsupported-value proxy"], ["mean_latency.png", "Mean model-call latency"], ["token_usage.png", "Input/output token usage"], ["accuracy_vs_tokens.png", "Accuracy vs. total tokens"]].map(([image, label]) => <figure key={image}><img src={`${API}/api/evaluation/plots/${image}`} alt={label} /><figcaption>{label}</figcaption></figure>)}</div>
      </>}
    </section>
  );
}

function percent(value, digits) {
  return value == null || Number.isNaN(Number(value)) ? "—" : `${(Number(value) * 100).toFixed(digits)}%`;
}
