import sys
import tkinter as tk
import tkinter.font as tkFont
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from capyle.utils import (set_icon, get_filename_dialog, get_logo,
                          prerun_ca, run_ca, extract_states)
from capyle.ca import CAConfig
from capyle.guicomponents import (_ConfigFrame, _CAGraph, _ScreenshotUI,
                                  _CreateCA, _AboutWindow)
from capyle import _PlaybackControls

class Display(object):
    WINDOW_TITLE = "CAPyLE"
    ROOT_PATH = sys.path[0]
    CA_PATH = ROOT_PATH + "/ca_descriptions/"

    def __init__(self, options):
        """
        Initialise the main GUI.
        This is the main GUI and can be run simply by invoking this method
        """
        self.ca_graph = None
        self.ca_filepath = options.path
        self.options = options
        self.root = tk.Tk()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
        self.root.wm_title(self.WINDOW_TITLE)
        set_icon(self.root)
        self.add_menubar()
        self.add_frames()
        self.playback_controls = _PlaybackControls(self)
        self.screenshotui = _ScreenshotUI(self.rtopframe)
        self.init_config_ui()
        self.load_ca()
        self.ca_graph = _CAGraph(self.ca_config.initial_grid, self.ca_config.states)
        self.ca_graph.set_colormap(self.ca_config.state_colors)
        self.ca_canvas = FigureCanvasTkAgg(self.ca_graph.fig,
                                           master=self.rcframe)
        self.ca_canvas.get_tk_widget().pack()
        self.root.mainloop()

    def add_menubar(self):
        """Function to add a menubar to the root window"""
        self.menubar = tk.Menu(self.root)
        file_menu = tk.Menu(self.menubar, tearoff=0)
        sim_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About CAPyLE", command=_AboutWindow)
        self.root.config(menu=self.menubar)

    def add_frames(self):
        """
        Add tk.Frames to the root window.
        Adds a left and right frame with the right frame divided
        into top and bottom
        """
        self.lframe = tk.Frame(self.root, height=500, width=200)
        self.lframe.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
        self.rframe = tk.Frame(self.root, height=500, width=300)
        self.rframe.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.BOTH)
        self.rbotframe = tk.Frame(self.rframe, height=100, width=300)
        self.rbotframe.pack(side=tk.BOTTOM, expand=tk.YES, fill=tk.BOTH,
                            pady=5)
        self.rtopframe = tk.Frame(self.rframe, height=40, width=200)
        self.rtopframe.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH,
                            pady=5)
        self.rcframe = tk.Frame(self.rframe, bd=2)
        self.rcframe.pack()
        title_font = tkFont.Font(self.root, family="Helvetica",
                                 size=20, weight=tkFont.BOLD)
        self.config_ui = None
        self.lbotframe = None

    def init_config_ui(self):
        """Initialise the config UI elements but do not add them to GUI yet"""
        logo_on = False
        with open(sys.path[0] + "/config.txt", "r") as f:
            for line in f:
                l = line.split("=")
                if l[0] == "logo":
                    logo_on = l[1].strip() == "1"
        if logo_on:
            logo = get_logo()
            img = tk.Label(self.lframe, image=logo)
            img.image = logo
            img.bind("<Button-1>", lambda x: _AboutWindow())
            img.pack()
        title_font = tkFont.Font(self.root, family="Helvetica",
                                 size=20, weight=tkFont.BOLD)
        self.loaded_title = tk.Label(self.lframe, text='', font=title_font)
        self.loaded_title.pack(side=tk.TOP)
        self.config_ui = None
        self.lbotframe = None

    def add_configuration_controls(self):
        """
        Add the configuration controls to the root window left frame.
        These controls are used to control the parameters of the CA like
        generations, dimensions, colors, neighbourhood, ...
        """
        self.loaded_title.config(text=self.ca_config.title)
        if self.config_ui is not None:
            self.config_ui.destroy()
        self.config_ui = _ConfigFrame(self.lframe, self.ca_config)
        self.config_ui.pack()
        if self.lbotframe is not None:
            self.lbotframe.destroy()
        self.lbotframe = tk.Frame(self.lframe)
        self.btn_run = tk.Button(self.lbotframe,
                                 text="Apply configuration & run CA",
                                 command=self.run_ca)
        self.btn_run.pack(side=tk.BOTTOM, pady=10)
        self.lbotframe.pack(fill=tk.BOTH, expand=True)

    def load_ca(self):
        """
        Load a CA description file.
        Pre runs the setup function in the description to populate the
        CAConfig object. Only then will the GUI be properly initialised
        (states must be known before adding config frame)
        Note:
            If manually specifying a path:
            sys.path[0] can be used to get the directory of main.py and then
            '/ca_descriptions/xxx.py' can be appended to create the filepath.
        Args:
            filepath (str): Full path to the CA description py file
        """
        if not self.ca_filepath == '':
            if self.ca_graph is not None:
                self.ca_graph.clear()
            self.ca_config = CAConfig(self.ca_filepath)
            self.ca_config = prerun_ca(self.ca_config, self.options)
            if self.ca_config is None:
                return
            self.root.wm_title(
                self.WINDOW_TITLE + " - " + self.ca_config.title)
            self.add_configuration_controls()
            self.playback_controls.ui.pack(side=tk.LEFT, padx=10)
            self.playback_controls.ui.sliderframe.pack()
            self.screenshotui.pack(side=tk.LEFT, padx=10)

    def run_ca(self):
        """
        Run the loaded CA passing in the config from GUI.
        Running the CA with run_ca returns the new CAConfig object
        and the Timeline. Timeline loaded by calling self.load_timeline
        Note:
            The config may overwritten in the CA description
        """
        self.ca_config, valid = self.config_ui.get_config(self.ca_config,
                                                          validate=True)
        if valid:
            self.ca_config, timeline = run_ca(self.ca_config, self.options)
            if self.ca_config is None or timeline is None:
                return
            if self.ca_config.states is None:
                self.ca_config.states = extract_states(timeline)
            self.load_timeline(timeline)
            self.config_ui.update(self.ca_config, self.ca_graph)

    def load_timeline(self, timeline):
        """
        Load a timeline into the GUI and display on the graph also enables playback and 
        screenshot UI controls.
        Args:
            timeline (np.ndarray): The grid state for each timestep
        """
        self.ca_graph = _CAGraph(timeline, self.ca_config.states,
                                 sequence=True)
        if self.ca_canvas is not None:
            self.ca_canvas.get_tk_widget().destroy()
        self.ca_canvas = FigureCanvasTkAgg(self.ca_graph.fig,
                                           master=self.rcframe)
        self.rcframe.config(borderwidth=5, relief=tk.GROOVE)
        self.ca_canvas.get_tk_widget().pack(padx=0, pady=0)
        if self.ca_config.state_colors is not None:
            self.ca_graph.set_colormap(self.ca_config.state_colors)
        maxframe = len(self.ca_graph.timeline) - 1
        self.update_controls(maxframe)
        self.screenshotui.set(graph=self.ca_graph, title=self.ca_config.title)
        self.screenshotui.enable()
        self.root.after(0, self.playback_controls.update())
    def update_controls(self, maxframe):
        """
        Update the UI controls when a timeline is loaded with
        the new parameters.
        Args:
            maxframe (int): The number of frames in the timeline
            (eg. the number of generations run)
        """
        self.playback_controls.ui.enable()
        self.playback_controls.refresh(maxframe)

if __name__ == "__main__":
    main()
