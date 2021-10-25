
import os
import argparse
import io
from time import time
from multiprocessing import Process

from . import pixel_colour_count

from rembg.bg import remove
import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
pixel_colour_count.THUMBNAIL_SIZE = 300

OUTPUT_CSV_FILE_TYPE = ".csv"
OUTPUT_IMAGE_FILE_TYPE = ".jpg"
OUTPUT_CSV_FILE_NAME = "combined_data"

WHITE_PROPORTION_THRESHOLD = 0.1 # Images with white pixels less than this proportion of the image are sent to background removal

HEADER = "Image Name, R, G, B, Count, Proportion"
FORMAT = "%i, %i, %i, %i, %.4f"                 # Format of the numbers in the csv file 
COMBINED_FORMAT = "%s, " + FORMAT

def processCSVs(csvPath):
    totalData = None

    for filename in os.listdir(csvPath):
        if filename == OUTPUT_CSV_FILE_NAME + OUTPUT_CSV_FILE_TYPE:
            continue

        data = np.atleast_2d( np.loadtxt(csvPath + filename, delimiter=",") )

        if totalData is None:
            totalData = np.empty( (0, data.shape[1] + 1), dtype="O" )

        newArray = np.empty( (data.shape[0], data.shape[1] + 1 ), dtype="O" )

        newArray[:,0] = filename.split(".")[0]

        newArray[:,1:] = data

        totalData = np.append(totalData, newArray, axis=0 )
    
    np.savetxt(csvPath + OUTPUT_CSV_FILE_NAME + OUTPUT_CSV_FILE_TYPE, totalData, delimiter=",", header=HEADER, fmt=COMBINED_FORMAT)


def processImage(filename, inputPath, outputCSVPath, outputImagePath):
    with Image.open(inputPath + filename) as image:
    
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

    totalImages = 0
    runningProcesses = []

    t0 = time()
    for filename in os.listdir(inputPath):
        print("Processing file:", filename)

        newProcess = Process(target=processImage, args=(filename, inputPath, outputCSVPath, outputImagePath))

        newProcess.start()

        runningProcesses.append(newProcess)

        totalImages += 1
    
    for _, process in enumerate(runningProcesses):
        process.join()

    print("Combining CSVs...")
    processCSVs(outputCSVPath)
    print("Done.")

    t1 = time()
    print("Time: {:.1f}s".format(t1-t0) )
    print("per image: {:.2f}s".format( (t1-t0)/totalImages ))


if __name__ == "__main__":
    main()







