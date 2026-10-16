"""Synthetic fixture source."""


def export_csv(rows, user):
    return "\n".join(",".join(map(str, row)) for row in rows)
