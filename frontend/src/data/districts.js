// Matches the exact 行政區 strings stored in the `facilities.district` column
// in Supabase (verified against the real imported dataset — these are NOT
// suffixed with 區). Order roughly reflects facility density, most first.
export const DISTRICTS = [
  '桃園', '中壢', '八德', '楊梅', '平鎮', '龜山',
  '蘆竹', '大園', '龍潭', '大溪', '新屋', '觀音',
];
