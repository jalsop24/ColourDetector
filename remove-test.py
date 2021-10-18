
from rembg.bg import remove
import numpy as np
import io
from PIL import Image

input_path = r".\test_images\sample2.png"
output_path = 'out.png'

f = np.fromfile(input_path)
result = remove(f)
img = Image.open(io.BytesIO(result)).convert("RGBA")
img.save(output_path)
