import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import type { GoldDiffPoint } from '../../api/types';
import { formatGold } from '../../utils/formatters';

interface GoldDiffChartProps {
  timeline: GoldDiffPoint[];
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: GoldDiffPoint }>;
  label?: number;
}) {
  if (!active || !payload?.length) return null;
  const data = payload[0].payload;
  const teamPositive = data.team_gold_diff >= 0;
  const playerPositive = data.player_gold_diff >= 0;

  return (
    <div
      className="panel"
      style={{
        padding: '10px 14px',
        fontSize: '12px',
        minWidth: '160px',
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.5)',
      }}
    >
      <p
        className="mb-2 text-xs font-bold uppercase tracking-wider font-display"
        style={{ color: '#c89b3c' }}
      >
        {data.minute}:00
      </p>
      <div className="flex justify-between gap-4" style={{ marginBottom: '4px' }}>
        <span style={{ color: '#7e8a96' }}>Team gold</span>
        <span
          className="tabular-nums"
          style={{
            color: teamPositive ? '#28a745' : '#dc3545',
            fontWeight: 600,
          }}
        >
          {teamPositive ? '+' : ''}
          {formatGold(data.team_gold_diff)}
        </span>
      </div>
      <div className="flex justify-between gap-4">
        <span style={{ color: '#7e8a96' }}>Player gold</span>
        <span
          className="tabular-nums"
          style={{
            color: playerPositive ? '#c89b3c' : '#dc3545',
            fontWeight: 600,
          }}
        >
          {playerPositive ? '+' : ''}
          {formatGold(data.player_gold_diff)}
        </span>
      </div>
    </div>
  );
}

export default function GoldDiffChart({ timeline }: GoldDiffChartProps) {
  if (timeline.length === 0) {
    return (
      <p className="py-8 text-center text-sm" style={{ color: '#7e8a96' }}>
        No gold data available.
      </p>
    );
  }

  // Calculate the percentage position of y=0 for the split gradient
  const goldValues = timeline.map((d) => d.team_gold_diff);
  const maxGold = Math.max(...goldValues, 0);
  const minGold = Math.min(...goldValues, 0);
  const range = maxGold - minGold || 1;
  const zeroPercent = (maxGold / range) * 100;

  return (
    <div
      style={{
        background: 'linear-gradient(180deg, rgba(10, 18, 26, 0.5) 0%, rgba(15, 25, 35, 0.3) 100%)',
        borderRadius: '0.5rem',
        padding: '1rem 0.5rem 0.5rem',
        border: '1px solid rgba(42, 58, 74, 0.3)',
      }}
      role="img"
      aria-label="Gold difference timeline chart showing team and player gold advantage over the course of the match"
    >
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart
          data={timeline}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="teamGoldSplit" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#28a745" stopOpacity={0.35} />
              <stop offset={`${zeroPercent}%`} stopColor="#28a745" stopOpacity={0.05} />
              <stop offset={`${zeroPercent}%`} stopColor="#dc3545" stopOpacity={0.05} />
              <stop offset="100%" stopColor="#dc3545" stopOpacity={0.35} />
            </linearGradient>

            <linearGradient id="playerGold" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#c89b3c" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#c89b3c" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(200, 155, 60, 0.06)"
            vertical={false}
          />

          <XAxis
            dataKey="minute"
            tick={{ fill: '#7e8a96', fontSize: 11 }}
            axisLine={{ stroke: '#2a3a4a' }}
            tickLine={false}
            tickFormatter={(v: number) => `${v}m`}
          />
          <YAxis
            tick={{ fill: '#7e8a96', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => formatGold(v)}
          />

          <Tooltip content={<CustomTooltip />} />

          <ReferenceLine
            y={0}
            stroke="rgba(200, 155, 60, 0.25)"
            strokeWidth={1}
            strokeDasharray="4 4"
          />

          <Area
            type="monotone"
            dataKey="team_gold_diff"
            stroke="#28a745"
            strokeWidth={2}
            fill="url(#teamGoldSplit)"
            dot={false}
            name="Team Gold Diff"
            animationDuration={1200}
            animationEasing="ease-out"
          />
          <Area
            type="monotone"
            dataKey="player_gold_diff"
            stroke="#c89b3c"
            strokeWidth={1.5}
            strokeDasharray="4 2"
            fill="url(#playerGold)"
            dot={false}
            name="Player Gold Diff"
            animationDuration={1500}
            animationEasing="ease-out"
            animationBegin={300}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
