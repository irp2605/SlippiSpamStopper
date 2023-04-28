import os
import time
import tkinter

import ttkwidgets.autocomplete
from ttkwidgets.autocomplete import autocompletecombobox
import customtkinter
import sys
import logging
import config
import slippi.event
from tkinter import filedialog
from tkinter import messagebox
import pip
import melee
# from playsound import playsound

from slippi.parse import parse
from slippi.parse import ParseEvent
from slippi.game import Game

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

# Past replay analysis globals
global replays_directory

# Live replay reaction globals
global live_selected_move
global max_consecutive_selected_move_uses
global live_response
global netplay_directory
global ISO_path

class SSSTabView(customtkinter.CTkTabview):

    def __init__(self, master, **kwargs):

        super().__init__(master, **kwargs)

        self.add("Live Game")
        self.add("Past Games")
        self.add("Settings")

        global replays_directory
        global netplay_directory
        global ISO_path
        replays_directory = netplay_directory = ISO_path = ""

        # Live Game Tab Setup
        ####################################

        # Labeling Live Game
        self.watch_for_label = customtkinter.CTkLabel(text="Watch For", master=self.tab("Live Game"))
        self.watch_for_label.grid(row=0, column=0, padx=100, pady=(50, 20))

        # Move Drop Down / Option Menu
        self.move_optionmenu_var = customtkinter.StringVar(value="DTHROW")
        global live_selected_move
        live_selected_move = "DTHROW"

        def move_optionmenu_callback(choice):
            global live_selected_move
            print("move selected: ", choice)
            live_selected_move = choice

        self.move_optionmenu = customtkinter.CTkOptionMenu(master=self.tab("Live Game"),
                                                         values=["DTHROW", "UTHROW", "NEUTRAL_B", "UTILT"],
                                                         command=move_optionmenu_callback,
                                                         variable=self.move_optionmenu_var)

        self.move_optionmenu.grid(row=1, column=0)

        # Number times entry

        def validate_times_entry(new_value):
            global max_consecutive_selected_move_uses
            if new_value == "" or new_value.isnumeric():
                max_consecutive_selected_move_uses = new_value
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
            global live_response
            print("move selected: ", choice)
            live_response = choice

        self.response_optionmenu= customtkinter.CTkOptionMenu(master=self.tab("Live Game"),
                                                             values=["Playing a Sound", "Using PySerial"],
                                                             command=response_optionmenu_callback,
                                                             variable=self.response_optionmenu_var)

        self.response_optionmenu.grid(row=1, column=2, padx=50)


        # Character optionmenu
        self.character_optionmenu_var = customtkinter.StringVar(value="Falco")

        all_chacters = ["Falco", "Fox", "Marth", "Cpt Falco", "Sheik", "Peach", "Puff", "Yoshi", "Dr Mario", "Mario", "Luigi", "Bowser",
                        "DK", "Ganondorf", "Ness", "Ice Climbers", "Kirby", "Samus", "Zelda", "Link", "Young Link",
                        "Pichu", "Pikachu", "Mewtwo", "G&W", "Roy"]

        def character_optionmenu_callback(choice):
            global character
            print("chachter selected: ", choice)
            character=choice

        self.character_optionmenu = customtkinter.CTkOptionMenu(master=self.tab("Live Game"),
                                                            values=all_chacters,
                                                            command=character_optionmenu_callback,
                                                            variable=self.character_optionmenu_var)

        self.character_optionmenu.grid(row=3, column=2, padx=50)

        # Start Button
        def live_start_button_event():
            print(self.character_optionmenu_var.get())
            global replays_directory
            global netplay_directory
            global ISO_path
            print(replays_directory)
            if netplay_directory == "" or ISO_path == "":
                tkinter.messagebox.showerror('Relevant Directories Not Set!',
                                             'Please set your netplay directory and the path to '
                                             'your ISO in the settings tab!')
            else:
                live_started()

        self.live_start_button = customtkinter.CTkButton(master=self.tab("Live Game"),
                                                         command=lambda: live_start_button_event(),
                                                         text="Start")
        self.live_start_button.grid(row=2, column=2)

        self.live_started_toplevel_window = None

        def live_started():
            self.live_start_button.configure(state='disabled')

            # lib melee first test
            # setting up lib melee dict
            self.live_move_dict = {
                "DTHROW": melee.enums.Action.THROW_DOWN,
                "UTHROW": melee.enums.Action.THROW_UP,
                "NEUTRAL_B": melee.enums.Action.NEUTRAL_B_ATTACKING,
                "UTILT": melee.enums.Action.UPTILT
            }

            # setting up array of all attacks to know when to reset attack count
            self.live_attack_list = [
                melee.enums.Action.BAIR,
                melee.enums.Action.DAIR,
                melee.enums.Action.DASH_ATTACK,
                melee.enums.Action.DOWNSMASH,
                melee.enums.Action.DOWNTILT,
                melee.enums.Action.DOWN_B_AIR,
                melee.enums.Action.DOWN_B_GROUND,
                melee.enums.Action.DOWN_B_GROUND_START,
                melee.enums.Action.DK_GROUND_POUND,
                melee.enums.Action.FAIR,
                melee.enums.Action.FIREFOX_AIR,
                melee.enums.Action.FIREFOX_GROUND,
                melee.enums.Action.FIREFOX_WAIT_AIR,
                melee.enums.Action.FIREFOX_WAIT_GROUND,
                melee.enums.Action.FOX_ILLUSION,
                melee.enums.Action.FOX_ILLUSION_SHORTENED,
                melee.enums.Action.FOX_ILLUSION_START,
                melee.enums.Action.FSMASH_HIGH,
                melee.enums.Action.FSMASH_LOW,
                melee.enums.Action.FSMASH_MID,
                melee.enums.Action.FSMASH_MID_HIGH,
                melee.enums.Action.FSMASH_MID_LOW,
                melee.enums.Action.FTILT_HIGH,
                melee.enums.Action.FTILT_HIGH_MID,
                melee.enums.Action.FTILT_LOW,
                melee.enums.Action.FTILT_LOW_MID,
                melee.enums.Action.FTILT_MID,
                melee.enums.Action.GRAB,
                melee.enums.Action.GUN_SHOOT,
                melee.enums.Action.GUN_SHOOT_AIR,
                melee.enums.Action.LASER_GUN_PULL,
                melee.enums.Action.LOOPING_ATTACK_START,
                melee.enums.Action.LOOPING_ATTACK_MIDDLE,
                melee.enums.Action.MARTH_COUNTER,
                melee.enums.Action.MARTH_COUNTER_FALLING,
                melee.enums.Action.NAIR,
                melee.enums.Action.NESS_SHEILD,
                melee.enums.Action.NESS_SHEILD_AIR,
                melee.enums.Action.NESS_SHEILD_START,
                melee.enums.Action.NEUTRAL_ATTACK_1,
                melee.enums.Action.NEUTRAL_ATTACK_2,
                melee.enums.Action.NEUTRAL_ATTACK_3,
                melee.enums.Action.NEUTRAL_B_ATTACKING,
                melee.enums.Action.NEUTRAL_B_ATTACKING_AIR,
                melee.enums.Action.NEUTRAL_B_CHARGING,
                melee.enums.Action.NEUTRAL_B_CHARGING_AIR,
                melee.enums.Action.NEUTRAL_B_FULL_CHARGE,
                melee.enums.Action.NEUTRAL_B_FULL_CHARGE_AIR,
                melee.enums.Action.SWORD_DANCE_1,
                melee.enums.Action.SWORD_DANCE_1_AIR,
                melee.enums.Action.SWORD_DANCE_2_HIGH,
                melee.enums.Action.SWORD_DANCE_2_HIGH_AIR,
                melee.enums.Action.SWORD_DANCE_2_MID,
                melee.enums.Action.SWORD_DANCE_2_MID_AIR,
                melee.enums.Action.SWORD_DANCE_3_HIGH,
                melee.enums.Action.SWORD_DANCE_3_HIGH_AIR,
                melee.enums.Action.SWORD_DANCE_3_LOW,
                melee.enums.Action.SWORD_DANCE_3_LOW_AIR,
                melee.enums.Action.SWORD_DANCE_3_MID,
                melee.enums.Action.SWORD_DANCE_3_MID_AIR,
                melee.enums.Action.SWORD_DANCE_4_HIGH,
                melee.enums.Action.SWORD_DANCE_4_HIGH_AIR,
                melee.enums.Action.SWORD_DANCE_4_LOW,
                melee.enums.Action.SWORD_DANCE_4_LOW_AIR,
                melee.enums.Action.SWORD_DANCE_4_MID,
                melee.enums.Action.SWORD_DANCE_4_MID_AIR,
                melee.enums.Action.THROW_BACK,
                melee.enums.Action.THROW_DOWN,
                melee.enums.Action.THROW_FORWARD,
                melee.enums.Action.THROW_UP,
                melee.enums.Action.UAIR,
                melee.enums.Action.UPSMASH,
                melee.enums.Action.UPTILT,
                melee.enums.Action.UP_B_AIR,
                melee.enums.Action.UP_B_GROUND
            ]

            # console creation
            try:
                console = melee.Console(path="C:\\Users\\irp26\\AppData\\Roaming\\Slippi Launcher\\netplay",
                                        logger=None)
            except FileNotFoundError:
                tkinter.messagebox.showerror('Error starting dolphin!',
                                             'Could not find important files to launch dolphin! Please check that your netplay directory is properly set!')
                self.live_start_button.configure(state='enabled')


            # controllers setup
            controller_player = melee.Controller(console=console,
                                                 port=1,
                                                 type=melee.ControllerType.GCN_ADAPTER)

            controller_opponent = melee.Controller(console=console,
                                                   port=2,
                                                   type=melee.ControllerType.GCN_ADAPTER)

            # running the console / opening dolphin
            console.run("D:\\Game Downloads\\Roms\\GC\\asdf\\SSBMv102.iso")

            # Connect to the console
            print("Connecting to console...")
            if not console.connect():
                print("ERROR: Failed to connect to the console.")
                sys.exit(-1)
            print("Console connected")

            print("Connecting controller to console...")
            if not controller_player.connect():
                print("ERROR: Failed to connect the controller.")
                sys.exit(-1)
            print("Controller connected")

            # gameplay movechecking loop
            global live_selected_move
            self.selected_move_consecutive_use_count = 0

            while True:
                gamestate = console.step()
                # step() returns None when the file ends
                if gamestate is None:
                    continue
                if gamestate.menu_state in [melee.Menu.IN_GAME, melee.Menu.SUDDEN_DEATH]:
                    discoveredPort = 1
                    discoveredPort = melee.port_detector(gamestate, melee.Character.FALCO, 0)
                    if gamestate.players[discoveredPort].action_frame == 1:
                        if gamestate.players[discoveredPort].action == self.live_move_dict.get(live_selected_move):
                            print("adding to selected move count    ")
                            self.selected_move_consecutive_use_count += 1
                            print(self.selected_move_consecutive_use_count)
                        else:
                            if (gamestate.players[discoveredPort].action in self.live_attack_list):
                                if (self.live_move_dict.get(
                                        live_selected_move) == melee.enums.Action.THROW_DOWN or self.live_move_dict.get(
                                        live_selected_move) == melee.enums.Action.THROW_UP):
                                    if (gamestate.players[discoveredPort].action == melee.enums.Action.GRAB):
                                        pass
                                    else:
                                        print("reset")
                                        self.selected_move_consecutive_use_count = 0
                                else:
                                    print("reset")
                                    self.selected_move_consecutive_use_count = 0

                    if self.selected_move_consecutive_use_count >= int(max_consecutive_selected_move_uses):
                        print("max move consecutive use triggered")
                        self.selected_move_consecutive_use_count = 0
                        # if (live_response == "Sound"):
                        # print("sound")

        # Past Games Analysis
        ##########################
        
        # Setting up other attack array
        self.other_attacks_list = [
            slippi.id.ActionState.ATTACK_11,
            slippi.id.ActionState.ATTACK_12,
            slippi.id.ActionState.ATTACK_13,
            slippi.id.ActionState.ATTACK_100_START,
            slippi.id.ActionState.ATTACK_DASH,
            slippi.id.ActionState.ATTACK_S_3_HI,
            slippi.id.ActionState.ATTACK_S_3_HI_S,
            slippi.id.ActionState.ATTACK_S_3_S,
            slippi.id.ActionState.ATTACK_S_3_LW_S,
            slippi.id.ActionState.ATTACK_S_3_LW,
            slippi.id.ActionState.ATTACK_HI_3,
            slippi.id.ActionState.ATTACK_LW_3,
            slippi.id.ActionState.ATTACK_S_4_HI,
            slippi.id.ActionState.ATTACK_S_4_HI_S,
            slippi.id.ActionState.ATTACK_S_4_S,
            slippi.id.ActionState.ATTACK_S_4_LW_S,
            slippi.id.ActionState.ATTACK_S_4_LW,
            slippi.id.ActionState.ATTACK_HI_4,
            slippi.id.ActionState.ATTACK_LW_4,
            slippi.id.ActionState.ATTACK_AIR_N,
            slippi.id.ActionState.ATTACK_AIR_F,
            slippi.id.ActionState.ATTACK_AIR_B,
            slippi.id.ActionState.ATTACK_AIR_HI,
            slippi.id.ActionState.ATTACK_AIR_LW,
            slippi.id.ActionState.THROW_F,
            slippi.id.ActionState.THROW_B,
            slippi.id.ActionState.THROW_HI,
            slippi.id.ActionState.THROW_LW
        ]

        # Setting up the dictionaries
        self.past_move_dict = {
            "DTHROW": slippi.id.ActionState.THROW_LW,
            "UTHROW": slippi.id.ActionState.THROW_HI,
            "NEUTRAL_B": slippi.event.Attack.NEUTRAL_SPECIAL,
            "UTILT": slippi.id.ActionState.ATTACK_HI_3
        }

        # Calculation settings
        self.past_calculation_setting_label = customtkinter.CTkLabel(text="Calculate based on:",
                                                                     master=self.tab("Past Games"))
        self.past_calculation_setting_label.place(x=130,
                                                  y=145)
        # Calculation option menu
        self.past_calculation_setting_optionmenu_var = customtkinter.StringVar(value="Moves")
        self.selected_calculation_setting = self.past_calculation_setting_optionmenu_var.get()

        def past_calculation_setting_optionmenu_callback(choice):
            print("calculation setting selected: ", choice)
            self.selected_calculation_setting = self.past_calculation_setting_optionmenu_var

        self.past_calculation_setting_optionmenu = customtkinter.CTkOptionMenu(master=self.tab("Past Games"),
                                                                               values=["Moves", "Frames"],
                                                                               command=past_calculation_setting_optionmenu_callback,
                                                                               variable=self.past_calculation_setting_optionmenu_var)
        self.past_calculation_setting_optionmenu.place(x=120,
                                                       y=180)

        # Move Drop Down / Option Menu
        self.past_move_optionmenu_var = customtkinter.StringVar(value="DTHROW")
        self.selected_move = self.past_move_dict[self.past_move_optionmenu_var.get()]

        def past_move_optionmenu_callback(choice):
            print("move selected: ", choice)
            self.selected_move = self.past_move_dict[self.past_move_optionmenu_var.get()]

        self.past_move_optionmenu = customtkinter.CTkOptionMenu(master=self.tab("Past Games"),
                                                              values=["DTHROW", "UTHROW", "NEUTRAL_B", "UTILT"],
                                                              command=past_move_optionmenu_callback,
                                                              variable=self.past_move_optionmenu_var)

        self.past_move_optionmenu.place(x=500,
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
            self.selected_move_count = 0
            self.total_games_frames = 0
            self.total_attacks_used = 0
            for filename in os.listdir(replays_directory):
                f = os.path.join(replays_directory, filename)
                if not os.path.isfile(f):
                    break

                print(f)
                try:
                    game = Game(f)
                except:
                    print("Skipped a file due to corrupted or missing data, probably EOF. File skipped: {}".format(f))
                    continue
                self.total_games_frames = self.total_games_frames + len(game.frames)
                for frame in game.frames:
                    if self.selected_calculation_setting == "Moves":
                        # print("found frame {} to contain state {} in age {}".format(frame.index, frame.ports[1].leader.post.state, frame.ports[1].leader.post.state_age))
                        if frame.ports[0].leader.post.state == self.selected_move:
                            if frame.ports[0].leader.post.state_age == 1.0:
                                self.selected_move_count = self.selected_move_count + 1
                                self.total_attacks_used = self.total_attacks_used + 1
                        elif frame.ports[0].leader.post.state in self.other_attacks_list and frame.ports[
                            0].leader.post.state_age == 1.0:
                            self.total_attacks_used = self.total_attacks_used + 1
                    else:
                        if frame.ports[1].leader.post.last_attack_landed == self.selected_move:
                            self.selected_move_count = self.selected_move_count + 1

            if self.selected_calculation_setting == "Moves":
                print("You used {} {} times out of {} attacks!".format(
                    get_key_from_value(self.past_move_dict, self.selected_move), self.selected_move_count,
                    self.total_attacks_used))
                self.move_percent = ((self.selected_move_count / self.total_attacks_used) * 100)
                print("You used that move for %s%% of attacks!" % round(self.move_percent, 2))
            else:
                print("You spent {} frames with {} as your last hit move!".format(self.selected_move_count,
                                                                                  get_key_from_value(
                                                                                      self.past_move_dict,
                                                                                      self.selected_move)))
                self.move_percent = ((self.selected_move_count / self.total_games_frames) * 100)
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
                                   y=30)

        # Replays folder path
        self.folder_path_label = customtkinter.CTkLabel(text="Folder Path Will Display Here",
                                                        master=self.tab("Settings"))
        self.folder_path_label.place(x=20, y=110)

        self.folder_label = customtkinter.CTkLabel(text="Replay Folder:", master=self.tab("Settings"))
        self.folder_label.place(x=20, y=80)

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
        self.folder_select_button.place(x=110, y=80)

        # Slippi netplay folder selection

        self.netplay_folder_path_label = customtkinter.CTkLabel(text="Netplay folder path will display here",
                                                           master=self.tab("Settings"))
        self.netplay_folder_path_label.place(x=20, y=180)

        self.netplay_folder_label = customtkinter.CTkLabel(text="Netplay Folder:", master=self.tab("Settings"))
        self.netplay_folder_label.place(x=20, y=150)

        def netplay_folder_select_button_event():
            global netplay_directory
            netplay_directory = tkinter.filedialog.askdirectory(initialdir='C:\\',
                                                                title='Select Your Dolphin Netplay Directory',
                                                                )
            if len(str(netplay_directory)) > 40:
                self.netplay_folder_path_label.configure(text=(str(netplay_directory)[0:41] + "..."))
            else:
                self.netplay_folder_path_label.configure(text=str(netplay_directory))

        self.netplay_folder_select_button = customtkinter.CTkButton(master=self.tab("Settings"),
                                                            text='Select Netplay Folder',
                                                            command=lambda: netplay_folder_select_button_event())
        self.netplay_folder_select_button.place(x=110, y=150)

        # ISO path
        self.ISO_path_label = customtkinter.CTkLabel(text="ISO Path Will Display Here",
                                                        master=self.tab("Settings"))
        self.ISO_path_label.place(x=20, y=250)

        self.ISO_label = customtkinter.CTkLabel(text="ISO File:", master=self.tab("Settings"))
        self.ISO_label.place(x=20, y=220)

        def ISO_select_button_event():
            global ISO_path
            ISO_path = tkinter.filedialog.askopenfilename(initialdir='C:\\',
                                                          filetypes=(("ISO files","*.iso"), ("All files","*.*")),
                                                          title='Select Your ISO File',
                                                        )
            if len(str(ISO_path)) > 40:
                self.ISO_path_label.configure(text=(str(ISO_path)[0:41] + "..."))
            else:
                self.ISO_path_label.configure(text=str(ISO_path))

        self.ISO_select_button = customtkinter.CTkButton(master=self.tab("Settings"),
                                                            text='Select ISO',
                                                            command=lambda: ISO_select_button_event())
        self.ISO_select_button.place(x=110, y=220)


        # Credits button
        def open_credits_window_button_event():
            pass

        self.open_credits_window_button = customtkinter.CTkButton(master=self.tab("Settings"),
                                                                  text='Credits',
                                                                  command=lambda: open_credits_window_button_event())


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
