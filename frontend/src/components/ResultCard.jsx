import { RULES_LAST_VERIFIED } from '../data/subsidyRules';

export default function ResultCard({ result, onRestart }) {
  return (
    <div className="w-full max-w-lg mx-auto">
      <h2 className="font-display text-2xl font-extrabold mb-1" style={{ color: 'var(--color-teal)' }}>
        您的試算結果
      </h2>
      <p className="text-sm text-ink/60 mb-6">身分別：{result.householdLabel}</p>

      <div className="rounded-2xl border-2 divide-y-2" style={{ borderColor: 'var(--color-sage)' }}>
        <Row label="每月給付額度上限" value={result.quota} emphasis />
        <Row label="政府補助" value={result.govPay} tone="teal" />
        <Row label="家庭自付額（約）" value={result.selfPay} tone="amber" />
      </div>

      <div className="mt-6 rounded-xl p-4 text-sm leading-relaxed" style={{ backgroundColor: 'var(--color-sage-light)', color: 'var(--color-ink)' }}>
        <p className="font-semibold mb-1">這只是試算，不是核定結果</p>
        <p>
          實際 CMS 需要等級由照顧管理專員到府評估後核定，額度可能與試算不同。
          請撥打長照專線 <strong>1966</strong>（免費）預約評估，或前往鄰近照顧管理中心辦理。
        </p>
        <p className="mt-2 text-xs text-ink/50">試算規則查證日期：{RULES_LAST_VERIFIED}（長照 3.0 分階段上路，金額仍可能調整）</p>
      </div>

      <button
        onClick={onRestart}
        className="mt-6 w-full px-5 py-3 rounded-xl font-bold text-base border-2"
        style={{ borderColor: 'var(--color-teal)', color: 'var(--color-teal)' }}
      >
        重新試算
      </button>
    </div>
  );
}

function Row({ label, value, tone, emphasis }) {
  const color = tone === 'teal' ? 'var(--color-teal)' : tone === 'amber' ? 'var(--color-amber)' : 'var(--color-ink)';
  return (
    <div className="flex items-center justify-between px-5 py-4">
      <span className={`text-sm ${emphasis ? 'font-semibold' : ''}`}>{label}</span>
      <span
        className={`font-display tabular-nums ${emphasis ? 'text-xl font-extrabold' : 'text-lg font-bold'}`}
        style={{ color }}
      >
        NT$ {value.toLocaleString('zh-Hant-TW')}
      </span>
    </div>
  );
}
