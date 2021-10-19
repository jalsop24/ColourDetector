
from background_removal import remove
import cv2
import os


input_path = ".\\test_images\\"
OUTPUT_PATH = ".\\opencv_output\\"
OUTPUT_FILE_TYPE = ".png"

for filename in os.listdir(input_path):
    if filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".jpeg"): 
        print("File:", input_path + filename)

        result = None

        try:
            result = remove(input_path + filename)
        except cv2.error:
            print("unable to process: " + filename)
            continue

        filename = str.split(filename, ".")[0] + OUTPUT_FILE_TYPE

        cv2.imwrite(OUTPUT_PATH + filename, result)