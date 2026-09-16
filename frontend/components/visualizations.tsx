"use client";

import { useMemo, useState } from "react";
import { ArrowRight, RotateCcw } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Visual } from "@/types";

function BinarySearch({ visual }: { visual: Visual }) {
  const values = visual.values;
  const target = values[Math.max(0, values.length - 2)];
  const [step, setStep] = useState(0);
  const stages = useMemo(() => {
    const result: { lo: number; hi: number; mid: number; found: boolean }[] =
      [];
    let lo = 0;
    let hi = values.length - 1;
    while (lo <= hi) {
      const mid = Math.floor((lo + hi) / 2);
      result.push({ lo, hi, mid, found: values[mid] === target });
      if (values[mid] === target) break;
      if (values[mid] < target) lo = mid + 1;
      else hi = mid - 1;
    }
    return result;
  }, [target, values]);
  const stage = stages[Math.min(step, stages.length - 1)];
  if (!stage) return null;
  return (
    <div className="visual-panel binary-visual">
      <div className="visual-top">
        <span>
          FIND <b>{target}</b>
        </span>
        <span>
          {step + 1} / {stages.length} COMPARISONS
        </span>
      </div>
      <div
        className="array"
        style={{
          gridTemplateColumns: `repeat(${values.length}, minmax(0, 1fr))`,
        }}
      >
        {values.map((n, i) => (
          <div
            key={i}
            className={`array-cell ${i < stage.lo || i > stage.hi ? "eliminated" : ""} ${i === stage.mid ? "midpoint" : ""}`}
          >
            <span>{n}</span>
            <small>{i}</small>
          </div>
        ))}
      </div>
      <div className="visual-bottom">
        <p>
          {stage.found
            ? `${target} found. No need to check every item.`
            : `${values[stage.mid]} ${values[stage.mid] < target ? "<" : ">"} ${target}. Keep the ${values[stage.mid] < target ? "right" : "left"} half.`}
        </p>
        <button
          className="text-button"
          onClick={() => setStep(stage.found ? 0 : step + 1)}
        >
          {stage.found ? "Replay" : "Next step"}
          {stage.found ? <RotateCcw size={15} /> : <ArrowRight size={15} />}
        </button>
      </div>
    </div>
  );
}

function VectorVisual({ visual }: { visual: Visual }) {
  const [x, setX] = useState(Math.max(-5, Math.min(5, visual.values[0] ?? 3)));
  const [y, setY] = useState(Math.max(-5, Math.min(5, visual.values[1] ?? 4)));
  const length = Math.sqrt(x * x + y * y);
  const angle = (-Math.atan2(y, x) * 180) / Math.PI;
  return (
    <div className="visual-panel vector-visual">
      <div
        className="vector-grid"
        role="img"
        aria-label={`Vector (${x}, ${y}) with magnitude ${length.toFixed(2)}`}
      >
        <div className="axis-x" />
        <div className="axis-y" />
        <div
          className="vector-line"
          style={{ width: `${length * 8}%`, transform: `rotate(${angle}deg)` }}
        >
          <span />
        </div>
        <span
          className="vector-coordinate"
          style={{ left: `${50 + x * 8}%`, top: `${50 - y * 8}%` }}
        >
          ({x}, {y})
        </span>
        <span className="origin">0</span>
        <span className="axis-label-x">x</span>
        <span className="axis-label-y">y</span>
      </div>
      <div className="vector-inputs">
        <label>
          x{" "}
          <input
            type="range"
            min="-5"
            max="5"
            value={x}
            onChange={(e) => setX(Number(e.target.value))}
          />
          <b>{x}</b>
        </label>
        <label>
          y{" "}
          <input
            type="range"
            min="-5"
            max="5"
            value={y}
            onChange={(e) => setY(Number(e.target.value))}
          />
          <b>{y}</b>
        </label>
        <p>
          Magnitude <b>{length.toFixed(2)}</b>
        </p>
      </div>
    </div>
  );
}

function GrowthVisual() {
  const [n, setN] = useState(32);
  const data = useMemo(
    () =>
      Array.from({ length: 17 }, (_, i) => {
        const x = Math.max(1, Math.round((n * i) / 16));
        return { n: x, linear: x, logarithmic: Math.log2(x) };
      }),
    [n],
  );
  return (
    <div className="visual-panel growth-visual">
      <div className="chart-legend">
        <span className="mint-dot" />
        log₂(n)
        <span className="purple-dot" />n
        <span className="chart-values">
          {Math.log2(n).toFixed(1)} vs {n}
        </span>
      </div>
      <div className="growth-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 8, right: 6, left: -25, bottom: 0 }}
          >
            <CartesianGrid stroke="var(--line)" vertical={false} />
            <XAxis
              dataKey="n"
              tick={{ fill: "var(--muted)", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              minTickGap={40}
            />
            <YAxis
              tick={{ fill: "var(--muted)", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "var(--panel)",
                border: "1px solid var(--line)",
                borderRadius: 12,
              }}
              formatter={(value) =>
                typeof value === "number" ? value.toFixed(1) : value
              }
            />
            <Line
              type="monotone"
              dataKey="linear"
              name="n"
              stroke="#b8a0ed"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="logarithmic"
              name="log₂(n)"
              stroke="#aee6bd"
              strokeWidth={3}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <label className="range-row">
        Input size{" "}
        <input
          type="range"
          min="8"
          max="128"
          step="8"
          value={n}
          onChange={(e) => setN(Number(e.target.value))}
        />
        <b>{n}</b>
      </label>
    </div>
  );
}

function StepsVisual({ visual }: { visual: Visual }) {
  const [step, setStep] = useState(0);
  return (
    <div className="visual-panel steps-visual">
      <span className="eyebrow">
        STEP {step + 1} OF {visual.labels.length}
      </span>
      <div className="step-expression" key={step}>
        {visual.labels[step]}
      </div>
      <div className="visual-bottom">
        <div className="step-dots">
          {visual.labels.map((_, i) => (
            <span key={i} className={i <= step ? "filled" : ""} />
          ))}
        </div>
        <button
          className="text-button"
          onClick={() => setStep((step + 1) % visual.labels.length)}
        >
          {step === visual.labels.length - 1 ? "Replay" : "Next step"}
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}

export function Visualization({ visual }: { visual: Visual }) {
  switch (visual.type) {
    case "array_elimination":
      return <BinarySearch visual={visual} />;
    case "vector":
      return <VectorVisual visual={visual} />;
    case "growth":
      return <GrowthVisual />;
    case "steps":
      return <StepsVisual visual={visual} />;
  }
}
