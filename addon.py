import xbmc
import xbmcgui
import xbmcaddon
import requests

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')

from utils import codeToIps

dialog = xbmcgui.Dialog()

code = dialog.input('Web Video Caster - Enter code from your app')
# dialog.notification('Web Video Caster Receiver', result, xbmcgui.NOTIFICATION_INFO)

ips = codeToIps(code.lower())

for ip in ips:
    try:
        requests.get(f"http://{ip}/web-receiver/discover.gif")
        dialog.notification('Web Video Caster Receiver', f"Connecting to {ip}...", xbmcgui.NOTIFICATION_INFO)
        xbmcgui.Window(10000).setProperty('wwc_connect_ip', ip)
        break
    except:
        pass

