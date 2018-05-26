import youtube_dl
import os
import re
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import logging
import shutil

class YTDTool(object):
    def __init__(self, urls:list, *, download=False):
        # Define our youtube urls in a list format
        self.urls = urls
        """
        Known error:
            'ffprobe or avprobe not found. Please install one'

        Where is this happening?
            This error can raise on windows machines.
            Probably this is your first run aswell.
        Solution:
            Download LIBAV http://builds.libav.org/windows/release-gpl/,
            I used libav-11.3-win64.7z. Just copy 'avprobe.exe' and all the folder
            content located from '/win64/usr/bin' to where 'youtube-dll.exe' is.
            Because this is python you can find the .exe file in the script folder
            where your python is located 
        """
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
            'outtmpl': 'export/%(title)s.%(ext)s',
            'nocheckcertificate': 'True',
            'noplaylist': 'True'
        }
        # Define our youtube_dl variable
        self.ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

        # Define variables to store our content to work with
        self.playlists = []
        self.songs = []
        self.loop = asyncio.get_event_loop()
        self.download = download

        # If there is no export folder, create one
        if self.download:
            if not os.path.exists('export'):
                oldmask = os.umask(000)
                os.makedirs('export', 0o777)
                os.umask(oldmask)

        # If there is no log folder, create one
        if not os.path.exists('log'):
            oldmask = os.umask(000)
            os.makedirs('log', 0o777)
            os.umask(oldmask)

        # Create logging for the application. This way I can track of what happens
        # When all of this code is executed. There is no information collected about
        # you or your system on my side of this software.

        # Create logger for our application
        # Check our OPT settings in order to determine out debug log level
        if ytdl_format_options["verbose"] == 'True':
            logging.basicConfig(level=logging.DEBUG)
            self.debug = True
        else:
            logging.basicConfig(level=logging.INFO)
            self.debug = False
        self.logger = logging.getLogger('YoutubeSoundTool')

        # Create file handler which logs debug messages
        file_handler = logging.FileHandler('log/DEBUG.log')
        file_handler.setLevel(logging.DEBUG)
        # Create console handler with a higher Log Level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        # Add handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _download(self):
        '''download urls from the url list'''
        for youtube_item in self.songs:
            data = self.ytdl.extract_info(youtube_item, download=True)
            self.logger.debug(data)

        # Clean up workspace
        if os.path.isdir('False'):
            shutil.rmtree('False')

    def _playlist_check(self):
        '''determine if url is a playlist'''
        url_number = 0

        for url in self.urls:
            if re.search(r'(https?://)?(www.)??youtube(.*?)/(watch)(.*?)', url):
                # regex magic to find any youtube playlist in the search
                if re.search(r'(https?://)?(www.)?youtube(.com)/[\w\d_\-?=&/]+',
                             url) and 'index' in url.lower() or 'list' in url.lower():
                    self.logger.info(f'playlist detected: {url}')
                    self.playlists.append(url)
                else:
                    # Song found.
                    self.logger.info(f'url detected: {url}')
                    self.songs.append(url)
            else:
                # If the url not starts with youtube, do nothing
                pass

            # hold track of the numbers of urls in the list
            url_number += 1

        # I could just add this where the playlist check itself it
        # But since its a function meant to check the complete list I leave it be
        # Which is a smart choice i believe
        self.loop.run_until_complete(self._strip_playlist())
        if self.download:
            self._download()

    async def _strip_playlist(self):
        """
        Flatten out youtube playlist. and append song urls to the song list
        """
        for url in self.playlists:
            # Make a list of all youtube links in the playlist
            final_urls = []  # results
            # Gather info about the search
            info = self.ytdl.extract_info(url, download=False, process=False)
            async with aiohttp.ClientSession() as session:
                async with session.get(url=info["webpage_url"]) as request:
                    webpage = await request.read()

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

            self.playlists.remove(url)

        # Debug stuff
        self.logger.debug('SONGS')
        self.logger.info(f'{len(self.songs)} songs found')
        self.logger.debug(self.songs)
        self.logger.debug('PLAYLISTS:')
        self.logger.debug(self.playlists)
        self.logger.debug('Expected a empty playlist')
        self.logger.debug('ENDED _strip_playlist\n' + str('='*25)+ '\n\n')

if __name__ == '__main__':
    youtube_tool = YTDTool(['YOUTUBE URL HERE', 'YOU ALSO CAN USE YOUTUBE PLAYLIST INSTEAD', 'MAYBE YET ANOTHER YOUTUBE VIDEO'], download=True)
    youtube_tool._playlist_check()
