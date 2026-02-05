import { useQuery } from '@tanstack/react-query';
import { api } from '../api/endpoints';

export function useMatchAnalysis(matchId: string, puuid: string) {
  return useQuery({
    queryKey: ['analysis', matchId, puuid],
    queryFn: () => api.getMatchAnalysis(matchId, puuid),
    staleTime: Infinity,
    enabled: !!matchId && !!puuid,
  });
}
