// 簽名視覺元素：把「長照給付額度」比喻成一張會逐步顯示額度的悠遊卡。
// 呼應研究資料中「政府每月發的一張數位悠遊卡」說法。
export default function EasyCard({ step, totalSteps, cmsLevel, householdLabel, quota }) {
  const progress = Math.min(step / totalSteps, 1);

  return (
    <div
      className="relative w-full max-w-sm mx-auto rounded-2xl overflow-hidden shadow-xl"
      style={{
        aspectRatio: '1.586',
        background: 'linear-gradient(135deg, var(--color-teal) 0%, var(--color-teal-light) 100%)',
      }}
    >
      {/* progress fill, rises from bottom like a balance loading */}
      <div
        className="absolute inset-x-0 bottom-0 transition-all duration-700 ease-out"
        style={{
          height: `${progress * 100}%`,
          background: 'linear-gradient(0deg, rgba(232,163,61,0.35) 0%, rgba(232,163,61,0.05) 100%)',
        }}
      />

      <div className="relative h-full p-6 flex flex-col justify-between text-paper">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-xs tracking-widest uppercase opacity-70 font-display">長照給付額度卡</p>
            <p className="text-sm mt-1 opacity-90">桃園長照導航 · Taoyuan LTC Navigator</p>
          </div>
          <div
            className="w-10 h-7 rounded-md"
            style={{ background: 'linear-gradient(135deg, var(--color-amber), var(--color-amber-light))' }}
            aria-hidden="true"
          />
        </div>

        <div>
          {cmsLevel ? (
            <p className="text-xs opacity-70 mb-1 font-display">CMS 第 {cmsLevel} 級・{householdLabel}</p>
          ) : (
            <p className="text-xs opacity-70 mb-1 font-display">尚未輸入資料</p>
          )}
          <p className="font-display font-extrabold text-3xl tabular-nums">
            {quota ? `NT$ ${quota.toLocaleString('zh-Hant-TW')}` : '— — —'}
          </p>
          <p className="text-xs opacity-70 mt-1">每月給付額度上限</p>
        </div>
      </div>
    </div>
  );
}
