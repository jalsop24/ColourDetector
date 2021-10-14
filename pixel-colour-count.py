import argparse
from PIL import Image, ImageDraw, ImageFont 
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from itertools import islice
from collections import Counter

def count_pixels(filename):

    color_count = {}

    with Image.open(filename) as image:

        width, height = image.size
        rgb_image = image.convert('RGB')

        pixels = rgb_image.getdata()

        color_count = Counter(pixels)

        return color_count
        
        # Iterate through each pixel in the image and keep a count per unique color

        for x in range(width):
            for y in range(height):
                rgb = rgb_image.getpixel((x, y))
                if rgb in color_count:
                    color_count[rgb] += 1
                else:
                    color_count[rgb] = 1

    return color_count

def main():

    parser = argparse.ArgumentParser(description='Calculates the sum of pixels per a color')
    parser.add_argument('image', nargs='?', default='.', help='The image to sum the pixels per a color of')

    args = parser.parse_args()
    color_count = count_pixels(args.image)                   
    sorted_counts = dict(sorted(color_count.items(),key=lambda item: item[1], reverse=True))
    
    # # only needed if want to print out the dictionary
    # color_index = 1
    # for color, count in sorted_counts.items(): 
    #     color_name = color
    #     print('{}.) {}: {}'.format(color_index, color_name, count))
    #     color_index += 1
    # # Display the total number of pixels
    # # print('\t{} pixels'.format(sum(color_count[color] for color in color_count)))

    threshold = 0.05

    average_colors_dict = {}

    i = 0
    j = i + 1

    for rgb_1_value, rgb_1_count in sorted_counts.items():

        # Check to avoid StopIteration

        if i == len(sorted_counts) - 1:
            break

        standalone_color = True

        matched_color = None

        color_1_rgb = sRGBColor(rgb_1_value[0],rgb_1_value[1],rgb_1_value[2], is_upscaled=True)
        color_1_lab = convert_color(color_1_rgb, LabColor)

        for rgb_2_value, rgb_2_count in average_colors_dict.items():

            color_2_rgb = sRGBColor(rgb_2_value[0],rgb_2_value[1],rgb_2_value[2], is_upscaled=True)
            color_2_lab = convert_color(color_2_rgb, LabColor)

            delta_e = delta_e_cie2000(color_1_lab, color_2_lab)

            if delta_e < 30:
                
                standalone_color = False

                matched_color = rgb_2_value

                break


        if standalone_color == True:

            average_colors_dict[rgb_1_value] = rgb_1_count

        else:
            # Calculate weighted RGB value

            rgb_2_value = matched_color
            rgb_2_count = average_colors_dict[matched_color]

            combined_pixel_count = rgb_2_count + rgb_1_count 
                
            average_r = (rgb_1_value[0]*rgb_1_count + rgb_2_value[0]*rgb_2_count ) / combined_pixel_count
            average_g = (rgb_1_value[1]*rgb_1_count + rgb_2_value[1]*rgb_2_count ) / combined_pixel_count
            average_b = (rgb_1_value[2]*rgb_1_count + rgb_2_value[2]*rgb_2_count ) / combined_pixel_count

            rgb_average = (average_r, average_g, average_b)

            del average_colors_dict[matched_color]
            average_colors_dict[rgb_average] = combined_pixel_count
        

    # print("colours", average_colors_dict)

    for color, count in average_colors_dict.items():

        proportion = count / sum(average_colors_dict.values())

        if proportion > threshold:

            print('{}:{}:{}'.format(color, count, proportion))

if __name__ == '__main__':
    main()