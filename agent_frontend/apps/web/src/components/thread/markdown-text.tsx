"use client";

import "./markdown-styles.css";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeKatex from "rehype-katex";
import remarkMath from "remark-math";
import { FC, memo, useState } from "react";
import { CheckIcon, CopyIcon } from "lucide-react";
import { SyntaxHighlighter } from "@/components/thread/syntax-highlighter";
import { EChartsRenderer, isEChartsConfig, extractChartTitle } from "@/components/thread/echarts-renderer";

import { TooltipIconButton } from "@/components/thread/tooltip-icon-button";
import { cn } from "@/lib/utils";

import "katex/dist/katex.min.css";

interface CodeHeaderProps {
  language?: string;
  code: string;
}

const useCopyToClipboard = ({
  copiedDuration = 3000,
}: {
  copiedDuration?: number;
} = {}) => {
  const [isCopied, setIsCopied] = useState<boolean>(false);

  const copyToClipboard = (value: string) => {
    if (!value) return;

    navigator.clipboard.writeText(value).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), copiedDuration);
    });
  };

  return { isCopied, copyToClipboard };
};

const CodeHeader: FC<CodeHeaderProps> = ({ language, code }) => {
  const { isCopied, copyToClipboard } = useCopyToClipboard();
  const onCopy = () => {
    if (!code || isCopied) return;
    copyToClipboard(code);
  };

  return (
    <div className="flex items-center justify-between gap-4 rounded-t-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white">
      <span className="lowercase [&>span]:text-xs">{language}</span>
      <TooltipIconButton tooltip="Copy" onClick={onCopy}>
        {!isCopied && <CopyIcon />}
        {isCopied && <CheckIcon />}
      </TooltipIconButton>
    </div>
  );
};

const defaultComponents: any = {
  h1: ({ className, ...props }: { className?: string }) => (
    <h1
      className={cn(
        "mb-8 scroll-m-20 text-4xl font-extrabold tracking-tight last:mb-0",
        className,
      )}
      {...props}
    />
  ),
  h2: ({ className, ...props }: { className?: string }) => (
    <h2
      className={cn(
        "mb-4 mt-8 scroll-m-20 text-3xl font-semibold tracking-tight first:mt-0 last:mb-0",
        className,
      )}
      {...props}
    />
  ),
  h3: ({ className, ...props }: { className?: string }) => (
    <h3
      className={cn(
        "mb-4 mt-6 scroll-m-20 text-2xl font-semibold tracking-tight first:mt-0 last:mb-0",
        className,
      )}
      {...props}
    />
  ),
  h4: ({ className, ...props }: { className?: string }) => (
    <h4
      className={cn(
        "mb-4 mt-6 scroll-m-20 text-xl font-semibold tracking-tight first:mt-0 last:mb-0",
        className,
      )}
      {...props}
    />
  ),
  h5: ({ className, ...props }: { className?: string }) => (
    <h5
      className={cn(
        "my-4 text-lg font-semibold first:mt-0 last:mb-0",
        className,
      )}
      {...props}
    />
  ),
  h6: ({ className, ...props }: { className?: string }) => (
    <h6
      className={cn("my-4 font-semibold first:mt-0 last:mb-0", className)}
      {...props}
    />
  ),
  p: ({ className, ...props }: { className?: string }) => (
    <p
      className={cn("mb-4 mt-0 leading-7 first:mt-0 last:mb-0", className)}
      {...props}
    />
  ),
  a: ({ className, ...props }: { className?: string }) => (
    <a
      className={cn(
        "text-blue-600 hover:text-blue-800 font-medium underline underline-offset-4 hover:underline-offset-2 transition-all",
        className,
      )}
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    />
  ),
  strong: ({ className, ...props }: { className?: string }) => (
    <strong
      className={cn("font-bold text-gray-900", className)}
      {...props}
    />
  ),
  em: ({ className, ...props }: { className?: string }) => (
    <em
      className={cn("italic", className)}
      {...props}
    />
  ),
  blockquote: ({ className, ...props }: { className?: string }) => (
    <blockquote
      className={cn("border-l-4 border-gray-300 pl-4 my-4 italic text-gray-700", className)}
      {...props}
    />
  ),
  ul: ({ className, ...props }: { className?: string }) => (
    <ul
      className={cn("my-4 ml-6 list-disc space-y-2 [&>li]:leading-7", className)}
      {...props}
    />
  ),
  ol: ({ className, ...props }: { className?: string }) => (
    <ol
      className={cn("my-4 ml-6 list-decimal space-y-2 [&>li]:leading-7", className)}
      {...props}
    />
  ),
  li: ({ className, ...props }: { className?: string }) => (
    <li
      className={cn("leading-7", className)}
      {...props}
    />
  ),
  hr: ({ className, ...props }: { className?: string }) => (
    <hr 
      className={cn("my-8 border-t-2 border-gray-200", className)} 
      {...props} 
    />
  ),
  table: ({ className, ...props }: { className?: string }) => (
    <div className="my-6 w-full overflow-x-auto rounded-lg border border-gray-200">
      <table
        className={cn(
          "w-full border-collapse text-sm",
          className,
        )}
        {...props}
      />
    </div>
  ),
  thead: ({ className, ...props }: { className?: string }) => (
    <thead
      className={cn("bg-gray-50", className)}
      {...props}
    />
  ),
  tbody: ({ className, ...props }: { className?: string }) => (
    <tbody
      className={cn("divide-y divide-gray-200", className)}
      {...props}
    />
  ),
  th: ({ className, ...props }: { className?: string }) => (
    <th
      className={cn(
        "px-4 py-3 text-left font-semibold text-gray-900 border-b-2 border-gray-200 [&[align=center]]:text-center [&[align=right]]:text-right",
        className,
      )}
      {...props}
    />
  ),
  td: ({ className, ...props }: { className?: string }) => (
    <td
      className={cn(
        "px-4 py-3 text-left text-gray-700 [&[align=center]]:text-center [&[align=right]]:text-right",
        className,
      )}
      {...props}
    />
  ),
  tr: ({ className, ...props }: { className?: string }) => (
    <tr
      className={cn(
        "hover:bg-gray-50 transition-colors",
        className,
      )}
      {...props}
    />
  ),
  sup: ({ className, ...props }: { className?: string }) => (
    <sup
      className={cn("text-xs [&>a]:no-underline", className)}
      {...props}
    />
  ),
  pre: ({ className, ...props }: { className?: string }) => (
    <pre
      className={cn(
        "my-4 overflow-x-auto rounded-lg bg-zinc-950 p-0 text-sm",
        className,
      )}
      {...props}
    />
  ),
  code: ({
    className,
    children,
    ...props
  }: {
    className?: string;
    children: React.ReactNode;
  }) => {
    const match = /language-(\w+)/.exec(className || "");

    if (match) {
      const language = match[1];
      const code = String(children).replace(/\n$/, "");

      // Try to detect ECharts configuration in JSON code blocks
      if (language === "json") {
        try {
          const parsed = JSON.parse(code);
          if (isEChartsConfig(parsed)) {
            const title = extractChartTitle(parsed);
            return <EChartsRenderer option={parsed} title={title} />;
          }
        } catch (e) {
          // Not valid JSON or not an ECharts config, fall through to normal rendering
        }
      }

      return (
        <div className="my-4">
          <CodeHeader language={language} code={code} />
          <SyntaxHighlighter language={language} className={className}>
            {code}
          </SyntaxHighlighter>
        </div>
      );
    }

    // Inline code
    return (
      <code 
        className={cn(
          "mx-0.5 rounded bg-gray-100 px-1.5 py-0.5 font-mono text-sm font-medium text-gray-800",
          className
        )} 
        {...props}
      >
        {children}
      </code>
    );
  },
};

const MarkdownTextImpl: FC<{ children: string; hideCopyButton?: boolean }> = ({ children, hideCopyButton = false }) => {
  const components = hideCopyButton ? {
    ...defaultComponents,
    code: ({
      className,
      children,
      ...props
    }: {
      className?: string;
      children: React.ReactNode;
    }) => {
      const match = /language-(\w+)/.exec(className || "");

      if (match) {
        const language = match[1];
        const code = String(children).replace(/\n$/, "");

        // Try to detect ECharts configuration in JSON code blocks
        if (language === "json") {
          try {
            const parsed = JSON.parse(code);
            if (isEChartsConfig(parsed)) {
              const title = extractChartTitle(parsed);
              return <EChartsRenderer option={parsed} title={title} />;
            }
          } catch (e) {
            // Not valid JSON or not an ECharts config, fall through to normal rendering
          }
        }

        return (
          <div className="my-4">
            <SyntaxHighlighter language={language} className={className}>
              {code}
            </SyntaxHighlighter>
          </div>
        );
      }

      // Inline code
      return (
        <code 
          className={cn(
            "mx-0.5 rounded bg-gray-100 px-1.5 py-0.5 font-mono text-sm font-medium text-gray-800",
            className
          )} 
          {...props}
        >
          {children}
        </code>
      );
    },
  } : defaultComponents;

  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[
          remarkGfm, 
          [remarkMath, { singleDollarTextMath: false }]
        ]}
        rehypePlugins={[rehypeKatex]}
        components={components}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
};

export const MarkdownText = memo(MarkdownTextImpl);
