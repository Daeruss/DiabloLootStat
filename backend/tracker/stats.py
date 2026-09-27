"""Агрегация статистики из JSON-документа UserState.data.

Структура data: {
  "bosses": { "<имя>": { "t": { "1".."12": {runs, myth, mythTal, splBaal, splMeph, splDiablo} } } },
  "current": ..., "torment": ...
}
"""

FIELDS = ["runs", "myth", "mythTal", "splBaal", "splMeph", "splDiablo"]


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
