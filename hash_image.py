import hashlib

def file_hash(file_path) -> str:
    """
    Takes the file path of an image and produces an
    md5 hash of the image for image identification
    """
    md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            md5.update(data)

    return md5.hexdigest()