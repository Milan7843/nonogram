import numpy as np
import keyboard
import pyautogui

intermediate_progress = False

def solve(field, get_square_position, show_progress):
    global intermediate_progress

    print("Starting the solving process! Press C at any time to cancel")

    state = np.zeros(shape=field[2])
    cols_done = np.zeros(field[2][0])
    rows_done = np.zeros(field[2][1])

    intermediate_progress = show_progress

    while (True):
        if keyboard.is_pressed('c'):
            break

        state = iteration(field, state, rows_done, cols_done, get_square_position)

        rows_done, cols_done = mark_rows_cols_as_done(state, rows_done, cols_done)

        print_progress(state)

        if (all(rows_done == 1) and all(cols_done == 1)):
            print(f'Crossword completed!')
            break

    if (not intermediate_progress):
        fill_in_all(state, get_square_position)
    
    return

def fill_in_all(state, get_square_position):
    use_dragging = True

    if use_dragging:
        for y in range(state.shape[1]):

            if keyboard.is_pressed('c'):
                break

            held = False
            held_start = 0
            for x in range(state.shape[0]):

                if keyboard.is_pressed('c'):
                    break

                # if we move into a new snake part
                if (state[x, y] == 1 and not held):
                    held = True
                    held_start = x
                # if we move out of a snake part
                elif (state[x,y] == 2 and held):
                    held = False
                    # drag along the snake
                    drag_squares(held_start, y, x-1, y, get_square_position)
            
            # If we are still holding down at the end, drag to the end
            if (held):
                    drag_squares(held_start, y, state.shape[0]-1, y, get_square_position)


    else:
        for y in range(state.shape[1]):
            if keyboard.is_pressed('c'):
                break
            for x in range(state.shape[0]):
                if keyboard.is_pressed('c'):
                    break
                if (state[x, y] == 1):
                    click_square(x,y, get_square_position)

def click_square(x,y, get_square_position, left=True):

    px, py = get_square_position(x,y)

    if (left):
        pyautogui.click(px, py)
    else:
        pyautogui.rightClick(px, py)

def drag_squares(from_x, from_y, to_x, to_y, get_square_position):

    from_px, from_py = get_square_position(from_x, from_y)
    to_px, to_py = get_square_position(to_x, to_y)

    # Move the mouse to the starting position
    pyautogui.moveTo(from_px, from_py)

    # Simulate mouse down (hold the mouse button)
    pyautogui.mouseDown()

    # Move the mouse to the ending position
    pyautogui.moveTo(to_px, to_py, duration=0)  # You can adjust the duration to control the speed of dragging

    # Simulate mouse up (release the mouse button)
    pyautogui.mouseUp()


def print_progress(state):
    print(f'Progress: {np.count_nonzero(state)} / {(len(state) * len(state[0]))} ({int((np.count_nonzero(state)) / (len(state) * len(state[0])) * 100)}%)')

def iteration(field, state, rows_done, cols_done, get_square_position):
    rows = field[0]
    columns = field[1]
    size = field[2]

    for i, row in enumerate(rows):
        if (rows_done[i] == 1):
            continue
        if keyboard.is_pressed('c'):
            break
        
        common_filled_squares, common_unfilled_squares = common_squares(row, size[0], True, i, state)
        for col in range(size[0]):
            if keyboard.is_pressed('c'):
                break
            if (common_filled_squares[col] == 1):
                state = mark_square_filled(state, col, i, get_square_position)
            if (common_unfilled_squares[col] == 1):
                state = mark_square_empty(state, col, i, get_square_position)

    for i, col in enumerate(columns):
        if (cols_done[i] == 1):
            continue
        if keyboard.is_pressed('c'):
            break

        common_filled_squares, common_unfilled_squares = common_squares(col, size[1], False, i, state)
        for row in range(size[1]):
            if keyboard.is_pressed('c'):
                break
            if (common_filled_squares[row] == 1):
                state = mark_square_filled(state, i, row, get_square_position)
            if (common_unfilled_squares[row] == 1):
                state = mark_square_empty(state, i, row, get_square_position)
    return state

def mark_rows_cols_as_done(state, rows_done, cols_done):
    for ri in range(state.shape[1]):
        row_done = True
        for i in range(state.shape[0]):
            if (state[i, ri] == 0):
                row_done = False
                break

        if (row_done):
            rows_done[ri] = 1

    for ci in range(state.shape[0]):
        col_done = True
        for i in range(state.shape[1]):
            if (state[ci, i] == 0):
                col_done = False
                break
        
        if (col_done):
            cols_done[ci] = 1
    return rows_done, cols_done


def mark_square_filled(state, x, y, get_square_position):
    global intermediate_progress
    if (intermediate_progress and state[x, y] != 1):
        click_square(x, y, get_square_position, True)
    state[x, y] = 1
    return state

def mark_square_empty(state, x, y, get_square_position):
    if (intermediate_progress and state[x, y] != 2):
        click_square(x, y, get_square_position, False)
    state[x, y] = 2
    return state

def generate_configurations(blocks, width, configs, is_row, row_col_index, state, current_config=[], spaces_used=0, index=0):

    if (index == len(blocks)):
        #print(f'final: {current_config}')
        if (is_valid(current_config, is_row, row_col_index, state)):
            configs.append(current_config)
        return

    if (len(current_config) == 0):
        current_config = np.zeros(shape=(width), dtype=int)

    #print(f'current config: {current_config} at {index}')
    current_block = blocks[index]
    squares_still_to_place = np.int32(np.sum(blocks[index+1:]))

    if (squares_still_to_place > 0):
        squares_still_to_place += 1 # keep one space between current and the others

    squares_left = width - squares_still_to_place - spaces_used

    possible_configs = squares_left - current_block + 1

    #print(f'current: {current_block}, left: {squares_left}, to place: {squares_still_to_place}, spaces used: {spaces_used}, possible configurations: {possible_configs}')

    for i in range(0, possible_configs):
        new_config = np.copy(current_config)
        for s in range(current_block):
            new_config[i+s+spaces_used] = 1

        if (is_valid_check_to_index(new_config, i+current_block+spaces_used, is_row, row_col_index, state)):
            new_spaces_used = spaces_used + current_block + 1 + i
            generate_configurations(blocks, width, configs, is_row, row_col_index, state, new_config, new_spaces_used, index+1)


def common_squares(blocks, width, is_row, row_col_index, state):
    configurations = []
    generate_configurations(blocks, width, configurations, is_row, row_col_index, state)
    
    # Check for common squares in all configurations
    common_filled_squares = [1 if all(config[i] == 1 for config in configurations) else 0 for i in range(width)]
    common_unfilled_squares = [1 if all(config[i] == 0 for config in configurations) else 0 for i in range(width)]
    
    return common_filled_squares, common_unfilled_squares

def is_valid_check_to_index(config, check_to_index, is_row, row_col_index, state):
    if (is_row):
        return is_valid_row(config, check_to_index, row_col_index, state)
    else:
        return is_valid_col(config, check_to_index, row_col_index, state)

def is_valid(config, is_row, row_col_index, state):
    if (is_row):
        return is_valid_row(config, len(config), row_col_index, state)
    else:
        return is_valid_col(config, len(config), row_col_index, state)
    
def is_valid_row(row, check_to_index, row_index, state):
    for i in range(check_to_index):
        # make sure that every value is legal
        if (state[i, row_index] == 2): # marked as empty already
            if (row[i] == 1): # but the row wasn't empty
                return False
        if (state[i, row_index] == 1): # marked as filled already
            if (row[i] == 0): # but the row was empty
                return False

    return True

def is_valid_col(col, check_to_index, col_index, state):
    for i in range(check_to_index):
        # make sure that every value is legal
        if (state[col_index, i] == 2): # marked as empty already
            if (col[i] == 1): # but the row wasn't empty
                return False
        if (state[col_index, i] == 1): # marked as filled already
            if (col[i] == 0): # but the row was empty
                return False

    return True