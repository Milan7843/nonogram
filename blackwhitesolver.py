import numpy as np
import keyboard
import pyautogui

import PerformanceTest as pt

intermediate_progress = False

def solve(field, get_square_position, show_progress):
    global intermediate_progress

    print("Starting the solving process! Press C at any time to cancel")

    state = np.zeros(shape=field[2])
    cols_done = np.zeros(field[2][0])
    rows_done = np.zeros(field[2][1])

    intermediate_progress = show_progress

    iteration_index = 0

    pt.add("solve")

    while (True):
        if keyboard.is_pressed('c'):
            break

        state = iteration(field, state, rows_done, cols_done, get_square_position, iteration_index)

        rows_done, cols_done = mark_rows_cols_as_done(state, rows_done, cols_done)

        print_progress(state)

        iteration_index += 1

        if (all(rows_done == 1) and all(cols_done == 1)):
            print(f'Crossword completed!')
            break

    pt.add("solve")

    if (not intermediate_progress):
        fill_in_all(state, get_square_position)
    
    pt.print_performance_hierarchy()

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



def iteration(field, state, rows_done, cols_done, get_square_position, iteration_index):
    rows = field[0]
    columns = field[1]
    size = field[2]

    do_big_only = iteration_index < 3

    print(f'Iteration {iteration_index+1} (big: {do_big_only})')
    
    pt.add("determine order")

    values_to_sort = []
    for i, row in enumerate(rows):
        # If the row is already done, we don't need to sort it
        if rows_done[i] == 1:
            values_to_sort.append(-100000)
            continue
        values_to_sort.append(np.sum(row) + len(row) - 1 + np.count_nonzero(state[:, i]))

    for i, col in enumerate(columns):
        # If the column is already done, we don't need to sort it
        if cols_done[i] == 1:
            values_to_sort.append(-100000)
            continue
        values_to_sort.append(np.sum(col) + len(col) - 1 + np.count_nonzero(state[i, :]))

    indices = np.argsort(-np.array(values_to_sort))
    
    pt.add("determine order")

    for j, i in enumerate(indices):
        if do_big_only and j > 40:
            break

        if keyboard.is_pressed('c'):
            break

        is_row = i < len(rows)
        if not is_row:
            i -= len(rows)

        if (is_row):
            if (rows_done[i] == 1):
                continue
            
            common_filled_squares, common_unfilled_squares = common_squares(rows[i], size[0], True, i, state)

            pt.add("marking squares")
            for col in range(size[0]):
                if keyboard.is_pressed('c'):
                    break
                if (common_filled_squares[col] == 1):
                    state = mark_square_filled(state, col, i, get_square_position)
                if (common_unfilled_squares[col] == 1):
                    state = mark_square_empty(state, col, i, get_square_position)
            pt.add("marking squares")

            print(f'{i+1} / {len(rows)} rows')

        else:
            if (cols_done[i] == 1):
                continue

            common_filled_squares, common_unfilled_squares = common_squares(columns[i], size[1], False, i, state)
            
            pt.add("marking squares")
            for row in range(size[1]):
                if keyboard.is_pressed('c'):
                    break
                if (common_filled_squares[row] == 1):
                    state = mark_square_filled(state, i, row, get_square_position)
                if (common_unfilled_squares[row] == 1):
                    state = mark_square_empty(state, i, row, get_square_position)
            pt.add("marking squares")

            print(f'{i+1} / {len(columns)} cols')
            

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
        #if (is_valid(current_config, is_row, row_col_index, state)):
        pt.add("create copy + append")
        configs.append(np.copy(current_config))
        pt.add("create copy + append")
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
        start = spaces_used + i
        end = start + current_block
        current_config[start:end] = 1

        check_to_index = i+current_block+spaces_used

        if (index == len(blocks)-1):
            check_to_index = width

        if (is_valid_check_to_index(current_config, check_to_index, is_row, row_col_index, state)):
            new_spaces_used = spaces_used + current_block + 1 + i
            generate_configurations(blocks, width, configs, is_row, row_col_index, state, current_config, new_spaces_used, index+1)

        # Backtrack
        current_config[start:end] = 0

def generate_configurations_big(blocks, width, configs, is_row, row_col_index, state):

    if (np.sum(blocks) < width * 0.4 or len(blocks) > 5):
        configs.append(np.ones(shape=(width), dtype=int) * 2)
        return
    
    generate_configurations(blocks, width, configs, is_row, row_col_index, state)
    return


def common_squares(blocks, width, is_row, row_col_index, state):
    configurations = []
    configurations_iter = []
    # print("starting generation")
    pt.add("generate configurations")
    generate_configurations(blocks, width, configurations, is_row, row_col_index, state)
    pt.add("generate configurations")
    # print(f"equal: {configurations == configurations_iter}")
    # print(f"finished generating {len(configurations)} configurations")
    
    # Check for common squares in all configurations
    pt.add("common squares")
    common_filled_squares = [1 if all(config[i] == 1 for config in configurations) else 0 for i in range(width)]
    common_unfilled_squares = [1 if all(config[i] == 0 for config in configurations) else 0 for i in range(width)]
    pt.add("common squares")
    
    return common_filled_squares, common_unfilled_squares

def is_valid_check_to_index(config, check_to_index, is_row, row_col_index, state):
    pt.add("validity check")
    if (is_row):
        valid = is_valid_row(config, check_to_index, row_col_index, state)
        pt.add("validity check")
        return valid
    else:
        valid = is_valid_col(config, check_to_index, row_col_index, state)
        pt.add("validity check")
        return valid

def is_valid(config, is_row, row_col_index, state):
    if (is_row):
        return is_valid_row(config, len(config), row_col_index, state)
    else:
        return is_valid_col(config, len(config), row_col_index, state)
    
def is_valid_row(row, check_to_index, row_index, state):
    for i in range(check_to_index):
        state_val = state[i, row_index]
        row_val = row[i]

        if state_val == 2 and row_val == 1:  # Marked as empty but row not empty
            return False
        if state_val == 1 and row_val == 0:  # Marked as filled but row empty
            return False

    return True

def is_valid_col(col, check_to_index, col_index, state):
    for i in range(check_to_index):
        state_val = state[col_index, i]
        col_val = col[i]

        if state_val == 2 and col_val == 1:  # Marked as empty but row not empty
            return False
        if state_val == 1 and col_val == 0:  # Marked as filled but row empty
            return False

    return True