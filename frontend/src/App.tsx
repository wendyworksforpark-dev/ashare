import { useMemo, useState, useEffect } from "react";
import { WatchlistView } from "./components/WatchlistView";
import { ControlPanel } from "./components/ControlPanel";
import { SearchBar } from "./components/SearchBar";
import { StockDetail } from "./components/StockDetail";
import { IndexChart } from "./components/IndexChart";
import { RefreshButton } from "./components/RefreshButton";
import { SimulatedPortfolioView } from "./components/SimulatedPortfolioView";
import type { Timeframe } from "./types/timeframe";
import type { MAConfig } from "./types/chartConfig";
import { DEFAULT_MA_CONFIG } from "./types/chartConfig";

const DEFAULT_KLINE_LIMIT = 120;
const KLINE_LIMIT_KEY = "klineLimit";

type ViewMode = "watchlist" | "stock" | "portfolio";

export default function App() {
  const [viewMode, setViewMode] = useState<ViewMode>("watchlist");
  const [selectedStock, setSelectedStock] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState<Timeframe>("day");
  const [maConfig, setMAConfig] = useState<MAConfig>(DEFAULT_MA_CONFIG);
  const [klineLimit, setKlineLimit] = useState<number>(() => {
    const saved = localStorage.getItem(KLINE_LIMIT_KEY);
    return saved ? parseInt(saved, 10) : DEFAULT_KLINE_LIMIT;
  });
  const [history, setHistory] = useState<
    Array<{ viewMode: ViewMode; selectedStock: string | null }>
  >([]);

  useEffect(() => {
    localStorage.setItem(KLINE_LIMIT_KEY, klineLimit.toString());
  }, [klineLimit]);

  const pushHistory = () => {
    setHistory(prev => [...prev, { viewMode, selectedStock }]);
  };

  const handlePortfolioClick = () => {
    pushHistory();
    setViewMode("portfolio");
  };

  const handleStockSelect = (ticker: string) => {
    pushHistory();
    setSelectedStock(ticker);
    setViewMode("stock");
  };

  const handleBackClick = () => {
    setHistory(prev => {
      if (prev.length === 0) {
        setViewMode("watchlist");
        setSelectedStock(null);
        return prev;
      }
      const next = [...prev];
      const last = next.pop()!;
      setViewMode(last.viewMode);
      setSelectedStock(last.selectedStock);
      return next;
    });
  };

  return (
    <div className="app">
      {/* 顶部导航栏 */}
      <header className="app__topbar">
        <div className="app__topbar-left">
          <span className="app__brand-label">A-SHARE MONITOR</span>
          <SearchBar onSelectStock={handleStockSelect} />
        </div>
        <div className="app__topbar-right">
          {viewMode !== "watchlist" && (
            <button className="topbar__button topbar__button--secondary" onClick={handleBackClick}>
              ← 返回
            </button>
          )}
          {viewMode === "watchlist" && (
            <>
              <RefreshButton />
              <button className="topbar__button topbar__button--secondary" onClick={handlePortfolioClick}>
                持仓
              </button>
            </>
          )}
        </div>
      </header>

      {/* 主内容区 */}
      <main className="app__main">
        {/* 指数区：上证(含表格) + 创业板(仅图) + 科创50(仅图) — 始终显示 */}
        <div className="dashboard dashboard--fullwidth">
          <div className="index-row">
            <IndexChart tsCode="000001.SH" maConfig={maConfig} onMAConfigChange={setMAConfig} />
            <IndexChart tsCode="399006.SZ" maConfig={maConfig} onMAConfigChange={setMAConfig} hideIndicators />
            <IndexChart tsCode="000688.SH" maConfig={maConfig} onMAConfigChange={setMAConfig} hideIndicators />
          </div>
        </div>

        {/* 内容区域 */}
        <div className="app__content">
          {viewMode === "watchlist" && (
            <WatchlistView
              maConfig={maConfig}
              onMAConfigChange={setMAConfig}
              onPortfolioClick={handlePortfolioClick}
            />
          )}
          {viewMode === "portfolio" && (
            <SimulatedPortfolioView />
          )}
          {viewMode === "stock" && selectedStock && (
            <StockDetail
              ticker={selectedStock}
              maConfig={maConfig}
              onMAConfigChange={setMAConfig}
              klineLimit={klineLimit}
              onKlineLimitChange={setKlineLimit}
            />
          )}
        </div>
      </main>
    </div>
  );
}
