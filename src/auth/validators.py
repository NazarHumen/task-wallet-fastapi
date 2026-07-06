def normalize_email(value: str) -> str:
    """Normalize an email and ensure it contains only Latin characters.

    Shared by the registration schema and the admin panel so both apply
    the exact same rule. Raises ``ValueError`` on non-ASCII input.
    """
    value = value.strip().lower()
    if not value.isascii():
        raise ValueError("Email must contain only Latin characters")
    return value
