# YoutubeSoundTool
Download 320bit mp3s from youtube urls

Simple, no video, just audio.
You can enter any youtube link. There is just one condition.

"The youtube link needs to contain the keyword 'watch' "

This is a simplistic version / idea that is growing its roots in to the ground aka **POC**.
Open up "run.py" and scroll down until you see somthing like this:

    if __name__ == '__main__':
        youtube_tool = YTDTool(['YOUTUBE URL HERE', 'YOU ALSO CAN USE YOUTUBE PLAYLIST INSTEAD', 'MAYBE YET ANOTHER YOUTUBE VIDEO'], download=True)
        youtube_tool._playlist_check()

Edit the second line and add your youtube links like so:

    if __name__ == '__main__':
        youtube_tool = YTDTool(['youtube_link', 'youtube_link', 'youtube_link'], download=True)
        youtube_tool._playlist_check()

I dont know what you download. So i cant be responsible for that. Keep in mind that downloading music illegal can have consequences. Once again I am not responsible for the data that you download with this software.

After you added your links you are good to go. Make sure you have all the packages installed with: 
    
    python -m pip install -r requirements.txt
    
You can start the program by running

    python run.py
    
Works for **python 3.6>=**   