import hashlib

def file_hash(file_path) :

    md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            md5.update(data)

    return md5.hexdigest()