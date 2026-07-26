// 長照 2.0 / 3.0 補助試算規則
// 資料來源：衛生福利部長期照顧司公告之「照顧及專業服務」給付基準
// 最後查證日期：2026-07-26 — 因應長照 3.0 分階段上路，數值可能異動，
// 正式核定金額仍以 1966 長照專線照顧管理專員評估結果為準。
export const RULES_LAST_VERIFIED = '2026-07-26';

// CMS（照顧管理評估量表）需要等級 2–8 對應每月「照顧及專業服務」給付額度上限（新台幣元）
export const CMS_LEVEL_QUOTA = {
  2: 10020,
  3: 15460,
  4: 18580,
  5: 24100,
  6: 28070,
  7: 32090,
  8: 36180,
};

// 身分別對應之自付比例
export const HOUSEHOLD_COPAY_RATE = {
  low_income: { label: '低收入戶', rate: 0 },
  mid_low_income: { label: '中低收入戶', rate: 0.05 },
  general: { label: '一般戶', rate: 0.16 },
};

export function calculateSubsidy(cmsLevel, householdType) {
  const quota = CMS_LEVEL_QUOTA[cmsLevel];
  const household = HOUSEHOLD_COPAY_RATE[householdType];
  if (!quota || !household) return null;

  const selfPay = Math.round(quota * household.rate);
  const govPay = quota - selfPay;

  return {
    quota,
    selfPay,
    govPay,
    rate: household.rate,
    householdLabel: household.label,
  };
}
