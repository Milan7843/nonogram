import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

def read_coloured_field_from_image(image, colours_image, num_colours, size, border):

    print("Reading the coloured field data now")

    generate_dataset_images(99)
    colours = read_colours(colours_image, num_colours)
    
    square_size_y = image.shape[0] / (border[1]+size[1])
    square_size_x = image.shape[1] / (border[0]+size[0])

    # Finding all column values
    columns = []
    for i in range(border[0], border[0]+size[0]):
        x_min = int(i * square_size_x)+3
        x_max = int((i+1) * square_size_x)+0
        
        #display_image(image[:, x_min:x_max])

        column = []
        for row in range(border[1]):
            y_min = int(row * square_size_y)+1
            y_max = int((row+1) * square_size_y)-2
            square = image[y_min:y_max, x_min:x_max]
            num = get_number_from_square(square, colours)
            if (num != 0):
                column.append(num)
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
            num = get_number_from_square(square, colours)
            if (num != 0):
                row.append(num)
        rows.append(row)

    field = (rows, columns, size)

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

    display_image(image)
    
    return colours

def generate_dataset_images(max):
    for i in range(1, max+1):
        # Create a blank image with white background
        width, height = 14, 14  # Dimensions of the image
        background_color = (255, 255, 255)  # White background
        image = Image.new("RGB", (width, height), color=background_color)

        # Initialize the drawing context
        draw = ImageDraw.Draw(image)

        # Define the text and font
        text = f"{i}"
        font_size = 11

        try:
            # Load a TrueType font (you can replace this path with any .ttf file)
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            # Fallback if the font file is not available
            font = ImageFont.load_default()

        # Calculate the text position to center it
        text_bbox = draw.textbbox((0, 0), text, font=font)  # Get bounding box of the text
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2 - 2

        # Add text to the image
        text_color = (0, 0, 0)  # Black color
        draw.text((text_x, text_y), text, fill=text_color, font=font)

        # Save the image as a PNG
        output_path = f"temp/{i}.png"
        image.save(output_path)

def get_dataset_img(num, background_colour, text_colour):
    image = cv2.imread(f'temp/{num}.png')
    image = (np.float32(image) / 255.0) * (background_colour - text_colour) + text_colour
    image = np.uint8(image)

    return image#image[2:-2, 2:-2]

def pixel_difference(img1, img2):
    return np.sum(np.abs(img1.astype(np.float32) - img2.astype(np.float32)))

def difference_score(input_img, dataset_img):
    best_match_score = np.inf
    # Iterate over positions using a sliding window
    for y in range(input_img.shape[0] - dataset_img.shape[0] + 1):
        for x in range(input_img.shape[1] - dataset_img.shape[1] + 1):
            # Extract the region from the input image
            region = input_img[y:y + dataset_img.shape[0], x:x + dataset_img.shape[1]]

            # Calculate the pixel-wise difference
            difference = pixel_difference(region, dataset_img)

            # Update the best match if the current difference is lower
            if difference < best_match_score:
                best_match_score = difference

    return best_match_score

def get_number_from_square(img, colours):
    best_match_index = None
    best_match_score = np.inf  # Initialize to a value that ensures any real score will be an improvement

    # Find the colour of the square
    print(colours)
    print(img[2, 2])
    colour = img[2, 2]

    colour_found = False
    for i in range(len(colours)):
        if colours[i][0] == colour[0] and colours[i][1] == colour[1] and colours[i][2] == colour[2]:
            colour_found = True
            break
    
    if not colour_found:
        print(f"Colour not found: {colour}")

    text_is_white = np.mean(img) * 3 > np.sum(colour)
    print(f"white text: {text_is_white} ({np.mean(img) * 3} vs {np.sum(colour)})")

    display_image(img)

    for i in range(1, 100):
        if np.sum(colour) == 218*3:
            continue

        dataset_img = get_dataset_img(i, colour, [255, 255, 255] if text_is_white else [0,0,0])

        #if (np.sum(colour) != 218*3):
        #    display_image(np.uint8(dataset_img))

        # Resize both images to a consistent size
        #dataset_img_resized = cv2.resize(dataset_img, (img.shape[1], img.shape[0]))

        difference = difference_score(img, dataset_img)

        # Update the best match if the current difference is lower
        if difference < best_match_score:
            best_match_score = difference
            best_match_index = i

    print(f'{best_match_index} with score {best_match_score}')

    #display_image(img, f'Best match: {best_match_index}')

    return best_match_index

def display_image(image, window_name='Captured Screen'):
    cv2.imshow(window_name, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()