# WyspaGier.pl minigolf private server
### Because the game is too fun to be lost to time.

This is a reimplementation of the server for the Multiplayer Minigolf game from website wyspagier.pl. The original server got shut down after Adobe Flash got removed from major browsers. This server allows connecting using the original .swf file you can get from archive.org.

## Starting the server
- `git clone https://github.com/malik1004x/wyspagolf_reborn.git`
- `cd wyspagolf_reborn`
- `pip install -r requirements.txt`
- `python3 main.py`

## Connecting to the server
- Get the SWF from a [WyspaGier snapshot](https://web.archive.org/web/20081106171829mp_/http://pgierki.wyspagier.pl/minigolf/swf/dfjkl23493fjklece39e39c.swf) on archive.org.
- Download [Ruffle](https://ruffle.rs) for your operating system. Flash Projector is more difficult to set up and doesn't provide any real advantage.
- Open Ruffle. Select the downloaded SWF in the "File or URL" field, then open " parameters".
- Add two file parameters: `surl` - your server's IP, and `sport` - your server's port number.
- Click Start and enjoy.
