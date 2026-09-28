"""Агрегация статистики из JSON-документа UserState.data.

Структура data: {
  "bosses": { "<имя>": { "t": { "1".."12": {runs, myth, mythTal, splBaal, splMeph, splDiablo} } } },
  "current": ..., "torment": ...
}
"""

FIELDS = ["runs", "myth", "mythTal", "mythSeal", "splBaal", "splMeph", "splDiablo"]

_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
TORMENT_KEYS = [str(i) for i in range(1, 13)]
TORMENT_OPTIONS = [{"key": k, "label": "T" + _ROMAN[i]} for i, k in enumerate(TORMENT_KEYS)]


def _empty():
    return {f: 0 for f in FIELDS}


def _add_stat(acc, stat):
    if not isinstance(stat, dict):
        return
    for f in FIELDS:
        v = stat.get(f)
        if isinstance(v, (int, float)):
            acc[f] += v


def totals_for_state(data):
    """Суммарные показатели по всем боссам и уровням Torment одного пользователя."""
    acc = _empty()
    bosses = (data or {}).get("bosses") or {}
    for boss in bosses.values():
        for stat in (boss.get("t") or {}).values():
            _add_stat(acc, stat)
    acc["splinters"] = acc["splBaal"] + acc["splMeph"] + acc["splDiablo"]
    return acc


def per_boss_totals(data):
    """{имя_босса: суммы по всем Torment} для одного пользователя."""
    result = {}
    bosses = (data or {}).get("bosses") or {}
    for name, boss in bosses.items():
        acc = _empty()
        for stat in (boss.get("t") or {}).values():
            _add_stat(acc, stat)
        acc["splinters"] = acc["splBaal"] + acc["splMeph"] + acc["splDiablo"]
        result[name] = acc
    return result


def _iter_stats(data, torment=None, boss=None):
    """Итерируем записи статистики с учётом фильтров по боссу и Torment."""
    bosses = (data or {}).get("bosses") or {}
    names = [boss] if boss else list(bosses.keys())
    for name in names:
        b = bosses.get(name)
        if not b:
            continue
        t = b.get("t") or {}
        keys = [torment] if torment else list(t.keys())
        for k in keys:
            yield name, t.get(k)


def totals_filtered(data, torment=None, boss=None):
    """Итоги одного пользователя с фильтрами (torment/boss = None → все)."""
    acc = _empty()
    for _, stat in _iter_stats(data, torment, boss):
        _add_stat(acc, stat)
    acc["splinters"] = acc["splBaal"] + acc["splMeph"] + acc["splDiablo"]
    return acc


def per_boss_filtered(data, torment=None):
    """{имя_босса: суммы} c фильтром по Torment."""
    result = {}
    for name, stat in _iter_stats(data, torment, None):
        acc = result.setdefault(name, _empty())
        _add_stat(acc, stat)
    for acc in result.values():
        acc["splinters"] = acc["splBaal"] + acc["splMeph"] + acc["splDiablo"]
    return result


def collect_boss_names(states):
    names = set()
    for st in states:
        for n in ((st.data or {}).get("bosses") or {}).keys():
            names.add(n)
    return sorted(names)


def is_empty(totals):
    return all(totals.get(f, 0) == 0 for f in FIELDS)


def merge_boss_into(bosses_data, src, dst):
    """Прибавляет статистику босса src к боссу dst внутри одного data.bosses.
    Возвращает True, если src был найден и что-то перенесено."""
    if src not in bosses_data:
        return False
    s = bosses_data.get(src) or {}
    d = bosses_data.setdefault(dst, {"t": {}})
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
    """Добавляет производные метрики: шанс мифика/талисмана и осколков за забег."""
    t = dict(totals)
    runs = t.get("runs", 0)
    t["myth_rate"] = round(t["myth"] / runs * 100, 1) if runs else 0
    t["tal_rate"] = round(t["mythTal"] / runs * 100, 1) if runs else 0
    t["seal_rate"] = round(t["mythSeal"] / runs * 100, 1) if runs else 0
    t["spl_per_run"] = round(t["splinters"] / runs, 2) if runs else 0
    return t
