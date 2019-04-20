from sign import sign, MARK_START


def test_sign_accepts_a_parameter_of_bytes():
    sign(b"test")


def test_sign_returns_bytes_containing_start_mark():
    assert MARK_START in sign(b"test")
