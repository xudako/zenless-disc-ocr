import cv2
import matplotlib.pyplot as plt
from PIL import Image
import pytesseract
import os
import numpy as np
from fractions import Fraction
import warnings
import time

STANDARD_ASPECT_RATIO = Fraction(16, 9)

# validate output
allowed = set()
drive_sets = ['Chaotic Metal', 'Fanged Metal', 'Freedom Blues', 'Hormone Punk', 'Inferno Metal', 'Polar Metal', 'Puffer Electro', 'Shockstar Disco', 'Soul Rock', 'Swing Jazz', 'Thunder Metal', 'Woodpecker Electro']
slots = [f' [{x}]' for x in range(1,7)]
level = {'Level 00/15', 'Lv. 0/15'}
stats = {'HP', 'ATK', 'DEF', 'CRIT Rate', 'CRIT DMG', 'Anomaly Proficiency', 'PEN Ratio', 'Physical DMG Bonus', 'Fire DMG Bonus', 'Ice DMG Bonus', 'Electric DMG Bonus', 'Ether DMG Bonus', 'Impact', 'Anomaly Mastery', 'Energy Regen', 'PEN'}
stats_vals = {'550', '79', '46', '7.5%', '12%', '6%', '23', '4.5%', '15%', '112', '19', '15', '3%', '4.8%', '2.4%', '9'}
for dset in drive_sets:
    for slot in slots:
        allowed.add(dset+slot)
allowed |= level | stats | stats_vals

# common errors
errors = [(')', '9'), ('48%', '4.8%'), ('Lw.0/15', 'Lv. 0/15'), ('9g', '9'), ('©) Lv.0/15', 'Lv. 0/15')]

# preprocessing functions
def crop_image(image, bbox):
    width = image.shape[1]
    height = image.shape[0]
    x0, y0, x1, y1 = bbox
    cropped_image = image[int(y0*height):int(y1*height), int(x0*width):int(x1*width)]
    return cropped_image

def preprocess_image(image, bbox):
    cropped_image = crop_image(image, bbox)
    gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    _, thresh_image = cv2.threshold(gray_image, 207, 255, cv2.THRESH_TOZERO)

    # cv2.imshow("crop", thresh_image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return thresh_image

# load images
folder_path = 'downloaded_images'
file_list = [f'downloaded_images/{f}' for f in os.listdir(folder_path) if f.endswith(('.png','.jpg'))]
images = [cv2.imread(path) for path in file_list]

results = []

t0 = time.time()
with open('error log.txt', 'w') as error_log:
    for image_id, image in enumerate(images):
        if image_id % 10 == 0:
            print(f'processing {image_id} of {len(file_list)} images')
        extracted_text = []
        width = image.shape[1]
        height = image.shape[0]
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                aspect_ratio = Fraction(width, height)
                if len(set(image[0,0])) == 1: # Cleanup
                    if aspect_ratio != STANDARD_ASPECT_RATIO:
                        aspect_correction = abs(int((width-height*STANDARD_ASPECT_RATIO)/2))
                        if aspect_ratio > STANDARD_ASPECT_RATIO:
                            image = image[0:height, aspect_correction:width-aspect_correction]
                        elif aspect_ratio < STANDARD_ASPECT_RATIO:
                            image = cv2.copyMakeBorder(image, 0, 0, aspect_correction, aspect_correction, cv2.BORDER_CONSTANT, None, value=0)
                        width = image.shape[1]
                    if image[int(0.347*height), int(0.691*width)][2] > 50: # cleanup - mobile
                        bboxes = {
                            "title":                (0.28, 0.15, 0.567, 0.203),
                            "level":                (0.28, 0.206, 0.39, 0.244),
                            "base_stat_name":       (0.29, 0.4, 0.43, 0.455),
                            "base_stat_value":      (0.445, 0.405, 0.49, 0.45),
                            "random_stat_name_1":   (0.29, 0.505, 0.39, 0.565),
                            "random_stat_value_1":  (0.443, 0.51, 0.488, 0.56),
                            "random_stat_name_2":   (0.51, 0.505, 0.615, 0.565),
                            "random_stat_value_2":  (0.665, 0.51, 0.71, 0.56),
                            "random_stat_name_3":   (0.29, 0.57, 0.39, 0.63),
                            "random_stat_value_3":  (0.443, 0.575, 0.488, 0.625),
                            "random_stat_name_4":   (0.51, 0.57, 0.615, 0.63),
                            "random_stat_value_4":  (0.665, 0.575, 0.71, 0.625),
                            "check_4":              (0.51, 0.57, 0.55, 0.63)
                        }
                    else: # cleanup - pc
                        bboxes = {
                            "title":                (0.32, 0.215, 0.56, 0.265),
                            "level":                (0.32, 0.267, 0.41, 0.297),
                            "base_stat_name":       (0.333, 0.42, 0.438, 0.47),
                            "base_stat_value":      (0.452, 0.425, 0.492, 0.461),
                            "random_stat_name_1":   (0.333, 0.505, 0.413, 0.555),
                            "random_stat_value_1":  (0.452, 0.512, 0.492, 0.548),
                            "random_stat_name_2":   (0.51, 0.505, 0.59, 0.555),
                            "random_stat_value_2":  (0.63, 0.512, 0.67, 0.548),
                            "random_stat_name_3":   (0.333, 0.555, 0.413, 0.605),
                            "random_stat_value_3":  (0.452, 0.562, 0.492, 0.598),
                            "random_stat_name_4":   (0.51, 0.555, 0.59, 0.605),
                            "random_stat_value_4":  (0.63, 0.562, 0.67, 0.598),
                            "check_4":              (0.51, 0.555, 0.59, 0.605)
                        }
                else: # Elfy
                    if aspect_ratio != STANDARD_ASPECT_RATIO:
                        aspect_correction = abs(int((width-height*STANDARD_ASPECT_RATIO)/2))
                        if aspect_ratio > STANDARD_ASPECT_RATIO:
                            image = image[0:height, 2*aspect_correction:width]
                        # else:
                        #     image = cv2.copyMakeBorder(image, 0, 0, 2*aspect_correction, 0, cv2.BORDER_CONSTANT, None, value=0) #GUESS, NEED IPAD ELFY TO CHECK
                        width = image.shape[1]
                    if image[int(0.29*height), int(0.33*width)][2] > 200: # elfy - pc
                        bboxes = {
                            "title":                (0.312, 0.175, 0.462, 0.245),
                            "level":                (0.343, 0.263, 0.423, 0.295),
                            "base_stat_name":       (0.322, 0.346, 0.412, 0.391),
                            "base_stat_value":      (0.42, 0.353, 0.455, 0.383),
                            "random_stat_name_1":   (0.322, 0.435, 0.392, 0.48),
                            "random_stat_value_1":  (0.42, 0.442, 0.455, 0.472),
                            "random_stat_name_2":   (0.322, 0.483, 0.392, 0.528),
                            "random_stat_value_2":  (0.42, 0.49, 0.455, 0.52),
                            "random_stat_name_3":   (0.322, 0.531, 0.392, 0.576),
                            "random_stat_value_3":  (0.42, 0.538, 0.455, 0.568),
                            "random_stat_name_4":   (0.322, 0.579, 0.392, 0.624),
                            "random_stat_value_4":  (0.42, 0.586, 0.455, 0.616),
                            "check_4":              (0.313, 0.58, 0.383, 0.618)
                        }
                    else: # elfy - mobile
                        bboxes = { # elfy - mobile
                            "title":                (0.11, 0.215, 0.32, 0.31),
                            "level":                (0.15, 0.326, 0.3, 0.373),
                            "base_stat_name":       (0.12, 0.435, 0.235, 0.485),
                            "base_stat_value":      (0.24, 0.44, 0.32, 0.48),
                            "random_stat_name_1":   (0.12, 0.545, 0.24, 0.6),
                            "random_stat_value_1":  (0.24, 0.55, 0.32, 0.595),
                            "random_stat_name_2":   (0.12, 0.605, 0.24, 0.655),
                            "random_stat_value_2":  (0.24, 0.61, 0.32, 0.65),
                            "random_stat_name_3":   (0.12, 0.66, 0.24, 0.71),
                            "random_stat_value_3":  (0.24, 0.665, 0.32, 0.705),
                            "random_stat_name_4":   (0.11, 0.715, 0.24, 0.765),
                            "random_stat_value_4":  (0.24, 0.72, 0.32, 0.76),
                            "check_4":              (0.11, 0.715, 0.24, 0.765)
                        }

        except RuntimeWarning:
            print(f'non-disc image detected at {file_list[image_id]}')
            continue

        # check for 4th substat
        check4 = crop_image(image, bboxes["check_4"])
        has4subs = np.any(np.all(check4 > [240, 240, 240], axis=-1))
        bboxes.pop("check_4")
        if not has4subs:
            bboxes.pop("random_stat_name_4")
            bboxes.pop("random_stat_value_4")

        # # display boxes
        # print(image[int(0.347*height), int(0.691*width)][2]) #cleanup, >50 is mobile
        # print(image[int(0.29*height), int(0.33*width)][2]) #elfy, >200 is pc
        # image_with_boxes = image.copy()
        # for key, bbox in bboxes.items():
        #     x, y, x1, y1 = bbox
        #     # Draw the rectangle
        #     cv2.rectangle(image_with_boxes, (int(x*width), int(y*height)), (int(x1*width), int(y1*height)), (0, 255, 0), 2)
        # cv2.circle(image_with_boxes, (int(0.132*width), int(0.363*height)), 2, (0, 255, 0), 2)
        # cv2.circle(image_with_boxes, (int(0.691*width), int(0.347*height)), 2, (0, 255, 0), 2)
        # plt.figure(figsize=(10, 10))
        # plt.imshow(cv2.cvtColor(image_with_boxes, cv2.COLOR_BGR2RGB))
        # plt.axis('off')
        # plt.show()

        # ocr
        for key, bbox in bboxes.items():
            preprocessed_image = preprocess_image(image, bbox)
            text = pytesseract.image_to_string(Image.fromarray(preprocessed_image), config='--oem 3 --psm 6')
            if not text: # if psm 6 fails to read image, try psm 7
                text = pytesseract.image_to_string(Image.fromarray(preprocessed_image), config='--oem 3 --psm 7')
            text = text.strip().replace('\n', ' ')
            if text not in allowed:
                flag = True
                for error in errors: # attempt to correct common errors
                    mistake, correction = error
                    if text == mistake:
                        text = correction
                        flag = False
                        break
                if flag:
                    print(f'{file_list[image_id][18:22]}: {text} at {key}')
                    error_log.write(f'{file_list[image_id][18:22]}: {text} at {key}\n')
            extracted_text.append(text)
        results.append(extracted_text)

# print results
t1 = time.time()
print(f'processing complete: {len(file_list)} images in {round(t1-t0,2)} seconds')
print()
for result in results:
    print(','.join(result))

with open('ocr output.txt', 'w') as file:
    for result in results[:-1]:
        file.write(','.join(result) + '\n')
    file.write(','.join(results[-1]))
