import numpy as np
import keyboard
import pyautogui

import PerformanceTest as pt

intermediate_progress = True

selected_colour = 1
global num_colours

def solve(field, get_square_position, show_progress, num_colours_input):
    global intermediate_progress
    global num_colours
    num_colours = num_colours_input

    print("Starting the solving process! Press C at any time to cancel")

    state = np.zeros(shape=field[2], dtype=np.int16)
    for y in range(state.shape[1]):
        for x in range(state.shape[0]):
            mark_all_colours_allowed_in_square(x, y, state, num_colours)

    pt.add("preprocessing")
    pt.add("removing colours that do not appear in row or col")
    remove_colours_that_do_not_appear_in_row_or_col(field, state)
    pt.add("removing colours that do not appear in row or col")

    pt.add("removing colours that cannot get so close to the borders")
    remove_colour_options_that_cannot_get_so_close_to_the_borders(field, state)
    pt.add("removing colours that cannot get so close to the borders")
    
    pt.add("preprocessing")

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

    print_state(state)

    pt.add("solve")

    if (not intermediate_progress):
        fill_in_all(state, get_square_position)

    return

def fill_in_all(state, get_square_position):
    global selected_colour
    use_dragging = False

    pt.add("fill in all squares")

    is_first = True
    if use_dragging:
        for y in range(state.shape[1]):

            if keyboard.is_pressed('c'):
                break

            held = False
            held_start = 0
            held_colour = 0
            for x in range(state.shape[0]):

                if keyboard.is_pressed('c'):
                    break

                # if we move into a new snake part
                state_colour = get_decided_colour(x, y, state)

                if held:
                    # already holding, stay in the same snake part
                    if state_colour == held_colour:
                        continue
                    else:
                        if state_colour == 0: # empty: no dragging
                            select_colour(held_colour)
                            drag_squares(held_start, y, x-1, y, get_square_position)

                            held = False
                            held_colour = 0
                            continue
                        else:
                            # drag along the snake
                            select_colour(held_colour)
                            drag_squares(held_start, y, x-1, y, get_square_position)

                            held = True
                            held_start = x
                            held_colour = state_colour
                else:
                    # not holding, start dragging
                    if state_colour == 0: # empty: no dragging
                        held_colour = 0
                        continue
                    else: # start dragging
                        held = True
                        held_start = x
                        held_colour = state_colour
            
            # If we are still holding down at the end, drag to the end
            if (held):
                select_colour(held_colour)
                drag_squares(held_start, y, state.shape[0]-1, y, get_square_position)


    else:
        for y in range(state.shape[1]):
            if keyboard.is_pressed('c'):
                break
            for x in range(state.shape[0]):
                if keyboard.is_pressed('c'):
                    break
                if (state[x, y] != 1):
                    if is_first and get_decided_colour(x, y, state) != selected_colour:
                        click_square(x,y, get_square_position)
                    pt.add("selecting colour")
                    select_colour(get_decided_colour(x, y, state))
                    pt.add("selecting colour")

                    pt.add("clicking square")
                    click_square(x,y, get_square_position)
                    pt.add("clicking square")
                    is_first = False

    pt.add("fill in all squares")


def click_square(x,y, get_square_position, left=True):

    px, py = get_square_position(x,y)

    if (left):
        pyautogui.click(px, py)
    else:
        pyautogui.rightClick(px, py)


def select_colour(colour_index):
    global selected_colour

    if selected_colour == colour_index:
        return
    
    pyautogui.press(f"{colour_index % 10}")
    selected_colour = colour_index


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
    progress = 0
    for y in range(state.shape[1]):
        for x in range(state.shape[0]):
            if is_square_decided(x, y, state):
                progress += 1

    print(f'Progress: {progress} / {(len(state) * len(state[0]))} ({int(progress / (len(state) * len(state[0])) * 100)}%)')

def remove_colours_that_do_not_appear_in_row_or_col(field, state):
    rows = field[0]
    columns = field[1]
    size = field[2]
    global num_colours

    for i, row in enumerate(rows):
        for colour in range(1, num_colours+1):
            colour_appears_in_row = any(colour == row_colour for (length, row_colour) in row)
            if not colour_appears_in_row:
                for x in range(size[0]):
                    mark_colour_not_allowed_in_square(colour, x, i, state)

    for i, column in enumerate(columns):
        for colour in range(1, num_colours+1):
            colour_appears_in_col = any(colour == col_colour for (length, col_colour) in column)
            if not colour_appears_in_col:
                for y in range(size[1]):
                    mark_colour_not_allowed_in_square(colour, i, y, state)

def remove_colour_options_that_cannot_get_so_close_to_the_borders(field, state):
    rows = field[0]
    columns = field[1]
    size = field[2]
    global num_colours

    for ri, row in enumerate(rows):
        #print(f"Row {ri}")
        for colour in range(1, num_colours+1):
            first_index = -1
            last_index = -1
            current_x = 0
            for (length, row_colour) in row:
                if row_colour == colour:
                    if first_index == -1:
                        first_index = current_x
                        break
                current_x += length

            current_x = size[0] - 1
            for (length, row_colour) in reversed(row):
                if row_colour == colour:
                    if last_index == -1:
                        last_index = current_x
                        break
                current_x -= length

            #print(f"Colour {colour}: {first_index} - {last_index}")
        
            if first_index != -1:
                for x in range(first_index):
                    mark_colour_not_allowed_in_square(colour, x, ri, state)
            if last_index != -1:
                for x in range(last_index+1, size[0]):
                    mark_colour_not_allowed_in_square(colour, x, ri, state)

    for ci, column in enumerate(columns):
        #print(f"Column {ci}")
        for colour in range(1, num_colours+1):
            first_index = -1
            last_index = -1
            current_x = 0
            for (length, column_colour) in column:
                if column_colour == colour:
                    if first_index == -1:
                        first_index = current_x
                        break
                current_x += length

            current_x = size[1] - 1
            for (length, column_colour) in reversed(column):
                if column_colour == colour:
                    if last_index == -1:
                        last_index = current_x
                        break
                current_x -= length

            #print(f"Colour {colour}: {first_index} - {last_index}")
        
            if first_index != -1:
                for x in range(first_index):
                    mark_colour_not_allowed_in_square(colour, ci, x, state)
            if last_index != -1:
                for x in range(last_index+1, size[1]):
                    mark_colour_not_allowed_in_square(colour, ci, x, state)


            



def iteration(field, state, rows_done, cols_done, get_square_position, iteration_index):
    rows = field[0]
    columns = field[1]
    size = field[2]

    do_big_only = iteration_index < 3

    print(f'Iteration {iteration_index+1} (big: {do_big_only})')

    values_to_sort = []
    for i, row in enumerate(rows):
        # If the row is already done, we don't need to sort it
        if rows_done[i] == 1:
            values_to_sort.append(-100000)
            continue
        values_to_sort.append(np.sum(val[0] for val in row) + len(row) - 1 + np.count_nonzero(state[:, i]))

    for i, col in enumerate(columns):
        # If the column is already done, we don't need to sort it
        if cols_done[i] == 1:
            values_to_sort.append(-100000)
            continue
        values_to_sort.append(np.sum(col) + len(col) - 1 + np.count_nonzero(state[i, :]))
    
    #print(rows)
    #print(columns)
    #print(values_to_sort)
    print_state(state)

    indices = np.arange(len(rows) + len(columns))#np.argsort(-np.array(values_to_sort))

    for j, i in enumerate(indices):
        #if do_big_only and j > 40:
        #    break

        if keyboard.is_pressed('c'):
            break

        is_row = i < len(rows)
        if not is_row:
            i -= len(rows)

        if (is_row):
            if (rows_done[i] == 1):
                continue
            
            common_filled_squares, common_unfilled_squares = common_squares(rows[i], size[0], True, i, state)
            for col in range(size[0]):
                if keyboard.is_pressed('c'):
                    break
                if (common_filled_squares[col] != 0):
                    state = mark_square_filled(state, col, i, get_square_position, common_filled_squares[col])
                if (common_unfilled_squares[col] == 1):
                    state = mark_square_empty(state, col, i, get_square_position)

            #print(f'{i+1} / {len(rows)} rows')

        else:
            if (cols_done[i] == 1):
                continue

            common_filled_squares, common_unfilled_squares = common_squares(columns[i], size[1], False, i, state)
            for row in range(size[1]):
                if keyboard.is_pressed('c'):
                    break
                if (common_filled_squares[row] != 0):
                    state = mark_square_filled(state, i, row, get_square_position, common_filled_squares[row])
                if (common_unfilled_squares[row] == 1):
                    state = mark_square_empty(state, i, row, get_square_position)

            #print(f'{i+1} / {len(columns)} cols')

        #print_state(state)
            

    return state

def mark_rows_cols_as_done(state, rows_done, cols_done):
    for ri in range(state.shape[1]):
        row_done = True
        for i in range(state.shape[0]):
            if not is_square_decided(i, ri, state):
                row_done = False
                break

        if (row_done):
            rows_done[ri] = 1

    for ci in range(state.shape[0]):
        col_done = True
        for i in range(state.shape[1]):
            if not is_square_decided(ci, i, state):
                col_done = False
                break
        
        if (col_done):
            cols_done[ci] = 1
    return rows_done, cols_done


def mark_square_filled(state, x, y, get_square_position, colour_index):
    global intermediate_progress
    mark_colour_only_in_square(colour_index, x, y, state)
    if (intermediate_progress and state[x, y] != 1):
        select_colour(colour_index)
        click_square(x, y, get_square_position, True)
    return state

def mark_square_empty(state, x, y, get_square_position):
    state[x, y] = 1
    if (intermediate_progress and state[x, y] != 2):
        click_square(x, y, get_square_position, False)
    return state

def generate_configurations(blocks, colours, width, configs, is_row, row_col_index, state, current_config=[], spaces_used=0, index=0):

    if (index == len(blocks)):
        #print(f'final: {current_config}')
        if (is_valid(current_config, is_row, row_col_index, state)):
            configs.append(current_config)
        return

    if (len(current_config) == 0):
        current_config = np.zeros(shape=(width), dtype=int)

    #if (not is_row and row_col_index == 2):
    #    print(f'blocks: {blocks}, colours {colours}')
    #    print(f'current config: {current_config} at {index}')
    current_block = blocks[index]
    current_colour = colours[index]
    squares_still_to_place = np.int32(np.sum(blocks[index+1:]))

    keep_space_between_blocks = False

    if (squares_still_to_place > 0 and index < len(blocks)-1 and colours[index+1] == current_colour):
        squares_still_to_place += 1 # keep one space between current and the others
        keep_space_between_blocks = True

    squares_left = width - squares_still_to_place - spaces_used

    possible_configs = squares_left - current_block + 1

    #if (not is_row and row_col_index == 2):
    #    print(f'current: {current_block}, left: {squares_left}, to place: {squares_still_to_place}, spaces used: {spaces_used}, possible configurations: {possible_configs}')

    for i in range(0, possible_configs):
        new_config = np.copy(current_config)
        for s in range(current_block):
            new_config[i+s+spaces_used] = current_colour

        if (is_valid_check_to_index(new_config, i+current_block+spaces_used, is_row, row_col_index, state)):
            new_spaces_used = spaces_used + current_block + (1 if keep_space_between_blocks else 0) + i
            generate_configurations(blocks, colours, width, configs, is_row, row_col_index, state, new_config, new_spaces_used, index+1)

def print_configurations(configs):
    for config in configs:
        for c in config:
            if c == 0:
                print('_', end='')
            else:
                print(f'{c}', end='')
        print('')

def print_state(state):
    global num_colours
    


    for x in range(state.shape[0] + 1):
        print('--', end='')

    print('')
    
    for y in range(state.shape[1]):
        print('|', end='')
        for x in range(state.shape[0]):
            if (state[x, y] == 1):
                print(' ', end='')
            elif is_square_decided(x, y, state):
                print(f'{get_decided_colour(x, y, state)}', end='')
            else:
                print(f'?', end='')
            print(f' ', end='')
        print('|')
    for x in range(state.shape[0] + 1):
        print('--', end='')
    print('')

    for colour_index in range(1, num_colours+1):
        print(f'Colour {colour_index}:')

        for x in range(state.shape[0] + 1):
            print('--', end='')

        print('')
        
        for y in range(state.shape[1]):
            print('|', end='')
            for x in range(state.shape[0]):
                if (state[x, y] == 1):
                    print(' ', end='')
                elif is_colour_allowed_in_square(colour_index, x, y, state):
                    print(f'{colour_index}', end='')
                else:
                    print(f' ', end='')
                print(f' ', end='')
            print('|')

        for x in range(state.shape[0] + 1):
            print('--', end='')
        print('')


    return
    for y in range(state.shape[1]):
        for x in range(state.shape[0]):
            print(f"[{x}, {y}]", end='')
            for i in range(0, num_colours+1):
                print(f"{"1" if is_colour_allowed_in_square(i, x, y, state) else 0}", end='')
            print(f' decided? {is_square_decided(x, y, state)}')

# Returns whether a square only has a single option left
def is_square_decided(x, y, state):
    global num_colours

    for i in range(0, num_colours+1):
        if is_colour_only_in_square(i, x, y, state):
            return True
        
    return False

def get_decided_colour(x, y, state):
    global num_colours

    for i in range(0, num_colours+1):
        if is_colour_only_in_square(i, x, y, state):
            return i
        
    return -1

def is_colour_only_in_square(colour, x, y, state):
    state_value = state[x, y]

    # Reading the specific bit of the colour index
    return (state_value & (1 << colour)) != 0 and state_value == (1 << colour)

def is_colour_allowed_in_square(colour, x, y, state):

    state_value = state[x, y]
    
    if state_value == -1:
        return False

    # Reading the specific bit of the colour index
    return (state_value & (1 << colour)) != 0

def mark_colour_only_in_square(colour, x, y, state):
    state[x, y] = (1 << colour)

def mark_colour_allowed_in_square(colour, x, y, state):
    state[x, y] |= (1 << colour)

def mark_all_colours_allowed_in_square(x, y, state, num_colours):
    for i in range(0, num_colours+1):
        mark_colour_allowed_in_square(i, x, y, state)

def mark_colour_not_allowed_in_square(colour, x, y, state):
    state[x, y] &= ~(1 << colour)


def common_squares(blocks, width, is_row, row_col_index, state):
    configurations = []
    configurations_iter = []
    # print("starting generation")
    pt.add("generate configurations")
    generate_configurations(list(block for (block, colour) in blocks), list(colour for (block, colour) in blocks), width, configurations, is_row, row_col_index, state)
    pt.add("generate configurations")

    #print_configurations(configurations)
    # print(f"equal: {configurations == configurations_iter}")
    # print(f"finished generating {len(configurations)} configurations")
    
    # Check for common squares in all configurations
    common_filled_squares = [configurations[0][i] if all(config[i] == configurations[0][i] for config in configurations) else 0 for i in range(width)]
    common_unfilled_squares = [1 if all(config[i] == 0 for config in configurations) else 0 for i in range(width)]
    
    # Removing colours that do not appear in any configuration for each square
    for i in range(width):
        for c in range(0, num_colours+1):
            # If the colour does not appear in any configuration, mark it as not allowed
            if all(config[i] != c for config in configurations):
                if is_row:
                    mark_colour_not_allowed_in_square(c, i, row_col_index, state)
                else:
                    mark_colour_not_allowed_in_square(c, row_col_index, i, state)
    
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
        # make sure that every value is legal
        if not is_colour_allowed_in_square(row[i], i, row_index, state):
            return False

    return True

def is_valid_col(col, check_to_index, col_index, state):
    for i in range(check_to_index):
        # make sure that every value is legal
        if not is_colour_allowed_in_square(col[i], col_index, i, state):
            return False

    return True