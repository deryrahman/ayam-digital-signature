import struct

class SHA1():

    def __init__(self):
        self.buffer_md = [
            0x67452301,
            0xEFCDAB89,
            0x98BADCFE,
            0x10325476,
            0xC3D2E1F0,
        ]

    def _roll_left(self, x, n):
        return ((x << n) | (x >> (32 - n))) & (1 << 32)-1

    def _expand(self, msg):
        """
        msg = bytes
        """
        pad = b'\x80' + b'\x00' * ((56 - ((len(msg) + 1) % 64)) % 64)
        bits_len = struct.pack(b'>Q', len(msg) * 8)
        return msg + pad + bits_len

    def _basic_op(self, a, b, c, d, e, w, k, f):
        """
        a, b, c, d, e = 4 bytes
        """
        res = (f(b, c, d) + e) & (1 << 32) - 1
        res = (self._roll_left(a, 5) + res) & (1 << 32) - 1
        res = (w + res) & (1 << 32) - 1
        res = (k + res) & (1 << 32) - 1
        b = self._roll_left(b, 30)
        return res, a, b, c, d

    def _h_sha(self, a, b, c, d, e, block):
        """
        block = 64 bytes
        """
        w = []
        k = [
            0x5A827999,
            0x6ED9EBA1,
            0x8F1BBCDC,
            0xCA62C1D6
        ]
        f = [
            lambda b, c, d: (b & c) | (~b & d),
            lambda b, c, d: b ^ c ^ d,
            lambda b, c, d: (b & c) | (b & d) | (c & d ),
            lambda b, c, d: b ^ c ^ d
        ]
        a_ori = a
        b_ori = b
        c_ori = c
        d_ori = d
        e_ori = e
        for t in range(80):
            if t < 16:
                w.append(struct.unpack(b'>I', block[t * 4:t * 4 + 4])[0])
            else:
                w.append(
                    self._roll_left(w[t - 16] ^ w[t - 14] ^ w[t - 8] ^ w[t - 3],
                                    1))
            a, b, c, d, e = self._basic_op(a, b, c, d, e, w[t], k[t // 20],
                                           f[t // 20])

        a = (a_ori + a) & (1 << 32) - 1
        b = (b_ori + b) & (1 << 32) - 1
        c = (c_ori + c) & (1 << 32) - 1
        d = (d_ori + d) & (1 << 32) - 1
        e = (e_ori + e) & (1 << 32) - 1
        return a, b, c, d, e

    def do_hash(self, msg):
        msg = self._expand(msg)
        a = self.buffer_md[0]
        b = self.buffer_md[1]
        c = self.buffer_md[2]
        d = self.buffer_md[3]
        e = self.buffer_md[4]
        for i in range(len(msg) // 64):
            a, b, c, d, e = self._h_sha(a, b, c, d, e, msg[i * 64:i * 64 + 64])
        result = '%08x%08x%08x%08x%08x' % (a, b, c, d, e)
        return result
