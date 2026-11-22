import { useEffect, useState } from "react";
import InvoiceUploader from "../components/InvoiceUploader.jsx";
import InvoiceResult from "../components/InvoiceResult.jsx";
import EvaluationDashboard from "../components/EvaluationDashboard.jsx";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const FALLBACK_PROMPTS = [
  { id: "p1", name: "P1 · Zero-shot baseline", technique: "Zero-shot", description: "Baseline without examples or role framing." },
  { id: "p2", name: "P2 · Role-based", technique: "Role-based", description: "Tests expert role framing." },
  { id: "p3", name: "P3 · Few-shot", technique: "Few-shot", description: "Uses two synthetic formatting examples." },
  { id: "p4", name: "P4 · Task decomposition", technique: "Task decomposition", description: "Extracts in conceptual passes." },
  { id: "p5", name: "P5 · Constraint-based", technique: "Constraint-based", description: "Emphasizes evidence and no invention." },
  { id: "p6", name: "P6 · Combined candidate", technique: "Combined", description: "Combination; not presumed best." },
];

export default function WorkspacePage() {
  const [prompts, setPrompts] = useState(FALLBACK_PROMPTS);
  const [promptId, setPromptId] = useState("p6");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [evaluation, setEvaluation] = useState(null);
  const [activeTab, setActiveTab] = useState("extract");

  useEffect(() => {
    fetch(`${API}/api/prompts`).then((response) => response.json()).then((data) => data.prompts && setPrompts(data.prompts)).catch(() => {});
    fetch(`${API}/api/evaluation/results`).then((response) => response.json()).then(setEvaluation).catch(() => setEvaluation({ available: false }));
  }, []);

  const processFile = async () => {
    if (!file) { setError("Choose an invoice or receipt to continue."); return; }
    setLoading(true); setError(""); setResult(null);
    const body = new FormData();
    body.append("file", file);
    body.append("prompt_version", promptId);
    try {
      const response = await fetch(`${API}/api/invoices/upload`, { method: "POST", body });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Processing failed.");
      setResult(data);
    } catch (exception) {
      setError(exception.message || "Cannot reach the API. Start the FastAPI backend on port 8000.");
    } finally { setLoading(false); }
  };

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand-mark">C11<span>AI</span></div>
        <div className="brand-copy"><strong>Invoice Intelligence</strong><small>DOCUMENT RESEARCH WORKSPACE</small></div>
        <div className="side-rule" />
        <p className="side-caption">WORKSPACE</p>
        <button className={`side-link ${activeTab === "extract" ? "selected" : ""}`} onClick={() => setActiveTab("extract")}><span>↗</span> Extract invoice</button>
        <button className={`side-link ${activeTab === "evaluation" ? "selected" : ""}`} onClick={() => setActiveTab("evaluation")}><span>▥</span> Prompt evaluation</button>
        <div className="sidebar-foot"><i /> Gemini first · Ollama fallback<br /><small>Human review required</small></div>
      </aside>
      <main className="main-content">
        <header className="topbar"><span>Workspace <b>/</b> {activeTab === "extract" ? "Invoice extraction" : "Prompt evaluation"}</span><div className="api-pill"><i /> Gemini · Ollama fallback</div></header>
        <div className="page-wrap">
          <section className="hero-row"><div><p className="eyebrow">C11 · PROMPT ENGINEERING STUDY</p><h1>{activeTab === "extract" ? "Invoice intelligence" : "Prompt evaluation"}</h1><p className="subhead">{activeTab === "extract" ? "Turn invoice documents into structured, reviewable data." : "Compare prompt strategies on the same fixed pilot dataset."}</p></div><div className="hero-badge"><span>01</span><small>EXTRACT<br />& REVIEW</small></div></section>
          {activeTab === "extract" ? <>
            <InvoiceUploader prompts={prompts} promptId={promptId} setPromptId={setPromptId} file={file} setFile={setFile} loading={loading} error={error} setError={setError} onSubmit={processFile} />
            <InvoiceResult result={result} prompts={prompts} />
          </> : <EvaluationDashboard evaluation={evaluation} />}
          <footer className="page-footer">C11 · Invoice Intelligence <span>Prompt performance is measured, never assumed.</span></footer>
        </div>
      </main>
    </div>
  );
}
