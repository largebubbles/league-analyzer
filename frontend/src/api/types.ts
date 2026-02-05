export interface SummonerResponse {
  puuid: string;
  game_name: string;
  tag_line: string;
  summoner_level: number;
  profile_icon_id: number;
}

export interface ParticipantSummary {
  puuid: string;
  summoner_name: string;
  champion_name: string;
  champion_id: number;
  team_id: number;
  kills: number;
  deaths: number;
  assists: number;
  total_damage_dealt_to_champions: number;
  gold_earned: number;
  cs: number;
  vision_score: number;
  win: boolean;
}

export interface MatchSummary {
  match_id: string;
  game_duration_seconds: number;
  game_mode: string;
  queue_id: number;
  game_creation: number;
  player: ParticipantSummary;
  participants: ParticipantSummary[];
}

export interface GoldDiffPoint {
  timestamp_ms: number;
  minute: number;
  team_gold_diff: number;
  player_gold_diff: number;
}

export interface ObjectiveEvent {
  timestamp_ms: number;
  minute: number;
  event_type: string;
  sub_type: string | null;
  team_id: number;
  is_player_team: boolean;
}

export interface KillEvent {
  timestamp_ms: number;
  minute: number;
  killer_champion: string;
  victim_champion: string;
  assisting_champions: string[];
  is_player_team_kill: boolean;
  position: { x: number; y: number } | null;
}

export interface TurningPoint {
  timestamp_ms: number;
  minute: number;
  gold_diff_before: number;
  gold_diff_after: number;
  gold_swing: number;
  severity: "minor" | "major" | "decisive";
  correlated_events: string[];
  insight: string;
}

export interface PlayerPerformance {
  champion_name: string;
  team_id: number;
  is_player: boolean;
  kills: number;
  deaths: number;
  assists: number;
  cs_per_min: number;
  gold_per_min: number;
  damage_share: number;
  gold_share: number;
  vision_score: number;
  kill_participation: number;
}

export interface MatchAnalysis {
  match_id: string;
  game_duration_seconds: number;
  win: boolean;
  gold_diff_timeline: GoldDiffPoint[];
  kill_events: KillEvent[];
  objective_events: ObjectiveEvent[];
  turning_points: TurningPoint[];
  player_performance: PlayerPerformance[];
  summary_insight: string;
}
