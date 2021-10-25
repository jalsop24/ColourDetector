
import argparse
import logging

from . import process_images

def main():
    parser = argparse.ArgumentParser(description='Process the given images into their dominant colours.')
    parser.add_argument("input", default=".", help='The input directory')
    parser.add_argument('outputCSV', default=".", help='Where the output csv files should go.')
    parser.add_argument('outputImages', default=".", help='Where the output image files should go.')
    
    args = parser.parse_args()

    inputPath = args.input
    outputCSVPath = args.outputCSV
    outputImagePath = args.outputImages

    logging.info("test")

if __name__ == "__main__":
    main()