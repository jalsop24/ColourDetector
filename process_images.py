
import os
import argparse
import io

import pixel_colour_count
from rembg.bg import remove
import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

OUTPUT_FILE_TYPE = ".csv"
WHITE_PROPORTION_THRESHOLD = 0.1

FORMAT = "%i %i %i %i %.4f"

def main():
    
    parser = argparse.ArgumentParser(description='Process the given images into their dominant colours.')
    parser.add_argument("input", default=".", help='The input directory')
    parser.add_argument('output', default=".", help='Where the output csv files should go.')
    
    args = parser.parse_args()

    inputPath = args.input
    outputPath = args.output

    for filename in os.listdir(inputPath):
        with Image.open(inputPath + filename) as image:
            print("Processing file:", filename)

            colourCount = pixel_colour_count.countPixels(image)

            threshold = image.width * image.height * WHITE_PROPORTION_THRESHOLD

            if colourCount[(255,255,255)] < threshold:
                # remove background
                result = remove(np.fromfile(inputPath + filename))
                fgImage = Image.open(io.BytesIO(result)).convert("RGBA")
                bgImage = Image.new("RGBA", fgImage.size, "WHITE")
                bgImage.paste(fgImage, (0,0), fgImage)
                image = bgImage.convert("RGB")


            paletteImage, paletteData = pixel_colour_count.getColours(image)

            print("saving...")
            np.savetxt( outputPath + str.split(filename, ".")[0] + OUTPUT_FILE_TYPE, paletteData, fmt=FORMAT )



if __name__ == "__main__":
    main()







