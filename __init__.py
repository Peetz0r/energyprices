import system, display, wifi, urequests, time, buttons, nvs, neopixel, machine

SUPPLIERS = {
  "": "entso-e",
  "AIP": "All In Power",
  "EE": "EasyEnergy",
  "EZ": "Energy Zero",
  "FR": "Frank Energie",
  "GSL": "Groenestroom Lokaal",
  "MDE": "Mijndomein Energie",
  "NE": "NextEnergy",
  "TI": "Tibber",
  "VON": "Vrij op Naam",
  "ZG": "ZonderGas",
  "ZP": "Zonneplan",
}

supplier = None
data = None
np = None

def btn_up(pressed):
  if pressed:
    scroll(-1)

def btn_down(pressed):
  if pressed:
    scroll(+1)

def scroll(n):
  global supplier, SUPPLIERS
  supplier = sorted(SUPPLIERS)[(sorted(SUPPLIERS).index(supplier)+n) % len(SUPPLIERS)]
  print(supplier, SUPPLIERS[supplier])
  draw()
  nvs.nvs_setstr("energy_prices", "supplier", supplier)

def btn_home(pressed):
  if pressed:
    display.drawText(28, 112, "Exiting", 0xffff00, "press_start_2p22")
    display.flush()
    system.home("foo")

def main():
  global supplier, data, current_hour, np

  print("Starting")

  buttons.attach(buttons.BTN_HOME, btn_home)
  buttons.attach(buttons.BTN_UP, btn_up)
  buttons.attach(buttons.BTN_DOWN, btn_down)

  supplier = nvs.nvs_getstr("energy_prices", "supplier") or ""

  np = neopixel.NeoPixel(machine.Pin(5, machine.Pin.OUT), 5)

  background()
  display.drawText(28, 112, "Connecting", 0xffff00, "press_start_2p22")
  display.flush()

  wifi.connect()
  wifi.wait()

  background()
  display.drawText(28, 112, "Loading", 0xffff00, "press_start_2p22")
  display.flush()

  print("Getting and setting the RTC to local time (Europe/Amsterdam)")

  t = urequests.get("http://worldtimeapi.org/api/timezone/Europe/Amsterdam").json()
  t = time.gmtime(t['unixtime'] + t['raw_offset'] - 946684800)
  machine.RTC().init( t[0:3] + (0,) + t[3:6] + (0,) )

  while True:
    t = time.gmtime()
    current_hour = t[3]

    print(f"Loading at {t}")

    data = [urequests.get(f"https://enever.nl/feed/stroomprijs_{dag}.php").json() for dag in ["vandaag", "morgen"]]
    draw()

    t = time.gmtime()
    # t[4] is minutes, t[5] is seconds, plus 5 second margin
    sleeping = (59-t[4])*60 + 59-t[5] + 5
    print(f"Sleeping for {int(sleeping / 60)}:{sleeping % 60:02} (mm:ss) starting at {t}")
    time.sleep(sleeping)



def background():
  display.clearMatrix()
  display.drawFill(0x000000)

  # grid
  for i in range(6):
    display.drawRect(20, i*40 -20, 2*24*6 + 2, 40, False, 0x808080)

  # cents labels
  for i in range(6):
    display.drawText(0, 212-(i*40), f"{i*10:2}", 0xffffff)

  # hour labels
  for i in range(9):
    display.drawText(18 + i*36, 224, str(i*6 % 24), 0xffffff)

  # supplier
  display.drawText(24, 4, SUPPLIERS[supplier], 0xffff00)

def draw():
  global data, current_hour, np
  background()
  for dagnr, dag in enumerate(data):
    for hour, price in enumerate(dag['data']):
      p = float(price[f'prijs{supplier}'])
      c = int(float(price['prijs'])*1000)
      if dagnr == 0 and current_hour == hour:
        # yellow
        c = 0xffff00
        for i in range(5):
          np[i] = ((c >> 6), 4 - (c >> 6), 0)
      else:
        c = (c << 16) + (0xff-c << 8)

      display.drawRect(22 + dagnr*144 + hour*6, 220 - p*400, 5, p*400, True, c)
  np.write()
  display.flush()

if not __name__ == "energy_prices":
 main()