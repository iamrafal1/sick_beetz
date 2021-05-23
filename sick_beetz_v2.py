import sys
import pygame
import os
import time
import random
import keyboard
import shelve
import datetime
import glob
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from pathlib import Path


class MusicAdt:
    def __init__(self):
        self._rand = False
        self._cursor = 0
        types = ('./**/*.wav', './**/*.mp3')
        self._files = []
        for files in types:
            self._files.extend(glob.glob(files, recursive=True))
        self._counter = 0
        self._shuffle_factor = 1.0
        self._paths = []
        self._added_paths = []
        self._create_setting_file()
        self._read_paths()
        self._check_all_paths()
        self._structure = self._files

    def _check_all_paths(self):
        if len(self._paths) > 0:
            for i in self._paths:
                if i in self._added_paths:
                    continue
                types = ('*.wav', '*.mp3')
                temp = []
                print(i, "------------")
                i = Path(i)
                print(i)
                for files in types:
                    temp.extend(i.rglob(files))
                for j in temp:
                    if j not in self._files:
                        self._files.append(j)
                self._added_paths.append(i)

    def _read_paths(self):
        sett = shelve.open("settings")
        for i in sett["paths"]:
            self._paths.append(i)
        sett.close()

    def _create_setting_file(self):
        sett = shelve.open("settings", writeback=True)
        flag = "paths" in sett
        if not flag:
            sett["paths"] = []
        sett.close()

    def setting_add_default_path(self, p):
        sett = shelve.open("settings", writeback=True)
        if p not in sett["paths"]:
            sett["paths"].append(p)
        self._paths.append(p)
        sett.close()

    def force_check_paths(self):
        self._check_all_paths()

    def play(self, name):
        self._reshuffle()
        print("counter =", self._counter, "song =", os.path.basename(name), "duration =",
              str(datetime.timedelta(seconds=self.song_length(name) // 1)))
        self._counter += 1
        if self._counter > 100:
            return None
        self._player(name)
        self.play(self._structure[self._cursor])

    def _reshuffle(self):
        if self._cursor > (self.length() * self._shuffle_factor):
            print("--------------")
            self._shuffle()


    def shuffle_and_play(self):
        self._structure = self._files
        random.shuffle(self._structure)
        self._rand = True
        self._cursor = 0
        print("--------New list---------")
        j = 0
        for i in self._structure:
            print(j, os.path.basename(i))
            j += 1
        print("--------Playing---------")
        self.play(self._structure[self._cursor])

    def set_playlist(self, playlist):
        if len(playlist) > 0:
            self._structure = playlist

    def reset_from_playlist(self):
        self._structure = self._files

    def _shuffle(self):
        self._structure = self._files
        random.shuffle(self._structure)
        self._rand = True
        self._cursor = 0
        print("--------New list---------")
        for i in self._structure:
            print(i)
        print("--------Playing---------")

    def _player(self, name):
        pygame.init()
        # edit quality
        pygame.mixer.pre_init(frequency=48000, size=32, buffer=1024)
        pygame.mixer.init()
        stepper = 0
        # file loading
        pygame.mixer.music.load(name)
        stepper += 1
        pygame.mixer.music.play()
        time.sleep(1)
        duration = self.song_length(name)
        # buttons
        while True:
            pygame.time.Clock().tick(10)
            if keyboard.is_pressed("z + space"):
                pygame.mixer.music.pause()
            elif keyboard.is_pressed("z + p"):
                pygame.mixer.music.unpause()
            elif keyboard.is_pressed("z + t"):
                timer = pygame.mixer.music.get_pos()
                timer = timer // 1000
                print(str(timer) + "/" + str(duration // 1) + " seconds")
            elif keyboard.is_pressed("z + right"):
                self.next_track()
                return
            elif keyboard.is_pressed("z + left"):
                self.previous_track()
                return
            elif keyboard.is_pressed("z + e"):
                sys.exit()
            elif keyboard.is_pressed("z + i"):
                self.search()
                return
            elif pygame.mixer.music.get_pos() // 1000 > (duration // 1) - 1:
                break
            else:
                continue
        self.next_track()

    def search(self):
        while True:
            inp = input("Please enter song name:")
            i = 0
            while i < len(self._structure):
                print(inp)
                print((os.path.basename(self._structure[i])))
                if f'{inp.lower()}' in f'{os.path.basename(self._structure[i]).lower()}':
                    self._cursor = i
                    return
                i += 1
            print("The song was not found!")

    def next_track(self):
        if self._rand is False:
            if self._cursor < self.length() - 1:
                self._cursor += 1
            else:
                self._cursor = 0
        else:
            self._cursor += 1

    def mix_and_match(self, playlists):
        new_list = []
        for i in playlists:
            for j in i:
                new_list.append(j)
        self._files = new_list

    def song_length(self, song):
        try:
            audio = MP3(song)
            length = audio.info.length
            return length
        except:
            audio = WAVE(song)
            length = audio.info.length
            return length

    def previous_track(self):
        if self._cursor != 0:
            self._cursor -= 1

    def length(self):
        return len(self._structure)


class Playlist:
    def __init__(self):
        self._list = []
        self._name = None
        self._cd = glob.glob("./**/*.(mp3|wma|wav)", recursive=True)

    def create_new_playlist(self, name):
        self._name = name
        self._list = []

    def get_existing_playlist(self, name):
        try:
            pl = shelve.open("playlists")
            self._list = pl[name]
            self._name = name
            print("Currently selected playlist: %s" % name)
            pl.close()
        except:
            print("Selecting and retrieving playlist from database was unsuccessful, the input name may be incorrect")
            self._list = []
            self._name = None

    def add(self, name):
        if name in self._cd:
            self._list.append(name)
        else:
            print("ERROR - %s not found in the current directory, adding item to playlist failed" % name)

    def add_many(self, name_list):
        for i in name_list:
            self.add(i)

    def print_cd(self):
        j = 0
        for i in self._cd:
            print(f"{j}. {os.path.basename(i)}")
            j += 1

    def get_current_playlist_name(self):
        return self._name

    def get_current_playlist(self):
        return self._list

    def remove_song_from_current_playlist(self, song):
        if song in self._list:
            self._list.remove(song)
            print("Removed %s" % song)
        else:
            print("Removing failed, song not found in the playlist")

    def remove_current_playlist(self):
        if self._name is not None:
            print("Are you sure? [type y or n]")
            confirm = input()
            if confirm == "y":
                pl = shelve.open("playlists", writeback=True)
                del pl[self._name]
                pl.close()
                print("Successfully deleted %s playlist" % self._name)
                self._name = None
                self._list = []
            else:
                return
        else:
            print("No playlist selected! Use get_existing_playlist or create_new_playlist")

    def save_playlist(self):
        if self._name is not None:
            pl = shelve.open("playlists", writeback=True)
            pl[self._name] = self._list
            pl.close()
            print("Adding to playlist successful")
        else:
            print("No playlist is selected!")


sick_beetz = MusicAdt()
sick_beetz.force_check_paths()
sick_beetz.shuffle_and_play()
# template for adding pathways
# sick_beetz.add_default_path("../../muza/muzyka/Axis Bold as Love [1967]")