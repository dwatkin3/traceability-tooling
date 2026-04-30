def classify_status(status: str, pass_values: list[str]) -> str:
    """
    Normalise execution status into one of:
    PASS, FAIL, IN_PROGRESS, NOT_STARTED, OTHER
    """

    s = (status or "").strip().lower()
    pass_values = [p.lower().strip() for p in pass_values]

    if s in pass_values:
        return "PASS"

    if "fail" in s:
        return "FAIL"

    if "progress" in s:
        return "IN_PROGRESS"

    if "start" in s:
        return "NOT_STARTED"

    return "OTHER"