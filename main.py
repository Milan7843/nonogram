import cv2
import pyautogui
import numpy as np
import keyboard
import blackwhitesolver
import colouredsolver
from skimage.metrics import structural_similarity as ssim
from colouredfieldreader import read_coloured_field_from_image
import PerformanceTest as pt

has_found_bottom_left = False
has_found_top_right = False
bottom_left = (0, 0)
top_right = (0, 0)
field_bottom_left = (0, 0)
field_top_right = (0, 0)
border = (4, 4) # left, top
size = (12, 12) # x,y


def main():
    global size
    global border
    global has_found_bottom_left
    global has_found_top_right
    global bottom_left
    global top_right

    # Display the captured image on 'c' key press
    keyboard.hook(on_key_press)

    # Taking input for border
    if input("Use previous data? (y/n): ") == "y":
        # Load data from previous runs from a file
        with open("data.txt", "r") as file:
            left_border = int(file.readline())
            top_border = int(file.readline())
            border = (left_border, top_border)
            width = int(file.readline())
            height = int(file.readline())
            coloured = file.readline() == "True\n"
            num_colours = int(file.readline())
            bottom_left = (int(file.readline()), int(file.readline()))
            top_right = (int(file.readline()), int(file.readline()))
            has_found_bottom_left = True
            has_found_top_right = True
            size = (width, height)
    else:
        left_border = int(input("Please enter the left border: "))
        top_border = int(input("Please enter the top border: "))
        border = (left_border, top_border)

        # Taking input for size
        width = int(input("Please enter the width of the field: "))
        height = int(input("Please enter the height of the field: "))
        size = (width, height)

        coloured = input("Is this a coloured field? (y/n): ") == "y"
        if coloured:
            num_colours = int(input("Please enter the number of colours: "))
        else:
            num_colours = 0

        # Writing this input for loading later
        with open("data.txt", "w") as file:
            file.write(f"{left_border}\n")
            file.write(f"{top_border}\n")
            file.write(f"{width}\n")
            file.write(f"{height}\n")
            file.write(f"{coloured}\n")
            file.write(f"{num_colours}\n")

    if coloured:
        field_img, colours_img = find_field_region_coloured(num_colours)
        field, colours = read_coloured_field_from_image(field_img, colours_img, num_colours, size, border)
        colouredsolver.solve(field, get_square_position, False, len(colours))
    else:
        field_img = find_field_region()
        field = read_field_from_image(field_img)
        blackwhitesolver.solve(field, get_square_position, False)
    
    pt.print_performance_hierarchy()

def capture_screen(region):
    screenshot = pyautogui.screenshot(region=region)
    image_np = np.array(screenshot)
    return cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

def display_image(image, window_name='Captured Screen'):
    cv2.imshow(window_name, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def get_square_position(x, y):
    global size
    global border

    orig_x = field_bottom_left[0]
    orig_y = field_top_right[1]
    width = field_top_right[0] - field_bottom_left[0]
    height = field_bottom_left[1] - field_top_right[1]
    
    square_size_y = height / (border[1]+size[1])
    square_size_x = width / (border[0]+size[0])

    xi = x+border[0]
    yi = y+border[1]

    px = xi * square_size_x + square_size_x / 2
    py = yi * square_size_y + square_size_y / 2

    return int(orig_x + px), int(orig_y + py)


def click_square(x, y, left=True):
    global size
    global border

    orig_x = field_bottom_left[0]
    orig_y = field_top_right[1]
    width = field_top_right[0] - field_bottom_left[0]
    height = field_bottom_left[1] - field_top_right[1]
    
    square_size_y = height / (border[1]+size[1])
    square_size_x = width / (border[0]+size[0])

    xi = x+border[0]
    yi = y+border[1]

    px = xi * square_size_x + square_size_x / 2
    py = yi * square_size_y + square_size_y / 2

    if (left):
        pyautogui.click(int(orig_x + px), int(orig_y + py))
    else:
        pyautogui.rightClick(int(orig_x + px), int(orig_y + py))

def get_mouse_position():
    return pyautogui.position() # = x,y

def find_field_region():
    global bottom_left
    global top_right
    global field_bottom_left
    global field_top_right
    global has_found_top_right
    print("Ready to find the field!")
    print("Please put the mouse to the bottom left of the bottom left corner of the field, and press C")
    while(not has_found_top_right):
        continue
    
    # Set the region you want to capture (x, y, width, height)
    x = bottom_left[0]
    y = top_right[1]
    w = top_right[0] - bottom_left[0]
    h = bottom_left[1] - top_right[1]
    capture_region = (x, y, w, h)

    # Capture the screen
    captured_image = capture_screen(capture_region)

    gray = cv2.cvtColor(captured_image, cv2.COLOR_RGB2GRAY)
    ret, binary_image = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    field_bottom_left, field_top_right = find_corners(binary_image)

    #print(f'{field_bottom_left[1]}:{field_top_right[1]}, {field_bottom_left[0]}:{field_top_right[0]}')

    border_width = 2

    cropped_image = captured_image[field_top_right[1]+border_width:field_bottom_left[1]-border_width, field_bottom_left[0]+border_width:field_top_right[0]-border_width]
    gray_cropped = gray[field_top_right[1]+border_width:field_bottom_left[1]-border_width, field_bottom_left[0]+border_width:field_top_right[0]-border_width]
    
    field_bottom_left = (x + field_bottom_left[0]+border_width, y + field_bottom_left[1]-border_width)
    field_top_right = (x + field_top_right[0]-border_width, y + field_top_right[1]+border_width)

    # Display the captured image
    display_image(cropped_image)

    return gray_cropped

def find_field_region_coloured(num_colours):
    global bottom_left
    global top_right
    global field_bottom_left
    global field_top_right
    global has_found_top_right
    print("Ready to find the field!")
    print("Please put the mouse to the bottom left of the bottom left corner of the field, and press C")
    while(not has_found_top_right):
        continue
    
    # Set the region you want to capture (x, y, width, height)
    x = bottom_left[0]
    y = top_right[1]
    w = top_right[0] - bottom_left[0]
    h = bottom_left[1] - top_right[1]
    capture_region = (x, y, w, h)

    # Capture the screen
    captured_image = capture_screen(capture_region)

    gray = cv2.cvtColor(captured_image, cv2.COLOR_RGB2GRAY)
    ret, binary_image = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    field_bottom_left, field_top_right = find_corners(binary_image)

    #print(f'{field_bottom_left[1]}:{field_top_right[1]}, {field_bottom_left[0]}:{field_top_right[0]}')

    border_width = 2

    cropped_image = captured_image[field_top_right[1]+border_width:field_bottom_left[1]-border_width, field_bottom_left[0]+border_width:field_top_right[0]-border_width]
    gray_cropped = gray[field_top_right[1]+border_width:field_bottom_left[1]-border_width, field_bottom_left[0]+border_width:field_top_right[0]-border_width]
    
    field_bottom_left = (x + field_bottom_left[0]+border_width, y + field_bottom_left[1]-border_width)
    field_top_right = (x + field_top_right[0]-border_width, y + field_top_right[1]+border_width)

    # Reading the colours
    colour_dist = 48
    colours_cropped = capture_screen((field_bottom_left[0], field_top_right[1] - int(colour_dist * 1.5), num_colours * colour_dist, colour_dist))

    # Display the captured image
    display_image(cropped_image)

    return cropped_image, colours_cropped

def read_field_from_image(image):
    global size
    global border

    print("Reading the field data now")
    
    square_size_y = image.shape[0] / (border[1]+size[1])
    square_size_x = image.shape[1] / (border[0]+size[0])

    # Finding all column values
    columns = []
    for i in range(border[0], border[0]+size[0]):
        x_min = int(i * square_size_x)+2
        x_max = int((i+1) * square_size_x)+1
        
        #display_image(image[:, x_min:x_max])

        column = []
        for row in range(border[1]):
            y_min = int(row * square_size_y)+1
            y_max = int((row+1) * square_size_y)-1
            square = image[y_min:y_max, x_min:x_max]
            num = get_number_from_square(square)
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
            num = get_number_from_square(square)
            if (num != 0):
                row.append(num)
        rows.append(row)

    field = (rows, columns, size)

    return field

def get_dataset_img(num):
    image = cv2.imread(f'dataset/{num}.png')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, binary_image = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    return gray[2:-2, 2:-2]

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

def get_number_from_square(img):
    global size
    best_match_index = None
    best_match_score = np.inf  # Initialize to a value that ensures any real score will be an improvement

    for i in range(0, 36):
        dataset_img = get_dataset_img(i)

        # Resize both images to a consistent size
        #dataset_img_resized = cv2.resize(dataset_img, (img.shape[1], img.shape[0]))

        difference = difference_score(img, dataset_img)

        # Update the best match if the current difference is lower
        if difference < best_match_score:
            best_match_score = difference
            best_match_index = i

    #print(f'{best_match_index} with score {best_match_score}')

    #display_image(img, f'Best match: {best_match_index}')

    return best_match_index

def on_key_press(key):
    global bottom_left
    global top_right
    global has_found_bottom_left
    global has_found_top_right
    if keyboard.is_pressed('c'):
        if (not has_found_bottom_left):
            mouse_position = get_mouse_position()
            bottom_left = mouse_position
            print(f"Bottom left found: {mouse_position}")
            has_found_bottom_left = True
            with open("data.txt", "a") as file:
                file.write(f"{bottom_left[0]}\n")
                file.write(f"{bottom_left[1]}\n")
            print("Now put the mouse to the top right of the top right corner of the field, and press C")
        elif (not has_found_top_right):
            mouse_position = get_mouse_position()
            top_right = mouse_position
            print(f"Top right found: {mouse_position}")
            has_found_top_right = True
            with open("data.txt", "a") as file:
                file.write(f"{top_right[0]}\n")
                file.write(f"{top_right[1]}\n")
    

# Finds the corners of the mask
def find_corners(image):
    # image.shape = y,x
    w = image.shape[1]
    h = image.shape[0]
    #print(image.shape)
    bottom_left = None
    top_right = None

    # Finding the bottom left
    for i in range(40):
        if (bottom_left != None):
            break

        for x in range(0, i+1):
            y = i-x

            ix = x
            iy = h-1-y

            if(image[iy,ix] < 127):
                bottom_left = (ix,iy)

    # Finding the top right
    for i in range(40):
        if (top_right != None):
            break

        for x in range(0, i+1):
            y = i-x

            ix = w-1-x
            iy = y

            if(image[iy,ix] < 127):
                top_right = (ix,iy)

    return bottom_left, top_right


if __name__ == "__main__":
    main()
