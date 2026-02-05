import { useQuery } from '@tanstack/react-query';
import { api } from '../api/endpoints';

export function useDDragonVersion() {
  return useQuery({
    queryKey: ['ddragon-version'],
    queryFn: async () => {
      const data = await api.getDDragonVersion();
      return data.version;
    },
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}
