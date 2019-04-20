from random import randint
from math import floor
from datetime import datetime as dt

INF = float('inf')

class ECCEG:
  def __init__(self, a=10, b=17, p=8191, base_point_idx=25, k_koblitz=20):
    self.p = p
    self.a = a
    self.b = b
    self.all_y_square = [i**2 for i in range(self.p)]
    self.valid_points = self.generate_valid_points()
    self.base_point = self.valid_points[base_point_idx]
    self.k_koblitz = k_koblitz

  # HELPER FUNCTION
  def __ecc_function(self, x):
    # return all valid Y while X = x
    result = []
    y_ = (x**3 + self.a*x + self.b) % self.p
    for y, y_square in enumerate(self.all_y_square):
      if y_square % self.p == y_:
        result.append(y)

    return result

  def __invmod(self, a, p):
    # invers a mod p
    for d in range(1, p):
      r = (d * a) % p
      if r == 1:
        break
    else:
      raise ValueError('%d has no inverse mod %d, please recheck ECC params' % (a, p))
    return d

  def sum_2_points(self, P, Q):
    # P and Q are point in field
    if (P[0] == 0 and P[1] == 0):
      return Q
    elif (Q[0] == 0 and Q[1] == 0):
      return P
    elif (P[1] + Q[1] == 0 and P[0] == Q[0]):
      return (INV, INV)
    elif (P[0] == Q[0] and P[1] == Q[1]):
      return self.multiply_with_point(2, P)
    else:
      gradien = ((P[1] - Q[1]) * self.__invmod((P[0] - Q[0]), self.p)) % self.p
      x = (gradien**2 - P[0] - Q[0]) % self.p
      y = (gradien*(P[0] - x) - P[1]) % self.p
      return (x, y)

  def subtract_2_points(self, P, Q):
    # P and Q are point in field
    return self.sum_2_points(P, (Q[0], (-1 * Q[1]) % self.p))

  def doubling_point(self, P):
    # P is point in field, return 2P
    if P[1] == 0:
      return (INV, INV)
    else:
      gradien = ((3*P[0]*P[0] + self.a) * self.__invmod(2*P[1], self.p)) % self.p
      x = (gradien**2 - 2*P[0]) % self.p
      y = (gradien*(P[0] - x) - P[1]) % self.p
      return (x, y)

  def multiply_with_point(self, k, P):
    # k is scalar, P is point in field
    result = (0, 0)
    temp = P
    k_as_binary = "{0:b}".format(k)
    for i in range(len(k_as_binary)-1, -1, -1):
      if k_as_binary[i] == '1':
        if i == len(k_as_binary)-1:
          result = temp
        else:
          result = self.sum_2_points(result, temp)
      temp = self.doubling_point(temp)
    
    return result;

  def generate_valid_points(self):
    result = []
    for x in range(self.p):
      arr_y = self.__ecc_function(x)
      for y in arr_y:
        result.append((x, y))

    return result

  def generate_key(self):
    private_key = randint(1, self.p - 1)
    public_key = self.multiply_with_point(private_key, self.base_point)

    return public_key, private_key

  def encode(self, b):
    for i in range(1, self.k_koblitz):
      x = ord(b)*self.k_koblitz + i
      arr_y = self.__ecc_function(x)
      if (len(arr_y) > 0):
        return (x, arr_y[0])
    return None

  def encrypt_point(self, P, public_key):
    # P and public_key are point
    k = randint(1, self.p - 1)
    p1 = self.multiply_with_point(k, self.base_point)
    p2 = self.sum_2_points(P, self.multiply_with_point(k, public_key))
    return (p1, p2)

  def decode(self, P):
    p_ = (P[0]-1)/self.k_koblitz
    return chr(int(floor(p_)))

  def decrypt_point(self, char_as_cip, private_key):
    # char_as_cip is tuple of point
    return self.subtract_2_points(char_as_cip[1], self.multiply_with_point(private_key, char_as_cip[0]))

  def encrypt(self, public_key, plain_text, cipher_path=''):
    # plain_text is string
    t1 = dt.now()
    cipher = ''
    for char in plain_text:
      char_as_point = self.encode(char)
      char_as_cip = self.encrypt_point(char_as_point, public_key)
      cipher += str(char_as_cip[0][0]) + ' '
      cipher += str(char_as_cip[0][1]) + ' '
      cipher += str(char_as_cip[1][0]) + ' '
      cipher += str(char_as_cip[1][1]) + ' '

    # print(cipher)

    # remove last space
    cipher = cipher[:-1]

    # save to file
    if cipher_path != '':
      with open(cipher_path, 'wb') as f:
        f.write(cipher)

    t2 = dt.now()
    return cipher, (t2-t1).microseconds

  def decrypt(self, private_key, cipher_text, plain_path=''):
    # cipher_text is array of points (ungrouped to pair)
    t1 = dt.now()
    # grouping cipher points
    points = cipher_text.split(' ')
    cipher = []
    for i in range(0, len(points), 4):
      p1 = (int(points[i]), int(points[i+1]))
      p2 = (int(points[i+2]), int(points[i+3]))
      cipher.append((p1, p2))

    # decrypt point
    plain_text = ''
    for c in cipher:
      char_as_point = self.decrypt_point(c, private_key)
      plain_char = self.decode(char_as_point)
      plain_text += plain_char

    # save to file
    if plain_path != '':
      with open(plain_path, 'wb') as f:
        f.write(plain_text)

    t2 = dt.now()
    return plain_text, (t2-t1).microseconds
