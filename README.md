# Minimal MicroPython Captive Portal served by Microdot

This code is tested on ESP32. It creates a wifi access point, and once connected to it a captive portal is opened (served from `index.html`).

* Works with uasyncio v3 (MicroPython 1.13+)
* Code: [captive.py](https://github.com/metachris/micropython-captiveportal/blob/master/captive.py)
* endpoint (`POST /save`) to store credentials in `wifi-creds.txt`
* support for serving static resources from `static`
* includes [MVP.css](https://andybrewer.github.io/mvp/) for no effort good looking portals. 


## Install

```shell
mpremote mip install github:miguelgrinberg/microdot/src/microdot/microdot.py
mpremote mip install github:carlo-colombo/micropython-captiveportal/captive.py
```

## Usage

### Copy `index.html` and optional additional files

```shell
mpremote cp index.html :
mpremote cp mvp.css :static/mvp.css
```

### Example: open the captive portal to set wifi username and password on the device. When credentials are present just connect to the Access Point.

```python
import captive
import uasyncio as asyncio

def do_connect(ssid, password):
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

# Entry point.
try:
    with open('wifi-creds.txt') as creds:
        print('creds found')

        ssid = creds.readline().strip()
        password = creds.readline().strip()
        
        do_connect(ssid, password)
        
        # execute your code after connecting
        main()

except OSError:
    try:
        myapp = captive.MyApp()
        asyncio.run(myapp.start(essid='captive test wifi'))

    except KeyboardInterrupt:
        print('Bye')

    finally:
        asyncio.new_event_loop()  # Clear retained stat
```


---

Notes

* License: MIT
* Repository: https://github.com/carlo-colombo/micropython-captiveportal

Built upon

- https://github.com/metachris/micropython-captiveportal
- https://github.com/p-doyle/Micropython-DNSServer-Captive-Portal

References

- https://docs.micropython.org/en/v1.14/library/uasyncio.html
- https://github.com/peterhinch/micropython-async/blob/master/v3/README.md
- https://github.com/peterhinch/micropython-async/blob/master/v3/docs/TUTORIAL.md
- https://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html#sec5
