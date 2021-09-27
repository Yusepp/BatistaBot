# BatistaBot
BatistaBot an alternative to Groovy and Rythm music based bots.
BatistaBot's deployment is done using free heroku server so you can use it 24/7. Feel free to ask me any questions about it!
Google's Firebase Firestore is used for saving data but you can really save it in a SQL.

![Barista Bot](https://i.gyazo.com/2d7a6637310d0e7ce9611b009d1cc4b0.png)

## Features
* Play songs and queue them!
* Stop/Pause/Resume current song!
* Skip current song!
* Check queue status!
* Remove song from the queue!
* Register/Login Online user!
* Save current queue as playlist for your user!
* Load/Delete a saved Playlist!
* Check all your saved playlists!


## Commands List
* `-h -help`: show all commands info.
* `-p <song's name or youtube url>`: play desired song.
* `-stop`: stop current queue.
* `-pause`: pause current song.
* `-resume`: resume paused song.
* `-q -queue`: display queue status.
* `-s -skip`: skip current song.
* `-rm -remove <index queue>`: remove song from the queue by position.
* `-register <username>`: create a new user.
* `-login <username>`: login user for online playlists services.
* `-save <playlistname> (requires login)`: save queue as playlist.
* `-load <playlistname> (requires login)`: load online playlist to your queue.
* `-delete <playlistname> (requires login)`: delete online playlist.
* `-mylists (requires login)`: check all your playlists.
* `-mylists <playlistname> (requires login)`: check songs from the chosen playlists.
* `-dc -disconnect`: disconnect bot from voice channel.


# Misc.
This is my first time creating a discord bot, I started this project due to Groovy and Rythm shutdowns. At first I was trying to keep it as simple as possible and use it for my friends' server but people just asked me to add more features that those bots lacked (e.g. save queue to online playlist). Feel free to use my bot as template, free open source code rules!
