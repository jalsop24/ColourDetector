import argparse
from PIL import Image, ImageFilter
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie1994, delta_e_cie2000
from collections import Counter
from time import time
import numpy as np

'''
Delta E	Perception
<= 1.0	Not perceptible by human eyes.
1 - 2	Perceptible through close observation.
2 - 10	Perceptible at a glance.
11 - 49	Colors are more similar than opposite
100	Colors are exact opposite
'''

DELTA_E_CUTOFF = 10      # Colours with a delta E > DELTA_E_CUTOFF form new colours in the palette
DELTA_E_BACKGROUND = 5  # Colours within this delta_E of (255,255,255) are assumed to be background
PRINT_THRESHOLD = 0.10  # Colours with a proportion larger than this will be printed at the end

NUM_PALETTE_COLOURS = 10
THUMBNAIL_SIZE = 300

OUTPUT_FILE_TYPE = ".png"
OUTPUT_PATH = ".\\palettes\\"

WHITE_LAB = convert_color(sRGBColor(255, 255, 255, is_upscaled=True), LabColor) 

deltaFunction = delta_e_cie2000


def countPixels(rgbImage):

    pixels = rgbImage.getdata()

    # returns a dict of {colour: pixels} 
    return Counter(pixels)


def getColours(image):

    if image.getbands() == ("R", "G", "B", "A"):
        fgImage = image.copy()
        bgImage = Image.new("RGBA", fgImage.size, "WHITE")
        bgImage.paste(fgImage, (0,0), fgImage)
        image = bgImage.convert("RGB")


    rgbImage = image.convert('RGB')

    maxDimension = max( rgbImage.width, rgbImage.height )

    if maxDimension > THUMBNAIL_SIZE:
        scaleFactor =  THUMBNAIL_SIZE / maxDimension
        rgbImage.thumbnail( (round(scaleFactor * rgbImage.width), round(scaleFactor * rgbImage.height)) )


    colourCount = countPixels(rgbImage)

    sortedCounts = dict(sorted(colourCount.items(),key=lambda item: item[1], reverse=True))
    
    averageColoursList = []

    for inputRGBValue, inputRGBCount in sortedCounts.items():

        uniqueColour = True

        matchedIndex = None

        inputSRGBValue = sRGBColor(inputRGBValue[0], inputRGBValue[1], inputRGBValue[2], is_upscaled=True)
        inputLABValue = convert_color(inputSRGBValue, LabColor)

        # If the colour is very close to white, assume it is background and ignore it
        if deltaFunction(inputLABValue, WHITE_LAB) < DELTA_E_BACKGROUND:
            continue

        # Compare this colour of pixel to the palette to see if it needs to be added as a new colour or not
        for i, referenceColourData in enumerate(averageColoursList):
            
            referenceRGBCount = referenceColourData[0]
            referenceRGBValue = referenceColourData[1]

            referenceSRGBValue = sRGBColor(referenceRGBValue[0], referenceRGBValue[1], referenceRGBValue[2], is_upscaled=True)
            referenceLABValue = convert_color(referenceSRGBValue, LabColor)

            delta_e = deltaFunction(inputLABValue, referenceLABValue)

            if delta_e < DELTA_E_CUTOFF:
                
                uniqueColour = False

                matchedIndex = i

                break


        # Update the colour palette 
        if uniqueColour:
            # Create a new colour within the palette

            averageColoursList.append( (inputRGBCount, inputRGBValue) )

        else:
            # Calculate weighted RGB value
            referenceColourData = averageColoursList[matchedIndex]

            referenceRGBCount = referenceColourData[0]
            referenceRGBValue = referenceColourData[1]
        
            combinedPixelCount = referenceRGBCount + inputRGBCount 
                
            average_r = (inputRGBValue[0]*inputRGBCount + referenceRGBValue[0]*referenceRGBCount ) / combinedPixelCount
            average_g = (inputRGBValue[1]*inputRGBCount + referenceRGBValue[1]*referenceRGBCount ) / combinedPixelCount
            average_b = (inputRGBValue[2]*inputRGBCount + referenceRGBValue[2]*referenceRGBCount ) / combinedPixelCount

            rgb_average = (average_r, average_g, average_b)

            # Remove pervious average colour and add in the new average colour
            averageColoursList.pop(i)
            averageColoursList.append( (combinedPixelCount, rgb_average) )

        # Sort the new palette in terms of most prominent colour
        averageColoursList.sort(key=lambda x: x[0], reverse=True)

    totalPixels = sum( [x[0] for _, x in enumerate(averageColoursList)] )

    displayColors = []

    outputData = []

    for _, referenceColourData in enumerate(averageColoursList):
        
        count = referenceColourData[0]
        color = referenceColourData[1]

        proportion = count / totalPixels

        if proportion > PRINT_THRESHOLD:
            rgbColour = ( round(color[0]), round(color[1]), round(color[2]) )
            displayColors.append( rgbColour )
            outputData.append( (rgbColour[0], rgbColour[1], rgbColour[2], count, proportion) )


    width = round( min(rgbImage.width, rgbImage.height)/NUM_PALETTE_COLOURS )
    for i, color in enumerate(displayColors):
        if i > NUM_PALETTE_COLOURS - 1:
            break
        color_image_square = Image.new("RGB", (width, width), color)
        rgbImage.paste(color_image_square, (i*width, 0))

    return rgbImage, np.array(outputData)
    


def main():

    parser = argparse.ArgumentParser(description='Calculates the sum of pixels per a color')
    parser.add_argument('image', nargs='?', default='.', help='The image to sum the pixels per a color of')
    
    args = parser.parse_args()

    with Image.open(args.image) as image:

        rgbImage, outputData = getColours(image)

        for _, data in enumerate(outputData):
            rgbColour = (data[0], data[1], data[2] )
            count = data[3]
            proportion = data[4]
            print('{} : {} : {:.3f}'.format( rgbColour , count, proportion))


        filename = str.split(args.image, ".")[-2] + OUTPUT_FILE_TYPE

        filename = str.split(filename, "\\")[-1]

        rgbImage.save( OUTPUT_PATH + filename )

    
    

if __name__ == '__main__':
    main()