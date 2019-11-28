#
# This is a picoweb example showing a centralized web page route
#
import picoweb

from ota_update.main.ota_updater import OTAUpdater

import time
import network




def index(req, resp):
    # You can construct an HTTP response completely yourself, having
    # a full control of headers sent...
    yield from resp.awrite("HTTP/1.0 200 OK\r\n")
    yield from resp.awrite("Content-Type: text/html\r\n")
    yield from resp.awrite("\r\n")
    yield from resp.awrite("<h2>Pyboard running Picoweb</h2>")
    yield from resp.awrite("<ul style=""list-style-type:circle;"">")
    yield from resp.awrite("<li>Check for updates<a href='CheckForUpdate'>Check</a>.</li>")
    yield from resp.awrite("<li>source file of main.py <a href='file'>source</a>.</li>")
    yield from resp.awrite("</ul>")
 

@app.route
def CheckForUpdates(req, resp):
    o = OTAUpdater()
    o.download_and_install_update_if_available('wifi-ssid', 'wifi-password')
    yield from app.sendfile(resp, 'static/Example.html')

@app.route
def source(req, resp):
    yield from app.sendfile(resp, 'main/main.py')

#### Parsing function

def GetIP() :
    connections = [("PS_House","pennington2017"),("ZORAN","zoransoft"), ("ZORAN_EXT","zoransoft")]
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    for connection in connections:
        sta_if.connect(connection[0], connection[1])
        start = time.ticks_ms()
        while sta_if.isconnected() == False:
            if(time.ticks_diff(time.ticks_ms(),start)) >5000:
                break
        if( sta_if.isconnected() ):
            print("connected to {} and listening on ip address {} ".format(connection[0], sta_if.ifconfig()[0]))
            break
        else:
            print("unable to connect to {}".format(connection[0]))
    if(not sta_if.isconnected()):
        print("unable to connect to wifi")
    return sta_if.ifconfig()[0]

ROUTES = [
    # You can specify exact URI string matches...
]

import ulogging as logging
logging.basicConfig(level=logging.INFO)


app = picoweb.WebApp(__name__, ROUTES)

"""
async def my_dns_server(args):
    while True:
       pass # code

def runService():
    import uasyncio as asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(my_dns_server(123))
"""

#runService()

# debug values:
# -1 disable all logging
# 0 (False) normal logging: requests and errors
# 1 (True) debug logging
# 2 extra debug logging
app.run(debug=1, host=GetIP(), port=80)

