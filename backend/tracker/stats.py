"""Агрегация статистики из JSON-документа UserState.data.

Структура data (с сезонами):
{
  "seasons": {
    "15": { "bosses": { "<имя>": { "t": { "1".."12": {runs, myth, ...} } } } }
  },
  "current": ..., "torment": ...
}
"""

FIELDS = ["runs", "myth", "mythTal", "mythSeal", "splBaal", "splMeph", "splDiablo"]

_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
TORMENT_KEYS = [str(i) for i in range(1, 13)]
TORMENT_OPTIONS = [{"key": k, "label": "T" + _ROMAN[i]} for i, k in enumerate(TORMENT_KEYS)]


def get_bosses(data, season):
    """Возвращает dict боссов для нужного сезона.
    Поддерживает и «сезонную», и старую «плоскую» структуру."""
    data = data or {}
    seasons = data.get("seasons")
    if isinstance(seasons, dict):
        s = seasons.get(str(season)) or {}
        return s.get("bosses") or {}
    return data.get("bosses") or {}  # legacy (ещё не мигрировано)


def all_season_keys(data):
    """Все ключи сезонов в данных пользователя (для обхода при объединении)."""
    data = data or {}
    seasons = data.get("seasons")
    if isinstance(seasons, dict):
        return list(seasons.keys())
    return []


def _empty():
    return {f: 0 for f in FIELDS}


def _add_stat(acc, stat):
    if not isinstance(stat, dict):
        return
    for f in FIELDS:
        v = stat.get(f)
        if isinstance(v, (int, float)):
            acc[f] += v


def _with_splinters(acc):
    acc["splinters"] = acc["splBaal"] + acc["splMeph"] + acc["splDiablo"]
    return acc


def totals_for_bosses(bosses):
    """Суммарные показатели по всем боссам и уровням Torment (dict боссов)."""
    acc = _empty()
    for boss in (bosses or {}).values():
        for stat in (boss.get("t") or {}).values():
            _add_stat(acc, stat)
    return _with_splinters(acc)


def _iter_stats(bosses, torment=None, boss=None):
    """Итерируем записи статистики с учётом фильтров по боссу и Torment."""
    bosses = bosses or {}
    names = [boss] if boss else list(bosses.keys())
    for name in names:
        b = bosses.get(name)
        if not b:
            continue
        t = b.get("t") or {}
        keys = [torment] if torment else list(t.keys())
        for k in keys:
            yield name, t.get(k)


def totals_filtered(bosses, torment=None, boss=None):
    """Итоги по dict боссов с фильтрами (torment/boss = None → все)."""
    acc = _empty()
    for _, stat in _iter_stats(bosses, torment, boss):
        _add_stat(acc, stat)
    return _with_splinters(acc)


def per_boss_filtered(bosses, torment=None):
    """{имя_босса: суммы} c фильтром по Torment."""
    result = {}
    for name, stat in _iter_stats(bosses, torment, None):
        acc = result.setdefault(name, _empty())
        _add_stat(acc, stat)
    for acc in result.values():
        _with_splinters(acc)
    return result


def collect_boss_names(states, season):
    """Имена боссов, встречающиеся у пользователей в указанном сезоне."""
    names = set()
    for st in states:
        for n in get_bosses(st.data, season).keys():
            names.add(n)
    return sorted(names)


def is_empty(totals):
    return all(totals.get(f, 0) == 0 for f in FIELDS)


def merge_boss_into(bosses, src, dst):
    """Прибавляет статистику босса src к боссу dst внутри dict боссов.
    Возвращает True, если src был найден и что-то перенесено."""
    if not bosses or src not in bosses:
        return False
    s = bosses.get(src) or {}
    d = bosses.setdefault(dst, {"t": {}})
    d.setdefault("t", {})
    for tk, stat in (s.get("t") or {}).items():
        acc = d["t"].setdefault(tk, {f: 0 for f in FIELDS})
        if not isinstance(stat, dict):
            continue
        for f in FIELDS:
            v = stat.get(f)
            if isinstance(v, (int, float)):
                acc[f] = acc.get(f, 0) + v
    return True


def with_rates(totals):
    """Добавляет производные метрики: шанс мифика/талисмана/печати и осколков за забег."""
    t = dict(totals)
    runs = t.get("runs", 0)
    t["myth_rate"] = round(t["myth"] / runs * 100, 1) if runs else 0
    t["tal_rate"] = round(t["mythTal"] / runs * 100, 1) if runs else 0
    t["seal_rate"] = round(t["mythSeal"] / runs * 100, 1) if runs else 0
    t["spl_per_run"] = round(t["splinters"] / runs, 2) if runs else 0
    return t
