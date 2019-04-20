from sign import sign


def test_sign_accepts_a_parameter_of_bytes():
    sign(b"test")
