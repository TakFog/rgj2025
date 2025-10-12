import os
import time

import vlc

class VideoPlayer:
    def __init__(self):
        self.loop = False
        self.instance = vlc.Instance('--fullscreen')
        self.player = self.instance.media_player_new()
        # event_manager = self.player.event_manager()
        # event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end)

    def play(self, path: str, loop: bool = False):
        print("Playing " + path)
        self.loop = loop
        player = self.player
        media = self.instance.media_new(os.path.abspath(path))
        player.set_media(media)
        player.set_fullscreen(True)
        player.play()

    # def _on_end(self, event):
    #     if self.loop:
    #         self.player.stop()
    #         self.player.play()

    def stop(self) -> bool:
        if not self.player.is_playing():
            return False
        self.player.stop()
        return True


if __name__ == "__main__":
    video_player = VideoPlayer()
    video_player.play(r"C:\Users\valen\PycharmProjects\rgj2025\video\matrix.mp4")
    time.sleep(30)
    video_player.play(r"C:\Users\valen\PycharmProjects\rgj2025\video\attacco.mp4")
    time.sleep(5)
    video_player.stop()

