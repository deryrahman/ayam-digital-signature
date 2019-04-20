from sha import SHA1


def test_sha():
    msg = "The quick brown fox jumps over the lazy dog".encode()
    msg_hash = "2fd4e1c67a2d28fced849ee1bb76e7391b93eb12"

    sha1 = SHA1()
    assert sha1.do_hash(msg) == msg_hash
