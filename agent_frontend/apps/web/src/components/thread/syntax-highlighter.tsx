import { Light as SyntaxHighlighterHljs } from "react-syntax-highlighter";
import javascript from "react-syntax-highlighter/dist/esm/languages/hljs/javascript";
import typescript from "react-syntax-highlighter/dist/esm/languages/hljs/typescript";
import python from "react-syntax-highlighter/dist/esm/languages/hljs/python";
import sql from "react-syntax-highlighter/dist/esm/languages/hljs/sql";
import { FC } from "react";
import { tomorrowNightBlue } from "react-syntax-highlighter/dist/esm/styles/hljs";

// Register HLJS languages you want to support
SyntaxHighlighterHljs.registerLanguage("javascript", javascript);
SyntaxHighlighterHljs.registerLanguage("js", javascript);
SyntaxHighlighterHljs.registerLanguage("jsx", javascript);
SyntaxHighlighterHljs.registerLanguage("typescript", typescript);
SyntaxHighlighterHljs.registerLanguage("ts", typescript);
SyntaxHighlighterHljs.registerLanguage("tsx", typescript);
SyntaxHighlighterHljs.registerLanguage("python", python);
SyntaxHighlighterHljs.registerLanguage("sql", sql);

interface SyntaxHighlighterProps {
  children: string;
  language: string;
  className?: string;
}

export const SyntaxHighlighter: FC<SyntaxHighlighterProps> = ({
  children,
  language,
  className,
}) => {
  const codeStyle = {
    margin: 0,
    width: "100%",
    height: "100%",
    background: "transparent",
    padding: "1.2rem 1rem",
    ...(language === "sql" && {
      fontFamily:
        '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
    }),
  } as const;

  return (
    <SyntaxHighlighterHljs
      language={language}
      style={tomorrowNightBlue}
      customStyle={codeStyle}
      className={className}
    >
      {children}
    </SyntaxHighlighterHljs>
  );
};
