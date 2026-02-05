import { useState, useRef, useEffect, useMemo, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

const STORAGE_KEY = 'lol-analyzer-recent-searches';
const MAX_RECENT = 10;

interface RecentSearch {
  gameName: string;
  tagLine: string;
}

function getRecentSearches(): RecentSearch[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveRecentSearch(gameName: string, tagLine: string) {
  const searches = getRecentSearches().filter(
    (s) => !(s.gameName.toLowerCase() === gameName.toLowerCase() && s.tagLine.toLowerCase() === tagLine.toLowerCase()),
  );
  searches.unshift({ gameName, tagLine });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(searches.slice(0, MAX_RECENT)));
}

export default function HomePage() {
  const [riotId, setRiotId] = useState('');
  const [error, setError] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>(() => getRecentSearches());
  const navigate = useNavigate();
  const wrapperRef = useRef<HTMLDivElement>(null);

  const inputLower = riotId.trim().toLowerCase();
  const filtered = useMemo(
    () =>
      inputLower
        ? recentSearches.filter((s) => {
            const full = `${s.gameName}#${s.tagLine}`.toLowerCase();
            return full.includes(inputLower);
          })
        : recentSearches,
    [recentSearches, inputLower],
  );

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  function navigateToPlayer(gameName: string, tagLine: string) {
    saveRecentSearch(gameName, tagLine);
    setRecentSearches(getRecentSearches());
    navigate(`/player/${encodeURIComponent(gameName)}/${encodeURIComponent(tagLine)}`);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setShowSuggestions(false);

    const trimmed = riotId.trim();
    if (!trimmed.includes('#')) {
      setError('Please enter a valid Riot ID in the format GameName#TagLine');
      return;
    }

    const hashIndex = trimmed.indexOf('#');
    const gameName = trimmed.slice(0, hashIndex).trim();
    const tagLine = trimmed.slice(hashIndex + 1).trim();

    if (!gameName || !tagLine) {
      setError('Both Game Name and Tag Line are required');
      return;
    }

    navigateToPlayer(gameName, tagLine);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!showSuggestions || filtered.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % filtered.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev <= 0 ? filtered.length - 1 : prev - 1));
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      const s = filtered[selectedIndex];
      navigateToPlayer(s.gameName, s.tagLine);
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center px-4">
      <div className="w-full max-w-lg text-center">
        <h1 className="mb-3 text-5xl font-extrabold tracking-tight text-gold-gradient font-display animate-enter delay-1">
          LoL Match Analyzer
        </h1>

        <p className="mb-10 text-lg font-medium animate-enter delay-2" style={{ color: '#7e8a96' }}>
          Understand why you win or lose
        </p>

        <form onSubmit={handleSubmit} className="space-y-4 animate-enter delay-3">
          <div className="relative" ref={wrapperRef}>
            <label htmlFor="riot-id-input" className="sr-only">
              Riot ID (GameName#TagLine)
            </label>
            <input
              id="riot-id-input"
              type="search"
              name="riot-id"
              value={riotId}
              onChange={(e) => {
                setRiotId(e.target.value);
                setShowSuggestions(true);
                setSelectedIndex(-1);
                if (error) setError('');
              }}
              onFocus={() => setShowSuggestions(true)}
              onKeyDown={handleKeyDown}
              placeholder="GameName#TagLine"
              aria-label="Riot ID in format GameName#TagLine"
              aria-expanded={showSuggestions && filtered.length > 0}
              aria-controls="suggestions-listbox"
              aria-activedescendant={
                selectedIndex >= 0 ? `suggestion-${selectedIndex}` : undefined
              }
              className="w-full rounded-lg border px-5 py-4 text-lg font-medium outline-none placeholder:font-normal"
              style={{
                backgroundColor: '#1a2634',
                borderColor: error ? '#dc3545' : '#2a3a4a',
                color: '#c8d0d9',
              }}
              autoComplete="off"
              spellCheck={false}
            />
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="pointer-events-none absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="#7e8a96"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>

            {showSuggestions && filtered.length > 0 && (
              <div
                id="suggestions-listbox"
                role="listbox"
                aria-label="Recent searches"
                className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border shadow-lg"
                style={{ backgroundColor: '#1a2634', borderColor: '#2a3a4a' }}
              >
                {filtered.map((s, i) => (
                  <button
                    key={`${s.gameName}#${s.tagLine}`}
                    id={`suggestion-${i}`}
                    role="option"
                    aria-selected={i === selectedIndex}
                    type="button"
                    className="flex w-full items-center gap-3 px-5 py-3 text-left transition-colors"
                    style={{
                      backgroundColor: i === selectedIndex ? '#243040' : 'transparent',
                      color: '#c8d0d9',
                    }}
                    onMouseEnter={() => setSelectedIndex(i)}
                    onClick={() => navigateToPlayer(s.gameName, s.tagLine)}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4 shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="#5a6672"
                      strokeWidth={2}
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <span className="text-sm font-medium">{s.gameName}</span>
                    <span className="text-sm" style={{ color: '#5a6672' }}>
                      #{s.tagLine}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {error && (
            <p className="text-sm font-medium" style={{ color: '#dc3545' }} role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="btn-gold w-full rounded-lg px-6 py-3.5 text-base font-bold uppercase tracking-wider font-display"
          >
            Search Player
          </button>
        </form>

        <p className="mt-6 text-sm animate-enter delay-4" style={{ color: '#5a6672' }}>
          Example: Faker#KR1 or Doublelift#NA1
        </p>
      </div>
    </div>
  );
}
