def describe_project_period_summary_plain(project_name: str, total: int, start, end) -> str:
    period = f"{start.strftime('%d/%m')} e {end.strftime('%d/%m')}"
    if total == 0:
        return f"{project_name}: nenhuma alteração registrada entre {period}."
    if total == 1:
        return f"{project_name}: 1 alteração realizada entre {period}."
    return f"{project_name}: {total} alterações realizadas entre {period}."
