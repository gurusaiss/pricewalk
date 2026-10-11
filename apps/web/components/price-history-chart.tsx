"use client";

import { TrendingUp } from "lucide-react";
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

const COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

export type ChartSeries = {
  id: string;
  label: string;
  points: { ts: string; price_paise: number }[];
};

type ChartPoint = { ts: number } & Record<string, number | undefined>;

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name?: string; value?: number; color?: string }[];
  label?: ReactNode;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-popover-foreground">
        {new Date(Number(label)).toLocaleDateString("en-IN", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })}
      </p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-1.5 text-muted-foreground">
          <span className="size-2 rounded-full" style={{ background: entry.color }} />
          <span className="truncate">{entry.name}:</span>
          <span className="font-medium text-popover-foreground">
            {formatRupees(entry.value !== undefined ? Math.round(entry.value * 100) : null)}
          </span>
        </div>
      ))}
    </div>
  );
}

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
      <div className="flex h-64 flex-col items-center justify-center gap-2 rounded-lg border border-dashed text-sm text-muted-foreground">
        <TrendingUp className="size-5 opacity-50" />
        No price history yet. Check back after the next scheduled check.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ left: -12 }}>
        <CartesianGrid strokeDasharray="3 6" className="stroke-border" vertical={false} />
        <XAxis
          dataKey="ts"
          tickFormatter={(ts) =>
            new Date(ts).toLocaleDateString("en-IN", { day: "numeric", month: "short" })
          }
          tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={(v) => `₹${v}`}
          tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
          axisLine={false}
          tickLine={false}
          width={56}
        />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
        {series.map((s, i) => (
          <Line
            key={s.id}
            type="monotone"
            dataKey={s.id}
            name={s.label}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2.25}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
