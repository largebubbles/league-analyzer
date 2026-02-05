import { useParams, Link } from 'react-router-dom';
import { useSummoner } from '../hooks/useSummoner';
import { useMatchHistory } from '../hooks/useMatchHistory';
import {
  profileIconUrl,
  formatTimeAgo,
  formatDuration,
  formatKDA,
  kdaRatio,
  queueName,
  championIconUrl,
} from '../utils/formatters';
import type { MatchSummary } from '../api/types';

/* ───────────────────────── Skeleton placeholders ───────────────────────── */

function ProfileSkeleton() {
  return (
    <div className="mx-auto mb-10 flex max-w-3xl items-center gap-6 px-4">
      <div className="h-24 w-24 shrink-0 rounded-full skeleton-shimmer" />
      <div className="flex-1 space-y-3">
        <div className="h-7 w-48 skeleton-shimmer" />
        <div className="h-5 w-32 skeleton-shimmer" />
      </div>
    </div>
  );
}

function MatchCardSkeleton() {
  return (
    <div
      className="rounded-lg border p-4 skeleton-shimmer"
      style={{ borderColor: '#2a3a4a', minHeight: '88px' }}
    />
  );
}

/* ───────────────────────── Match Card component ───────────────────────── */

function MatchCard({ match, puuid }: { match: MatchSummary; puuid: string }) {
  const p = match.player;
  const win = p.win;
  const borderColor = win ? '#28a745' : '#dc3545';
  const accentBg = win ? 'rgba(40, 167, 69, 0.08)' : 'rgba(220, 53, 69, 0.08)';
  const kda = kdaRatio(p.kills, p.deaths, p.assists);

  return (
    <Link
      to={`/match/${match.match_id}?puuid=${puuid}`}
      className={`block rounded-lg border-l-4 card-hover ${win ? 'card-win' : 'card-loss'}`}
      style={{
        borderLeftColor: borderColor,
        backgroundColor: accentBg,
      }}
    >
      <div className="flex items-center gap-4 p-4">
        <img
          src={championIconUrl(p.champion_name)}
          alt={`${p.champion_name} champion icon`}
          width={56}
          height={56}
          className="h-14 w-14 shrink-0 rounded-lg"
          style={{ border: `2px solid ${borderColor}` }}
          loading="lazy"
        />

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <span
              className="text-sm font-bold uppercase font-display"
              style={{ color: win ? '#28a745' : '#dc3545' }}
            >
              {win ? 'Victory' : 'Defeat'}
            </span>
            <span className="text-xs" style={{ color: '#7e8a96' }}>
              {queueName(match.queue_id)}
            </span>
            <span className="text-xs" style={{ color: '#7e8a96' }}>
              {formatDuration(match.game_duration_seconds)}
            </span>
          </div>

          <div className="mt-1 flex items-baseline gap-3">
            <span
              className="text-base font-semibold"
              style={{ color: '#c8d0d9' }}
            >
              {p.champion_name}
            </span>
            <span
              className="text-sm font-medium tabular-nums"
              style={{ color: '#c8d0d9' }}
            >
              {formatKDA(p.kills, p.deaths, p.assists)}
            </span>
            <span
              className="text-xs font-medium tabular-nums"
              style={{
                color:
                  kda === 'Perfect'
                    ? '#c89b3c'
                    : parseFloat(kda) >= 3
                      ? '#28a745'
                      : parseFloat(kda) >= 2
                        ? '#c8d0d9'
                        : '#dc3545',
              }}
            >
              {kda} KDA
            </span>
          </div>

          <div className="mt-1 flex items-center gap-3 text-xs tabular-nums" style={{ color: '#7e8a96' }}>
            <span>{p.cs} CS</span>
            <span>{p.vision_score} Vision</span>
          </div>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-1">
          <span className="text-xs" style={{ color: '#7e8a96' }}>
            {formatTimeAgo(match.game_creation)}
          </span>
          <span
            className="mt-1 text-xs font-medium analyze-arrow"
            style={{ color: '#c89b3c' }}
          >
            Analyze &rarr;
          </span>
        </div>
      </div>
    </Link>
  );
}

/* ───────────────────────── Player Page ───────────────────────── */

export default function PlayerPage() {
  const { gameName = '', tagLine = '' } = useParams<{
    gameName: string;
    tagLine: string;
  }>();

  const decodedGameName = decodeURIComponent(gameName);
  const decodedTagLine = decodeURIComponent(tagLine);

  const {
    data: summoner,
    isLoading: summonerLoading,
    isError: summonerError,
  } = useSummoner(decodedGameName, decodedTagLine);

  const {
    data: matches,
    isLoading: matchesLoading,
    isError: matchesError,
  } = useMatchHistory(summoner?.puuid ?? '');

  if (summonerError) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
        <div className="panel px-8 py-10 animate-enter">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="mx-auto mb-4 h-12 w-12"
            fill="none"
            viewBox="0 0 24 24"
            stroke="#dc3545"
            strokeWidth={1.5}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
            />
          </svg>
          <h2
            className="mb-2 text-xl font-bold font-display"
            style={{ color: '#dc3545' }}
          >
            Player Not Found
          </h2>
          <p className="mb-4 text-sm" style={{ color: '#7e8a96' }}>
            Could not find a summoner with Riot ID{' '}
            <span className="font-medium" style={{ color: '#c8d0d9' }}>
              {decodedGameName}#{decodedTagLine}
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
    <div className="mx-auto max-w-4xl px-4 py-8">
      {/* ── Profile header ── */}
      {summonerLoading ? (
        <ProfileSkeleton />
      ) : summoner ? (
        <div className="mb-10 flex items-center gap-6 animate-enter">
          <div className="relative shrink-0">
            <img
              src={profileIconUrl(summoner.profile_icon_id)}
              alt={`${summoner.game_name}'s profile icon`}
              width={96}
              height={96}
              className="h-24 w-24 rounded-full"
              style={{ border: '3px solid #c89b3c' }}
            />
            <span
              className="absolute -bottom-2 left-1/2 -translate-x-1/2 rounded-full px-3 py-0.5 text-xs font-bold tabular-nums"
              style={{ backgroundColor: '#c89b3c', color: '#0f1923' }}
            >
              {summoner.summoner_level}
            </span>
          </div>

          <div>
            <h1 className="text-3xl font-bold font-display" style={{ color: '#c8d0d9' }}>
              {summoner.game_name}
              <span className="ml-1 text-lg font-normal" style={{ color: '#7e8a96' }}>
                #{summoner.tag_line}
              </span>
            </h1>
            <p className="mt-1 text-sm" style={{ color: '#7e8a96' }}>
              Level {summoner.summoner_level}
            </p>
          </div>
        </div>
      ) : null}

      {/* ── Match history heading ── */}
      <div className="mb-4 flex items-center justify-between animate-enter delay-1">
        <h2 className="text-lg font-semibold font-display" style={{ color: '#c89b3c' }}>
          Match History
        </h2>
        {matches && (
          <span className="text-xs tabular-nums" style={{ color: '#7e8a96' }}>
            {matches.length} recent matches
          </span>
        )}
      </div>

      {/* ── Match list ── */}
      <div className="space-y-3">
        {matchesLoading || summonerLoading ? (
          Array.from({ length: 5 }).map((_, i) => <MatchCardSkeleton key={i} />)
        ) : matchesError ? (
          <div className="panel px-6 py-8 text-center">
            <p className="text-sm" style={{ color: '#dc3545' }}>
              Failed to load match history. Please try again later.
            </p>
          </div>
        ) : matches && matches.length > 0 ? (
          matches.map((match, i) => (
            <div
              key={match.match_id}
              className="animate-enter"
              style={{ animationDelay: `${0.05 + i * 0.04}s` }}
            >
              <MatchCard
                match={match}
                puuid={summoner?.puuid ?? ''}
              />
            </div>
          ))
        ) : (
          <div className="panel px-6 py-8 text-center">
            <p className="text-sm" style={{ color: '#7e8a96' }}>
              No recent matches found.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
