# constants
TEXT_COLORS = {
    "PURPLE": "\033[95m",
    "CYAN": "\033[96m",
    "DARKCYAN": "\033[36m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
    "END": "\033[0m",
}


def color_text(text: str, *attrs: str) -> str:
    """
    Color a line for shell printing.
    The string is encapsulated and rest of line will have default format.

    @param text: (str) text to be printed
    @param attrs: (list[str]) used color or "BOLD" or "UNDERLINE".
    @returns: (str) formated string closed by an END tag.
    """
    for attr in attrs:
        text = TEXT_COLORS[attr.upper()] + text + TEXT_COLORS["END"]
    return text
