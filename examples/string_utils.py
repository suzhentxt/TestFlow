"""Small deterministic string helpers for TestFlow demonstrations."""


def normalize_text(s):
    """Trim text and collapse repeated whitespace into single spaces."""
    if s is None:
        raise ValueError("s cannot be None")

    return " ".join(s.strip().split())


def is_palindrome(s):
    """Return True when text is a palindrome, ignoring case and spaces."""
    if s is None:
        raise ValueError("s cannot be None")

    normalized = "".join(s.lower().split())
    return normalized == normalized[::-1]


def truncate(s, max_length):
    """Return text unchanged or cut to max_length characters."""
    if s is None:
        raise ValueError("s cannot be None")
    if max_length < 0:
        raise ValueError("max_length cannot be negative")

    if len(s) <= max_length:
        return s
    return s[:max_length]


def parse_csv_line(line):
    """Parse a simple comma-separated line and strip whitespace from values."""
    if line is None:
        raise ValueError("line cannot be None")
    if line == "":
        return []

    return [value.strip() for value in line.split(",")]
