from blake3 import blake3
import time
from PIL import Image
from PIL.ExifTags import TAGS

def file_hash(file_path) -> str:
    """
    Takes the file path of an image and produces a
    BLAKE3 hash of the image for image identification.
    """
    blake3_hash = blake3()

    with open(file_path, "rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            blake3_hash.update(data)

    return blake3_hash.hexdigest()

def extract_raw(file_path) -> ...:
    """
    Takes the data stored in an image file and
    extracts it to be stored
    """
    image = Image.open(file_path)
    image_info = {
        "Filename": image.filename,
        "Image Size": image.size,
        "Image Height": image.height,
        "Image Width": image.width,
        "Image Format": image.format,
        "Image Mode": image.mode,
        "Image is Animatedd": getattr(image, "is_animated", False),
        "Frames in Image": getattr(image, "n_frames", 1)
    }

def extract_exif(file_path) -> ...:
    """
    Takes the exif data stored in an image file
    and extracts it to be stored
    """
    image = Image.open(file_path)
    exif_data = image.getexif()

    exif_info = {}
    for tag_id in exif_data:
        tag = TAGS.get(tag_id, tag_id)
        data = exif_data.get(tag_id)
        if isinstance(data, bytes):
            data = data.decode()
        exif_info[tag] = data
        

start = time.time()
print(file_hash('cat_test.jpg'))
end = time.time()
print((end - start) * 10**3, 'ms')