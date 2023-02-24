import sys
import inspect
import argparse
# ---- Set up path to modules ----
this_file_loc = (inspect.stack()[0][1])
main_dir_loc = this_file_loc[:this_file_loc.index('main.py')]
sys.path.append(main_dir_loc)
sys.path.append(main_dir_loc + 'capyle')
sys.path.append(main_dir_loc + 'capyle/ca')
sys.path.append(main_dir_loc + 'capyle/guicomponents')

from capyle import Display

def parse_options():
    """Parse command line options."""
    parser = argparse.ArgumentParser(description=("This is a command line interface (CLI) for "
                                                  f"the forest fire simulation module."),
                                     epilog="Ethan Jones, 2022-11-11")
    parser.add_argument("-f", "--model-path", dest="path", action="store", type=str,
                        required=True, help="Specify the *FULL* file path to CA model.")
    parser.add_argument("-w", "--wind-direction", dest="wind_dir", action="store", type=str,
                        required=False, help="Specify direction of prevailing wind from [N, E, S, W] etc.")
    parser.add_argument("-d", "--drop-water-coords", dest="water_drop", action="store", nargs='+', type=int,
                        required=False, help="Whitespace separated coords for where water should be dropped e.g. --drop-water-coords 4 6")
    parser.add_argument("-t", "--drop-water-time", dest="water_time", action="store", type=int,
                        required=False, help="Time interval for the water to be dropped. Each time drop is 4 hours.")
    parser.add_argument("-ws", "--wind-speed", dest="wind_speed", action="store", type=int,
                        required=False, help="Wind speed measurements are km/h.")
    parser.add_argument("-e", "--forest-extension", dest="f_ext", action="store", type=int,
                        required=False, help="Choice of pre-chosen forest extensions.")
    parser.add_argument("-i", "--start-incinerator", dest="incin", action="store_true",
                        required=False, help="Specify whether fire starts at incinerator.")
    parser.add_argument("-p", "--start-power-plant", dest="pp", action="store_true",
                        required=False, help="Specify whether fire starts at power plant.")
    options = parser.parse_args()
    return options

def main():
    """Initialise the GUI"""
    options = parse_options()
    print("[Forest Fire Simulator]     Loading the CA model and config file...")
    w = Display(options)

if __name__ == "__main__":
    main()