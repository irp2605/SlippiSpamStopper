import os
import time
import tkinter
import customtkinter
import sys
import logging
from pygtail import Pygtail
import config
import slippi.event
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler, PatternMatchingEventHandler
from tkinter import filedialog
from tkinter import messagebox
from typing import Iterator
import pip
from PIL import Image, ImageTk
import subprocess

from slippi.parse import parse
from slippi.parse import ParseEvent
from slippi.game import Game

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

global replays_directory
global watchdog_label
global handlers


class Watchdog(PatternMatchingEventHandler, Observer):
    def __init__(self, path='.', patterns='*', logfunc=print):
        PatternMatchingEventHandler.__init__(self, patterns)
        Observer.__init__(self)
        self.schedule(self, path=path, recursive=False)
        self.log = logfunc

    def on_created(self, event):
        global watchdog_label
        global handlers
        self.log(f"hey, {event.src_path} has been created!")
        if watchdog_label is None:
            print("no label")
        else:
            watchdog_label.configure(text=event.src_path)
        handlers = {ParseEvent.METADATA: print}
        file_path = event.src_path
        file_path = file_path.replace("/", "\\")
        file_path = file_path.replace("\\", "\\\\")
        print("right before the subprocess")
        print(file_path)
        config.init()
        config.myList.append(file_path)
        print("Exists? %s" % os.path.exists(file_path))
        print("Is file? %s" % os.path.isfile(file_path))
        # ame(file_path)
        # f = subprocess.Popen('tail -c+1 -f %s' % file_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        time.sleep(0.5)
        while True:
            time.sleep(0.5)
            with open(file_path, "rb") as f:
                parse(f, handlers=handlers)


class LiveStartedToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        global watchdog_label

        self.geometry("300x300")
        self.resizable(False, False)
        self.title("SlippiSpamStopper Live Game")
        # self.iconphoto(r"rescources/images/SlippiSpamStopperPNGIcon.ico")
        self.watchdog = None
        self.watch_path = replays_directory

        self.start_watchdog()

        watchdog_label = customtkinter.CTkLabel(text="Waiting for file creation", master=self)
        watchdog_label.place(x=10, y=150)

    def log(self, message):
        print(message)

    def start_watchdog(self):
        if self.watchdog is None:
            self.watchdog = Watchdog(path=self.watch_path, logfunc=self.log)
            self.watchdog.start()
            self.log('Watchdog Started')


class SSSTabView(customtkinter.CTkTabview):

    def __init__(self, master, **kwargs):

        super().__init__(master, **kwargs)

        self.add("Live Game")
        self.add("Past Games")
        self.add("Settings")

        global replays_directory
        replays_directory = ""

        # Live Game Tab Setup
        ####################################

        # Labeling Live Game
        self.watch_for_label = customtkinter.CTkLabel(text="Watch For", master=self.tab("Live Game"))
        self.watch_for_label.grid(row=0, column=0, padx=100, pady=(50, 20))

        # Move Drop Down / Option Menu
        self.move_optionmenu_var = customtkinter.StringVar(value="DTHROW")

        def move_optionmenu_callback(choice):
            print("move selected: ", choice)

        self.move_combobox = customtkinter.CTkOptionMenu(master=self.tab("Live Game"),
                                                         values=["DTHROW", "UTHROW", "NEUTRAL_B", "UTILT"],
                                                         command=move_optionmenu_callback,
                                                         variable=self.move_optionmenu_var)

        self.move_combobox.grid(row=1, column=0)

        # Number times entry

        def validate_times_entry(new_value):
            if new_value == "" or new_value.isnumeric():
                return True
            else:
                return False

        self.times_entry_vcmd = (self.winfo_toplevel().register(validate_times_entry), '%P')

        self.times_entry = customtkinter.CTkEntry(master=self.tab("Live Game"), placeholder_text="3",
                                                  validatecommand=self.times_entry_vcmd,
                                                  validate='key')
        self.times_entry.grid(row=2, column=0, pady=(25, 20))

        # Times Label
        self.watch_for_label = customtkinter.CTkLabel(text="Times", master=self.tab("Live Game"))
        self.watch_for_label.grid(row=3, column=0, padx=100, pady=(0, 20))

        # Respond by Label
        self.watch_for_label = customtkinter.CTkLabel(text="Respond By", master=self.tab("Live Game"))
        self.watch_for_label.grid(row=2, column=1, padx=60, pady=(0, 40))

        # Response Option
        self.response_optionmenu_var = customtkinter.StringVar(value="Playing a Sound")

        def response_optionmenu_callback(choice):
            print("move selected: ", choice)

        self.response_combobox = customtkinter.CTkOptionMenu(master=self.tab("Live Game"),
                                                             values=["Playing a Sound", "Using PySerial"],
                                                             command=response_optionmenu_callback,
                                                             variable=self.response_optionmenu_var)

        self.response_combobox.grid(row=1, column=2, padx=50)

        # Start Button
        def live_start_button_event():
            global replays_directory
            replays_directory = "C:\\Users\\test\\Documents\\Slippi"
            print(replays_directory)
            if replays_directory == "":
                tkinter.messagebox.showerror('Replays Directory Not Set!',
                                             'Please set your replays directory in the settings tab!')
            else:
                live_started()

        self.live_start_button = customtkinter.CTkButton(master=self.tab("Live Game"),
                                                         command=lambda: live_start_button_event(),
                                                         text="Start")
        self.live_start_button.grid(row=2, column=2)

        self.live_started_toplevel_window = None

        def live_started():
            if self.live_started_toplevel_window is None or not self.live_started_toplevel_window.winfo_exists():
                self.live_started_toplevel_window = LiveStartedToplevelWindow(self.winfo_toplevel())
                self.live_started_toplevel_window.grab_set()
            else:
                self.live_started_toplevel_window.focus()

        # Past Games Analysis
        ##########################

        # Move Drop Down / Option Menu
        self.past_move_dict = {
            "DTHROW": slippi.event.Attack.DOWN_THROW,
            "UTHROW": slippi.event.Attack.UP_THROW,
            "NEUTRAL_B": slippi.event.Attack.NEUTRAL_SPECIAL,
            "UTILT": slippi.event.Attack.UP_TILT
        }

        self.past_move_optionmenu_var = customtkinter.StringVar(value="DTHROW")
        self.selected_move = self.past_move_dict[self.past_move_optionmenu_var.get()]

        def past_move_optionmenu_callback(choice):
            print("move selected: ", choice)
            self.selected_move = self.past_move_dict[self.past_move_optionmenu_var.get()]

        self.past_move_combobox = customtkinter.CTkOptionMenu(master=self.tab("Past Games"),
                                                              values=["DTHROW", "UTHROW", "NEUTRAL_B", "UTILT"],
                                                              command=past_move_optionmenu_callback,
                                                              variable=self.past_move_optionmenu_var)

        self.past_move_combobox.place(x=500,
                                      y=130)
        # Watch For Label
        self.past_watch_for_label = customtkinter.CTkLabel(text="Watch For", master=self.tab("Past Games"))
        self.past_watch_for_label.place(x=540,
                                        y=95)

        # Start Button
        def get_key_from_value(dict, val):
            keys = [k for k, v in dict.items() if v == val]
            if keys:
                return keys[0]
            return None

        def past_start_button_event():
            game = Game("C:\\Users\\test\\Documents\\Slippi\\Game_20230403T225300.slp")
            print(self.selected_move)
            print(game.metadata)
            self.selected_move_count = 0
            for frame in game.frames:
                if frame.ports[1].leader.post.last_attack_landed == self.selected_move:
                    self.selected_move_count = self.selected_move_count + 1
            print("You spent {} frames with {} as your last hit move!".format(self.selected_move_count,
                                                                              get_key_from_value(self.past_move_dict,
                                                                                                 self.selected_move)))
            self.move_percent = ((self.selected_move_count / (len(game.frames))) * 100)
            print("That was the last move you hit for %s%% of frames!" % round(self.move_percent, 2))

        self.past_start_button = customtkinter.CTkButton(master=self.tab("Past Games"),
                                                         command=lambda: past_start_button_event(),
                                                         text="Start")

        self.past_start_button.place(x=500,
                                     y=220)

        # Settings Tab
        ###############################################

        # Settings Darkmode Label
        # self.settings_theme_label = customtkinter.CTkLabel(text="Darkmode:", master=self.tab("Settings"))
        # self.place(x=0,
        #           y=50)

        # Dark Mode Switch
        self.darkmode_switch_var = customtkinter.StringVar(value="on")

        def darkmode_switch_event():
            print("switch toggled")
            if self.darkmode_switch_var.get() == "on":
                customtkinter.set_appearance_mode("dark")
            else:
                customtkinter.set_appearance_mode("light")

        self.darkmode_switch = customtkinter.CTkSwitch(master=self.tab("Settings"),
                                                       text="Dark Mode Toggle",
                                                       command=lambda: darkmode_switch_event(),
                                                       variable=self.darkmode_switch_var,
                                                       onvalue="on",
                                                       offvalue="off")
        self.darkmode_switch.place(x=20,
                                   y=50)

        self.folder_path_label = customtkinter.CTkLabel(text="Folder Path Will Display Here",
                                                        master=self.tab("Settings"))
        self.folder_path_label.place(x=20, y=170)

        self.folder_label = customtkinter.CTkLabel(text="Replay Folder:", master=self.tab("Settings"))
        self.folder_label.place(x=20, y=120)

        def folder_select_button_event():
            global replays_directory
            replays_directory = tkinter.filedialog.askdirectory(initialdir='C:\\',
                                                                title='Select Your Replay Directory',
                                                                )
            if len(str(replays_directory)) > 40:
                self.folder_path_label.configure(text=(str(replays_directory)[0:41] + "..."))
            else:
                self.folder_path_label.configure(text=str(replays_directory))

        self.folder_select_button = customtkinter.CTkButton(master=self.tab("Settings"),
                                                            text='Select Folder',
                                                            command=lambda: folder_select_button_event())
        self.folder_select_button.place(x=110, y=120)


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Basic Window Settings Setup
        self.geometry("750x400")
        self.title("SlippiSpamStopper")
        self.iconbitmap(True, r"rescources/images/SlippiSpamStopperPNGIcon.ico")
        self.iconbitmap(bitmap=r"rescources/images/SlippiSpamStopperPNGIcon.ico")
        self.iconbitmap(default=r"rescources/images/SlippiSpamStopperPNGIcon.ico")

        self.resizable(False, False)

        self.tab_view = SSSTabView(master=self, width=700, height=360)
        self.tab_view.pack(expand=True)


app = App()
app.mainloop()
