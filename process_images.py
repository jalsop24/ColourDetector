
import os
import argparse
import io
from time import time
from multiprocessing import Process

import pixel_colour_count
from rembg.bg import remove
import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

OUTPUT_CSV_FILE_TYPE = ".csv"
OUTPUT_IMAGE_FILE_TYPE = ".jpg"
WHITE_PROPORTION_THRESHOLD = 0.1 # Images with white pixels less than this proportion of the image are sent to background removal

FORMAT = "%i, %i, %i, %i, %.4f" # Format of the numbers in the csv file 

CHUNK_SIZE = 10

def processImage(filename, inputPath, outputCSVPath, outputImagePath):
    with Image.open(inputPath + filename) as image:
            print("Processing file:", filename)

            
            colourCount = pixel_colour_count.countPixels(image)

            threshold = image.width * image.height * WHITE_PROPORTION_THRESHOLD

            if colourCount[(255,255,255)] < threshold:
                # remove background
                result = remove(np.fromfile(inputPath + filename))
                image = Image.open(io.BytesIO(result)).convert("RGBA")


            paletteImage, paletteData = pixel_colour_count.getColours(image)

            np.savetxt( outputCSVPath + str.split(filename, ".")[0] + OUTPUT_CSV_FILE_TYPE, paletteData, fmt=FORMAT )

            paletteImage.save( outputImagePath + str.split(filename, ".")[0] + OUTPUT_IMAGE_FILE_TYPE )

def main():
    
    parser = argparse.ArgumentParser(description='Process the given images into their dominant colours.')
    parser.add_argument("input", default=".", help='The input directory')
    parser.add_argument('outputCSV', default=".", help='Where the output csv files should go.')
    parser.add_argument('outputImages', default=".", help='Where the output image files should go.')
    
    args = parser.parse_args()

    inputPath = args.input
    outputCSVPath = args.outputCSV
    outputImagePath = args.outputImages

    i = 0
    totalImages = 0
    runningProcesses = []

    t0 = time()
    for filename in os.listdir(inputPath):
        
        newProcess = Process(target=processImage, args=(filename, inputPath, outputCSVPath, outputImagePath))

        newProcess.start()

        runningProcesses.append(newProcess)

        i += 1
        totalImages += 1
        i %= CHUNK_SIZE
    
    for _, process in enumerate(runningProcesses):
        process.join()

    

    t1 = time()
    print("Time: {:.1f}s".format(t1-t0) )
    print("per image: {:.2f}s".format( (t1-t0)/totalImages ))


if __name__ == "__main__":
    main()







