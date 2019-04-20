MARK_START = b"<petok>"
MARK_END = b"</petok>"


def sign(data):
    return data + MARK_START + MARK_END
