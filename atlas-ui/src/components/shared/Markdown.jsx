import { Fragment } from "react";
import { parseBlocks } from "../../utils/markdownBlocks";

const INLINE_TOKEN =
  /(`[^`\n]+`)|(\*\*[^*\n]+\*\*)|(__[^_\n]+__)|(\*[^*\n]+\*)|(_[^_\n]+_)|(\[[^\]]+\]\([^)\s]+\))/g;

function renderInline(text, keyPrefix = "i") {
  if (!text) return null;
  const parts = [];
  let lastIdx = 0;
  let i = 0;
  let m;
  INLINE_TOKEN.lastIndex = 0;
  while ((m = INLINE_TOKEN.exec(text)) !== null) {
    if (m.index > lastIdx) {
      parts.push(text.slice(lastIdx, m.index));
    }
    const tok = m[0];
    const k = `${keyPrefix}-${i++}`;
    if (tok.startsWith("`")) {
      parts.push(<code key={k}>{tok.slice(1, -1)}</code>);
    } else if (tok.startsWith("**") || tok.startsWith("__")) {
      parts.push(<strong key={k}>{tok.slice(2, -2)}</strong>);
    } else if (tok.startsWith("*") || tok.startsWith("_")) {
      parts.push(<em key={k}>{tok.slice(1, -1)}</em>);
    } else if (tok.startsWith("[")) {
      const lm = tok.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/);
      if (lm) {
        parts.push(
          <a
            key={k}
            href={lm[2]}
            target="_blank"
            rel="noopener noreferrer"
          >
            {lm[1]}
          </a>
        );
      } else {
        parts.push(tok);
      }
    }
    lastIdx = m.index + m[0].length;
  }
  if (lastIdx < text.length) parts.push(text.slice(lastIdx));
  return parts.map((p, idx) =>
    typeof p === "string" ? <Fragment key={`s-${idx}`}>{p}</Fragment> : p
  );
}

function renderListItem(text, keyPrefix) {
  const task = String(text || "").match(/^\[([\sxX])\]\s+(.*)$/s);
  if (task) {
    const checked = task[1].toLowerCase() === "x";
    return (
      <li
        className={`md-task${checked ? " md-task--done" : ""}`}
        key={keyPrefix}
      >
        <span className="md-task-mark" aria-hidden>
          {checked ? "☑" : "☐"}
        </span>
        {renderInline(task[2].trim(), keyPrefix)}
      </li>
    );
  }
  const labeled = String(text || "").match(/^\*\*([^*]+)\*\*\s*:?\s*(.*)$/s);
  if (labeled) {
    const body = labeled[2].trim();
    return (
      <li key={keyPrefix} className="md-labeled-list-item">
        <span className="md-labeled-list-item-label">{labeled[1].trim()}</span>
        {body ? (
          <span className="md-labeled-list-item-body">
            {renderInline(body, keyPrefix)}
          </span>
        ) : null}
      </li>
    );
  }
  return <li key={keyPrefix}>{renderInline(text, keyPrefix)}</li>;
}

function renderBlock(block, idx) {
  const k = `b-${idx}`;
  switch (block.type) {
    case "heading": {
      const Tag = `h${Math.min(6, Math.max(1, block.level))}`;
      return <Tag key={k}>{renderInline(block.text, k)}</Tag>;
    }
    case "p": {
      const trimmed = block.text.trim();
      const boldOnly = trimmed.match(/^\*\*([^*]+)\*\*\s*$/);
      if (boldOnly) {
        return (
          <h3 key={k} className="md-section-heading">
            {boldOnly[1].trim()}
          </h3>
        );
      }
      const inlineLabel = trimmed.match(/^\*\*([^*]+)\*\*\s*:?\s*(.+)$/s);
      if (inlineLabel?.[2]?.trim()) {
        return (
          <div key={k} className="md-labeled-block">
            <div className="md-labeled-block-label">{inlineLabel[1].trim()}</div>
            <p className="md-labeled-block-body">
              {renderInline(inlineLabel[2].trim(), k)}
            </p>
          </div>
        );
      }
      return (
        <p key={k} className="md-body-paragraph">
          {block.text.split("\n").map((seg, j, arr) => (
            <Fragment key={`l-${j}`}>
              {renderInline(seg, `${k}-${j}`)}
              {j < arr.length - 1 ? <br /> : null}
            </Fragment>
          ))}
        </p>
      );
    }
    case "ul":
      return (
        <ul key={k} className="md-list">
          {block.items.map((it, j) => renderListItem(it, `u-${k}-${j}`))}
        </ul>
      );
    case "ol":
      return (
        <ol key={k} className="md-list">
          {block.items.map((it, j) => renderListItem(it, `o-${k}-${j}`))}
        </ol>
      );
    case "code":
      return (
        <pre key={k}>
          <code>{block.text}</code>
        </pre>
      );
    case "quote":
      return <blockquote key={k}>{renderInline(block.text, k)}</blockquote>;
    case "hr":
      return <hr key={k} />;
    case "table":
      return (
        <table key={k}>
          <thead>
            <tr>
              {block.header.map((h, j) => (
                <th key={`th-${j}`}>{renderInline(h, `${k}-h-${j}`)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, ri) => (
              <tr key={`tr-${ri}`}>
                {row.map((cell, ci) => (
                  <td key={`td-${ri}-${ci}`}>
                    {renderInline(cell, `${k}-${ri}-${ci}`)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    default:
      return null;
  }
}

export default function Markdown({ text, className = "md" }) {
  const blocks = parseBlocks(text || "");
  if (blocks.length === 0) {
    return <div className="empty-state">empty artifact</div>;
  }
  return (
    <div className={className}>{blocks.map((b, i) => renderBlock(b, i))}</div>
  );
}
