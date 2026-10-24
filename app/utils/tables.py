from app.utils.colors import paint, visible_len


def pad(text, width, align="left"):
    text = str(text)
    gap = max(0, width - visible_len(text))
    if align == "right":
        return " " * gap + text
    if align == "center":
        left = gap // 2
        return " " * left + text + " " * (gap - left)
    return text + " " * gap


def render_table(headers, rows, aligns=None, footers=None):
    aligns = aligns or ["left"] * len(headers)
    footers = footers or []
    widths = [visible_len(header) for header in headers]
    for row in list(rows) + list(footers):
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], visible_len(cell))

    vertical = paint("│", "blue")

    def border(left, middle, right):
        return paint(left + middle.join("─" * (width + 2) for width in widths) + right, "blue")

    def line(cells, styles=()):
        parts = []
        for index, cell in enumerate(cells):
            text = paint(cell, *styles) if styles else str(cell)
            parts.append(" " + pad(text, widths[index], aligns[index]) + " ")
        return vertical + vertical.join(parts) + vertical

    output = [border("┌", "┬", "┐")]
    output.append(line([str(header) for header in headers], ("bold", "cyan")))
    output.append(border("├", "┼", "┤"))
    for row in rows:
        output.append(line(row))
    if footers:
        output.append(border("├", "┼", "┤"))
        for row in footers:
            output.append(line(row, ("bold",)))
    output.append(border("└", "┴", "┘"))
    return "\n".join(output)


def render_pairs(pairs):
    width = max(len(key) for key, _ in pairs)
    return "\n".join(f"{paint(key.ljust(width), 'dim')} : {value}" for key, value in pairs)
