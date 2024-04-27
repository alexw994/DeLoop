import os
import io
import base64
from PIL import Image
from io import BytesIO
import numpy as np

def image_to_base64(image):
    # PIL.Image -> base64string
    bytes_io = BytesIO()
    image.save(bytes_io, format='jpeg')
    bytes_io.seek(0)
    byte_data = bytes_io.getvalue()
    base64_str = base64.b64encode(byte_data).decode('utf-8')
    return "data:image/jpeg;base64," + base64_str

def base64_to_image(input_str):
    # base64string -> PIL.Image
    data = base64.b64decode(input_str.split('data:image/jpeg;base64,')[1])
    image = Image.open(BytesIO(data))
    return image
