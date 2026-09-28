// Доменная логика трекера: боссы, уровни Torment, структура статистики.

export const DEFAULT_BOSSES = [
  "Дурьель",
  "Андариэль",
  "Варшан",
  "Григоль",
  "Зир",
  "Белиал",
  "Мефисто",
  "Баал",
  "Диабло",
];

export const NUM_FIELDS = [
  "runs",
  "myth",
  "mythTal",
  "mythSeal",
  "splBaal",
  "splMeph",
  "splDiablo",
];

const ROMAN = [
  "I", "II", "III", "IV", "V", "VI",
  "VII", "VIII", "IX", "X", "XI", "XII",
];
// [ключ, подпись] для уровней сложности Torment I–XII
export const TORMENTS = ROMAN.map((r, i) => [String(i + 1), "T" + r]);
export const TORMENT_KEYS = TORMENTS.map((t) => t[0]);
export const DEFAULT_TORMENT = "12";

export function newStat() {
  return {
    runs: 0,
    myth: 0,
    mythTal: 0,
    mythSeal: 0,
    splBaal: 0,
    splMeph: 0,
    splDiablo: 0,
  };
}

export function newBoss() {
  const t = {};
  TORMENT_KEYS.forEach((k) => (t[k] = newStat()));
  return { t };
}

// приводим одну запись статистики к полному набору числовых полей
export function normStat(s) {
  if (!s || typeof s !== "object") s = {};
  NUM_FIELDS.forEach((f) => {
    if (typeof s[f] !== "number") s[f] = 0;
  });
  return s;
}

// приводим босса к структуре { t: {1..12: stat} },
// перенося старые «плоские» данные в Torment по умолчанию
export function normBoss(b) {
  if (!b || typeof b !== "object") return newBoss();
  if (!b.t || typeof b.t !== "object") {
    const legacy = normStat({
      runs: b.runs,
      myth: b.myth,
      splBaal: b.splBaal,
      splMeph: b.splMeph,
      splDiablo: b.splDiablo,
    });
    b = { t: {} };
    TORMENT_KEYS.forEach(
      (k) => (b.t[k] = k === DEFAULT_TORMENT ? legacy : newStat())
    );
  } else {
    TORMENT_KEYS.forEach((k) => (b.t[k] = normStat(b.t[k])));
  }
  return b;
}

export function defaultState() {
  const bosses = {};
  DEFAULT_BOSSES.forEach((b) => (bosses[b] = newBoss()));
  return { bosses, current: DEFAULT_BOSSES[0], torment: DEFAULT_TORMENT };
}

// нормализуем произвольный объект состояния (из БД / из файла импорта)
export function normState(raw) {
  let st = raw && typeof raw === "object" && raw.bosses ? raw : defaultState();
  Object.keys(st.bosses).forEach((name) => {
    st.bosses[name] = normBoss(st.bosses[name]);
  });
  if (!TORMENT_KEYS.includes(st.torment)) st.torment = DEFAULT_TORMENT;
  if (!st.bosses[st.current]) st.current = Object.keys(st.bosses)[0];
  return st;
}
