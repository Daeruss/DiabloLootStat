<script setup>
import { computed, nextTick, reactive, ref, watch } from "vue";
import { api } from "./api";
import {
  TORMENTS,
  TORMENT_KEYS,
  DEFAULT_TORMENT,
  newStat,
  newBoss,
  normState,
  defaultState,
} from "./tracker";

// ── Состояние приложения ──
const user = ref(null); // профиль Telegram или null
const ready = ref(false); // завершилась ли первичная проверка авторизации
const botId = ref("");
const saveStatus = ref("");
const newBossName = ref("");
const importInput = ref(null);
const signingIn = ref(false);
const loginError = ref("");

const state = reactive({ bosses: {}, current: "", torment: DEFAULT_TORMENT });
let loaded = false; // защита от сохранения во время начальной загрузки

// ── Производные данные ──
const bossNames = computed(() => Object.keys(state.bosses));

const curStat = computed(() => {
  const boss = state.bosses[state.current];
  if (!boss) return newStat();
  return boss.t[state.torment];
});

const totalSpl = computed(
  () => curStat.value.splBaal + curStat.value.splMeph + curStat.value.splDiablo
);

const rate = computed(() => {
  const s = curStat.value;
  return s.runs > 0 ? ((s.myth / s.runs) * 100).toFixed(1) + "%" : "—";
});
const rateTal = computed(() => {
  const s = curStat.value;
  return s.runs > 0 ? ((s.mythTal / s.runs) * 100).toFixed(1) + "%" : "—";
});
const rateDetail = computed(() => {
  const s = curStat.value;
  if (s.runs <= 0) return "";
  const splNote = `, ${(totalSpl.value / s.runs).toFixed(2)} осколк(ов) за забег`;
  if (s.myth > 0) {
    const oneIn = (s.runs / s.myth).toFixed(1);
    return `≈ 1 мифик каждые ${oneIn} забег(ов)${splNote}`;
  }
  return `Мификов пока не было${splNote}`;
});

const mainCounters = [
  { type: "runs", title: "Забеги на босса", cls: "", hint: "Нажимай «+» после каждого убийства" },
  { type: "myth", title: "Выпало мификов", cls: "myth", hint: "Мифическое (Uber Unique) обмундирование" },
  { type: "mythTal", title: "Мифические талисманы", cls: "mythtal", hint: "Мифические талисманы" },
];
const splinterCounters = [
  { type: "splBaal", title: "Осколки Баала", cls: "baal" },
  { type: "splMeph", title: "Осколки Мефисто", cls: "meph" },
  { type: "splDiablo", title: "Осколки Диабло", cls: "diablo" },
];

// ── Мутации ──
function inc(type, delta) {
  const boss = state.bosses[state.current];
  if (!boss) return;
  const s = boss.t[state.torment];
  s[type] = Math.max(0, s[type] + delta);
}

function selectTorment(key) {
  state.torment = key;
}

function addBoss() {
  const name = newBossName.value.trim();
  if (!name) return;
  if (state.bosses[name]) {
    alert("Такой босс уже есть");
    return;
  }
  state.bosses[name] = newBoss();
  state.current = name;
  newBossName.value = "";
}

function deleteBoss() {
  if (bossNames.value.length <= 1) {
    alert("Нельзя удалить последнего босса");
    return;
  }
  if (!confirm(`Удалить босса «${state.current}» вместе со статистикой?`)) return;
  delete state.bosses[state.current];
  state.current = Object.keys(state.bosses)[0];
}

function resetCurrent() {
  const label = TORMENTS.find((t) => t[0] === state.torment)[1];
  if (!confirm(`Сбросить счётчики для «${state.current}» на ${label}?`)) return;
  state.bosses[state.current].t[state.torment] = newStat();
}

// ── Экспорт / импорт (резервные копии в файл) ──
function exportData() {
  const stamp = new Date().toISOString().slice(0, 16).replace("T", "_").replace(":", "-");
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `d4_boss_stats_${stamp}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function triggerImport() {
  importInput.value.click();
}

function onImportFile(e) {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const parsed = normState(JSON.parse(reader.result));
      applyState(parsed);
      scheduleSave();
      alert("Данные успешно загружены из файла.");
    } catch (err) {
      alert("Не удалось прочитать файл: " + err.message);
    }
  };
  reader.readAsText(file);
}

// ── Синхронизация с сервером ──
function applyState(st) {
  loaded = false;
  state.bosses = st.bosses;
  state.current = st.current;
  state.torment = st.torment;
  nextTick(() => (loaded = true));
}

async function loadState() {
  const res = await api("/state/");
  const empty = !res.data || !res.data.bosses;
  const st = normState(res.data);
  applyState(st);
  if (empty) {
    // первый вход — сразу сохраняем состояние по умолчанию
    await saveNow();
  }
}

let saveTimer = null;
function scheduleSave() {
  if (!loaded || !user.value) return;
  saveStatus.value = "сохранение…";
  clearTimeout(saveTimer);
  saveTimer = setTimeout(saveNow, 600);
}

async function saveNow() {
  clearTimeout(saveTimer);
  try {
    await api("/state/", { method: "PUT", body: { data: JSON.parse(JSON.stringify(state)) } });
    saveStatus.value = "сохранено ✓";
  } catch (err) {
    saveStatus.value = "ошибка сохранения: " + err.message;
  }
}

// любое изменение статистики → отложенное сохранение в БД
watch(state, scheduleSave, { deep: true });

// ── Авторизация через Telegram ──
window.onTelegramAuth = async (tgUser) => {
  signingIn.value = true;
  loginError.value = "";
  try {
    const profile = await api("/auth/telegram/", { method: "POST", body: tgUser });
    user.value = profile;
    await loadState();
  } catch (err) {
    loginError.value =
      "Не удалось войти: " +
      err.message +
      (err.status ? ` (HTTP ${err.status})` : "");
  } finally {
    signingIn.value = false;
  }
};

// Прямой переход верхнего окна на страницу авторизации Telegram (без iframe).
// Надёжнее официального виджета в браузерах с жёсткой защитой от трекеров
// (например, Yandex Browser), где iframe oauth.telegram.org может блокироваться.
function loginRedirect() {
  if (!botId.value) {
    loginError.value = "Сервер не сообщил bot_id — проверьте TELEGRAM_BOT_TOKEN.";
    return;
  }
  const origin = location.origin;
  const url =
    "https://oauth.telegram.org/auth" +
    "?bot_id=" + encodeURIComponent(botId.value) +
    "&origin=" + encodeURIComponent(origin) +
    "&return_to=" + encodeURIComponent(origin + "/") +
    "&request_access=write" +
    "&embed=0";
  window.location.href = url;
}

async function logout() {
  try {
    await api("/auth/logout/", { method: "POST" });
  } catch (e) {
    /* ignore */
  }
  user.value = null;
  loaded = false;
  Object.assign(state, defaultState());
}

// oauth.telegram.org (embed=0) возвращает данные в hash: #tgAuthResult=<base64(JSON)>
function parseTgAuthResult() {
  const m = location.hash.match(/tgAuthResult=([^&]+)/);
  if (!m) return null;
  try {
    let b64 = decodeURIComponent(m[1]).replace(/-/g, "+").replace(/_/g, "/");
    while (b64.length % 4) b64 += "=";
    return JSON.parse(atob(b64));
  } catch (e) {
    return null;
  }
}

// ── Инициализация ──
(async () => {
  try {
    const cfg = await api("/config/");
    botId.value = cfg.bot_id || "";
  } catch (e) {
    /* ignore */
  }

  // 1) вернулись из Telegram с результатом в hash — логинимся по нему
  const tgResult = parseTgAuthResult();
  if (tgResult) {
    history.replaceState({}, "", location.pathname);
    await window.onTelegramAuth(tgResult);
  }

  // 2) иначе проверяем существующую сессию
  if (!user.value) {
    try {
      user.value = await api("/me/");
      await loadState();
    } catch (e) {
      user.value = null;
    }
  }

  ready.value = true;
})();
</script>

<template>
  <div v-if="!ready" class="center-note">Загрузка…</div>

  <!-- Экран входа -->
  <div v-else-if="!user" class="login">
    <h1>⚔️ Diablo 4 Tracker</h1>
    <p>
      Войдите через Telegram, чтобы вести статистику дропа боссов.
      Данные сохраняются в облаке и привязаны к вашему аккаунту.
    </p>
    <button v-if="botId" class="btn tg-login-btn" @click="loginRedirect">
      Войти через Telegram
    </button>
    <p v-if="signingIn" style="color: var(--gold)">Входим…</p>
    <p v-if="loginError" style="color: var(--red-bright)">{{ loginError }}</p>
    <p v-if="!botId" style="color: var(--red-bright)">
      На сервере не настроен Telegram-бот (TELEGRAM_BOT_TOKEN/USERNAME).
    </p>
  </div>

  <!-- Основное приложение -->
  <template v-else>
    <div class="topbar">
      <span class="save-state">{{ saveStatus }}</span>
      <span class="user-chip">
        <img v-if="user.photo_url" :src="user.photo_url" alt="" />
        {{ user.first_name || user.username || "Игрок" }}
        <button class="btn btn-del" @click="logout">выйти</button>
      </span>
    </div>

    <div class="wrap">
      <h1>⚔️ Diablo 4 — Счётчик дропа боссов</h1>
      <p class="subtitle">
        Трекер забегов, мификов и осколков — отдельно по каждому уровню Torment.
        Данные хранятся в облаке.
      </p>

      <div class="boss-select">
        <select v-model="state.current">
          <option v-for="name in bossNames" :key="name" :value="name">{{ name }}</option>
        </select>
        <button class="btn btn-del" title="Удалить выбранного босса" @click="deleteBoss">
          ✕ удалить
        </button>
        <div class="new-boss">
          <input
            v-model="newBossName"
            type="text"
            placeholder="Новый босс…"
            maxlength="30"
            @keydown.enter="addBoss"
          />
          <button class="btn" @click="addBoss">+ добавить</button>
        </div>
      </div>

      <div class="torment-tabs">
        <button
          v-for="[key, label] in TORMENTS"
          :key="key"
          class="torment-tab"
          :class="{ active: key === state.torment }"
          @click="selectTorment(key)"
        >
          {{ label }}
        </button>
      </div>

      <div class="stats">
        <div class="stat runs"><div class="num">{{ curStat.runs }}</div><div class="lbl">Забегов</div></div>
        <div class="stat myth"><div class="num">{{ curStat.myth }}</div><div class="lbl">Мификов выпало</div></div>
        <div class="stat mythtal"><div class="num">{{ curStat.mythTal }}</div><div class="lbl">Талисманов выпало</div></div>
        <div class="stat splinter"><div class="num">{{ totalSpl }}</div><div class="lbl">Осколков всего</div></div>
        <div class="stat rate"><div class="num">{{ rate }}</div><div class="lbl">Шанс мифика за забег</div></div>
        <div class="stat rate"><div class="num">{{ rateTal }}</div><div class="lbl">Шанс талисмана за забег</div></div>
      </div>

      <div class="counters">
        <div
          v-for="c in mainCounters"
          :key="c.type"
          class="counter-card"
          :class="c.cls"
        >
          <h3>{{ c.title }}</h3>
          <div class="ctrl">
            <button class="big-btn minus" @click="inc(c.type, -1)">−</button>
            <span class="val">{{ curStat[c.type] }}</span>
            <button class="big-btn plus" @click="inc(c.type, 1)">+</button>
          </div>
          <div class="hint">{{ c.hint }}</div>
        </div>
      </div>

      <div class="section-title">Осколки (Splinters) <span>— падают с боссов</span></div>
      <div class="splinters">
        <div
          v-for="c in splinterCounters"
          :key="c.type"
          class="counter-card"
          :class="c.cls"
        >
          <h3>{{ c.title }}</h3>
          <div class="ctrl">
            <button class="big-btn minus" @click="inc(c.type, -1)">−</button>
            <span class="val">{{ curStat[c.type] }}</span>
            <button class="big-btn plus" @click="inc(c.type, 1)">+</button>
          </div>
        </div>
      </div>

      <div class="footer-actions">
        <span class="muted-note">{{ rateDetail }}</span>
        <button class="btn btn-del" @click="resetCurrent">
          Сбросить счётчики (этот босс + Torment)
        </button>
      </div>

      <div class="data-bar">
        <div class="data-buttons">
          <button class="btn" @click="exportData">💾 Экспорт в файл</button>
          <button class="btn" @click="triggerImport">📁 Импорт из файла</button>
          <input
            ref="importInput"
            type="file"
            accept="application/json,.json"
            hidden
            @change="onImportFile"
          />
        </div>
        <p class="data-note">
          Статистика автоматически сохраняется в облаке под вашим аккаунтом.
          «Экспорт» — резервная копия в файл на случай ручного переноса.
        </p>
      </div>
    </div>
  </template>
</template>
