import argparse
from PIL import Image, ImageFilter
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from collections import Counter
import numpy as np
from numba import jit

import cProfile

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
WHITE_LAB = np.array( [WHITE_LAB.lab_l, WHITE_LAB.lab_a, WHITE_LAB.lab_b] )

# deltaFunction = delta_e_cie2000

@jit
def deltaFunction(lab_color_vector, lab_color_matrix, Kl=1, Kc=1, Kh=1):
    """
    Calculates the Delta E (CIE2000) of two colors.
    """
    L, a, b = lab_color_vector

    avg_Lp = (L + lab_color_matrix[:, 0]) / 2.0

    C1 = np.sqrt(np.sum(np.power(lab_color_vector[1:], 2)))
    C2 = np.sqrt(np.sum(np.power(lab_color_matrix[:, 1:], 2), axis=1))

    avg_C1_C2 = (C1 + C2) / 2.0

    G = 0.5 * (1 - np.sqrt(np.power(avg_C1_C2, 7.0) / (np.power(avg_C1_C2, 7.0) + np.power(25.0, 7.0))))

    a1p = (1.0 + G) * a
    a2p = (1.0 + G) * lab_color_matrix[:, 1]

    C1p = np.sqrt(np.power(a1p, 2) + np.power(b, 2))
    C2p = np.sqrt(np.power(a2p, 2) + np.power(lab_color_matrix[:, 2], 2))

    avg_C1p_C2p = (C1p + C2p) / 2.0

    h1p = np.degrees(np.arctan2(b, a1p))
    h1p += (h1p < 0) * 360

    h2p = np.degrees(np.arctan2(lab_color_matrix[:, 2], a2p))
    h2p += (h2p < 0) * 360

    avg_Hp = (((np.fabs(h1p - h2p) > 180) * 360) + h1p + h2p) / 2.0

    T = 1 - 0.17 * np.cos(np.radians(avg_Hp - 30)) + \
        0.24 * np.cos(np.radians(2 * avg_Hp)) + \
        0.32 * np.cos(np.radians(3 * avg_Hp + 6)) - \
        0.2 * np.cos(np.radians(4 * avg_Hp - 63))

    diff_h2p_h1p = h2p - h1p
    delta_hp = diff_h2p_h1p + (np.fabs(diff_h2p_h1p) > 180) * 360
    delta_hp -= (h2p > h1p) * 720

    delta_Lp = lab_color_matrix[:, 0] - L
    delta_Cp = C2p - C1p
    delta_Hp = 2 * np.sqrt(C2p * C1p) * np.sin(np.radians(delta_hp) / 2.0)

    S_L = 1 + ((0.015 * np.power(avg_Lp - 50, 2)) / np.sqrt(20 + np.power(avg_Lp - 50, 2.0)))
    S_C = 1 + 0.045 * avg_C1p_C2p
    S_H = 1 + 0.015 * avg_C1p_C2p * T

    delta_ro = 30 * np.exp(-(np.power(((avg_Hp - 275) / 25), 2.0)))
    R_C = np.sqrt((np.power(avg_C1p_C2p, 7.0)) / (np.power(avg_C1p_C2p, 7.0) + np.power(25.0, 7.0)))
    R_T = -2 * R_C * np.sin(2 * np.radians(delta_ro))

    return np.sqrt(
        np.power(delta_Lp / (S_L * Kl), 2) +
        np.power(delta_Cp / (S_C * Kc), 2) +
        np.power(delta_Hp / (S_H * Kh), 2) +
        R_T * (delta_Cp / (S_C * Kc)) * (delta_Hp / (S_H * Kh)))


def countPixels(rgbImage):

    pixels = rgbImage.getdata()

    # returns a dict of {colour: pixels} 
    return Counter(pixels)


def processColours(colours):
    
    labColours = np.empty( (len(colours), 8)  )
    
    i = 0
    for rgbValue, count in colours.items():
        labValue = convert_color( sRGBColor(rgbValue[0], rgbValue[1], rgbValue[2], is_upscaled=True), LabColor)

        labValue = np.array( [labValue.lab_l, labValue.lab_a, labValue.lab_b] )

        deltaE = deltaFunction(labValue, np.atleast_2d(WHITE_LAB) )[0]

        labColours[i, 0] = rgbValue[0] 
        labColours[i, 1] = rgbValue[1]
        labColours[i, 2] = rgbValue[2]
        labColours[i, 3] = labValue[0]
        labColours[i, 4] = labValue[1]
        labColours[i, 5] = labValue[2]
        labColours[i, 6] = deltaE
        labColours[i, 7] = count
        i += 1

    return labColours

@jit
def combineColours(colourData):

    averageColoursList = np.zeros( (colourData.shape[0], 7), dtype=np.float32 )
    uniqueColours = 0

    for x in range( len(colourData[:,0]) ):
        
        data = colourData[x]
        inputRGB = np.array([ data[0], data[1], data[2] ])
        inputLAB = np.array([ data[3], data[4], data[5] ])
        inputCount = data[7]

        uniqueColour = True
        matchedIndex = None

        # Compare this colour of pixel to the palette to see if it needs to be added as a new colour or not
        for i in range( len(averageColoursList) ):

            referenceColourData = averageColoursList[i]
            referenceCount = referenceColourData[6]
            
            referenceRGB = np.array([ referenceColourData[0], referenceColourData[1], referenceColourData[2] ])
            referenceLAB = np.array([ referenceColourData[3], referenceColourData[4], referenceColourData[5] ])

            delta_e = deltaFunction( inputLAB , np.atleast_2d(referenceLAB) )[0]

            if delta_e < DELTA_E_CUTOFF:
                
                uniqueColour = False

                matchedIndex = i

                break


        # Update the colour palette 
        if uniqueColour:
            # Create a new colour within the palette
            averageColoursList[uniqueColours, 0] = data[0]
            averageColoursList[uniqueColours, 1] = data[1]
            averageColoursList[uniqueColours, 2] = data[2]
            averageColoursList[uniqueColours, 3] = data[3]
            averageColoursList[uniqueColours, 4] = data[4]
            averageColoursList[uniqueColours, 5] = data[5]
            averageColoursList[uniqueColours, 6] = data[7]
            
            uniqueColours = uniqueColours + 1

        else:
            # Calculate weighted RGB value
            referenceColourData = averageColoursList[matchedIndex]

            referenceCount = referenceColourData[6]

            referenceRGB = np.array([ referenceColourData[0], referenceColourData[1], referenceColourData[2] ])
            referenceLAB = np.array([ referenceColourData[3], referenceColourData[4], referenceColourData[5] ])
        
            combinedPixelCount = referenceCount + inputCount
                
            averageR = (inputRGB[0]*inputCount + referenceRGB[0]*referenceCount ) / combinedPixelCount
            averageG = (inputRGB[1]*inputCount + referenceRGB[1]*referenceCount ) / combinedPixelCount
            averageB = (inputRGB[2]*inputCount + referenceRGB[2]*referenceCount ) / combinedPixelCount

            averageL = (inputLAB[0]*inputCount + referenceLAB[0]*referenceCount ) / combinedPixelCount
            averageA = (inputLAB[1]*inputCount + referenceLAB[1]*referenceCount ) / combinedPixelCount
            averageB_LAB = (inputLAB[2]*inputCount + referenceLAB[2]*referenceCount ) / combinedPixelCount

            # Remove pervious average colour and add in the new average colour
            averageColoursList[i, 0] = averageR
            averageColoursList[i, 1] = averageG
            averageColoursList[i, 2] = averageB
            averageColoursList[i, 3] = averageL
            averageColoursList[i, 4] = averageA
            averageColoursList[i, 5] = averageB_LAB
            averageColoursList[i, 6] = combinedPixelCount 

        # Sort the new palette in terms of most prominent colour
        averageColoursList.sort()
        averageColoursList = np.flip(averageColoursList, -1)

    return averageColoursList

def getColours(image):

    # Check if image is RGBA, if so then convert it to RGB with white background
    if image.getbands() == ("R", "G", "B", "A"):
        fgImage = image.copy()
        bgImage = Image.new("RGBA", fgImage.size, "WHITE")
        bgImage.paste(fgImage, (0,0), fgImage)
        image = bgImage.convert("RGB")

    rgbImage = image.convert('RGB')

    # Resize image to reduce workload
    maxDimension = max( rgbImage.width, rgbImage.height )
    if maxDimension > THUMBNAIL_SIZE:
        scaleFactor =  THUMBNAIL_SIZE / maxDimension
        rgbImage.thumbnail( (round(scaleFactor * rgbImage.width), round(scaleFactor * rgbImage.height)) )

    # Get colour : pixels data, sort by volume of pixels.
    colourCount = countPixels(rgbImage)
    sortedCounts = dict(sorted(colourCount.items(),key=lambda item: item[1], reverse=True))
    averageColoursList = []
    
    colourData = processColours(sortedCounts)

    # If the colour is very close to white, assume it is background and ignore it
    whiteFilter = colourData[:, 6] > DELTA_E_BACKGROUND
    filteredData = colourData[whiteFilter]

    averageColoursList = combineColours(filteredData)

    totalPixels = sum( [x[-1] for _, x in enumerate(averageColoursList)] )

    displayColors = []

    outputData = []

    for _, referenceColourData in enumerate(averageColoursList):
        
        count = referenceColourData[-1]
        color = (referenceColourData[0], referenceColourData[1], referenceColourData[2])

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
    # cProfile.run("main()")
    main()