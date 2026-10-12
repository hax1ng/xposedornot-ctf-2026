import base64
from Crypto.Cipher import AES

b64 = "VkxUMeZoD+qNYOhzGsb9qRLLvgY7cpsJH+9DxAn03g8JUs/4zveqobhruztkcmu1pJrl6JxxasuERAfZV7KWFwNvh43uqDeFvZXGLmrMv85huZ0hOXooFDMtcATo5gL1qYa5+bp9V8sjmBNx2EzjDjZIauJMY+NjbRrKMgMQ0kiBcQQdGpoDf6NnSanrx8vzmMSzP1pSaNC/JO/5x+jHW8bJA5Cs6EO/EJUyilMsJ9mKGh5u/o26vN9FguQxAbaypgtkRmXtvTcnCZftZcbx1VRGr+qks2zVWbtZumPoHBy0tSMf5SADpmPoolG0NItILoGFGPRwuLLxDZYrukPTgA2qZoDDhzRD2w8zaJqzfl0akUO6Lg91DVQh53yht97+5wY2ZA=="
blob = base64.b64decode(b64)
assert blob[:4] == b"VLT1", blob[:4]
ct = blob[4:]
key = bytes.fromhex("8b3f7e2a1c4d6f9b" + "0e8a7c5d2f1b3e6a")
iv = b"\x00"*16
pt = AES.new(key, AES.MODE_CBC, iv).decrypt(ct)
print("keylen", len(key), "ctlen", len(ct))
print(repr(pt))
# strip PKCS7
try:
    pad = pt[-1]
    if 1 <= pad <= 16:
        print("unpadded:", pt[:-pad].decode(errors="replace"))
except Exception as e:
    print(e)
