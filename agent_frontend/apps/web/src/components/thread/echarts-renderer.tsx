"use client";

import { FC, useEffect, useRef } from "react";
import ReactECharts from "echarts-for-react";
import { EChartsOption } from "echarts";

interface EChartsRendererProps {
  option: EChartsOption;
  title?: string;
}

/**
 * Renders an ECharts visualization from an option configuration object
 */
export const EChartsRenderer: FC<EChartsRendererProps> = ({ option, title }) => {
  const chartRef = useRef<ReactECharts>(null);

  useEffect(() => {
    // Resize chart when container size changes
    const handleResize = () => {
      if (chartRef.current) {
        chartRef.current.getEchartsInstance().resize();
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className="bg-background p-6 shadow-sm">
      {title && (
        <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>
      )}
      <ReactECharts
        ref={chartRef}
        option={option}
        style={{ height: "500px", width: "100%" }}
        opts={{ renderer: "canvas" }}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
};

/**
 * Attempts to detect if a JSON object is an ECharts configuration
 * by checking for common ECharts properties
 */
export function isEChartsConfig(obj: any): boolean {
  if (!obj || typeof obj !== "object") return false;

  // Check for common ECharts properties
  const echartsProps = [
    "xAxis",
    "yAxis",
    "series",
    "grid",
    "tooltip",
    "legend",
    "visualMap",
    "dataZoom",
    "timeline",
    "graphic",
    "calendar",
    "radar",
    "parallel",
    "geo",
  ];

  // If the object has any of these properties, it's likely an ECharts config
  return echartsProps.some((prop) => prop in obj);
}

/**
 * Extracts title from ECharts config if present
 */
export function extractChartTitle(config: any): string | undefined {
  if (config?.title?.text) {
    return config.title.text;
  }
  return undefined;
}
