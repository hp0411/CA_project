"""
A 2D cellular automata model for simulating a forest fire - extended off of capyle, see ref section.

Model considers terrain type and its flammability as well as varying wind speeds and directions.

See README.md file for detailed documentation and attached report for detailed explanation and
justification as to why certain design decisions were made.

Author: Ethan Jones, Thanh Hang Phan, Aslihan Ilgin Okan, Hamza Karim

"""
import re
import sys
import argparse
import inspect
import random

import numpy as np
from scipy.ndimage import rotate
import random

# Handle local imports
this_file_loc = (inspect.stack()[0][1])
main_dir_loc = this_file_loc[:this_file_loc.index('ca_descriptions')]
sys.path.append(main_dir_loc)
sys.path.append(main_dir_loc + 'capyle')
sys.path.append(main_dir_loc + 'capyle/ca')
sys.path.append(main_dir_loc + 'capyle/guicomponents')

from capyle.ca import Grid2D, Neighbourhood, CAConfig, randomise2d
import capyle.utils as utils

CHAPARRAL = 0 #Define the different states within the model
LAKE = 1
FOREST = 2
SCRUBLAND = 3
BURNT = 4
TOWN = 5
FIRE = 6

rotate_scores = { #Defines the rotation rates; used for rotating the wind kernel to match wind direction
    "N": 0,
    "W": 1,
    "S": 2,
    "E": 3
}

flammability_score = { #Defines flammability scores, these have been quantified and justified in the brief.
    0: 3, # burns easily - CHAPPARAL
    1: 0, # does not burn - LAKE
    2: 1, # does not burn easily - FOREST
    3: 2, # burns easily but not as easy as chaparral - SCRUBLAND
    4: 0, # does not burn - BURNT
    5: 1, # burns but not as easily as scrubland - TOWN
    6: 0  # does not burn easily cos it's already burning - FIRE
}


#variable for time for town fire is set to -1 initially
time_for_town_fire = -1


def add_forest_extension(grid):

    if FOREST_EXTENSION_LAYOUT == 1:
        grid[5:31, 1:52] = FOREST
    elif FOREST_EXTENSION_LAYOUT == 2:
        grid[71:87, 1:60] = FOREST
        grid[87:100, 1:35] = FOREST
    elif FOREST_EXTENSION_LAYOUT == 3:
        grid[11:81, 52:72] = FOREST
        grid[71:81, 1:52] = FOREST
    elif FOREST_EXTENSION_LAYOUT == 4:
        grid[11:81, 61:72] = FOREST
    elif FOREST_EXTENSION_LAYOUT == 5:
        grid[11:81, 72:75] = FOREST
        grid[11:81, 58:61] = FOREST
        grid[8:11, 58:75] = FOREST
        grid[79:82, 58:75] = FOREST
    return grid

def define_initial_grid():
    """
    Defines the starting grid of the environment including ignition sources. 
    
    Note: if no ignition source is passed, the system will quit out.
    
    Returns
    -------
    `start_grid`: np.array
        A 2D array detailing the layout of the initial environment grid using aforementioned states.
    """
    start_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
    start_grid[0:102, 0:1] = BURNT # left border
    start_grid[0:102, 101:102] = BURNT # right border
    start_grid[0:1, 0:102] = BURNT # top border
    start_grid[101:102, 0:102] = BURNT # bottom border
    start_grid[36:41, 11:52] = LAKE
    start_grid[41:71, 1:52] = FOREST
    start_grid[11:31, 31:52] = FOREST
    start_grid[11:81, 61:72] = SCRUBLAND
    start_grid = add_forest_extension(start_grid)
    start_grid[88:93, 38:43] = TOWN
    if INCINERATOR_SOURCE:
        start_grid[0, 101] = FIRE
        start_grid[0, 100] = FIRE
    if POWER_PLANT_SOURCE:
        start_grid[0, 0] = FIRE
        start_grid[0, 1] = FIRE
    if not INCINERATOR_SOURCE and POWER_PLANT_SOURCE:
        sys.exit(-1)
    return start_grid

def get_neighbourhood(grid, x_coord, y_coord):
    """
    Retrieves the Moore neighbourhood of a given cell.
    
    Parameters
    ----------
    `grid`: np.array
        A 2D array containing the states of the grid at the current timestep.
    `x_coord`: int
        The x coordinate for the cell whose neighbourhood is being retrieved.
    `y_coord`: int
        The y coordinate for the cell whose neighbourhood is being retrieved.
    
    Returns
    -------
    `neighbourhood`: np.array
        A 2D array containing the neighbourhood states of the passed in cell - uses Moore neighbourhood.
    """
    neighbourhood = np.array(
        [
         [grid[x_coord-1][y_coord-1], grid[x_coord-1][y_coord], grid[x_coord-1][y_coord+1]],
         [grid[x_coord][y_coord-1], grid[x_coord][y_coord], grid[x_coord][y_coord+1]],
         [grid[x_coord+1][y_coord-1], grid[x_coord+1][y_coord], grid[x_coord+1][y_coord+1]]
        ]
    )
    return neighbourhood

def apply_flamability_scores(neighbourhood):
    """
    Maps the states of a Moore neighbourhood to the aforementioned flammability scores.
    
    Parameters
    ----------
    `neighbourhood`: np.array
        A 2D array containing the neighbourhood states of a cell within the grid - uses a Moore
        neighbourhood.
    
    Returns
    -------
    `neighbourhood`: np.array
         A 2D array containing the neighbourhood flammability scores of a cell within the grid -
        uses a Moore neighbourhood.
    """
    for i in range(len(neighbourhood)):
        for j in range(len(neighbourhood[i])):
                cell = neighbourhood[i][j]
                neighbourhood[i][j] = flammability_score.get(cell)
    return neighbourhood

def apply_wind_kernel(grid, cells_to_burn_this_iter):
    """
    Applys the wind kernel to the cells that ignited in the current iter. Uses a probabilistic model
    that implements inverse proportionality between ignition probability and distance from a fire
    source. Also considers wind direction to encourage cells in the direction of the wind to ignite
    easier than other directions - see report for all details.
    
    Parameters
    ----------
    `grid`: np.array
        A 2D array containing the states of the grid at the current timestep.
    `cells_to_burn_this_iter`: List
        A list of cells that ignited in the current iteration.
    
    Returns
    -------
    `additonal_cells_to_burn`: List
        A list of additonal cells that will be ignited due to the implemented wind speed / direction
        model.
    """
    additonal_cells_to_burn = []
    for cell in cells_to_burn_this_iter: #Loop through all cells that ignited in the iteration
        x, y = cell[0], cell[1]
        neighbourhood = get_neighbourhood(grid, x, y) #Gets 3x3 neighbourhood of the current cell
        flamability_neighbourhood = apply_flamability_scores(neighbourhood) #Map neighbourhood states to flammability scores
        wind_modified_neighbourhood = neighbourhood+WIND_KERNEL #Add flammability scores with wind kernel
        count = 0 #Counter to keep track of which cell within 3x3 grid we are referring to
        for row in wind_modified_neighbourhood:
            for cell in row:
                if cell >= 4:
                    if count == 1: #If current cell is north of the fire
                        if WIND_DIR == "N":
                            add_prob = 0.15 #Give bonus probability if wind is in the same direction of the cell being assessed
                        else:
                            add_prob = 0.03
                        if all(coord < 96 for coord in [x, y]) and all(coord > 5 for coord in [x, y]): #Ensure that the grid bounds won't be overran
                            for z in range (1, int(cell)): #Loop through number of cells based on wind_modified_neighbourhood (between 1-3 cells)
                                dist_factor = 0.075 #Distance factor - ignition probability should be reversely proportional to distance from fire
                                if grid[x-z][y] not in [1, 4, 6]: #Ensure cell isn't fire, lake or burnt
                                    prob = random.random() * (1+add_prob) - dist_factor #Random probability of ignition based on wind direction and distance
                                    if prob > 0.35: #Set threshold for north cell lower than others - encourage fire to spread to north
                                        additonal_cells_to_burn.append([x-z, y])
                                if grid[x-z][y-z] not in [1, 4, 6]:
                                    prob = random.random() * (1+add_prob) - dist_factor
                                    if prob > 0.45:
                                        additonal_cells_to_burn.append([x-z, y-z])
                                if grid[x-z][y+z] not in [1, 4, 6]:
                                    prob = random.random() * (1+add_prob) - dist_factor
                                    if prob > 0.45:
                                        additonal_cells_to_burn.append([x-z, y+z])
                                dist_factor = dist_factor + 0.075 #Increase distance factor as we migrate away from fire source cell.
                    elif count == 5: #If current cell is east of the fire
                        if WIND_DIR == "E":
                            add_prob = 0.15 #Give bonus probability if wind is in the same direction of the cell being assessed
                        else:
                            add_prob = 0.03
                        if all(coord < 96 for coord in [x, y]) and all(coord > 5 for coord in [x, y]): #Ensure that the grid bounds won't be overran
                            for z in range (1, int(cell)): #Loop through number of cells based on wind_modified_neighbourhood (between 1-3 cells)
                                dist_factor = 0.075 #Distance factor - ignition probability should be reversely proportional to distance from fire
                                if grid[x-z][y+z] not in [1, 4, 6]: #Ensure cell isn't fire, lake or burnt
                                    prob = random.random() * (1+add_prob) - dist_factor #Random probability of ignition based on wind direction and distance
                                    if prob > 0.45:
                                        additonal_cells_to_burn.append([x-z, y+z])
                                if grid[x][y+z] not in [1, 4, 6]:
                                    prob = random.random() * (1+add_prob) - dist_factor
                                    if prob > 0.35: #Set threshold for east cell lower than others - encourage fire to spread to east
                                        additonal_cells_to_burn.append([x, y+z])
                                if grid[x+z][y+z] not in [1, 4, 6]:
                                    prob = random.random() * (1+add_prob) - dist_factor
                                    if prob > 0.45:
                                        additonal_cells_to_burn.append([x+z, y+z])
                                dist_factor = dist_factor + 0.075 #Increase distance factor as we migrate away from fire source cell.
                    elif count == 3: #If current cell is west of the fire
                        if WIND_DIR == "W":
                            add_prob = 0.15 #Give bonus probability if wind is in the same direction of the cell being assessed
                        else:
                            add_prob = 0.03
                        if all(coord < 96 for coord in [x, y]) and all(coord > 5 for coord in [x, y]): #Ensure that the grid bounds won't be overran
                            for z in range (1, int(cell)): #Loop through number of cells based on wind_modified_neighbourhood (between 1-3 cells)
                                dist_factor = 0.075 #Distance factor - ignition probability should be reversely proportional to distance from fire
                                if grid[x-z][y-z] not in [1, 4, 6]: #Ensure cell isn't fire, lake or burnt
                                    prob = random.random() * (1+add_prob) - dist_factor #Random probability of ignition based on wind direction and distance
                                    if prob > 0.45:
                                        additonal_cells_to_burn.append([x-z, y-z])
                                if grid[x][y-z] not in [1, 4, 6]:
                                    prob = random.random() * (1+add_prob) - dist_factor
                                    if prob > 0.35: #Set threshold for west cell lower than others - encourage fire to spread to west
                                        additonal_cells_to_burn.append([x, y-z])
                                    additonal_cells_to_burn.append([x, y-z])
                                if grid[x+z][y-z] not in [1, 4, 6]:
                                    prob = random.random() * (1+add_prob) - dist_factor
                                    if prob > 0.45:
                                        additonal_cells_to_burn.append([x+z, y-z])
                                dist_factor = dist_factor + 0.075 #Increase distance factor as we migrate away from fire source cell.
                    elif count == 7: #If current cell is south of the fire
                        if WIND_DIR == "S":
                            add_prob = 0.15 #Give bonus probability if wind is in the same direction of the cell being assessed
                        else:
                            add_prob = 0.03
                        if all(coord < 96 for coord in [x, y]) and all(coord > 5 for coord in [x, y]): #Ensure that the grid bounds won't be overran
                            for val in range (1, int(cell)): #Loop through number of cells based on wind_modified_neighbourhood (between 1-3 cells)
                                dist_factor = 0.075 #Distance factor - ignition probability should be reversely proportional to distance from fire
                                if grid[x+val][y+val] not in [1, 4, 6]: #Ensure cell isn't fire, lake or burnt
                                    prob = random.random() * (1+add_prob) - dist_factor #Random probability of ignition based on wind direction and distance
                                    if prob > 0.45:
                                        additonal_cells_to_burn.append([x+val, y+val])
                                if grid[x+val][y] not in [1, 4, 6]:
                                    prob = random.random() * (1+add_prob+0.1) - dist_factor
                                    if prob > 0.35: #Set threshold for south cell lower than others - encourage fire to spread to south
                                        additonal_cells_to_burn.append([x+val, y])
                                if grid[x+val][y-val] not in [1, 4, 6]:
                                    prob = random.random() * (1+add_prob) - dist_factor
                                    if prob > 0.45:
                                        additonal_cells_to_burn.append([x+val, y-val])
                                dist_factor = dist_factor + 0.075 #Increase distance factor as we migrate away from fire source cell.
                count += 1
    return additonal_cells_to_burn #Return list of cells to be ignited due to random probability due to wind

def wind_kernel():
    """
    Defines a speed and direction sensitive wind kernel. Only functional if wind direction is one 
    of: N, E, S or W. Uses scipy to streamline rotation of the kernel.
    
    Returns
    -------
    `directed_kernel`: np.array
        A 2D array (3x3 kernel) that details the wind direction and speed.
    """
    base_kernel = np.array(
        [
         [1, 1, 1],
         [0, 0, 0],
         [0, 0, 0]
        ]
    )
    speed_kernel = base_kernel * WIND_SPEED #Implement wind speed; highest wind speed category is 3
    directed_kernel = rotate(speed_kernel, angle=0+(90*rotate_scores.get(WIND_DIR))) #Rotate kernel to match direction - only works for N, E, S, W
    return directed_kernel

def transition_func(grid, neighbourstates, neighbourcounts, iterations):
    """
    The implemented transition function. Executed each iteration to update the grid based on a 
    series of state transition functions defined. Also includes mitigation strategies such as
    forest extension and water drop.
    
    Parameters
    ----------
    `grid`: np.array
        A 2D array containing the states of the grid at the current timestep.
    `neighbourstates`: np.array
        A multi-dimensional array that details the neighbour states of each cell within the grid.
    `neighbourcounts`: np.array
        A multi-dimensional array that details the number of neighbours with each state for each
        cell within the grid.
    `iterations`: int
        In essence a counter used to count the number of iterations.
    
    Returns
    -------
    `grid`: np.array
        A 2D array containing the states of the grid after the transition function has been applied.
    `iterations`: int
        An incremented iteration count.
    """
    state_of_town_squares = grid[88:93, 38:43]
    for x in state_of_town_squares:
        for y in x:
            if (x == BURNT).any():
                time_for_town_fire = iterations
    cells_to_burn_this_iter = []
    for x_coord in range(1,102):
        for y_coord in range(1,102):
            current_cell = grid[x_coord][y_coord]
            if current_cell not in [LAKE, BURNT]: #State transition functions - same as before; no change here
                neighbourhood = get_neighbourhood(grid, x_coord, y_coord)
                fire_neighbours = np.count_nonzero(neighbourhood == 6)
                if current_cell == CHAPARRAL and fire_neighbours >= 2:
                    cells_to_burn_this_iter.append((x_coord, y_coord))
                if current_cell == FOREST and fire_neighbours >= 3:
                    cells_to_burn_this_iter.append((x_coord, y_coord))
                if current_cell == SCRUBLAND and fire_neighbours >= 1:
                    cells_to_burn_this_iter.append((x_coord, y_coord))
                if current_cell == TOWN and fire_neighbours >= 1:
                    cells_to_burn_this_iter.append((x_coord, y_coord))
    for cell in cells_to_burn_this_iter:
        x, y = cell[0], cell[1]
        grid[x][y] = FIRE
    if WIND_DIR != "None": #If there is wind, we apply it here; at the end of the iteration
        additonal_cells_to_burn = apply_wind_kernel(grid, cells_to_burn_this_iter)
        for cell in additonal_cells_to_burn:
            x, y = cell[0], cell[1]
            grid[x][y] = FIRE
    iterations += 1
    return grid, iterations

  

def drop_water(grid, iterations):

    if iterations == WATER_TIME:
        y_coord, x_coord = WATER_COORDS
        rand_water_dist = random.randint(1,6) #Randomly select the water distribution when dropped; equal probability.
        if rand_water_dist == 1:
            for x in range(x_coord-2, x_coord+2):
                for y in range(y_coord-1, y_coord+2):
                    if x or y > GRID_SIZE:
                        continue
                    elif grid[x, y] == LAKE or grid[x, y] == BURNT:
                        continue
                    elif grid[x, y] == FIRE:
                        grid[x, y] = BURNT #12km^2
                    else:
                        grid[x, y] = LAKE
        elif rand_water_dist == 2:
            x = x_coord
            for y in range(y_coord-6, y_coord+6):
                if x or y > GRID_SIZE:
                    continue
                elif grid[x, y] == LAKE or grid[x, y] == BURNT:
                    continue
                elif grid[x, y] == FIRE:
                    grid[x, y] = BURNT #12km^2
                else:
                    grid[x, y] = LAKE
        elif rand_water_dist == 3:
            y = y_coord
            for x in range(x_coord-6, x_coord+6):
                if x or y > GRID_SIZE:
                    continue
                elif grid[x, y] == LAKE or grid[x, y] == BURNT:
                    continue
                elif grid[x, y] == FIRE:
                    grid[x, y] = BURNT #12km^2
                else:
                    grid[x, y] = LAKE
        elif rand_water_dist == 4:
            for x in range(x_coord-1, x_coord+2):
                for y in range(y_coord-2, y_coord+2):
                    if x or y > GRID_SIZE:
                        continue
                    elif grid[x, y] == LAKE or grid[x, y] == BURNT:
                        continue
                    elif grid[x, y] == FIRE:
                        grid[x, y] = BURNT #12km^2
                    else:
                        grid[x, y] = LAKE
        elif rand_water_dist == 5:
            for x in range(x_coord-1, x_coord):
                for y in range(y_coord-3, y_coord+3):
                    if x or y > GRID_SIZE:
                        continue
                    elif grid[x, y] == LAKE or grid[x, y] == BURNT:
                        continue
                    elif grid[x, y] == FIRE:
                        grid[x, y] = BURNT #12km^2
                    else:
                        grid[x, y] = LAKE
        elif rand_water_dist == 6:
            for x in range(x_coord-3, x_coord+3):
                for y in range(y_coord-1, y_coord):
                    if x or y > GRID_SIZE:
                        continue
                    elif grid[x, y] == LAKE or grid[x, y] == BURNT:
                        continue
                    elif grid[x, y] == FIRE:
                        grid[x, y] = BURNT #12km^2
                    else:
                        grid[x, y] = LAKE
    return grid


def setup(args):
    """
    Set-up the config of the automata model.
    
    Parameters
    ----------
    `args`: List
        A list containing the arguments passed into the model.
    
    Returns
    -------
    `config` :CAConfig object
        An object used to store all parameters and arguments for the model.
    """
    global ITERS #variable for "generations" / time stamps
    global GRID_SIZE
    global INCINERATOR_SOURCE
    global POWER_PLANT_SOURCE
    global WATER_COORDS
    global WATER_TIME
    global WIND_DIR
    global WIND_SPEED

    global WIND_KERNEL

    global FOREST_EXTENSION_LAYOUT

    config_path = args[0]
    config = utils.load(config_path)
    config.title = "Forest fire simulation"
    config.dimensions = 2
    config.states = (CHAPARRAL, LAKE, FOREST, SCRUBLAND, BURNT, TOWN, FIRE)
    config.state_colors = [
        (0.8, 0.8, 0),
        (0.2, 0.6, 1),
        (0, 0.4, 0),
        (1, 1, 0.2),
        (0.4, 0.4, 0.4), 
        (0, 0, 0),
        (1, 0, 0)
    ]
    GRID_SIZE = 102
    
    config.num_generations = 95

    config.grid_dims = (GRID_SIZE, GRID_SIZE)
    INCINERATOR_SOURCE = True if args[2] == "True" else False
    POWER_PLANT_SOURCE = True if args[3] == "True" else False
    if args[4] != "None":
        if args[6] != "None":
            coords = re.sub("[][,']", "", args[4]).split(" ")
            WATER_COORDS = (int(coords[0]), int(coords[1]))
            WATER_TIME = int(args[6])
    if args[5] != "None":
        dir = args[5]
        if dir in ["N", "E", "S", "W"]:
            WIND_DIR = dir
   
    if args[7] != "None":
        speed = int(args[7])
        if speed <= 30: #Creates 3 bands of wind speeds, slow, medium and fast; if over 30 then no wind is applied
            WIND_SPEED = round(speed/10)
            WIND_KERNEL = wind_kernel()

        
    if args[8] != "None":
        FOREST_EXTENSION_LAYOUT = int(args[8])

    init_grid = define_initial_grid()
    config.initial_grid = init_grid
    if int(args[1]) == 0:
        print("[Forest Fire Simulator]     Loaded")
        config.save()
        sys.exit()
    ITERS = 0
    return config

def main():
    # Open the config object
    config = setup(sys.argv[1:])
    print("[Forest Fire Simulator]  Running simulation")
    # Create grid object
    grid = Grid2D(config, transition_func)
    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()
    # save updated config to file
    config.save()
    # save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()
