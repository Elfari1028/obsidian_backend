#!/usr/bin/env python 
# -*- coding:utf-8 -*-

import base64
import hashlib
from Crypto.Cipher import AES


class DeAesCrypt:
    def __init__(self, data, key, pad):
        self.key = key.encode('utf-8')
        self.data = data.encode('utf-8')
        self.pad = pad.lower()

        hash_obj = hashlib.md5()
        hash_obj.update(key.encode())
        res_md5 = hash_obj.hexdigest()
        self.iv = res_md5[:16].encode('utf-8')

    @property
    def decrypt_aes(self):
        real_data = base64.b64decode(self.data)
        my_aes = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypt_data = my_aes.decrypt(real_data)
        return self.get_str(decrypt_data)

    def get_str(self, bd):
        if self.pad == "zero":
            return ''.join([chr(i) for i in bd if i != 0])
        else:
            return "Exception: No Such Fill Pattern"
