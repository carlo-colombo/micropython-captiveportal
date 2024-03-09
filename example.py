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
        
        main()

except OSError:
    try:
        myapp = captive.MyApp()
        asyncio.run(myapp.start(essid='captive test wifi'))

    except KeyboardInterrupt:
        print('Bye')

    finally:
        asyncio.new_event_loop()  # Clear retained stat