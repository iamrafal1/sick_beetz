import pathlib
import sys
import pygame
import os
import time
import random
import shelve
import datetime
import glob
import tkinter
import tkinter.filedialog
from tkinter import ttk
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from pathlib import Path


class MusicAdt:
    def __init__(self):
        self.cursor = 0
        self._counter = 0
        self._shuffle_factor = 1.0
        self._paths = []
        self._added_paths = []
        self.structure = []
        self.paused = False
        pygame.init()
        pygame.mixer.pre_init(frequency=48000, size=32, buffer=1024)
        pygame.mixer.init()

    def check_if_playing(self):
        if pygame.mixer.music.get_busy():
            return True
        else:
            return False

    def pause(self):
        pygame.mixer.music.pause()
        self.paused = True

    def load(self):
        pygame.mixer.music.load(self.structure[self.cursor])

    def play(self):
        if self.paused is False:
            pygame.mixer.music.play()
        else:
            pygame.mixer.music.unpause()
            self.paused = False

    def load_and_play(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.load(self.structure[self.cursor])
        pygame.mixer.music.play()

    def stop(self):
        pygame.mixer.music.stop()

    def set_position(self, position):
        pygame.mixer.music.stop()
        pygame.mixer.music.play()
        pygame.mixer.music.set_pos(position)

    def get_song_time(self):
        return pygame.mixer.music.get_pos() // 1000

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
        if self.cursor != 0:
            self.cursor -= 1
        pygame.mixer.music.load(self.structure[self.cursor])
        self.play()

    def next_track(self):
        if self.cursor < self.length() - 1:
            self.cursor += 1
        else:
            self.cursor = 0
        pygame.mixer.music.load(self.structure[self.cursor])
        self.play()

    def length(self):
        return len(self.structure)



class Playlist:
    def __init__(self):
        self._paths = []
        self._added_paths = []
        types = ('./**/*.wav', './**/*.mp3')
        self._files = []
        for files in types:
            self._files.extend(glob.glob(files, recursive=True))
        self._read_paths()
        self._check_all_paths()
        self._send_all_to_music_adt()
        self.save_playlist("All songs", self._files)
        sick_beetz.load()

    def _send_all_to_music_adt(self):
        sick_beetz.structure = self._files

    def _check_all_paths(self):
        if len(self._paths) > 0:
            for i in self._paths:
                if i in self._added_paths:
                    continue
                types = ('*.wav', '*.mp3')
                temp = []
                i = Path(i)
                for files in types:
                    temp.extend(i.rglob(files))
                for j in temp:
                    if j not in self._files:
                        self._files.append(str(j))
                self._added_paths.append(i)

    def _read_paths(self):
        for i in sett.access_setting("paths"):
            self._paths.append(i)

    def force_check_paths(self):
        self._paths = []
        self._read_paths()
        self._check_all_paths()

    def get_existing_playlist(self, name):
        try:
            pl = shelve.open("playlists")
            my_list = pl[name]
            pl.close()
            return my_list
        except:
            print("Selecting and retrieving playlist from database was unsuccessful, the input name may be incorrect")

    def get_all_playlist_names(self):
        pl = shelve.open("playlists")
        names = pl.keys()
        return names

    '''Potentially add method for all items in database, keys and values'''

    def remove_playlist(self, name):
        pl = shelve.open("playlists", writeback=True)
        del pl[name]
        pl.close()
        print("Successfully deleted %s playlist" % name)

    def save_playlist(self, name, playlist):
        pl = shelve.open("playlists", writeback=True)
        pl[name] = playlist
        pl.close()
        print("Adding to playlist successful")


class SettingsFile:

    def __init__(self):
        self.name = "settings"
        s = shelve.open(self.name)
        if "reshuffle" not in s.keys():
            s["reshuffle"] = 1.0
        if "paths" not in s.keys():
            s["paths"] = []
        s.close()

    def access_setting(self, name):
        st = shelve.open(self.name)
        temp = st[name]
        st.close()
        return temp

    def save_setting(self, name, value):
        st = shelve.open(self.name, writeback=True)
        st[name] = value
        st.close()


class MainWindow:

    def __init__(self):
        self.app = tkinter.Tk()
        self._tab_control = ttk.Notebook(self.app)
        self._now_playing = NowPlaying(self._tab_control)
        self._songs = Songs(self._tab_control)
        self._playlists = Playlists(self._tab_control)
        self._settings = Settings(self._tab_control)
        self._declare_tabs()
        self._prev_list = tkinter.Listbox(self._now_playing.frame)
        self._now_playing.change_song()
        self.app.title("Sick Beetz")
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)

        # self._now_playing._current_song['text'] = "pizza" (accessing data from frame class nad modifying it)

        # ttk.Label(tab1, text=”Welcome to GeeksForGeeks”).grid(column=0, row=0, padx=30, pady=30) (template)

    def _declare_tabs(self):
        self._tab_control.add(self._now_playing.frame, text='Now Playing')
        self._tab_control.add(self._songs.frame, text='Songs')
        self._tab_control.add(self._playlists.frame, text='Playlists')
        self._tab_control.add(self._settings.frame, text='Settings')
        self._tab_control.grid(row=0, column=0)

    def on_closing(self):
        sick_beetz.stop()
        print("terminating")
        time.sleep(0.5)
        del self._now_playing
        self.app.destroy()


class NowPlaying:

    def __init__(self, parent):
        self._parent = parent
        self.frame = tkinter.Frame(self._parent)
        self._counter = 0
        self._song_length = sick_beetz.song_length(sick_beetz.structure[sick_beetz.cursor]) // 1
        self._progress_interval = self._song_length // 100
        self._progress_tracking = self._progress_interval
        self._progress_bar_width = 0
        self._current_song = tkinter.Label(self.frame, text=str(os.path.basename(sick_beetz.structure[0]))[:-4],
                                           wraplength=250)
        self._prev_list = tkinter.Listbox(self.frame, height=6, width=30)
        self._prev_list.insert(0, "Previous 5")
        self._next_list = tkinter.Listbox(self.frame, height=6, width=30)
        self._next_list.insert(0, "Next 5")
        self._progress_bar = tkinter.Canvas(self.frame, bg="white", height=10, width=300)
        self._image_canvas = tkinter.Label(self.frame, bg="white")
        self._current_time = tkinter.Label(self.frame, text=str(datetime.timedelta(seconds=self._counter)))
        self._end_time = tkinter.Label(self.frame, text=str(datetime.timedelta(seconds=self._song_length)))
        self._prev_track = tkinter.Button(self.frame, text="Prev", command=self.play_prev_track)
        self._next_track = tkinter.Button(self.frame, text="Next", command=self.play_next_track)
        self._play_pause = tkinter.Button(self.frame, text="Play/Pause", command=self.play_checker)
        self._repeat_button = tkinter.Button(self.frame, text="Repeat", command=self.repeat)
        self._repeat_check = False
        self._position()
        self.set_next_list()
        self.set_previous_list()
        self.prev_time = 0
        self._progress_x = 0
        self._offset = 0
        self._angle = 0
        self._next_list.bind('<<ListboxSelect>>', self.on_select_next)
        self._prev_list.bind('<<ListboxSelect>>', self.on_select_prev)
        self.frameCnt = 69
        self.current_frame = 0
        self.iterator = 0
        self._frames = []
        self.load_frames()
        self.looper()


    def _position(self):
        self._current_song.grid(row=1, column=1, columnspan=3)
        self._prev_list.grid(row=1, column=0, rowspan=6, sticky='e')
        self._next_list.grid(row=1, column=4, rowspan=6, sticky='w')
        self._image_canvas.grid(row=3, column=1, columnspan=3)
        self._progress_bar.grid(row=8, column=1, columnspan=3)
        self._current_time.grid(row=8, column=0, sticky='e')
        self._end_time.grid(row=8, column=4, sticky='w')
        self._repeat_button.grid(row=9, column=0, sticky="e")
        self._prev_track.grid(row=9, column=1)
        self._next_track.grid(row=9, column=3)
        self._play_pause.grid(row=9, column=2)
        self._progress_bar.bind('<Button-1>', self.getx)

    def on_select_next(self, event):
        w = event.widget
        index = int(w.curselection()[0])
        sick_beetz.cursor += index
        sick_beetz.load_and_play()
        self.change_song()
        app._songs.current_song()

    def on_select_prev(self, event):
        w = event.widget
        index = int(w.curselection()[0])
        sick_beetz.cursor -= index
        sick_beetz.load_and_play()
        self.change_song()
        app._songs.current_song()

    def set_previous_list(self):
        i = sick_beetz.cursor - 1
        j = 1
        self._prev_list.delete(1, tkinter.END)
        while i > -1 and j < 6:
            self._prev_list.insert(j, str(os.path.basename(sick_beetz.structure[i]))[:-4])
            i -= 1
            j += 1

    def set_next_list(self):
        i = sick_beetz.cursor + 1
        j = 1
        self._next_list.delete(1, tkinter.END)
        while i < sick_beetz.length() and j < 6:
            self._next_list.insert(j, str(os.path.basename(sick_beetz.structure[i]))[:-4])
            i += 1
            j += 1

    def repeat(self):
        if self._repeat_check is False:
            self._repeat_check = True
            self._repeat_button.config(relief=tkinter.SUNKEN)
        else:
            self._repeat_check = False
            self._repeat_button.config(relief=tkinter.RAISED)

    def play_checker(self):
        if sick_beetz.check_if_playing() is True:
            sick_beetz.pause()
        else:
            sick_beetz.play()

    def change_song(self):
        self.set_next_list()
        self.set_previous_list()
        self._counter = 0
        self._song_length = sick_beetz.song_length(sick_beetz.structure[sick_beetz.cursor]) // 1
        self._progress_interval = self._song_length / 100
        self._end_time['text'] = str(datetime.timedelta(seconds=self._song_length))
        self._current_song['text'] = str(os.path.basename(sick_beetz.structure[sick_beetz.cursor]))[:-4]
        self._current_time['text'] = str(datetime.timedelta(seconds=self._counter // 1))
        self._progress_tracking = self._progress_interval
        self._progress_bar.delete("all")
        self._progress_bar_width = 0
        self._offset = 0

    def play_next_track(self):
        if self._repeat_check is not True:
            sick_beetz.next_track()
            self.change_song()
            app._songs.current_song()
        else:
            sick_beetz.stop()
            sick_beetz.load_and_play()
            self.change_song()
            app._songs.current_song()


    def play_prev_track(self):
        sick_beetz.previous_track()
        self.change_song()
        app._songs.current_song()

    def getx(self, event):
        self._progress_x = event.x # percent of bar
        self._offset = (self._song_length / 100) * (self._progress_x / 3)
        self._counter = self._offset // 1
        self._current_time['text'] = str(datetime.timedelta(seconds=self._counter))
        self._progress_tracking = self._progress_interval + self._counter
        self._progress_bar_width = self._progress_x
        self._progress_bar.delete('all')
        self._progress_bar.create_rectangle(0, 0, self._progress_bar_width, 10, fill="purple")
        self._progress_x = 0
        sick_beetz.set_position(self._offset)

    def load_frames(self):
        i = 0
        self._image_canvas.configure(image=tkinter.PhotoImage(file='rotation.gif', format='gif -index %i' % i))
        while i < 70:
            self._frames.append(tkinter.PhotoImage(file='rotation.gif', format='gif -index %i' % i))
            if i == 0:
                self._image_canvas.configure(image=self._frames[i])
            i += 1

    def looper(self):
        #old loop start
        st = sick_beetz.get_song_time() + self._offset
        if st > self._counter:
            self._counter = st
            self._current_time["text"] = str(datetime.timedelta(seconds=self._counter // 1))
        if self._counter >= self._progress_tracking:
            self._progress_tracking += self._progress_interval
            self._progress_bar_width += 3
            self._progress_bar.create_rectangle(0, 0, self._progress_bar_width, 10, fill="purple")
        if st > self._song_length - 2:
            self.play_next_track()
        if sick_beetz.check_if_playing():
            if self.current_frame > self.frameCnt:
                self.current_frame = 0
            self._image_canvas.configure(image=self._frames[self.current_frame])
            self.current_frame += 1
        self.frame.after(40, self.looper)



class Songs:

    def __init__(self, parent):
        self._parent = parent
        self.frame = tkinter.Frame(self._parent)
        self.options = [
            "Name asc",
            "Name desc",
            "Duration asc",
            "Duration desc",
            "Shuffle"
        ]
        self.clicked = tkinter.StringVar()
        self._current_sort = None
        self._restore = False
        self._previous_cursor = None
        self.clicked.set("Name asc")
        self.sv = tkinter.StringVar()
        self.search = tkinter.Entry(self.frame, width=30, textvariable=self.sv)
        self.search.insert(0, "search")
        self.sv.trace("w", lambda name, index, mode, sv=self.sv: self.callback())
        self.drop = tkinter.OptionMenu(self.frame, self.clicked, *self.options)
        self.button = tkinter.Button(self.frame, text="Sort", command=self.sort)
        self.label = tkinter.Label(self.frame, text=" ")
        self.number_label = tkinter.Label(self.frame, text="No.")
        self.track_label = tkinter.Label(self.frame, text="Track")
        self.duration_label = tkinter.Label(self.frame, text="Duration")
        self.number = tkinter.Listbox(self.frame, height=13, activestyle="none", selectbackground="gray75", selectforeground="deep pink")
        self.name = tkinter.Listbox(self.frame, width=70, height=13, activestyle="none", selectbackground="gray75", selectforeground="deep pink")
        self.duration = tkinter.Listbox(self.frame, height=13, activestyle="none", selectbackground="gray75", selectforeground="deep pink")
        self.playlist = tkinter.Label(self.frame, text="All Songs")
        self.dirty_list = []
        self.showing_list = []
        self.temp_list = []
        self.reshuffle_factor = float(sett.access_setting("reshuffle"))
        self.reshuffle = len(sick_beetz.structure) * (self.reshuffle_factor// 1)
        self.position()
        self.create_table()
        sick_beetz.load()
        self.name.bind("<MouseWheel>", self.mousewheel1)
        self.number.bind("<MouseWheel>", self.mousewheel2)
        self.duration.bind("<MouseWheel>", self.mousewheel3)
        self.name.bind('<<ListboxSelect>>', self.play_song)


    def position(self):
        self.drop.grid(row=0, column=0)
        self.button.grid(row=0, column=1, sticky="w")
        self.search.grid(row=0, column=2)
        self.label.grid(row=1, column=0)
        self.playlist.grid(row=1, column=1)
        self.number_label.grid(row=2, column=0, sticky="w")
        self.track_label.grid(row=2, column=1, sticky="w")
        self.duration_label.grid(row=2, column=2, sticky="w")
        self.number.grid(row=3, column=0)
        self.name.grid(row=3, column=1)
        self.duration.grid(row=3, column=2, sticky="w")

    def mousewheel1(self, event):
        self.number.yview_scroll(-4 * int(event.delta / 120), "units")
        self.duration.yview_scroll(-4 * int(event.delta / 120), "units")

    def mousewheel2(self, event):
        self.name.yview_scroll(-4 * int(event.delta / 120), "units")
        self.duration.yview_scroll(-4 * int(event.delta / 120), "units")

    def mousewheel3(self, event):
        self.number.yview_scroll(-4 * int(event.delta / 120), "units")
        self.name.yview_scroll(-4 * int(event.delta / 120), "units")

    def create_table(self):
        self.dirty_list = []
        for i in sick_beetz.structure:
            self.dirty_list.append((i, sick_beetz.song_length(i)))
        self.name_asc()
        self.colour_coordinate()
        self.current_song()

    def check_reshuffle(self):
        if self._previous_cursor >= (self.reshuffle_factor * len(self.showing_list)) // 1:
            self.shuffle()
            self.colour_coordinate()
            sick_beetz.cursor = 0
            self._previous_cursor = None
            sick_beetz.load_and_play()
            app._now_playing.change_song()
            self.current_song()

    def name_asc(self):
        self.dirty_list = sorted(self.dirty_list, key=lambda name: os.path.basename(name[0]))
        sick_beetz.structure = []
        self.showing_list = []
        j = 0
        for i in self.dirty_list:
            self.showing_list.append((j, os.path.basename(i[0])[:-4], str(datetime.timedelta(seconds=i[1] // 1))))
            sick_beetz.structure.append(i[0])
            j += 1
        self.number.delete(0, tkinter.END)
        self.name.delete(0, tkinter.END)
        self.duration.delete(0, tkinter.END)
        for i in self.showing_list:
            self.number.insert(i[0], i[0])
            self.name.insert(i[0], i[1])
            self.duration.insert(i[0], i[2])
        self._current_sort = "Name asc"

    def name_desc(self):
        self.dirty_list = sorted(self.dirty_list, key=lambda name: os.path.basename(name[0]), reverse=True)
        sick_beetz.structure = []
        self.showing_list = []
        j = 0
        for i in self.dirty_list:
            self.showing_list.append((j, os.path.basename(i[0])[:-4], str(datetime.timedelta(seconds=i[1] // 1))))
            sick_beetz.structure.append(i[0])
            j += 1
        self.number.delete(0, tkinter.END)
        self.name.delete(0, tkinter.END)
        self.duration.delete(0, tkinter.END)
        for i in self.showing_list:
            self.number.insert(i[0], i[0])
            self.name.insert(i[0], i[1])
            self.duration.insert(i[0], i[2])
        self._current_sort = "Name desc"

    def dur_asc(self):
        self.dirty_list = sorted(self.dirty_list, key=lambda name: name[1])
        sick_beetz.structure = []
        self.showing_list = []
        j = 0
        for i in self.dirty_list:
            self.showing_list.append((j, os.path.basename(i[0])[:-4], str(datetime.timedelta(seconds=i[1] // 1))))
            sick_beetz.structure.append(i[0])
            j += 1
        self.number.delete(0, tkinter.END)
        self.name.delete(0, tkinter.END)
        self.duration.delete(0, tkinter.END)
        for i in self.showing_list:
            self.number.insert(i[0], i[0])
            self.name.insert(i[0], i[1])
            self.duration.insert(i[0], i[2])
        self._current_sort = "Duration asc"

    def dur_desc(self):
        self.dirty_list = sorted(self.dirty_list, key=lambda name: name[1], reverse=True)
        sick_beetz.structure = []
        self.showing_list = []
        j = 0
        for i in self.dirty_list:
            self.showing_list.append((j, os.path.basename(i[0])[:-4], str(datetime.timedelta(seconds=i[1] // 1))))
            sick_beetz.structure.append(i[0])
            j += 1
        self.number.delete(0, tkinter.END)
        self.name.delete(0, tkinter.END)
        self.duration.delete(0, tkinter.END)
        for i in self.showing_list:
            self.number.insert(i[0], i[0])
            self.name.insert(i[0], i[1])
            self.duration.insert(i[0], i[2])
        self._current_sort = "Duration desc"

    def shuffle(self):
        random.shuffle(self.dirty_list)
        sick_beetz.structure = []
        self.showing_list = []
        j = 0
        for i in self.dirty_list:
            self.showing_list.append((j, os.path.basename(i[0])[:-4], str(datetime.timedelta(seconds=i[1] // 1))))
            sick_beetz.structure.append(i[0])
            j += 1
        self.number.delete(0, tkinter.END)
        self.name.delete(0, tkinter.END)
        self.duration.delete(0, tkinter.END)
        for i in self.showing_list:
            self.number.insert(i[0], i[0])
            self.name.insert(i[0], i[1])
            self.duration.insert(i[0], i[2])
        self._current_sort = "Shuffle"

    def sort(self):
        self.label.config(text=self.clicked.get())
        if not self.label['text'] == self._current_sort or self._restore:
            if self.label['text'] == "Name asc":
                self.name_asc()
            elif self.label['text'] == "Name desc":
                self.name_desc()
            elif self.label['text'] == "Duration asc":
                self.dur_asc()
            elif self.label['text'] == "Duration desc":
                self.dur_desc()
        if self.label['text'] == "Shuffle":
            self.shuffle()
        self.colour_coordinate()
        self.current_song()
        if self._restore is not True:
            sick_beetz.load_and_play()
            app._now_playing.change_song()
        self._restore = False

    def callback(self):
        text = self.sv.get()
        self.temp_list = []
        if len(text) == 0:
            self._restore = True
            self.sort()
        else:
            for i in self.showing_list:
                if text.lower() in i[1].lower():
                    self.temp_list.append(i)
            self.number.delete(0, tkinter.END)
            self.name.delete(0, tkinter.END)
            self.duration.delete(0, tkinter.END)
            for i in self.temp_list:
                self.number.insert(i[0], i[0])
                self.name.insert(i[0], i[1])
                self.duration.insert(i[0], i[2])
            self.colour_coordinate()

    def play_song(self, event):
        w = event.widget
        index = int(w.curselection()[0])
        cursor_index = self.number.get(index)
        sick_beetz.cursor = cursor_index
        sick_beetz.load_and_play()
        app._now_playing.change_song()
        self.current_song()

    def colour_coordinate(self):
        if self.temp_list == []:
            i = 0
            while i < len(self.showing_list):
                if i % 2 == 0:
                    self.name.itemconfig(i, bg="ivory")
                    self.number.itemconfig(i, bg="ivory")
                    self.duration.itemconfig(i, bg="ivory")
                else:
                    self.name.itemconfig(i, bg="light blue")
                    self.number.itemconfig(i, bg="light blue")
                    self.duration.itemconfig(i, bg="light blue")
                i += 1
        else:
            i = 0
            while i < len(self.temp_list):
                if i % 2 == 0:
                    self.name.itemconfig(i, bg="ivory")
                    self.number.itemconfig(i, bg="ivory")
                    self.duration.itemconfig(i, bg="ivory")
                else:
                    self.name.itemconfig(i, bg="light blue")
                    self.number.itemconfig(i, bg="light blue")
                    self.duration.itemconfig(i, bg="light blue")
                i += 1


    def current_song(self):
        if self._previous_cursor:
            self.check_reshuffle()
        cursor = sick_beetz.cursor
        counter = 0
        if self._previous_cursor is not None:
            self.name.itemconfig(self._previous_cursor, fg="black")
            self.number.itemconfig(self._previous_cursor, fg="black")
            self.duration.itemconfig(self._previous_cursor, fg="black")

        self._previous_cursor = cursor
        if self.temp_list == []:
            self.name.itemconfig(cursor, fg="deep pink")
            self.number.itemconfig(cursor, fg="deep pink")
            self.duration.itemconfig(cursor, fg="deep pink")
        else:
            for i in self.temp_list:
                if cursor == i[0]:
                    break
                counter += 1
            self.name.itemconfig(counter, fg="deep pink")
            self.number.itemconfig(counter, fg="deep pink")
            self.duration.itemconfig(counter, fg="deep pink")


class Playlists:
    """Needs to update occasionally"""
    def __init__(self, parent):
        self._parent = parent
        self.frame = tkinter.Frame(self._parent)
        self.name_list = tkinter.Listbox(self.frame, width=70)
        self.song_number = tkinter.Listbox(self.frame)
        self.total_duration = tkinter.Listbox(self.frame)
        self.name_label = tkinter.Label(self.frame, text="Name")
        self.song_number_label = tkinter.Label(self.frame, text="Total songs")
        self.total_duration_label = tkinter.Label(self.frame, text="Total duration")
        self.new_playlist = tkinter.Button(self.frame, text="New +", command=self.add_new)    # Command = add new
        self.new_name = tkinter.Entry(self.frame)
        self.new_name.insert(0, "New playlist name")
        self.all_playlists = playlist_access.get_all_playlist_names()
        self.position()
        self.m = tkinter.Menu(self.name_list, tearoff=0)
        self.m.add_command(label="Edit Playlist", command=self.edit)
        self.m.add_command(label="Delete Playlist", command=self.delete)
        self.m.add_command(label="Load Playlist", command=self.load)
        self.m.add_command(label="Mix and Match", command=self.mix)
        self.name_list.bind("<Button-3>", self.do_popup)


    def position(self):
        self.new_playlist.grid(row=0, column=0, sticky="e")
        self.new_name.grid(row=0, column=1, sticky="w")
        self.name_label.grid(row=1, column=0)
        self.song_number_label.grid(row=1, column=2)
        self.total_duration_label.grid(row=1, column=3)
        self.name_list.grid(row=2, column=0, columnspan=2)
        self.song_number.grid(row=2, column=2)
        self.total_duration.grid(row=2, column=3)

    def do_popup(self, event):
        try:
            self.m.tk_popup(event.x_root, event.y_root)
        finally:
            self.m.grab_release()

    def add_new(self):
        name = self.new_name.get()
        if name not in self.all_playlists:
            self.name_list.insert(tkinter.END, name)
            self.song_number.insert(tkinter.END, 0)
            self.total_duration.insert(tkinter.END, 0)
            PlaylistAdder([], name)

    def mix(self):
        name = self.name_list.get(self.name_list.curselection())
        my_list = playlist_access.get_existing_playlist(name)
        for i in my_list:
            if i not in sick_beetz.structure:
                sick_beetz.structure.append(i)
        app._songs.create_table()
        app._songs.playlist['text'] = "Mix"
        app._songs.current_song()
        app._songs.reshuffle = len(my_list) * sett.access_setting("reshuffle")

    def refresh(self):
        self.all_playlists = playlist_access.get_all_playlist_names()
        self.name_list.delete(0, tkinter.END)
        self.song_number.delete(0, tkinter.END)
        self.total_duration.delete(0, tkinter.END)
        self.fill_tables()

    def edit(self):
        name = self.name_list.get(self.name_list.curselection())
        my_list = playlist_access.get_existing_playlist(name)
        wind = PlaylistAdder(my_list, name)

    def delete(self):
        name = self.name_list.get(self.name_list.curselection())
        playlist_access.remove_playlist(name)
        self.all_playlists = playlist_access.get_all_playlist_names()
        self.name_list.delete(0, tkinter.END)
        self.song_number.delete(0, tkinter.END)
        self.total_duration.delete(0, tkinter.END)
        self.fill_tables()

    def load(self):
        name = self.name_list.get(self.name_list.curselection())
        my_list = playlist_access.get_existing_playlist(name)
        sick_beetz.structure = my_list
        app._songs.create_table()
        app._songs.playlist['text'] = name
        app._songs.current_song()
        app._songs.reshuffle =  len(my_list) * sett.access_setting("reshuffle")


    def fill_tables(self):
        j = 0
        for i in self.all_playlists:
            values = playlist_access.get_existing_playlist(i)
            self.name_list.insert(j, i)
            self.song_number.insert(j, len(values))
            sum = 0
            mylist = app._songs.dirty_list
            for k in values:
                for l in mylist:
                    if k in str(l[0]):
                        sum += l[1]
                        break
            self.total_duration.insert(j, str(datetime.timedelta(seconds=sum // 1)))
            j += 1
        self.colour_coordinate()

    def colour_coordinate(self):
        i = 0
        while i < len(self.all_playlists):
             if i % 2 == 0:
                self.name_list.itemconfig(i, bg="ivory")
                self.song_number.itemconfig(i, bg="ivory")
                self.total_duration.itemconfig(i, bg="ivory")
             else:
                self.name_list.itemconfig(i, bg="light blue")
                self.song_number.itemconfig(i, bg="light blue")
                self.total_duration.itemconfig(i, bg="light blue")
             i += 1


class PlaylistAdder:
    def __init__(self, list2, l2_name):
        self.window = tkinter.Tk()
        self.l1 = playlist_access.get_existing_playlist("All songs")
        self.l2 = list2
        self.l2_name = l2_name
        self.list1 = tkinter.Listbox(self.window, width=70, height=13)
        self.list2 = tkinter.Listbox(self.window, width=70, height=13)
        self.list1_label = tkinter.Label(self.window)
        self.list2_label = tkinter.Label(self.window)
        self.save_button = tkinter.Button(self.window, text="Save", command=self.save)
        self.position()
        self.fill_tables()
        self.list1.bind('<<ListboxSelect>>', self.add_to_list2)
        self.list2.bind('<<ListboxSelect>>', self.remove_from_list2)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def position(self):
        self.list1_label.grid(row=0, column=0)
        self.list2_label.grid(row=0, column=2)
        self.list1.grid(row=1, column=0, columnspan=2)
        self.list2.grid(row=1, column=2, columnspan=2)
        self.save_button.grid(row=3, column=0)

    def fill_tables(self):
        j = 0
        for i in self.l1:
            self.list1.insert(j, i)
            if j % 2 == 0:
                self.list1.itemconfig(j, bg="ivory")
            else:
                self.list1.itemconfig(j, bg="light blue")
            j += 1
        j = 0
        if self.l2 != []:
            for i in self.l2:
                self.list2.insert(j, i)
                if j % 2 == 0:
                    self.list2.itemconfig(j, bg="ivory")
                else:
                    self.list2.itemconfig(j, bg="light blue")
                j += 1

    def colour_coordinate(self):
        j = 0
        if self.l2 != []:
            for i in self.l2:
                if j % 2 == 0:
                    self.list2.itemconfig(j, bg="ivory")
                else:
                    self.list2.itemconfig(j, bg="light blue")
                j += 1

    def add_to_list2(self, event):
        w = event.widget
        index = w.curselection()
        name = self.list1.get(index)
        if name not in self.l2:
            self.l2.append(name)
            self.list2.insert(len(self.l2), name)
            self.colour_coordinate()

    def remove_from_list2(self, event):
        w = event.widget
        index = int(w.curselection()[0])
        name = self.list2.get(index)
        self.l2.remove(name)
        self.list2.delete(index)
        self.colour_coordinate()

    def save(self):
        playlist_access.save_playlist(self.l2_name, self.l2)
        app._playlists.refresh()
        self.window.destroy()

    def on_closing(self):
        app._playlists.refresh()
        self.window.destroy()


class Settings:
    # Remember to change settings in playlist class
    def __init__(self, parent):
        self._parent = parent
        self.frame = tkinter.Frame(self._parent)
        self.paths = sett.access_setting("paths")
        self.paths_list = tkinter.Listbox(self.frame, height=6, width=70)
        self.paths_label = tkinter.Label(self.frame, text="Paths", font="default 10 underline")
        self.add_button = tkinter.Button(self.frame, text="Add new+", command=self.new_path)
        self.reshuffle_label = tkinter.Label(self.frame,
                                             text="Reshuffle factor (after what % of list does it reshuffle)",
                                             font="default 10 underline")
        self.reshuffle_entry = tkinter.Entry(self.frame)
        self.reshuffle = 0
        self.note = tkinter.Label(self.frame, text="Save and Restart app to apply changes")
        self.save_button = tkinter.Button(self.frame, text="Save", command=self.save)
        self.position()
        self.fill_info()

    def position(self):
        self.paths_label.grid(row=0, column=0, sticky="w")
        self.add_button.grid(row=1, column=0, sticky="w")
        self.paths_list.grid(row=2, column=0, sticky="w", pady=5)
        self.reshuffle_label.grid(row=3, column=0, sticky="w", pady=5)
        self.reshuffle_entry.grid(row=4, column=0, sticky="w")
        self.save_button.grid(row=5, column=0, sticky="w", pady=5)
        self.note.grid(row=6, column=0, sticky="w", pady=5)

    def fill_info(self):
        self.fill_table()
        reshuffle = sett.access_setting("reshuffle")
        self.reshuffle_entry.insert(0, reshuffle)

    def fill_table(self):
        self.paths_list.delete(0, tkinter.END)
        j = 0
        for i in self.paths:
            self.paths_list.insert(j, i)
        self.colour_coordinate()

    def colour_coordinate(self):
        j = 0
        if self.paths != []:
            for i in self.paths:
                if j % 2 == 0:
                    self.paths_list.itemconfig(j, bg="ivory")
                else:
                    self.paths_list.itemconfig(j, bg="light blue")
                j += 1

    def new_path(self):
        pathway = tkinter.filedialog.askdirectory()
        pathway = os.path.relpath(pathway, os.getcwd())
        self.paths.append(pathway)
        self.fill_table()

    def save(self):
        sett.save_setting("reshuffle", self.reshuffle_entry.get())
        sett.save_setting("paths", self.paths)




sick_beetz = MusicAdt()
sett = SettingsFile()
playlist_access = Playlist()
app = MainWindow()
app._playlists.fill_tables()
app.app.mainloop()


