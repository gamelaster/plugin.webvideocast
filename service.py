import json
import os
from threading import Thread
import time
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import requests
import xbmcvfs
from wwc_receiver import WwcReceiver

addon = xbmcaddon.Addon()
monitor = xbmc.Monitor()
dialog = xbmcgui.Dialog()

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')

def get_current_volume():
    request = json.dumps({
        "jsonrpc": "2.0",
        "method": "Application.GetProperties",
        "params": {
            "properties": ["volume"]
        },
        "id": 1
    })

    response = xbmc.executeJSONRPC(request)
    response_data = json.loads(response)

    return response_data['result']['volume']

def set_volume_with_slider(desired_volume):    
    # Show the volume slider by using xbmc.executebuiltin
    xbmc.executebuiltin(f'SetVolume({desired_volume}, true)')

# Useful!! https://forum.kodi.tv/showthread.php?tid=348739

class WwcPlayer(xbmc.Player):
    def __init__(self):
        super().__init__()
        self.seek_position = 0
        xbmc.log("-gu Custom player initialized", level=xbmc.LOGDEBUG)

    def onAVStarted(self):
        receiver.media_info.duration = int(self.getTotalTime()*1000)
        receiver.media_info.audio_tracks = self.getAvailableAudioStreams()
        #xbmc.log(f"[WWC] audio streams: " +str(), level=xbmc.LOGDEBUG)
        xbmc.log(f"[WWC] duration: {receiver.media_info.duration}", level=xbmc.LOGDEBUG)
        receiver.event_state_changed('loaded')
        if self.seek_position != 0:
            self.seekTime(self.seek_position)
            self.seek_position = 0
        else:
            receiver.event_state_changed('playing')
    
    def onPlayBackPaused(self):
        receiver.event_state_changed('paused')
        xbmc.log("-gu Playback is paused", level=xbmc.LOGDEBUG)

    def onPlayBackResumed(self):
        receiver.event_state_changed('playing')
        xbmc.log("-gu Playback has resumed", level=xbmc.LOGDEBUG)

    def onPlayBackStopped(self):
        xbmc.log("-gu Playback has stopped", level=xbmc.LOGDEBUG)

    def onPlayBackEnded(self):
        xbmc.log("-gu Playback has ended", level=xbmc.LOGDEBUG)

    def onPlayBackSeek(self, time, seekOffset):
        xbmc.log(f"-gu Playback seeked to {time}ms with offset {seekOffset}ms", level=xbmc.LOGDEBUG)
        receiver.event_state_changed('playing')

    def onPlayBackSeekChapter(self, chapter):
        xbmc.log(f"-gu Playback seeked to chapter {chapter}", level=xbmc.LOGDEBUG)

    def onPlayBackError(self):
        xbmc.log("-gu Error occurred during playback", level=xbmc.LOGDEBUG)

    # TODO: Playback has stopped is called when fail to load

class KodiWwcReceiver(WwcReceiver):
    def on_finish(self):
        pass

    def on_error(self, message, more_info):
        dialog.notification('Web Video Caster Receiver', message, xbmcgui.NOTIFICATION_ERROR)

    def on_info(self, message):
        dialog.notification('Web Video Caster Receiver', message, xbmcgui.NOTIFICATION_INFO)
        

    def platform_play_video(self, url, position, headers):
        player.seek_position = int(position) / 1000
        url_full = url
        if headers != None and len(headers) > 0:
            url_full = url_full + '|' + urllib.parse.urlencode(headers)

        xbmc.log("[WWC] urlfull: " + url_full, level=xbmc.LOGDEBUG)
        player.play(url_full)

    def platform_video_get_position(self):
        if player.isPlaying():
            tt = int(round(player.getTime()*1000))
            xbmc.log(f"[WWC] time: {tt}", level=xbmc.LOGDEBUG)
            return tt
        return 0
    
    def platform_state_change(self, state):
        if state == 'pause' or state == 'resume':
            player.pause()
        elif state == 'stop':
            player.stop()

    def platform_set_position(self, position):
        player.seekTime(float(position / 1000))

    def platform_set_subtitles(self, url):
        if url == None:
            player.showSubtitles(False)
            return
        temp_dir = xbmcvfs.translatePath('special://temp/')
        file_name = os.path.basename(url)
        temp_file_path = xbmcvfs.translatePath(temp_dir + file_name)

        try:
            resp = requests.get(url)
        except:
            # TODO: Logging
            return

        temp_file = xbmcvfs.File(temp_file_path, 'w')
        temp_file.write(resp.content)
        temp_file.close()
        player.setSubtitles(temp_file_path)
        player.showSubtitles(True)
        
    def platform_get_volume(self):
        return float(get_current_volume()) / 100.0    

    def platform_set_volume(self, volume):
        set_volume_with_slider(float(volume) * 100.0)

    def platform_debug_print(self, message):
        xbmc.log("[WWC] " + str(message), level=xbmc.LOGDEBUG)

    def platform_set_audio_track(self, audio_track_index):
        player.setAudioStream(audio_track_index)

exit = False

def receiver_thread_func():
    global receiver
    global exit
    while not exit:
        if receiver != None:
            receiver.tick()
        else:
            time.sleep(1)

receiver: WwcReceiver = None
player = WwcPlayer()

receiver_thread = Thread(target = receiver_thread_func)
# receiver_thread.start()

while not monitor.abortRequested():
    # ugly but... doing IPC in Kodi is painful
    connect_ip = xbmcgui.Window(10000).getProperty('wwc_connect_ip')
    if connect_ip != "":
        receiver = KodiWwcReceiver(f"http://{connect_ip}/")
        xbmcgui.Window(10000).setProperty('wwc_connect_ip', '')
        receiver_thread.start()

    if monitor.waitForAbort(1):
        break

exit = True
receiver_thread.join()