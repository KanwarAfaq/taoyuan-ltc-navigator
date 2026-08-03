import { useEffect, useState } from 'react';
import { getFacilityByToken, updateVacancyByToken } from '../api/facilities';

const STATUS_OPTIONS = [
  { value: 'available', label: '有名額', color: 'var(--color-teal)' },
  { value: 'full', label: '已額滿', color: 'var(--color-amber)' },
  { value: 'unknown', label: '暫不提供資訊', color: 'var(--color-sage)' },
];

export default function FacilityUpdatePage({ token }) {
  const [state, setState] = useState('loading'); // loading | not_found | error | ready
  const [facility, setFacility] = useState(null);
  const [saving, setSaving] = useState(false);
  const [savedJustNow, setSavedJustNow] = useState(false);

  useEffect(() => {
    getFacilityByToken(token)
      .then((data) => {
        setFacility(data);
        setState('ready');
      })
      .catch((err) => {
        setState(err.message === 'NOT_FOUND' ? 'not_found' : 'error');
      });
  }, [token]);

  const handleUpdate = async (status) => {
    setSaving(true);
    setSavedJustNow(false);
    try {
      const updated = await updateVacancyByToken(token, status);
      setFacility(updated);
      setSavedJustNow(true);
    } catch (err) {
      setState('error');
    } finally {
      setSaving(false);
    }
  };

  if (state === 'loading') {
    return <CenteredMessage text="載入中..." />;
  }

  if (state === 'not_found') {
    return (
      <CenteredMessage>
        <p className="font-semibold text-lg mb-2">找不到這個連結對應的機構</p>
        <p className="text-ink/60 text-sm">請確認網址是否正確，或聯繫系統管理員。</p>
      </CenteredMessage>
    );
  }

  if (state === 'error') {
    return (
      <CenteredMessage>
        <p className="font-semibold text-lg mb-2">連線發生問題</p>
        <p className="text-ink/60 text-sm">請稍後再試一次。</p>
      </CenteredMessage>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-10">
      <div className="w-full max-w-md">
        <p className="font-display text-sm font-bold mb-2" style={{ color: 'var(--color-amber)' }}>
          機構名額更新
        </p>
        <h1 className="font-display text-2xl font-extrabold mb-1" style={{ color: 'var(--color-teal)' }}>
          {facility.name}
        </h1>
        <p className="text-ink/60 text-sm mb-8">{facility.address}</p>

        <p className="font-semibold mb-3">目前名額狀態：</p>
        <div className="space-y-3 mb-6">
          {STATUS_OPTIONS.map((opt) => {
            const selected = facility.vacancy_status === opt.value;
            return (
              <button
                key={opt.value}
                onClick={() => handleUpdate(opt.value)}
                disabled={saving}
                className="w-full text-left px-5 py-4 rounded-xl border-2 font-semibold transition-colors disabled:opacity-50"
                style={{
                  borderColor: selected ? opt.color : 'var(--color-sage)',
                  backgroundColor: selected ? 'var(--color-sage-light)' : 'white',
                  color: 'var(--color-ink)',
                }}
              >
                {opt.label}
                {selected && <span className="ml-2 text-sm font-normal text-ink/50">（目前狀態）</span>}
              </button>
            );
          })}
        </div>

        {savedJustNow && (
          <p className="text-center text-sm font-medium" style={{ color: 'var(--color-teal)' }}>
            ✅ 已更新
          </p>
        )}

        {facility.vacancy_updated_at && (
          <p className="text-center text-xs text-ink/40 mt-4">
            上次更新：{new Date(facility.vacancy_updated_at).toLocaleString('zh-Hant-TW')}
          </p>
        )}
      </div>
    </div>
  );
}

function CenteredMessage({ text, children }) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center max-w-sm">{text ? <p>{text}</p> : children}</div>
    </div>
  );
}
