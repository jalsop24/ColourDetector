
from rembg.bg import remove
import numpy as np
import io
from PIL import Image, ImageFile
import os

ImageFile.LOAD_TRUNCATED_IMAGES = True

input_path = ".\\test_images\\"
output_path = ".\\rembg_output\\"

ouput_file_type = ".png"

for filename in os.listdir(input_path):
    if filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".jpeg"): 
        print("File:", input_path + filename)

        image = np.fromfile(input_path + filename)

        result = remove(image, 
            model_name="u2net", 
            alpha_matting=True, 
            alpha_matting_foreground_threshold=150,
            alpha_matting_background_threshold=10
            )

        img = Image.open(io.BytesIO(result)).convert("RGBA")
        filename = str.split(filename, ".")[0] + ouput_file_type

        img.save(output_path + filename)

    


