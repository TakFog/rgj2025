import vlc
import time

# Percorso del video
video_path = r"/video/matrix_short.mp4"

player = vlc.MediaPlayer(video_path)
player.set_fullscreen(True)
player.play()

time.sleep(5)

player.stop()
#
# # Crea un'istanza VLC
# instance = vlc.Instance('--fullscreen')
# player = instance.media_player_new()
#
# # Carica il video
# media = instance.media_new(video_path)
# player.set_media(media)
#
# # Avvia il video
# player.play()
# time.sleep(1)  # tempo per avviare il player
#
# # Imposta fullscreen
# # player.set_fullscreen(True)
#
# # Imposta il loop
# event_manager = player.event_manager()
#
# def restart(event):
#     # Riavvia il video alla fine
#     player.stop()
#     player.play()
#     player.set_fullscreen(True)
#
# # Registra l'evento "EndReached" per riavviare il video
# event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, restart)

# # Mantieni il programma attivo
# while True:
#     time.sleep(1)
