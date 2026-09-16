"use client";
import { useMemo } from "react";
import katex from "katex";

export function MathBlock({ equation }: { equation: string }) {
  const html = useMemo(
    () =>
      katex.renderToString(equation, {
        throwOnError: false,
        trust: false,
        strict: "ignore",
        displayMode: true,
        maxExpand: 100,
        maxSize: 10,
      }),
    [equation],
  );
  return (
    <div className="math-block" dangerouslySetInnerHTML={{ __html: html }} />
  );
}
