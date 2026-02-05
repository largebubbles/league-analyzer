import { useParams, useSearchParams, Link } from 'react-router-dom';
import { useMatchAnalysis } from '../hooks/useMatchAnalysis';
import { formatDuration, formatGold, championIconUrl } from '../utils/formatters';
import type {
  MatchAnalysis,
  TurningPoint,
  ObjectiveEvent,
  KillEvent,
  PlayerPerformance,
} from '../api/types';
import GoldDiffChart from '../components/analysis/GoldDiffChart';

/* ═══════════════════════════ Constants ═══════════════════════════ */

const SEVERITY_STYLES: Record<
  TurningPoint['severity'],
  { bg: string; border: string; text: string; label: string }
> = {
  decisive: {
    bg: 'rgba(200, 155, 60, 0.12)',
    border: '#c89b3c',
    text: '#c89b3c',
    label: 'Decisive',
  },
  major: {
    bg: 'rgba(234, 150, 50, 0.10)',
    border: '#ea9632',
    text: '#ea9632',
    label: 'Major',
  },
  minor: {
    bg: 'rgba(100, 116, 139, 0.10)',
    border: '#64748b',
    text: '#94a3b8',
    label: 'Minor',
  },
};

const OBJECTIVE_ICONS: Record<string, string> = {
  DRAGON: '\u{1F409}',
  BARON: '\u{1F451}',
  HERALD: '\u{1F980}',
  TOWER: '\u{1F3F0}',
  INHIBITOR: '\u{1F6E1}',
  HORDE: '\u{1F41B}',
};

const OBJECTIVE_NAMES: Record<string, string> = {
  DRAGON: 'Dragon',
  BARON: 'Baron Nashor',
  HERALD: 'Rift Herald',
  TOWER: 'Tower',
  INHIBITOR: 'Inhibitor',
  HORDE: 'Void Grubs',
};

const DRAGON_SUB_NAMES: Record<string, string> = {
  FIRE_DRAGON: 'Infernal',
  WATER_DRAGON: 'Ocean',
  EARTH_DRAGON: 'Mountain',
  AIR_DRAGON: 'Cloud',
  HEXTECH_DRAGON: 'Hextech',
  CHEMTECH_DRAGON: 'Chemtech',
  ELDER_DRAGON: 'Elder',
};

/* Hoisted static styles for table cells */
const HEADER_STYLE: React.CSSProperties = {
  color: '#7e8a96',
  padding: '8px 12px',
  fontSize: '11px',
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  textAlign: 'left',
};

const CELL_STYLE: React.CSSProperties = {
  padding: '8px 12px',
  fontSize: '13px',
  color: '#c8d0d9',
  fontVariantNumeric: 'tabular-nums',
};

/* ═══════════════════════════ Small helpers ═══════════════════════════ */

function objectiveIcon(eventType: string): string {
  return OBJECTIVE_ICONS[eventType] || '\u{2694}';
}

function objectiveLabel(event: ObjectiveEvent): string {
  const name = OBJECTIVE_NAMES[event.event_type] || event.event_type;
  if (event.event_type === 'DRAGON' && event.sub_type) {
    const dragonName = DRAGON_SUB_NAMES[event.sub_type] || event.sub_type;
    return `${dragonName} Drake`;
  }
  if (event.sub_type && event.event_type === 'TOWER') {
    return `${event.sub_type} ${name}`;
  }
  return name;
}

/* ═══════════════════════════ Skeleton ═══════════════════════════ */

function AnalysisSkeleton() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="h-10 w-64 skeleton-shimmer" />
      <div className="h-48 skeleton-shimmer" />
      <div className="h-72 skeleton-shimmer" />
      <div className="grid grid-cols-2 gap-6">
        <div className="h-64 skeleton-shimmer" />
        <div className="h-64 skeleton-shimmer" />
      </div>
    </div>
  );
}

/* ═══════════════════════════ Section components ═══════════════════════════ */

function MatchHeader({ analysis }: { analysis: MatchAnalysis }) {
  const win = analysis.win;
  return (
    <div className="flex flex-wrap items-center gap-4">
      <span
        className="rounded-md px-4 py-1.5 text-sm font-extrabold uppercase tracking-wider font-display"
        style={{
          backgroundColor: win ? 'rgba(40, 167, 69, 0.15)' : 'rgba(220, 53, 69, 0.15)',
          color: win ? '#28a745' : '#dc3545',
          border: `1px solid ${win ? '#28a745' : '#dc3545'}`,
        }}
      >
        {win ? 'Victory' : 'Defeat'}
      </span>

      <span className="text-sm font-medium tabular-nums" style={{ color: '#7e8a96' }}>
        {formatDuration(analysis.game_duration_seconds)}
      </span>

      <span
        className="rounded-full px-3 py-0.5 text-xs font-medium tabular-nums"
        style={{ backgroundColor: '#1a2634', color: '#c8d0d9' }}
      >
        Match {analysis.match_id.replace(/^NA1_/, '')}
      </span>
    </div>
  );
}

function SummaryInsight({ text }: { text: string }) {
  return (
    <div
      className="rounded-lg border-l-4 p-5"
      style={{
        borderLeftColor: '#c89b3c',
        backgroundColor: 'rgba(200, 155, 60, 0.06)',
      }}
    >
      <h3
        className="mb-2 text-xs font-bold uppercase tracking-widest font-display"
        style={{ color: '#c89b3c' }}
      >
        Match Insight
      </h3>
      <p className="text-sm leading-relaxed" style={{ color: '#c8d0d9' }}>
        {text}
      </p>
    </div>
  );
}

function TurningPointCards({ points }: { points: TurningPoint[] }) {
  if (points.length === 0) {
    return (
      <p className="py-4 text-center text-sm" style={{ color: '#7e8a96' }}>
        No significant turning points detected.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {points.map((tp) => {
        const s = SEVERITY_STYLES[tp.severity];
        const positive = tp.gold_swing > 0;
        return (
          <div
            key={`tp-${tp.timestamp_ms}-${tp.severity}`}
            className="rounded-lg border p-4"
            style={{ backgroundColor: s.bg, borderColor: s.border }}
          >
            <div className="mb-2 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className="rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase font-display"
                  style={{ backgroundColor: s.border, color: '#0f1923' }}
                >
                  {s.label}
                </span>
                <span className="text-xs font-medium tabular-nums" style={{ color: '#7e8a96' }}>
                  {Math.max(0, tp.minute - 3)}:00 &ndash; {tp.minute}:00
                </span>
              </div>
              <span
                className="text-sm font-bold tabular-nums"
                style={{ color: positive ? '#28a745' : '#dc3545' }}
              >
                {positive ? '+' : ''}
                {formatGold(tp.gold_swing)} gold
              </span>
            </div>
            <p className="text-sm leading-relaxed" style={{ color: '#c8d0d9' }}>
              {tp.insight}
            </p>
            {tp.correlated_events.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {tp.correlated_events.map((evt, j) => (
                  <span
                    key={`${tp.timestamp_ms}-evt-${j}`}
                    className="rounded-full px-2 py-0.5 text-[10px] font-medium"
                    style={{ backgroundColor: '#0f1923', color: '#7e8a96' }}
                  >
                    {evt}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ObjectiveTimeline({ events }: { events: ObjectiveEvent[] }) {
  if (events.length === 0) {
    return (
      <p className="py-4 text-center text-sm" style={{ color: '#7e8a96' }}>
        No objective events recorded.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {events.map((evt) => {
        const isAlly = evt.is_player_team;
        return (
          <div
            key={`obj-${evt.timestamp_ms}-${evt.event_type}`}
            className="timeline-item flex items-center gap-3 rounded-lg border px-4 py-2.5"
            style={{
              backgroundColor: isAlly
                ? 'rgba(40, 167, 69, 0.06)'
                : 'rgba(220, 53, 69, 0.06)',
              borderColor: isAlly
                ? 'rgba(40, 167, 69, 0.20)'
                : 'rgba(220, 53, 69, 0.20)',
            }}
          >
            <span className="text-lg" aria-hidden="true">{objectiveIcon(evt.event_type)}</span>
            <span
              className="min-w-[3rem] text-xs font-medium tabular-nums"
              style={{ color: '#7e8a96' }}
            >
              {evt.minute}:00
            </span>
            <span
              className="text-sm font-medium"
              style={{ color: isAlly ? '#28a745' : '#dc3545' }}
            >
              {isAlly ? 'Your team' : 'Enemy team'}
            </span>
            <span className="text-sm" style={{ color: '#c8d0d9' }}>
              {objectiveLabel(evt)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function KillTimeline({ kills }: { kills: KillEvent[] }) {
  if (kills.length === 0) return null;

  return (
    <div className="space-y-1.5">
      {kills.map((k) => {
        const isAlly = k.is_player_team_kill;
        return (
          <div
            key={`kill-${k.timestamp_ms}-${k.killer_champion}-${k.victim_champion}`}
            className="timeline-item flex items-center gap-3 rounded px-3 py-1.5 text-sm"
            style={{
              backgroundColor: isAlly
                ? 'rgba(40, 167, 69, 0.05)'
                : 'rgba(220, 53, 69, 0.05)',
            }}
          >
            <span
              className="w-12 shrink-0 text-xs font-medium tabular-nums"
              style={{ color: '#7e8a96' }}
            >
              {k.minute}:{String(Math.floor((k.timestamp_ms / 1000) % 60)).padStart(2, '0')}
            </span>
            <span style={{ color: isAlly ? '#28a745' : '#dc3545' }}>
              {k.killer_champion}
            </span>
            <span style={{ color: '#7e8a96' }} aria-hidden="true">&rarr;</span>
            <span style={{ color: isAlly ? '#dc3545' : '#28a745' }}>
              {k.victim_champion}
            </span>
            {k.assisting_champions.length > 0 && (
              <span className="text-xs" style={{ color: '#7e8a96' }}>
                +{k.assisting_champions.length} assist{k.assisting_champions.length > 1 ? 's' : ''}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

function PlayerStatsTable({ players }: { players: PlayerPerformance[] }) {
  const team100 = players.filter((p) => p.team_id === 100);
  const team200 = players.filter((p) => p.team_id === 200);

  function renderRow(p: PlayerPerformance) {
    const highlighted = p.is_player;
    const rowBg = highlighted
      ? 'rgba(200, 155, 60, 0.08)'
      : 'transparent';
    const borderLeft = highlighted ? '3px solid #c89b3c' : '3px solid transparent';

    return (
      <tr
        key={`${p.team_id}-${p.champion_name}`}
        className="table-row-hover"
        style={{ backgroundColor: rowBg, borderLeft }}
      >
        <td style={CELL_STYLE}>
          <div className="flex items-center gap-2">
            <img
              src={championIconUrl(p.champion_name)}
              alt={`${p.champion_name} champion icon`}
              width={28}
              height={28}
              className="h-7 w-7 rounded"
              loading="lazy"
            />
            <span
              className="font-medium"
              style={{ color: highlighted ? '#c89b3c' : '#c8d0d9' }}
            >
              {p.champion_name}
            </span>
          </div>
        </td>
        <td style={CELL_STYLE}>
          {p.kills}/{p.deaths}/{p.assists}
        </td>
        <td style={CELL_STYLE}>{p.cs_per_min.toFixed(1)}</td>
        <td style={CELL_STYLE}>{p.gold_per_min.toFixed(0)}</td>
        <td style={CELL_STYLE}>{(p.damage_share * 100).toFixed(1)}%</td>
        <td style={CELL_STYLE}>{p.vision_score}</td>
        <td style={CELL_STYLE}>{(p.kill_participation * 100).toFixed(0)}%</td>
      </tr>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse" style={{ minWidth: '640px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #2a3a4a' }}>
            <th style={HEADER_STYLE}>Champion</th>
            <th style={HEADER_STYLE}>KDA</th>
            <th style={HEADER_STYLE}>CS/min</th>
            <th style={HEADER_STYLE}>Gold/min</th>
            <th style={HEADER_STYLE}>Dmg Share</th>
            <th style={HEADER_STYLE}>Vision</th>
            <th style={HEADER_STYLE}>KP</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td
              colSpan={7}
              className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider font-display"
              style={{ color: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.06)' }}
            >
              Blue Side (Team 1)
            </td>
          </tr>
          {team100.map(renderRow)}

          <tr>
            <td
              colSpan={7}
              style={{ height: '2px', backgroundColor: '#2a3a4a' }}
            />
          </tr>

          <tr>
            <td
              colSpan={7}
              className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider font-display"
              style={{ color: '#dc3545', backgroundColor: 'rgba(220, 53, 69, 0.06)' }}
            >
              Red Side (Team 2)
            </td>
          </tr>
          {team200.map(renderRow)}
        </tbody>
      </table>
    </div>
  );
}

/* ═══════════════════════════ Section wrapper ═══════════════════════════ */

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="panel p-5">
      <h3
        className="mb-4 text-sm font-bold uppercase tracking-wider font-display"
        style={{ color: '#c89b3c' }}
      >
        {title}
      </h3>
      {children}
    </section>
  );
}

/* ═══════════════════════════ Page ═══════════════════════════ */

export default function MatchAnalysisPage() {
  const { matchId = '' } = useParams<{ matchId: string }>();
  const [searchParams] = useSearchParams();
  const puuid = searchParams.get('puuid') ?? '';

  const { data: analysis, isLoading, isError } = useMatchAnalysis(matchId, puuid);

  if (isLoading) {
    return <AnalysisSkeleton />;
  }

  if (isError || !analysis) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
        <div className="panel px-8 py-10 animate-enter">
          <h2 className="mb-2 text-xl font-bold font-display" style={{ color: '#dc3545' }}>
            Analysis Unavailable
          </h2>
          <p className="mb-4 text-sm" style={{ color: '#7e8a96' }}>
            Could not load analysis for match{' '}
            <span className="font-medium" style={{ color: '#c8d0d9' }}>
              {matchId}
            </span>
          </p>
          <Link
            to="/"
            className="btn-gold inline-block rounded-lg px-5 py-2 text-sm font-semibold"
          >
            Back to Search
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="animate-enter delay-1">
        <MatchHeader analysis={analysis} />
      </div>

      <div className="animate-enter delay-2">
        <SummaryInsight text={analysis.summary_insight} />
      </div>

      <hr className="divider-gold" />

      <div className="animate-enter delay-3">
        <Section title="Gold Difference Over Time">
          <GoldDiffChart timeline={analysis.gold_diff_timeline} />
        </Section>
      </div>

      <div className="animate-enter delay-4">
        <div className="grid gap-6 lg:grid-cols-2">
          <Section title="Turning Points">
            <TurningPointCards points={analysis.turning_points} />
          </Section>
          <Section title="Objective Timeline">
            <ObjectiveTimeline events={analysis.objective_events} />
          </Section>
        </div>
      </div>

      <hr className="divider-gold" />

      <div className="animate-enter delay-5">
        <Section title="Kill Timeline">
          <KillTimeline kills={analysis.kill_events} />
        </Section>
      </div>

      <div className="animate-enter delay-6">
        <Section title="Player Performance">
          <PlayerStatsTable players={analysis.player_performance} />
        </Section>
      </div>
    </div>
  );
}
