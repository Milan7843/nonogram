import time

performance_points = []

DISABLED = False

def get_current_time():
    return time.perf_counter()

def add(name):
    if DISABLED: return

    global performance_points    

    index = find(name)

    debug = False

    # First point: no data yet
    if index == -1:
        parent = None
        for p_point in performance_points:
            # The point cannot be a child itself for this
            if not p_point[5] and add_child_recursively(p_point):
                parent = p_point
                break
        #                          name, current time or 0,  sum, sample count, children (indices)  is child
        performance_points.append((name, get_current_time(), 0.0, 0,            [],                 False))

        if parent != None:
            i = len(performance_points)-1
            performance_points[i] = (performance_points[i][0], performance_points[i][1], \
                performance_points[i][2], performance_points[index][3], \
                performance_points[i][4], True)

        return
    else: # When we find the performance point for the second time, we check whether it was found for an 2n-th time

        if performance_points[index][1] != 0.0: # already has a first point
            
            if debug:
                print(f'before {performance_points[index]}')
                print(performance_points[index][2] + (get_current_time() - performance_points[index][1]))

            performance_points[index] = (performance_points[index][0], 0.0, \
                performance_points[index][2] + (get_current_time() - performance_points[index][1]), \
                performance_points[index][3]+1, performance_points[index][4], performance_points[index][5])
            
            if debug:
                print(f'after {performance_points[index]}')

        else: # doesnt have a first point yet
            performance_points[index] = (performance_points[index][0], get_current_time(), \
                performance_points[index][2], performance_points[index][3], \
                performance_points[index][4], performance_points[index][5])
    


    return


def add_child_recursively(p_point):
    if DISABLED: return
    global performance_points

    # The p-point is not ongoing (has equal number of starts and ends), and thus it cannot be this child
    if not is_ongoing(p_point):
        return False

    for child_index in p_point[4]:
        # Return true if the point was added to any child
        if add_child_recursively(performance_points[child_index]):
            return True

    p_point[4].append(len(performance_points))
    return True


def print_performance():
    if DISABLED: return
    global performance_points

    for i, p_point in enumerate(performance_points):
        if p_point[3] > 1:
            delta = p_point[2] * 1000
            avg = delta / p_point[3]
            print(f'{i+1}. {p_point[0] :<20} {delta:.4f}ms, avg of {avg:.4f}ms over {p_point[3]} times')
        else:
            delta = p_point[2] * 1000
            print(f'{i+1}. {p_point[0] :<20} {delta:.4f}ms')

    performance_points = []
    return


def print_performance_hierarchy():
    if DISABLED: return
    global performance_points

    print('------------------------------------')
    print('PERFORMANCE OVERVIEW\n')

    for i, p_point in enumerate(performance_points):
        if not p_point[5]: # If it is not a child
            print_performance_point(p_point)

    performance_points = []
    return



def print_performance_point(p_point, parent=None, depth = 0):
    if DISABLED: return
    delta = p_point[2] * 1000

    prefix = ' ' * depth

    str = f'{prefix}'
    str += f'{p_point[0] :<30}'

    percentage_of_parent = 100
    
    if parent is not None and parent[2] != 0.0:
        percentage_of_parent = delta / (parent[2] * 1000) * 100

    str += f'{percentage_of_parent:.1f}% of parent. '

    str += f'{delta:8.4f}ms, '

    if p_point[3] > 1:
        avg = delta / p_point[3]
        
        str += f'avg of {avg:.4f}ms over {p_point[3]} times'

    print(str)
    
    for p_child in p_point[4]:
        print_performance_point(performance_points[p_child], p_point, depth + 4)


# Returns whether a performance point is currently waiting for its second counterpart
def is_ongoing(p_point):
    return p_point[1] != 0.0




def find(name):
    global performance_points
    # Seeing if there is already a performance point with the given name
    for i, p_point in enumerate(performance_points):
        if p_point[0] == name:
            return i

    # Not found
    return -1