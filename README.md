# CAPyLE
CAPyLE is a cross-platform teaching tool designed and built as part of a final year computer science project. It aims to aid the teaching of cellular automata and how they can be used to model natural systems.

It is written completely in python with minimal dependencies.

![CAPyLE Screenshot on macOS](http://pjworsley.github.io/capyle/sample.png)

## Installation
The installation guide can be found on the [CAPyLE webpages](http://pjworsley.github.io/capyle/installationguide.html)

## Usage
Detailed usage can be found on the [CAPyLE webpages](http://pjworsley.github.io/capyle/).

For COM3524 assignment, additional features have been developed and tested in Python 3.8.13 - original codebase is ~Python3.4.x

### Command line arguments

Running ```>> python .\main.py -h``` from the root directory will yield the argparse helper:

```
python .\main.py -h
usage: main.py [-h] -f PATH [-w WIND_DIR] [-d WATER_DROP [WATER_DROP ...]] [-t WATER_TIME] [-i] [-p]

This is a command line interface (CLI) for the forest fire simulation module.

required arguments: 
  -f PATH, --model-path PATH
                        Specify the FULL file path to CA model.

  either one of the flags below:

  -i, --start-incinerator
                        Specify whether fire starts at incinerator.
  -p, --start-power-plant
                        Specify whether fire starts at power plant.

optional arguments:
  -h, --help            show this help message and exit
  
  -w WIND_DIR, --wind-direction WIND_DIR
                        Specify direction of prevailing wind from [N, E, S, W] etc.
  -d WATER_DROP [WATER_DROP ...], --drop-water-coords WATER_DROP [WATER_DROP ...]
                        Whitespace separated coords for where water should be dropped e.g. --drop-water-coords 4 6
  -t WATER_TIME, --drop-water-time WATER_TIME
                        Time interval for the water to be dropped. Each time drop is 4 hours.
  -ws, WIND_SPEED --wind-speed 
                        Wind speed measurements are km/h.

Ethan Jones, 2022-11-11
```

### Initial setup

1. Clone the repo using: `>> git clone https://github.com/pjworsley/capyle.git [target-directory]`.
2. Change into the root directory as such: `cd [target-directory]`.
3. Install the additional requirements on top of the COM3524 lab environment using the following ```pip install -r "requirements.txt"``` from the root directory.

### Example usage

Running ```>> python .\main.py -f "C:\Users\ethan\Desktop\uni\final_year\COM3524\Assignment\CA_assignment\ca_descriptions\ff_2d.py" -w "NE" -d 40 22 -t 4 -p``` means:

* -f flag -> This points the application to the 2D automata model; ensure full file path is provided.
* -w flag -> Provides a prevailing wind in the north-east direction.
* -d flag -> Chooses the coordinates (40, 26) as the place for water to be dumped.
* -t flag -> Defines the time interval the water will be dumped at.
* -p flag -> Sets an initial fire at the power plant.

Note that, by default, a fire starts at the incinerator at t=0.

**Note that these functionalities have yet to be implemented, moreso the work has focussed on the restructuring of the original codebase to allow command line arguments.**

## Licence
CAPyLE is licensed under a BSD licence, the terms of which can be found in the LICENCE file.

Copyright 2017 Peter Worsley
