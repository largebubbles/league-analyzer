import { useQuery } from '@tanstack/react-query';
import { api } from '../api/endpoints';

export function useSummoner(gameName: string, tagLine: string) {
  return useQuery({
    queryKey: ['summoner', gameName, tagLine],
    queryFn: () => api.getSummoner(gameName, tagLine),
    staleTime: 5 * 60 * 1000,
    enabled: !!gameName && !!tagLine,
  });
}
