from sha import SHA1

sha1 = SHA1()
print(sha1.do_hash('The quick brown fox jumps over the lazy dog'.encode()))
