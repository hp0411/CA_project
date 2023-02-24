# Name: NAME
# Dimensions: 2

# --- Set up executable path, do not edit ---
import sys
import inspect
this_file_loc = (inspect.stack()[0][1])
main_dir_loc = this_file_loc[:this_file_loc.index('ca_descriptions')]
sys.path.append(main_dir_loc)
sys.path.append(main_dir_loc + 'capyle')
sys.path.append(main_dir_loc + 'capyle/ca')
sys.path.append(main_dir_loc + 'capyle/guicomponents')
# ---

from capyle.ca import Grid2D, Neighbourhood, randomise2d
import capyle.utils as utils


def setup(args):
    """Set up the config object used to interact with the GUI"""
    config_path = args[0]
    config = utils.load(config_path)
    # -- THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED --
    config.title = "NAME"
    config.dimensions = 2
    # 0: no fuel, 1: fuel not burned, 2: burning_fuel, 3: burnt fuel
    config.states = (0,1,2,3)
    # -------------------------------------------------------------------------

    # ---- Override the defaults below (these may be changed at anytime) ----

    config.num_generations = 150
    config.grid_dims = (50,50)

    numrows, numcols = config.grid_dims
    # Reference: https://www.geeksforgeeks.org/python-using-2d-arrays-lists-the-right-way/
    initial_grid = [[[1]*numcols]*numrows] # chaparral
    initial_grid[5:12][15:25] = 1 # forest
    initial_grid[20:35][0:25] = 1 # forest 
    initial_grid[12:15][5:25] = 0 # lake
    initial_grid[5:40][30:32] = 1 # scrubland
    config.initial_grid = initial_grid

    wind_directions = ['north', 'east', 'south', 'west']
    config.wind_directions = wind_directions

    # ----------------------------------------------------------------------

    # the GUI calls this to pass the user defined config
    # into the main system with an extra argument
    # do not change
    if len(args) == 2:
        config.save()
        sys.exit()
    return config


def transition_function(grid, neighbour_states, neighbour_terrain_types):
    """Function to apply the transition rules
    and return the new grid"""
    # possible neighbour_terrain_types: chaparral, lake, forest, scrubland
    # chaparral: catch fire easily, can burn for several days
    # lake: body of water
    # forest: don't catch fire easily, but once alight can burn for up to a month
    # scrubland: highly flammable, each square km can burn for several hours
    return grid


def main():
    """ Main function that sets up, runs and saves CA"""
    # Get the config object from set up
    config = setup(sys.argv[1:])

    # Create grid object using parameters from config + transition function
    grid = Grid2D(config, transition_function)

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # Save updated config to file
    config.save()
    # Save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()
