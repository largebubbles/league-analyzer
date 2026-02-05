export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function formatGold(gold: number): string {
  if (Math.abs(gold) >= 1000) {
    return `${(gold / 1000).toFixed(1)}k`;
  }
  return gold.toString();
}

export function formatTimeAgo(epochMs: number): string {
  const diff = Date.now() - epochMs;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return 'just now';
}

export function formatKDA(kills: number, deaths: number, assists: number): string {
  return `${kills}/${deaths}/${assists}`;
}

export function kdaRatio(kills: number, deaths: number, assists: number): string {
  if (deaths === 0) return 'Perfect';
  return ((kills + assists) / deaths).toFixed(2);
}

export function championIconUrl(championName: string, version?: string): string {
  const v = version || _cachedVersion;
  return `https://ddragon.leagueoflegends.com/cdn/${v}/img/champion/${championName}.png`;
}

export function profileIconUrl(iconId: number, version?: string): string {
  const v = version || _cachedVersion;
  return `https://ddragon.leagueoflegends.com/cdn/${v}/img/profileicon/${iconId}.png`;
}

let _cachedVersion = '16.3.1';

export function setDDragonVersion(version: string) {
  _cachedVersion = version;
}

const QUEUE_NAMES: Record<number, string> = {
  420: 'Ranked Solo',
  440: 'Ranked Flex',
  400: 'Normal Draft',
  430: 'Normal Blind',
  450: 'ARAM',
  900: 'URF',
};

export function queueName(queueId: number): string {
  return QUEUE_NAMES[queueId] || 'Other';
}
