// Оригинальные простые иконки-глифы для счётчиков (не игровые ассеты).
// Цвета совпадают с цветами счётчиков, чтобы читалось с одного взгляда.

const shard = (color) =>
  `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="${color}"><path d="M13.5 1.5 4 13l6.5 9.5L20 9.5z" opacity=".9"/><path d="M13.5 1.5 20 9.5l-9.5 13z" opacity=".55"/></svg>`;

export const ICONS = {
  // Забеги на босса — череп
  runs: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="#c8aa6e"><path d="M12 2C7.58 2 4 5.36 4 9.5c0 2.29 1.08 4.05 2.5 5.29V17a1 1 0 0 0 1 1h1v-2h1.5v2h1.5v-2h1.5v2H15v-2h1a1 1 0 0 0 1-1v-2.21C18.92 13.55 20 11.79 20 9.5 20 5.36 16.42 2 12 2ZM9 12a1.75 1.75 0 1 1 0-3.5A1.75 1.75 0 0 1 9 12Zm6 0a1.75 1.75 0 1 1 0-3.5A1.75 1.75 0 0 1 15 12Z"/></svg>`,

  // Мифическое обмундирование — гранёный самоцвет
  myth: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="#d97f2b"><path d="M6 3h12l3 5-9 13L3 8z" opacity=".9"/><path d="M3 8h18l-9 13z" opacity=".55"/><path d="M9 3 6 8h12L15 3z" opacity=".7"/></svg>`,

  // Мифические талисманы — табличка-амулет с руной
  mythTal: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="#d94fb0"><path d="M7 2h10a2 2 0 0 1 2 2v13l-7 5-7-5V4a2 2 0 0 1 2-2z" opacity=".85"/><path d="M12 7v6m0 0-2-2m2 2 2-2" stroke="#1a0d16" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`,

  // Мифические печати — восьмиконечная звезда-медальон
  mythSeal: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="#9b6dff"><path d="m12 1 2.3 3 3.6-1 .1 3.7 3.5 1.2-2 3.1 2 3.1-3.5 1.2-.1 3.7-3.6-1L12 23l-2.3-3-3.6 1-.1-3.7L2.5 16l2-3.1-2-3.1 3.5-1.2.1-3.7 3.6 1z"/><circle cx="12" cy="12" r="3.1" fill="#2a1150"/></svg>`,

  // Осколки — кристаллы в цвете каждого босса
  splBaal: shard("#6f9fd0"),
  splMeph: shard("#b57fd9"),
  splDiablo: shard("#d9634f"),
};
