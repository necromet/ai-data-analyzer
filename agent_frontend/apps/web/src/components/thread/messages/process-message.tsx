import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, CheckCircle2, Clock } from "lucide-react";
import { MarkdownText } from "../markdown-text";

interface ProcessSection {
  type: "sql_review" | "execution_success" | "other";
  title: string;
  content: string;
  fullText: string;
}

function parseProcessSections(content: string): ProcessSection[] {
  const sections: ProcessSection[] = [];
  
  // Pattern for SQL Query Ready for Review
  const sqlReviewPattern = /\*\*SQL Query Ready for Review\*\*([\s\S]*?)(?=\*\*SQL Query Ready for Review\*\*|The SQL Query executed successfully!|$)/g;
  
  // Pattern for SQL Query executed successfully
  const executionSuccessPattern = /The SQL Query executed successfully![^\n]*/g;
  
  let match;
  
  // Find all SQL Review sections
  while ((match = sqlReviewPattern.exec(content)) !== null) {
    sections.push({
      type: "sql_review",
      title: "SQL Query Ready for Review",
      content: match[1].trim(),
      fullText: match[0],
    });
  }
  
  // Find all execution success messages
  const successMatches = content.match(executionSuccessPattern);
  if (successMatches) {
    successMatches.forEach((match) => {
      sections.push({
        type: "execution_success",
        title: "SQL Query Executed Successfully",
        content: match.replace("The SQL Query executed successfully!", "").trim(),
        fullText: match,
      });
    });
  }
  
  return sections;
}

export function ProcessMessage({ content }: { content: string }) {
  const sections = parseProcessSections(content);
  
  if (sections.length === 0) {
    return <MarkdownText>{content}</MarkdownText>;
  }
  
  // Split the content and render sections appropriately
  let remainingContent = content;
  const elements: React.ReactElement[] = [];
  
  sections.forEach((section, index) => {
    const sectionIndex = remainingContent.indexOf(section.fullText);
    
    if (sectionIndex > 0) {
      // Render content before this section
      const beforeContent = remainingContent.slice(0, sectionIndex).trim();
      if (beforeContent) {
        elements.push(
          <div key={`before-${index}`} className="py-1">
            <MarkdownText>{beforeContent}</MarkdownText>
          </div>
        );
      }
    }
    
    // Render the collapsible section
    elements.push(
      <CollapsibleProcessSection
        key={`section-${index}`}
        section={section}
        defaultExpanded={index === sections.length - 1}
      />
    );
    
    // Update remaining content
    remainingContent = remainingContent.slice(sectionIndex + section.fullText.length);
  });
  
  // Render any remaining content after all sections
  if (remainingContent.trim()) {
    elements.push(
      <div key="after" className="py-1">
        <MarkdownText>{remainingContent}</MarkdownText>
      </div>
    );
  }
  
  return <div className="flex flex-col gap-2">{elements}</div>;
}

function CollapsibleProcessSection({
  section,
  defaultExpanded = false,
}: {
  section: ProcessSection;
  defaultExpanded?: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  
  const getIcon = () => {
    switch (section.type) {
      case "sql_review":
        return <Clock className="w-4 h-4" />;
      case "execution_success":
        return <CheckCircle2 className="w-4 h-4" />;
      default:
        return null;
    }
  };
  
  const getColorStyle = (): React.CSSProperties => {
    switch (section.type) {
      case "sql_review":
        return {
          borderColor: "var(--color-muted)",
          backgroundColor: "var(--color-muted)",
        };
      case "execution_success":
        return {
          borderColor: "var(--color-muted)",
          backgroundColor: "var(--color-muted)",
        };
      default:
        return {
          borderColor: "var(--color-border)",
          backgroundColor: "var(--color-muted)",
        };
    }
  };
  
  const getHeaderStyle = (): React.CSSProperties => {
    switch (section.type) {
      case "sql_review":
        return { color: "var(--color-primary)" };
      case "execution_success":
        return { color: "var(--color-primary)" };
      default:
        return { color: "var(--destructive)" };
    }
  };
  
  return (
    <div className="border rounded-lg overflow-hidden" style={getColorStyle()}>
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between gap-2 hover:opacity-80 transition-opacity"
        style={getHeaderStyle()}
        initial={{ scale: 1 }}
        whileTap={{ scale: 0.98 }}
      >
        <div className="flex items-center gap-2">
          {getIcon()}
          <span className="font-semibold text-sm">{section.title}</span>
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="w-4 h-4" />
        </motion.div>
      </motion.button>
      
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 py-3 border-t border-current/10">
              <MarkdownText hideCopyButton={true}>{section.content}</MarkdownText>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
