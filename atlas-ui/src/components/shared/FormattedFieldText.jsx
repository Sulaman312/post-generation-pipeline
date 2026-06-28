import Markdown from "./Markdown";

/** Renders artifact field copy with full markdown formatting (lists, bold, links). */
export default function FormattedFieldText({ text, className = "" }) {
  const raw = String(text ?? "").trim();
  if (!raw) {
    return <span className="muted">—</span>;
  }
  const cls = ["md", "md--field", className].filter(Boolean).join(" ");
  return <Markdown text={text} className={cls} />;
}
