MARK_START = b"<petok>"
MARK_END = b"</petok>"


def sign(data):
    return MARK_START + MARK_END
