import { memo, useEffect, useState } from "react";

/** 경과 초를 스스로 갱신하는 작은 시계. 부모를 다시 그리지 않도록 분리한다. */
export const Elapsed = memo(function Elapsed({ since, className = "" }: { since: number; className?: string }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 100);
    return () => window.clearInterval(t);
  }, []);
  return (
    <span className={`tabular-nums ${className}`} aria-live="off">
      {((now - since) / 1000).toFixed(1)}초
    </span>
  );
});
