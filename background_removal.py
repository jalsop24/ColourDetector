
import argparse
import cv2
import numpy as np
import os

MODEL_PATH = ".\\model.yml.gz"

OUTPUT_PATH = ".\\opencv_output\\"

OUTPUT_FILETYPE = ".png"

edgeDetector = cv2.ximgproc.createStructuredEdgeDetection(MODEL_PATH)

def findSignificantContour(edgeImg):
    contours, hierarchy = cv2.findContours(
        edgeImg,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )
        # Find level 1 contours
    level1Meta = []
    for contourIndex, tupl in enumerate(hierarchy[0]):
        # Filter the ones without parent
        if tupl[3] == -1:
            tupl = np.insert(tupl.copy(), 0, [contourIndex])
            level1Meta.append(tupl)
    # From among them, find the contours with large surface area.
    contoursWithArea = []
    for tupl in level1Meta:
        contourIndex = tupl[0]
        contour = contours[contourIndex]
        area = cv2.contourArea(contour)
        contoursWithArea.append([contour, area, contourIndex])

    contoursWithArea.sort(key=lambda meta: meta[1], reverse=True)
    largestContour = contoursWithArea[0][0]
    return largestContour

def findEdges(image):
    imageCopy = image.copy().astype(np.float32) / 255.0
    edges = ( edgeDetector.detectEdges(imageCopy) * 255).astype(np.uint8)
    return edges

def clip(image, cutoff=127.5):
    return 255 * (2 * (image.astype(np.float32) - cutoff)).clip(0, 1).astype(np.uint8)

def remove(image):
    KERNEL_SIZE = 3
    kernel = np.ones((KERNEL_SIZE, KERNEL_SIZE), np.uint8)

    # load image
    img = cv2.imread(image)

    # convert to gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find edges
    # edges = cv2.Canny(gray, 50, 200)
    # edges = cv2.morphologyEx(edges, cv2.MORPH_DILATE, kernel, iterations=1)
    edges = findEdges(img) 

    # edges = clip(edges, cutoff=0)

    blur  = cv2.GaussianBlur(edges, (0,0), sigmaX=1, sigmaY=1, borderType = cv2.BORDER_DEFAULT)

    contour = np.zeros(img.shape[:2], dtype=np.uint8)

    largestContour = findSignificantContour(blur)

    cv2.drawContours(contour, [largestContour], 0, (255,255,255), 2, cv2.LINE_AA)



    cv2.fillPoly(contour, [largestContour], (255,255,255))

    #cv2.drawContours(contour, contours, -1, (255,255,255), 2, cv2.LINE_AA)

     
    contour = cv2.morphologyEx(contour, cv2.MORPH_OPEN, kernel, iterations=10)

    contour = 255*(2*(contour.astype(np.float32))-255.0).clip(0, 1).astype(np.uint8)

    # put mask into alpha channel
    result = (img.copy().astype(np.float32) + cv2.cvtColor( (255-contour), cv2.COLOR_GRAY2BGR).astype(np.float32)).clip(0, 255).astype(np.uint8)
    result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
    result[:, :, 3] = contour

    #cv2.imshow("INPUT", img)
    #cv2.imshow("GRAY", gray)
    #cv2.imshow("EDGES", edges)
    #cv2.imshow("BLUR", blur)
    #cv2.imshow("CONTOUR", contour)

    return result


def main(image=None):
    parser = argparse.ArgumentParser(description='Calculates the sum of pixels per a color')
    parser.add_argument('image', nargs='?', default='.', help='The image to sum the pixels per a color of')
    
    args = parser.parse_args()

    if image is None:
        image = args.image

    result = remove(image)

    filename = str.split(image, ".")[-2] + OUTPUT_FILETYPE

    filename = str.split(filename, "\\")[-1]

    print(str.split(image, ".")[-2])
    print(filename)

    # save resulting masked image
    cv2.imwrite(OUTPUT_PATH + filename, result)

    cv2.imshow("RESULT", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    


if __name__ == "__main__":
    main()


