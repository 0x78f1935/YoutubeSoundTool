import tkinter as tk
import asyncio
import re
import youtube_dl
from bs4 import BeautifulSoup
import urllib.request
import os
import threading
import shutil


class YoutubeSoundTool(tk.Frame):
    def __init__(self, master=None, loop=None):
        super().__init__(master)

        if not os.path.exists('downloads'):
            oldmask = os.umask(000)
            os.makedirs('downloads', 0o777)
            os.umask(oldmask)

        # Create window title
        self.winfo_toplevel().title("YoutubeSoundTool")
        self.loop = loop

        # Define variables to store our content to work with
        self.urls = []
        self.playlists = []
        self.songs = []

        # Define youtube dl options
        # Verbose in ytdl OPT works for the complete script
        ytdl_format_options = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'cachedir': 'False',
            'ignoreerrors': 'True',
            'verbose': 'False',
            'outtmpl': 'downloads/%(title)s.mp3', #%(ext)s
            'nocheckcertificate': 'True',
            'noplaylist': 'True'
        }

        # Set debug variables
        if ytdl_format_options["verbose"] == 'False':
            self.debug_mode = False
        else:
            self.debug_mode = True

        # Define our youtube_dl variable
        self.ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

    def showEnd_output(self):
        self.text_output.see(tk.END)
        self.text_output.edit_modified(0)  # IMPORTANT - or <<Modified>> will not be called later.

    def body_add_entitie(self):
        # Create label frame
        layout = tk.Frame(master=self.master).grid(row=0, sticky=tk.E)

        # Add a label for a text output
        self.entitie_total_urls = tk.Label(layout, text=f'Input url:')
        self.entitie_total_urls.grid(row=1, sticky=tk.W)
        self.entitie_total_urls = tk.Label(layout, text=f'Urls to process: {len(self.urls)}')
        self.entitie_total_urls.grid(row=4, sticky=tk.W)
        self.entitie_total_vids = tk.Label(layout, text=f'Videos to download: {len(self.songs)}')
        self.entitie_total_vids.grid(row=5, sticky=tk.W)

        # Add a text field for a input
        self.entitie_entry = tk.Entry(layout)
        self.entitie_entry.grid(row=2, sticky=tk.W+tk.E)

        # Create add to queue button
        tk.Button(master=self.master, text="Add...", command=self.add_entity).grid(row=2, column=1, sticky=tk.E)
        # Create strip playlist btn
        tk.Button(master=self.master, text="Down", command=self.download).grid(row=3, column=1, sticky=tk.E)

        # Create label frame
        layout = tk.Frame(master=self.master).grid(row=8, sticky=tk.W)
        self.text_output = tk.Text(layout, bd=1, relief=tk.SUNKEN, height=25)
        self.text_output.see(tk.END)
        self.text_output.grid(row=8, column=0, sticky=tk.W+tk.E)

    def footer_quit_button(self):
        # Create label frame
        layout = tk.Frame(master=self.master).grid(row=5, column=1, sticky=tk.W)
        # Add a quit button
        tk.Button(master=layout, text="QUIT", fg="red", command=root.destroy).grid(row=5, column=1, sticky=tk.W)

    def footer_status_bar(self):
        # Create label frame
        layout = tk.Frame(master=self.master).grid(row=6, sticky=tk.W)
        self.status = tk.Label(layout, text="Insert a youtube link..", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.grid(row=7, column=0, sticky=tk.W+tk.E)

        # Add version number
        tk.Label(layout, text='| v1.0.1').grid(row=6, column=1, sticky=tk.W)

    def _download(self):
        """
        Download thread
        """
        self.text_output.insert(tk.END, "Download started, This can take a minute\n")
        self.text_output.insert(tk.END, "\tDownloading:\n")
        self.showEnd_output()

        for youtube_item in self.songs:
            print(f'Downloading: {youtube_item}')
            self.text_output.insert(tk.END, f"\t\t{youtube_item}\n")
            # Download item
            data = self.ytdl.extract_info(youtube_item, download=True)
            print(data)

        # Clean up workspace
        if os.path.isdir('False'):
            shutil.rmtree('False')

        # It can get messy if the terminal not gets cleaned.
        self.text_output.delete("1.0", tk.END)

        downloaded_files = '\n'.join([f'\t\t- {f[:55]}' for f in os.listdir('downloads') if os.path.isfile(os.path.join('downloads', f))])
        fmt = f"Your download(s) is complete. You can find your files over here:\n\n" \
              f"\t{os.path.abspath('downloads')}\n\n" \
              f"\tThe following files have been downloaded:\n\n"
        self.text_output.insert(tk.END, fmt)
        self.text_output.insert(tk.END, downloaded_files)
        self.showEnd_output()

        self.change_status('Finished downloading')
        # Lock entry while downloading
        self.entitie_entry.config(state=tk.NORMAL)
        self.entitie_total_urls["text"] = f'Urls to process: {len(self.urls)}'
        self.entitie_total_vids["text"] = f'Videos to download: {len(self.songs)}'
        self.playlists = []
        self.songs = []
        self.urls = []

    def download(self):
        """
        Download urls from the url list
        """
        # It can get messy if the terminal not gets cleaned.
        self.text_output.delete("1.0", tk.END)
        # Lock entry while downloading
        self.entitie_entry.config(state=tk.DISABLED)

        # Start the download
        self.change_status('Download(s) started')
        _thread_strip_playlist = threading.Thread(target=self._download)
        _thread_strip_playlist.daemon = True
        _thread_strip_playlist.start()

    def change_status(self, args:str):
        self.status["text"] = args
        return

    def _strip_playlist(self, url:str):
        self.text_output.insert(tk.END, "Playlist detected, Stripping links..\n")
        self.showEnd_output()
        # Make a list of all youtube links in the playlist
        final_urls = []  # results
        # Gather info about the search
        info = self.ytdl.extract_info(url, download=False, process=False)

        with urllib.request.urlopen(info["webpage_url"]) as request:
            webpage = request.read()

        soup = BeautifulSoup(webpage, 'html.parser')
        vid_url_pat = re.compile(r'watch\?v=\S+?list=')
        vid_url_matches = list(set(re.findall(vid_url_pat, str(soup))))

        # If url is a video, append it to the results
        for vid_url in vid_url_matches:
            if '&' in vid_url:
                url_amp = vid_url.index('&')
                final_urls.append('http://www.youtube.com/' + vid_url[:url_amp])

        for item in final_urls:
            self.songs.append(item)

        # Notfiy user
        self.text_output.insert(tk.END, "\tLinks found:\n")
        self.text_output.insert(tk.END, '\n'.join([f'\t\t- {x[:55]}' for x in final_urls]))
        self.text_output.insert(tk.END, "\n\nReady for download, or add another link..\n\n")
        self.showEnd_output()

        self.entitie_total_vids["text"] = f'Videos to download: {len(self.songs)}'

    def add_entity(self):
        """
        Check if links is processable
        If so determine if link is a playlist or not
        """
        # Process url if its a valid url
        url_number = 0

        # Get url
        url = self.entitie_entry.get()

        # Update GUI
        self.entitie_entry.delete(0, len(url))

        if re.search(r'(https?://)?(www.)??youtube(.*?)/(watch)(.*?)', url):
            self.urls.append(url)
            # regex magic to find any youtube playlist in the search
            if re.search(r'(https?://)?(www.)?youtube(.com)/[\w\d_\-?=&/]+',
                         url) and 'index' in url.lower() or 'list' in url.lower():
                print(f'playlist detected: {url}')
                self.change_status('playlist detected')

                print(url)
                if url not in self.playlists:
                    _thread_strip_playlist = threading.Thread(target=self._strip_playlist, args=(url,))
                    _thread_strip_playlist.daemon = True
                    _thread_strip_playlist.start()
                    self.playlists.append(url)
                    self.entitie_total_urls["text"] = f'Urls to process: {len(self.urls)}'

                else:
                    self.change_status('Url already fetched')
            else:
                # Song found.
                print(f'url detected: {url}')
                self.songs.append(url)
                self.entitie_total_urls["text"] = f'Urls to process: {len(self.urls)}'
                self.entitie_total_vids["text"] = f'Videos to download: {len(self.songs)}'
                self.text_output.insert(tk.END, "Single video detected, Stripping link..\n")
                # Notfiy user
                self.text_output.insert(tk.END, "\tLink found:\n")
                self.text_output.insert(tk.END, f'\n\t\t- {url[:55]}')
                self.text_output.insert(tk.END, "\n\nReady for download, or add another link..\n\n")
                self.showEnd_output()

        else:
            # If the url not starts with youtube, do nothing
            pass

            # hold track of the numbers of urls in the list
            url_number += 1


if __name__ == '__main__':
    # Create a loop we could hook into
    loop = asyncio.get_event_loop()
    # Define parent root
    root = tk.Tk()
    root.resizable(0, 0)
    # Define YoutubeSoundTool
    YoutubeSoundTool = YoutubeSoundTool(master=root, loop=loop)

    # Add GUI elements
    loop.create_task(YoutubeSoundTool.body_add_entitie())
    loop.create_task(YoutubeSoundTool.footer_quit_button())
    loop.create_task(YoutubeSoundTool.footer_status_bar())

    # Start program
    loop.create_task(root.mainloop())