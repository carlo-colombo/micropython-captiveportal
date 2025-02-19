"""
Minimal captive portal, using uasyncio v3 (MicroPython 1.13+) with a fallback for earlier versions of uasyncio/MicroPython.

* License: MIT
* Repository: https://github.com/metachris/micropython-captiveportal
* Author: Chris Hager <chris@linuxuser.at> / https://twitter.com/metachris

Built upon:
- https://github.com/p-doyle/Micropython-DNSServer-Captive-Portal

References:
- http://docs.micropython.org/en/latest/library/uasyncio.html
- https://github.com/peterhinch/micropython-async/blob/master/v3/README.md
- https://github.com/peterhinch/micropython-async/blob/master/v3/docs/TUTORIAL.md
- https://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html#sec5
"""
import gc
import sys
import network
import socket
import uasyncio as asyncio

# Helper to detect uasyncio v3
IS_UASYNCIO_V3 = hasattr(asyncio, "__version__") and asyncio.__version__ >= (3,)


# Access point settings
SERVER_IP = '10.0.0.1'
SERVER_SUBNET = '255.255.255.0'


def wifi_start_access_point(essid):
    """ setup the access point """
    wifi = network.WLAN(network.AP_IF)
    wifi.active(True)
    wifi.ifconfig((SERVER_IP, SERVER_SUBNET, SERVER_IP, SERVER_IP))
    wifi.config(essid=essid, authmode=network.AUTH_OPEN)
    print('Network config:', wifi.ifconfig())


def _handle_exception(loop, context):
    """ uasyncio v3 only: global exception handler """
    print('Global exception handler')
    sys.print_exception(context["exception"])
    sys.exit()


class DNSQuery:
    def __init__(self, data):
        self.data = data
        self.domain = ''
        tipo = (data[2] >> 3) & 15  # Opcode bits
        if tipo == 0:  # Standard query
            ini = 12
            lon = data[ini]
            while lon != 0:
                self.domain += data[ini + 1:ini + lon + 1].decode('utf-8') + '.'
                ini += lon + 1
                lon = data[ini]
        # print("DNSQuery domain:" + self.domain)

    def response(self, ip):
        if self.domain:
            packet = self.data[:2] + b'\x81\x80'
            packet += self.data[4:6] + self.data[4:6] + b'\x00\x00\x00\x00'  # Questions and Answers Counts
            packet += self.data[12:]  # Original Domain Name Question
            packet += b'\xC0\x0C'  # Pointer to domain name
            packet += b'\x00\x01\x00\x01\x00\x00\x00\x3C\x00\x04'  # Response type, ttl and resource data length -> 4 bytes
            packet += bytes(map(int, ip.split('.')))  # 4bytes of IP
        # print(packet)
        return packet
    
 
from microdot import Microdot, send_file, redirect

app = Microdot()

@app.route("/generate_204")
async def index(request):
    return redirect("/")

@app.post("/save")
async def save(req):
    with open('wifi-creds.txt', 'w+') as creds:
        creds.write(req.form.get('ssid')+'\n')
        creds.write(req.form.get('password'))
    return redirect("/?credentials-stored")

@app.route('/static/<path:path>')
async def static(request, path):
    print(path)
    if '..' in path:
        # directory traversal is not allowed
        return 'Not found', 404
    return send_file('static/' + path)

@app.route('/api/networks')
async def list_networks(req):
    return [{'name': w[0]} for w in networks]

@app.route('/')
async def index(request):
    return send_file('index.html')

async def start_server():
    return await app.start_server(debug=True, port=80)

class MyApp:
    async def start(self, essid='captive portal ssid'):
        # Get the event loop
        loop = asyncio.get_event_loop()

        # Add global exception handler
        loop.set_exception_handler(_handle_exception)
        
        global networks
        wifi = network.WLAN(network.STA_IF)
        wifi.active(True)
        networks = wifi.scan()
        networks.sort(key=lambda w: -w[3])
        for net in networks:
            print(net)

        # Start the wifi AP
        wifi_start_access_point(essid)

        # Create the server and add task to event loop
        # server = asyncio.start_server(self.handle_http_connection, "0.0.0.0", 80)
        loop.create_task(start_server())

        # Start the DNS server task
        loop.create_task(self.run_dns_server())

        # Start looping forever
        print('Looping forever...')
        loop.run_forever()

    async def run_dns_server(self):
        """ function to handle incoming dns requests """
        udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udps.setblocking(False)
        udps.bind(('0.0.0.0', 53))

        while True:
            try:
                # gc.collect()
                yield asyncio.core._io_queue.queue_read(udps)
                data, addr = udps.recvfrom(4096)
                # print("Incoming DNS request...")

                DNS = DNSQuery(data)
                udps.sendto(DNS.response(SERVER_IP), addr)

                # print("Replying: {:s} -> {:s}".format(DNS.domain, SERVER_IP))

            except Exception as e:
                print("DNS server error:", e)
                await asyncio.sleep_ms(3000)

        udps.close()
