"use client";

import type { ReactNode } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatRupees } from "@/lib/api";

const COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2"];

export type ChartSeries = {
  id: string;
  label: string;
  points: { ts: string; price_paise: number }[];
};

type ChartPoint = { ts: number } & Record<string, number | undefined>;

export function PriceHistoryChart({ series }: { series: ChartSeries[] }) {
  const tsSet = new Set<number>();
  for (const s of series) {
    for (const p of s.points) {
      tsSet.add(new Date(p.ts).getTime());
    }
  }
  const allTs = Array.from(tsSet).sort((a, b) => a - b);

  const data: ChartPoint[] = allTs.map((ts) => {
    const row: ChartPoint = { ts };
    for (const s of series) {
      const match = s.points.find((p) => new Date(p.ts).getTime() === ts);
      if (match) {
        row[s.id] = match.price_paise / 100;
      }
    }
    return row;
  });

  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        No price history yet - check back after the next scheduled check.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis
          dataKey="ts"
          tickFormatter={(ts) => new Date(ts).toLocaleDateString("en-IN")}
          className="text-xs"
        />
        <YAxis tickFormatter={(v) => `₹${v}`} className="text-xs" />
        <Tooltip
          labelFormatter={(ts: ReactNode) => new Date(Number(ts)).toLocaleString("en-IN")}
          formatter={(value: unknown) =>
            formatRupees(typeof value === "number" ? Math.round(value * 100) : null)
          }
        />
        <Legend />
        {series.map((s, i) => (
          <Line
            key={s.id}
            type="monotone"
            dataKey={s.id}
            name={s.label}
            stroke={COLORS[i % COLORS.length]}
            dot={false}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
