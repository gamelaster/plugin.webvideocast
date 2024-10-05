import time
import requests

class MediaInfo:
    def __init__(self) -> None:
        self.url = None
        self.mime_type = None
        self.type = None
        self.width = None
        self.height = None
        self.duration = None
        self.audio_tracks = None
        self.cur_audio_track = 0

class WwcReceiver:
    def __init__(self, serverUrl: str):
        self.device_id = 'm1thlfmfsgyrcs1wav5yzrvg0vnwl'
        self.media_info: MediaInfo = None
        self.recv_info = {
            "deviceId": self.device_id,
            "label": "Kodi",
            "icon": "https://gami.ee/files/kodi.png"
        }
        self.headers = {
            'Client-Id': self.device_id,
            'Cookie': 'deviceId=' + self.device_id,
        }

        self.server_url = serverUrl
        self.state = 'initialize'
    
    def tick(self):
        if self.state == 'initialize':
            for n in range(5):
                try:
                    self.request_connection()
                    self.state = 'connecting'
                    break
                except Exception as e:
                    if n == 4:
                        self.on_error("Failed to connect to the device", e)
                        self.on_finish()
                        self.state = 'idle'
        elif self.state == 'connecting' or self.state == 'poll':
            self.do_long_poll()

    def request_connection(self):
        data = {
            "media": None,
            "receiver": self.recv_info
        }
        r = requests.post(self.server_url + 'web-receiver-io/request-connection', json=data, headers=self.headers, timeout=2)
        if r.status_code != 200:
            raise Exception(f"Invalid status_code received for request_connection: {r.status_code}")

    def do_long_poll(self):
        data = {
            "media": None,
            "receiver": self.recv_info
        }
        r = requests.post(self.server_url + 'web-receiver-io/longPoll', json=data, headers=self.headers, timeout=None)
        ret = ""
        if r.status_code == 200:
            ret = r.json()
        self.platform_debug_print("Long poll, code {}, return: {}".format(r.status_code, ret))
        if r.status_code != 200:
            self.platform_sleep(1)

        if r.status_code == 200:
            if self.state == 'connecting':
                self.state = 'poll'
                self.on_info("Successfully connected")
            func_name = "handle_" + self.__camel_to_snake(ret["cmd"])
            method = getattr(self, func_name, None)
            if method:
                method(ret)
            else:
                self.platform_debug_print(f"Method {func_name} not found")

    # Requests handlers

    def handle_get_media(self, data):
        audio_tracks = []
        if self.media_info and self.media_info.audio_tracks:
            for index in range(len(self.media_info.audio_tracks)):
                track_name = self.media_info.audio_tracks[index]
                audio_tracks.append({
                    "language": track_name,
                    "name": track_name,
                    "track": index,
                    "current": index == self.media_info.cur_audio_track
                })
        
        data = {
            "type": self.media_info.type if self.media_info else None,
            "url": self.__get_media(),
            "media": self.__get_media(),
            "mimeType": self.media_info.mime_type if self.media_info else None,
            "width": self.media_info.width if self.media_info else "0",
            "height": self.media_info.height if self.media_info else "0",
            "poster": None,
            "audioTracks": audio_tracks,
            "headers": None,
            "textTracks": [

            ]
        }
        res = self.__post('media', data)

    def handle_load_media(self, data):
        # send state cmd
        self.media_info = MediaInfo()
        self.media_info.url = data['url']
        self.media_info.mime_type = data['mimeType']
        self.media_info.type = data['media']
        self.media_info.width = 0
        self.media_info.height = 0

        self.platform_play_video(data['url'], data['position'], data.get('headers', {}))
        data = {
            "media": self.__get_media(),
            "state": "loading" # or loaded
        }
        self.__post('state', data)


    def handle_position_get(self, data):
        # send position
        data = {
            "media": self.__get_media(),
            "position": self.platform_video_get_position(),
            "duration": self.media_info.duration if self.media_info else None
        }
        self.platform_debug_print(data)
        self.__post('position', data)
        
    
    def handle_volume_get(self, data):
        data = {
            "media": self.__get_media(),
            "volume": self.platform_get_volume()
        }
        self.__post('volume', data)

    def handle_pause(self, data):
        self.platform_state_change('pause')
    
    def handle_play(self, data):
        self.platform_state_change('resume')

    def handle_stop(self, data):
        self.platform_state_change('stop')
        self.event_state_changed('idle')
        self.media_info = None

    def handle_position_set(self, data):
        self.event_state_changed('paused')
        self.platform_set_position(data['position'])

    def handle_subtitles_stop(self, data):
        self.platform_set_subtitles(None)

    def handle_subtitles_set(self, data):
        self.platform_debug_print(data)
        self.platform_set_subtitles(data['url'])

    def handle_volume_set(self, data):
        self.platform_set_volume(data['volume'])

    def handle_audio_track_set(self, data):
        audio_track = int(data['track'])
        self.media_info.cur_audio_track = audio_track
        self.platform_set_audio_track(audio_track)
        # We need to trigger this so it's updated in UI
        self.handle_get_media({})

    # Callbacks

    def on_finish(self):
        self.platform_debug_print("Receiver finished")

    def on_error(self, message, more_info):
        self.platform_debug_print(f"Error happened: {message}, {more_info}")

    def on_info(self, message):
        pass

    # Platform related

    def platform_sleep(self, duration):
        time.sleep(duration)

    def platform_debug_print(self, message):
        print(message)

    def platform_play_video(self, url, position, headers):
        print(f"Play {url} pos {position}, headers {headers}")

    def platform_video_get_position(self):
        return 0
    
    def platform_state_change(self, state):
        pass

    def platform_set_position(self, position):
        pass
    
    def platform_set_subtitles(self, url):
        pass

    def platform_get_volume(self):
        return 1

    def platform_set_volume(self, volume):
        pass

    def platform_set_audio_track(self, audio_track_index):
        pass

    # Platform call those

    def event_state_changed(self, state):
        data = {
            "media": self.__get_media(),
            "state": state
        }
        self.__post('state', data)


    # Utilities

    def __get_media(self):
        if self.media_info != None:
            return self.media_info.url
        return None

    def __post(self, cmd, data = None):
        r = requests.post(self.server_url + f"web-receiver-io/{cmd}", json=data, headers=self.headers)
        return r

    def __camel_to_snake(self, s):
        return ''.join(['_'+c.lower() if c.isupper() else c for c in s]).lstrip('_')