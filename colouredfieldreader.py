import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import PerformanceTest as pt

def read_coloured_field_from_image(image, colours_image, num_colours, size, border):

    print("Reading the coloured field data now")

    pt.add("reading field")

    #generate_dataset_images(99)
    colours = read_colours(colours_image, num_colours)
    
    square_size_y = image.shape[0] / (border[1]+size[1])
    square_size_x = image.shape[1] / (border[0]+size[0])

    #print(f"square size: {square_size_x}x{square_size_y}")
    default_square_size_x = 19.167
    default_square_size_y = 18.17647
    square_ratio_x = square_size_x / default_square_size_x
    square_ratio_y = square_size_y / default_square_size_y
    #print(f"square ratio: {square_ratio_x} and {square_ratio_y}")
    zoom_ratio = (square_ratio_x + square_ratio_y) / 2.0
    print(f"Zoom: {zoom_ratio}")

    # Finding all column values
    columns = []
    for i in range(border[0], border[0]+size[0]):
        x_min = int(i * square_size_x)+1
        x_max = int((i+1) * square_size_x)+1
        
        #display_image(image[:, x_min:x_max])

        column = []
        for row in range(border[1]):
            y_min = int(row * square_size_y)+0
            y_max = int((row+1) * square_size_y)-2
            square = image[y_min:y_max, x_min:x_max]
            num, color_index = get_number_from_square(square, colours, size[1], zoom_ratio)
            if (num != 0):
                column.append((num, color_index))
        columns.append(column)

    # Finding all row values
    rows = []
    for i in range(border[1], border[1]+size[1]):
        y_min = int(i * square_size_y)+2
        y_max = int((i+1) * square_size_y)+1
        
        #display_image(image[:, x_min:x_max])

        row = []
        for col in range(border[0]):
            x_min = int(col * square_size_x)
            x_max = int((col+1) * square_size_x)
            square = image[y_min:y_max, x_min:x_max]
            num, color_index = get_number_from_square(square, colours, size[0], zoom_ratio)
            if (num != 0):
                row.append((num, color_index))
        rows.append(row)

    field = (rows, columns, size)

    print(rows)
    print(columns)

    pt.add("reading field")

    return field, colours

def read_colours(image, num_colours):
    colour_distance = 48

    (width, height) = (image.shape[1], image.shape[0])

    colours = []
    x = colour_distance // 2
    for i in range(num_colours):
        colours.append(image[height//2, x])
        #image[height//2, x] = (255, 255, 255)
        x += colour_distance
    
    return colours

def generate_dataset_images(max):
    for i in range(1, max+1):
        generate_dataset_image(i, False)
        generate_dataset_image(i, True)

def generate_dataset_image(num, bold=False):
    # Create a blank image with white background
    width, height = 14, 14  # Dimensions of the image
    background_color = (255, 255, 255)  # White background
    image = Image.new("RGB", (width, height), color=background_color)

    # Initialize the drawing context
    draw = ImageDraw.Draw(image)

    # Define the text and font
    text = f"{num}"
    font_size = 11

    try:
        # Load a TrueType font (you can replace this path with any .ttf file)
        font = ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", font_size)
    except IOError:
        # Fallback if the font file is not available
        font = ImageFont.load_default()

    spacing = 0.0

    if not bold:
        if num == 11:
            spacing = -1.0
    
    # Calculate manual letter placement
    letter_positions = []
    x = 0  # Start at x=0 for calculating total width
    for char in text:
        bbox = draw.textbbox((0, 0), char, font=font)
        char_width = bbox[2] - bbox[0]  # Width of the character
        letter_positions.append((char, x))
        x += char_width + spacing  # Add custom spacing

    # Compute total text width after manual spacing
    total_text_width = letter_positions[-1][1] + char_width

    # Calculate starting position to center the text
    text_x = (width - total_text_width) // 2
    text_y = (height - font_size) // 2

    # Draw each character manually with custom spacing
    for char, offset_x in letter_positions:
        draw.text((text_x + offset_x, text_y), char, fill=(0, 0, 0), font=font)

    # Save the image
    output_path = f"temp/{num}{bold}.png"
    image.save(output_path)

def get_dataset_img(num, background_colour, text_colour, bold=False):
    image = cv2.imread(f'temp/{num}{bold}.png')
    image = (np.float32(image) / 255.0) * (background_colour - text_colour) + text_colour
    image = np.uint8(image)

    # double image size
    image = cv2.resize(image, (image.shape[1]*2, image.shape[0]*2))

    return image[2:-2, 2:-2]

def pixel_difference(img1, img2):
    return np.sum(np.abs(img1.astype(np.float32) - img2.astype(np.float32)))

def difference_score(input_img, dataset_img):
    best_match_score = np.inf

    pt.add("difference score")

    # Iterate over positions using a sliding window
    for y in range(input_img.shape[0] - dataset_img.shape[0] + 1):
        for x in range(input_img.shape[1] - dataset_img.shape[1] + 1):
            # Extract the region from the input image
            region = input_img[y:y + dataset_img.shape[0], x:x + dataset_img.shape[1]]

            # Calculate the pixel-wise difference
            pt.add("pixel difference")
            difference = pixel_difference(region, dataset_img)
            pt.add("pixel difference")

            # Update the best match if the current difference is lower
            if difference < best_match_score:
                best_match_score = difference

    if False:
        for y in range(input_img.shape[0] - dataset_img.shape[0] + 1):
            for x in range(input_img.shape[1] - dataset_img.shape[1] + 1):
                # Extract the region from the input image
                region = input_img[y:y + dataset_img.shape[0], x:x + dataset_img.shape[1]]

                # Calculate the pixel-wise difference
                difference = pixel_difference(region, dataset_img)

                # Update the best match if the current difference is lower
                if difference == best_match_score:
                    display_images([region, dataset_img, np.uint8(cv2.resize(np.abs(region.astype(np.float32) - dataset_img.astype(np.float32)), 
                        (dataset_img.shape[0] * 20, dataset_img.shape[1] * 20), interpolation = cv2.INTER_NEAREST))])

    pt.add("difference score")

    return best_match_score

def get_number_from_square(img, colours, max_possible_value, zoom_ratio):
    best_match_index = None
    best_match_score = np.inf  # Initialize to a value that ensures any real score will be an improvement

    # Find the colour of the square
    #print(colours)
    #print(img[2, 2])
    colour = img[2, 2]

    # Empty squares will be ignored
    is_empty_square = np.sum(colour) == 218*3 or np.mean(img) * 3 == np.sum(colour)

    if is_empty_square:
        return 0, 0

    colour_found = False
    for i in range(len(colours)):
        if colours[i][0] == colour[0] and colours[i][1] == colour[1] and colours[i][2] == colour[2]:
            colour_found = True
            break
    
    if not colour_found:
        print(f"Colour not found: {colour}")
        return 0, 0
    
    # double image size
    resized_img = cv2.resize(img, (np.round(img.shape[1]*2 / zoom_ratio).astype(int), np.round(img.shape[0]*2 / zoom_ratio).astype(int)))

    text_is_white = np.mean(img) * 3 > np.sum(colour)
    #print(f"white text: {text_is_white} ({np.mean(img) * 3} vs {np.sum(colour)})")

    #display_image(resized_img)

    for i in range(1, max_possible_value + 1):
        if np.sum(colour) == 218*3:
            continue

        dataset_img = get_dataset_img(i, colour, [255, 255, 255] if text_is_white else [0,0,0], text_is_white)

        # display_images([resized_img, dataset_img])

        #if (np.sum(colour) != 218*3):
        #    display_image(np.uint8(dataset_img))

        # Resize both images to a consistent size
        #dataset_img_resized = cv2.resize(dataset_img, (img.shape[1], img.shape[0]))

        difference = difference_score(resized_img, dataset_img)

        #print(f"Number {i} with score {difference}")

        # Update the best match if the current difference is lower
        if difference < best_match_score:
            best_match_score = difference
            best_match_index = i

    colour_index = 0
    for i in range(len(colours)):
        if colours[i][0] == colour[0] and colours[i][1] == colour[1] and colours[i][2] == colour[2]:
            colour_index = i

    if False:
        print(f'{best_match_index} with score {best_match_score}, colour: {colour} ({colour_index})')
        
        display_image(resized_img)

    #display_image(resized_img, f'Best match: {best_match_index}')

    return best_match_index, colour_index + 1

def display_image(image, window_name='Captured Screen'):
    cv2.imshow(window_name, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def display_images(images, window_name='Captured Screen'):
    for i, image in enumerate(images):
        cv2.imshow(f"{window_name} {i+1}", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()