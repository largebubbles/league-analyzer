import { fetchApi } from './client';
import type { SummonerResponse, MatchSummary, MatchAnalysis } from './types';

export const api = {
  getSummoner: (gameName: string, tagLine: string) =>
    fetchApi<SummonerResponse>(`/summoner/${encodeURIComponent(gameName)}/${encodeURIComponent(tagLine)}`),

  getMatchHistory: (puuid: string, count = 20) =>
    fetchApi<MatchSummary[]>(`/matches/${puuid}?count=${count}`),

  getMatchAnalysis: (matchId: string, puuid: string) =>
    fetchApi<MatchAnalysis>(`/analysis/${matchId}?puuid=${puuid}`),

  getDDragonVersion: () =>
    fetchApi<{ version: string }>('/ddragon-version'),
};
