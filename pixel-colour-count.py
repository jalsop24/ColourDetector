import argparse
from PIL import Image, ImageFilter
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie1994, delta_e_cie2000
from collections import Counter
from time import time
import os

'''
Delta E	Perception
<= 1.0	Not perceptible by human eyes.
1 - 2	Perceptible through close observation.
2 - 10	Perceptible at a glance.
11 - 49	Colors are more similar than opposite
100	Colors are exact opposite
'''

DELTA_E_CUTOFF = 8      # Colours with a delta E > DELTA_E_CUTOFF form new colours in the palette
DELTA_E_BACKGROUND = 5  # Colours within this delta_E of (255,255,255) are assumed to be background
PRINT_THRESHOLD = 0.10  # Colours with a proportion larger than this will be printed at the end

NUM_PALETTE_COLOURS = 10
THUMBNAIL_SIZE = 300

WHITE_LAB = convert_color(sRGBColor(255, 255, 255, is_upscaled=True), LabColor) 

delta_function = delta_e_cie2000

def count_pixels(rgb_image):

    pixels = rgb_image.getdata()

    # returns a dict of {colour: pixels} 
    return Counter(pixels)
        

def main():

    parser = argparse.ArgumentParser(description='Calculates the sum of pixels per a color')
    parser.add_argument('image', nargs='?', default='.', help='The image to sum the pixels per a color of')
    
    args = parser.parse_args()

    t0 = time()

    rgb_image = None

    with Image.open(args.image) as image:

        rgb_image = image.convert('RGB')
        if max( rgb_image.width, rgb_image.height ) > THUMBNAIL_SIZE:
            rgb_image.thumbnail( (THUMBNAIL_SIZE, THUMBNAIL_SIZE) )

    color_count = count_pixels(rgb_image)

    sorted_counts = dict(sorted(color_count.items(),key=lambda item: item[1], reverse=True))
    
    average_colors_list = []

    for rgb_1_value, rgb_1_count in sorted_counts.items():

        standalone_color = True

        matched_index = None

        color_1_rgb = sRGBColor(rgb_1_value[0],rgb_1_value[1],rgb_1_value[2], is_upscaled=True)
        color_1_lab = convert_color(color_1_rgb, LabColor)

        # If the colour is very close to white, assume it is background and ignore it
        if delta_function(color_1_lab, WHITE_LAB) < DELTA_E_BACKGROUND:
            continue

        # Compare this colour of pixel to the palette to see if it needs to be added as a new colour or not
        for i, color_data in enumerate(average_colors_list):
            
            rgb_2_count = color_data[0]
            rgb_2_value = color_data[1]

            color_2_rgb = sRGBColor(rgb_2_value[0], rgb_2_value[1], rgb_2_value[2], is_upscaled=True)
            color_2_lab = convert_color(color_2_rgb, LabColor)

            delta_e = delta_function(color_1_lab, color_2_lab)

            if delta_e < DELTA_E_CUTOFF:
                
                standalone_color = False

                matched_index = i

                break


        # Update the colour palette 
        if standalone_color == True:
            # Create a new colour within the palette

            average_colors_list.append( (rgb_1_count, rgb_1_value) )

        else:
            # Calculate weighted RGB value
            color_data = average_colors_list[matched_index]

            rgb_2_count = color_data[0]
            rgb_2_value = color_data[1]
        
            combined_pixel_count = rgb_2_count + rgb_1_count 
                
            average_r = (rgb_1_value[0]*rgb_1_count + rgb_2_value[0]*rgb_2_count ) / combined_pixel_count
            average_g = (rgb_1_value[1]*rgb_1_count + rgb_2_value[1]*rgb_2_count ) / combined_pixel_count
            average_b = (rgb_1_value[2]*rgb_1_count + rgb_2_value[2]*rgb_2_count ) / combined_pixel_count

            rgb_average = (average_r, average_g, average_b)

            # Remove pervious average colour and add in the new average colour
            average_colors_list.pop(i)
            average_colors_list.append( (combined_pixel_count, rgb_average) )

        # Sort the new palette in terms of most prominent colour
        average_colors_list.sort(key=lambda x: x[0], reverse=True)

    total_pixels = sum( [x[0] for _, x in enumerate(average_colors_list)] )

    display_colors = []

    print(f"Time: {time() - t0}")
    print(f"Colours: {len(average_colors_list)}")
    print("Foreground Proportion: {:.3f}".format(total_pixels/(rgb_image.width*rgb_image.height)))

    for _, color_data in enumerate(average_colors_list):
        
        count = color_data[0]
        color = color_data[1]

        proportion = count / total_pixels

        if proportion > PRINT_THRESHOLD:
            rgb_color = ( round(color[0]), round(color[1]), round(color[2]) )
            display_colors.append( rgb_color )
            print('{} : {} : {:.3f}'.format( rgb_color , count, proportion))
    

    width = round( min(rgb_image.width, rgb_image.height)/NUM_PALETTE_COLOURS )
    for i, color in enumerate(display_colors):
        if i > NUM_PALETTE_COLOURS - 1:
            break
        color_image_square = Image.new("RGB", (width, width), color)
        rgb_image.paste(color_image_square, (i*width, 0))

    rgb_image.save( args.image[:-4] + "_palette.png" )
    

if __name__ == '__main__':
    main()