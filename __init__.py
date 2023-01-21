import display, wifi, urequests, time, buttons, nvs, neopixel, machine, mch22

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

def btn_up(pressed):
  while buttons.value(buttons.BTN_UP):
    scroll_supplier(-1)

def btn_down(pressed):
  while buttons.value(buttons.BTN_DOWN):
    scroll_supplier(+1)

def btn_left(pressed):
  while buttons.value(buttons.BTN_LEFT):
    scroll_hour(-1)

def btn_right(pressed):
  while buttons.value(buttons.BTN_RIGHT):
    scroll_hour(+1)

def btn_press(pressed):
  global selected_hour, cheapest_hour
  if pressed:
    selected_hour = cheapest_hour
    draw()

def scroll_hour(n):
  global selected_hour, num_hours
  selected_hour = (selected_hour+n) % num_hours
  draw()
  time.sleep_ms(100)


def scroll_supplier(n):
  global supplier, SUPPLIERS
  supplier = sorted(SUPPLIERS)[(sorted(SUPPLIERS).index(supplier)+n) % len(SUPPLIERS)]
  print(supplier, SUPPLIERS[supplier])
  draw()
  nvs.nvs_setstr("energy_prices", "supplier", supplier)
  time.sleep_ms(100)


def btn_home(pressed):
  if pressed:
    background()
    display.drawText(28, 108, "Exiting", 0xffff00, "press_start_2p22")
    display.flush()
    mch22.exit_python()

def main():
  global supplier, data, current_hour, selected_hour, cheapest_hour, np, num_hours

  print("Starting")

  buttons.attach(buttons.BTN_HOME, btn_home)
  buttons.attach(buttons.BTN_UP, btn_up)
  buttons.attach(buttons.BTN_DOWN, btn_down)
  buttons.attach(buttons.BTN_LEFT, btn_left)
  buttons.attach(buttons.BTN_RIGHT, btn_right)
  buttons.attach(buttons.BTN_PRESS, btn_press)

  supplier = nvs.nvs_getstr("energy_prices", "supplier") or ""
  np = neopixel.NeoPixel(machine.Pin(5, machine.Pin.OUT), 5)

  background()
  display.drawText(28, 108, "Connecting", 0xffff00, "press_start_2p22")
  display.flush()

  wifi.connect()
  wifi.wait()

  background()
  display.drawText(28, 108, "Loading.", 0xffff00, "press_start_2p22")
  display.flush()

  print("Getting and setting the RTC to local time (Europe/Amsterdam)")

  t = urequests.get("http://worldtimeapi.org/api/timezone/Europe/Amsterdam").json()
  t = time.gmtime(t['unixtime'] + t['raw_offset'] - 946684800)
  machine.RTC().init( t[0:3] + (0,) + t[3:6] + (0,) )
  # ~ machine.RTC().init((2023, 1, 20, 0, 19, 59, 30, 0))

  while True:
    t = time.gmtime()
    current_hour = t[3]
    print(f"Loading at {t}")

    selected_hour = None
    data = [None, None]

    background()
    display.drawText(28, 108, "Loading..", 0xffff00, "press_start_2p22")
    display.flush()

    data[0] = urequests.get("https://enever.nl/feed/stroomprijs_vandaag.php").json()
    display.drawText(28, 108, "Loading...", 0xffff00, "press_start_2p22")
    display.flush()

    data[1] = urequests.get("https://enever.nl/feed/stroomprijs_morgen.php").json()
    display.drawText(28, 108, "Loading....", 0xffff00, "press_start_2p22")
    display.flush()

    num_hours = sum([len(data[i]['data']) for i in range(2)])

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
    display.drawRect(20, i*40 -24, 2*24*6 + 2, 40, False, 0x808080)

  # cents labels
  for i in range(6):
    display.drawText(0, 212-(i*40), f"{i*10:2}", 0xffffff)

  # hour labels
  for i in range(9):
    display.drawText(18 + i*36, 225, str(i*6 % 24), 0xffffff)

  # supplier
  display.drawText(24, 0, SUPPLIERS[supplier], 0xffff00)

def draw():
  global data, np, current_hour, cheapest_hour, selected_hour
  background()

  cheapest_hour = current_hour

  for dagnr, dag in enumerate(data):
    for hour, price in enumerate(dag['data']):
      hour += dagnr*24
      p = float(price[f'prijs{supplier}'])
      c = int(float(price['prijs'])*1000)
      if dagnr == 0 and hour == current_hour:
        # yellow
        for i in range(5):
          np[i] = ((c >> 5), 7 - (c >> 5), 0)
        c = 0xffff00
      else:
        c = (c << 16) + (0xff-c << 8)

      if hour > current_hour:
        if price['prijs'] < data[int(cheapest_hour/24)]['data'][cheapest_hour%24]['prijs']:
          cheapest_hour = hour

      display.drawRect(22 + hour*6, 216 - p*400, 5, p*400, True, c)

  if selected_hour is None:
    selected_hour = cheapest_hour

  p = float(data[int(selected_hour/24)]['data'][selected_hour%24][f'prijs{supplier}'])
  display.drawRect(22 + selected_hour*6, 216 - p*400, 5, p*400, True, 0xffff00)

  c = int(float(data[int(selected_hour/24)]['data'][selected_hour%24][f'prijs'])*1000)
  np[4] = ((c >> 5), 7 - (c >> 5), 0)

  display.drawLine(24 +  current_hour*6, 217, 24 +  current_hour*6, 225, 0xffff00)
  display.drawLine(24 + selected_hour*6, 217, 24 + selected_hour*6, 225, 0xffff00)
  display.drawLine(24 +  current_hour*6, 221, 24 + selected_hour*6, 221, 0xffff00)

  delay_hours = (selected_hour - current_hour)
  if delay_hours > 0:
    delay_hours = f"+{delay_hours}"
  x = 304 - display.getTextWidth(str(delay_hours), "press_start_2p22")
  display.drawText(x, 28, str(delay_hours), 0xffff00, "press_start_2p22")

  np.write()
  display.flush()

if not __name__ == "energy_prices":
 main()
