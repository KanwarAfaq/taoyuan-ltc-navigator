import { useEffect, useState } from 'react';
import { matchFacilities } from '../api/facilities';

const PRECISION_LABEL = {
  address: null, // exact — no caveat needed
  street: null,
  district: '約略位置，實際地點請以電話確認',
};

export default function FacilityMatches({ district }) {
  const [state, setState] = useState('loading'); // loading | error | done
  const [facilities, setFacilities] = useState([]);

  useEffect(() => {
    let cancelled = false;
    setState('loading');

    matchFacilities(district)
      .then((data) => {
        if (cancelled) return;
        setFacilities(data);
        setState('done');
      })
      .catch(() => {
        if (cancelled) return;
        setState('error');
      });

    return () => {
      cancelled = true;
    };
  }, [district]);

  if (state === 'loading') {
    return (
      <div className="text-center py-8 text-ink/60">
        <p>正在搜尋 {district} 的日照中心...</p>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div className="rounded-xl p-4 text-sm" style={{ backgroundColor: 'var(--color-sage-light)' }}>
        <p className="font-semibold mb-1">目前無法載入機構資料</p>
        <p className="text-ink/70">
          可能是後端服務尚未啟動。若您是開發者，請確認 FastAPI 伺服器正在執行中
          （<code className="text-xs bg-white px-1 rounded">uvicorn main:app --reload</code>）。
        </p>
      </div>
    );
  }

  if (facilities.length === 0) {
    return (
      <div className="text-center py-8 text-ink/60">
        <p>{district} 目前沒有符合條件的日照中心資料</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {facilities.map((f) => (
        <div key={f.id} className="rounded-xl border-2 p-4" style={{ borderColor: 'var(--color-sage)' }}>
          <div className="flex items-start justify-between gap-3">
            <h3 className="font-semibold text-base" style={{ color: 'var(--color-teal)' }}>
              {f.name}
            </h3>
            {f.org_type && (
              <span
                className="shrink-0 text-xs px-2 py-1 rounded-full font-medium"
                style={{ backgroundColor: 'var(--color-sage-light)', color: 'var(--color-teal)' }}
              >
                {f.org_type}
              </span>
            )}
          </div>
          <p className="text-sm text-ink/70 mt-1">{f.address}</p>
          {f.phone && (
            <a href={`tel:${f.phone.split(/[#\s]/)[0]}`} className="text-sm font-medium mt-1 inline-block" style={{ color: 'var(--color-amber)' }}>
              📞 {f.phone}
            </a>
          )}
          {PRECISION_LABEL[f.geocode_precision] && (
            <p className="text-xs text-ink/40 mt-2">⚠ {PRECISION_LABEL[f.geocode_precision]}</p>
          )}
        </div>
      ))}
    </div>
  );
}
