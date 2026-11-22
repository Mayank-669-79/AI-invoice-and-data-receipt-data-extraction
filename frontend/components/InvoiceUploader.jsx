export default function InvoiceUploader({ prompts, promptId, setPromptId, file, setFile, loading, error, setError, onSubmit }) {
  const chooseFile = (next) => {
    if (!next) return;
    if (next.size > 15 * 1024 * 1024) {
      setError("Maximum file size is 15 MB.");
      setFile(null);
      return;
    }
    setFile(next);
    setError("");
  };

  const selectedPrompt = prompts.find((prompt) => prompt.id === promptId) || prompts.at(-1);
  return (
    <section className="workspace-card">
      <div className="section-top"><div><span className="step">01</span><div><h2>Upload a document</h2><p>PDF, image, or plain text · up to 15 MB</p></div></div><span className="supported">PDF · JPG · PNG · TXT</span></div>
      <label className={`dropzone ${file ? "has-file" : ""}`} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); chooseFile(event.dataTransfer.files?.[0]); }}>
        <input type="file" accept=".pdf,.jpg,.jpeg,.png,.txt,application/pdf,image/jpeg,image/png,text/plain" onChange={(event) => chooseFile(event.target.files?.[0])} />
        <span className="upload-glyph">↑</span>
        <strong>{file ? file.name : "Drop a document here"}</strong>
        <span>{file ? `${(file.size / 1024).toFixed(0)} KB · ready to process` : "or browse files from your device"}</span>
        {!file && <small>Scanned PDFs and images use OCR; text PDFs are read directly</small>}
      </label>
      <div className="prompt-row"><div><label htmlFor="prompt-choice">Prompt configuration</label><small>{selectedPrompt?.description}</small></div><select id="prompt-choice" value={promptId} onChange={(event) => setPromptId(event.target.value)}>{prompts.map((prompt) => <option key={prompt.id} value={prompt.id}>{prompt.name}</option>)}</select></div>
      {error && <div className="error-box" role="alert">{error}</div>}
      <button className="primary-button" disabled={loading || !file} onClick={onSubmit}>{loading ? <><span className="spinner" /> Processing document…</> : <>Extract invoice data <span>→</span></>}</button>
      <p className="privacy-note">Files are processed for this request and are not saved to an invoice history. Auto mode sends extracted text to Gemini first, with local Ollama fallback.</p>
    </section>
  );
}
