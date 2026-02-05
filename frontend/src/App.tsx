import { Component, useEffect, type ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import HomePage from './pages/HomePage';
import PlayerPage from './pages/PlayerPage';
import MatchAnalysisPage from './pages/MatchAnalysisPage';
import { useDDragonVersion } from './hooks/useDDragonVersion';
import { setDDragonVersion } from './utils/formatters';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function DDragonInit() {
  const { data: version } = useDDragonVersion();
  useEffect(() => {
    if (version) setDDragonVersion(version);
  }, [version]);
  return null;
}

/* ── Error Boundary ── */

interface ErrorBoundaryState {
  hasError: boolean;
}

class ErrorBoundary extends Component<
  { children: ReactNode },
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
          <div className="panel px-8 py-10">
            <h2
              className="mb-2 text-xl font-bold font-display"
              style={{ color: '#dc3545' }}
            >
              Something Went Wrong
            </h2>
            <p className="mb-4 text-sm" style={{ color: '#7e8a96' }}>
              An unexpected error occurred. Please try reloading the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="btn-gold rounded-lg px-5 py-2 text-sm font-semibold"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <DDragonInit />
      <BrowserRouter>
        <div className="min-h-screen" style={{ backgroundColor: '#0f1923' }}>
          <header
            className="sticky top-0 z-50 navbar-glow backdrop-blur-sm"
            style={{ backgroundColor: 'rgba(15, 25, 35, 0.9)' }}
          >
            <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
              <Link
                to="/"
                className="flex items-center gap-2 text-xl font-bold tracking-wide text-gold-gradient font-display"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="h-6 w-6"
                  aria-hidden="true"
                  style={{ color: '#c89b3c' }}
                >
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
                LoL Analyzer
              </Link>

              <nav className="flex items-center gap-6">
                <Link
                  to="/"
                  className="nav-link text-sm font-medium"
                  style={{ color: '#c8d0d9' }}
                >
                  Home
                </Link>
              </nav>
            </div>
          </header>

          <main id="main">
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/player/:gameName/:tagLine" element={<PlayerPage />} />
                <Route path="/match/:matchId" element={<MatchAnalysisPage />} />
              </Routes>
            </ErrorBoundary>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
