import argparse
from PIL import Image, ImageDraw, ImageFont 
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from itertools import islice
from collections import Counter
from time import time

'''
Delta E	Perception
<= 1.0	Not perceptible by human eyes.
1 - 2	Perceptible through close observation.
2 - 10	Perceptible at a glance.
11 - 49	Colors are more similar than opposite
100	Colors are exact opposite
'''
DELTA_E_CUTOFF = 10     # Colours with a delta E > DELTA_E_CUTOFF form new colours in the palette
PRINT_THRESHOLD = 0.05  # Colours with a proportion larger than this will be printed at the end

def count_pixels(filename):

    color_count = {}

    with Image.open(filename) as image:

        rgb_image = image.convert('RGB')

        pixels = rgb_image.getdata()

        # returns a dict of {colour: pixels} 
        color_count = Counter(pixels)

        return color_count
        

def main():

    parser = argparse.ArgumentParser(description='Calculates the sum of pixels per a color')
    parser.add_argument('image', nargs='?', default='.', help='The image to sum the pixels per a color of')
    
    t0 = time()

    args = parser.parse_args()
    color_count = count_pixels(args.image)                   
    sorted_counts = dict(sorted(color_count.items(),key=lambda item: item[1], reverse=True))
    
    average_colors_list = []

    for rgb_1_value, rgb_1_count in sorted_counts.items():

        standalone_color = True

        matched_index = None

        color_1_rgb = sRGBColor(rgb_1_value[0],rgb_1_value[1],rgb_1_value[2], is_upscaled=True)
        color_1_lab = convert_color(color_1_rgb, LabColor)

        # Compare this colour of pixel to the palette to see if it needs to be added as a new colour or not
        for i, color_data in enumerate(average_colors_list):
            
            rgb_2_count = color_data[0]
            rgb_2_value = color_data[1]

            color_2_rgb = sRGBColor(rgb_2_value[0],rgb_2_value[1],rgb_2_value[2], is_upscaled=True)
            color_2_lab = convert_color(color_2_rgb, LabColor)

            delta_e = delta_e_cie2000(color_1_lab, color_2_lab)

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
        

    # print("colours", average_colors_list)

    for _, color_data in enumerate(average_colors_list):
        
        count = color_data[0]
        color = color_data[1]

        proportion = count / sum(sorted_counts.values())

        if proportion > PRINT_THRESHOLD:
            print('{} : {} : {:.3f}'.format( ( round(color[0]), round(color[1]), round(color[2]) ), count, proportion))


    print(f"Time: {time() - t0}")
    print(f"Colours: {len(average_colors_list)}")

if __name__ == '__main__':
    main()