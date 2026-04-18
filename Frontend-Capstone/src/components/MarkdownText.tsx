type MarkdownTextProps = {
  content: string;
  className?: string;
};

type MarkdownBlock =
  | { type: "heading"; content: string }
  | { type: "list"; items: string[] }
  | { type: "quote"; lines: string[] }
  | { type: "paragraph"; content: string };

function renderInline(text: string) {
  const parts: Array<{ type: "text" | "bold" | "code"; value: string }> = [];
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let lastIndex = 0;

  for (const match of text.matchAll(pattern)) {
    const [token] = match;
    const index = match.index ?? 0;

    if (index > lastIndex) {
      parts.push({ type: "text", value: text.slice(lastIndex, index) });
    }

    if (token.startsWith("**") && token.endsWith("**")) {
      parts.push({ type: "bold", value: token.slice(2, -2) });
    } else if (token.startsWith("`") && token.endsWith("`")) {
      parts.push({ type: "code", value: token.slice(1, -1) });
    }

    lastIndex = index + token.length;
  }

  if (lastIndex < text.length) {
    parts.push({ type: "text", value: text.slice(lastIndex) });
  }

  return parts.map((part, index) => {
    if (part.type === "bold") {
      return <strong key={`${part.type}-${index}`} className="font-semibold text-slate-950">{part.value}</strong>;
    }
    if (part.type === "code") {
      return (
        <code key={`${part.type}-${index}`} className="rounded bg-slate-100 px-1.5 py-0.5 text-[0.95em] text-slate-800">
          {part.value}
        </code>
      );
    }
    return <span key={`${part.type}-${index}`}>{part.value}</span>;
  });
}

export default function MarkdownText({ content, className = "" }: MarkdownTextProps) {
  const blocks: MarkdownBlock[] = [];
  const lines = content.split(/\r?\n/);
  let currentList: string[] = [];
  let currentQuote: string[] = [];

  const flushList = () => {
    if (currentList.length) {
      blocks.push({ type: "list", items: currentList });
      currentList = [];
    }
  };

  const flushQuote = () => {
    if (currentQuote.length) {
      blocks.push({ type: "quote", lines: currentQuote });
      currentQuote = [];
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushList();
      flushQuote();
      continue;
    }

    if (line.startsWith("### ")) {
      flushList();
      flushQuote();
      blocks.push({ type: "heading", content: line.slice(4).trim() });
      continue;
    }

    if (line.startsWith("- ")) {
      flushQuote();
      currentList.push(line.slice(2).trim());
      continue;
    }

    if (line.startsWith("> ")) {
      flushList();
      currentQuote.push(line.slice(2).trim());
      continue;
    }

    flushList();
    flushQuote();
    blocks.push({ type: "paragraph", content: line });
  }

  flushList();
  flushQuote();

  return (
    <div className={`space-y-4 text-sm leading-7 text-slate-600 ${className}`}>
      {blocks.map((block, index) => {
        if (block.type === "heading") {
          return (
            <h3 key={`${block.type}-${index}`} className="text-lg font-semibold text-slate-950">
              {renderInline(block.content)}
            </h3>
          );
        }

        if (block.type === "list") {
          return (
            <ul key={`${block.type}-${index}`} className="space-y-2">
              {block.items.map((item) => (
                <li key={item} className="flex gap-3">
                  <span className="mt-2 h-2 w-2 rounded-full bg-cyan-600" />
                  <span>{renderInline(item)}</span>
                </li>
              ))}
            </ul>
          );
        }

        if (block.type === "quote") {
          return (
            <div key={`${block.type}-${index}`} className="space-y-3 border-l-2 border-cyan-200 pl-4 italic text-slate-600">
              {block.lines.map((line, lineIndex) => (
                <p key={`${line}-${lineIndex}`}>{renderInline(line)}</p>
              ))}
            </div>
          );
        }

        return <p key={`${block.type}-${index}`}>{renderInline(block.content)}</p>;
      })}
    </div>
  );
}
