import { useQuery } from '@tanstack/react-query';
import { api } from '../api/endpoints';

export function useMatchHistory(puuid: string, count = 20) {
  return useQuery({
    queryKey: ['matches', puuid, count],
    queryFn: () => api.getMatchHistory(puuid, count),
    staleTime: 2 * 60 * 1000,
    enabled: !!puuid,
  });
}
