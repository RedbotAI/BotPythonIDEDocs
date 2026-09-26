from lv_gui import GUI
import lvgl as lv
import sys
_screen_state = sys.modules.setdefault("_botpython_display_state", {})

class Screen240:
    WIDTH = 240
    HEIGHT = 240
    ROWS = 9
    def __init__(self):
        self.pending = {}
        self.colors = _screen_state.setdefault('colors', {})
        # Reuse the firmware display/event loop across independently executed programs.
        active = lv.screen_active()
        if active is None:
            if 'gui' not in _screen_state:
                _screen_state['gui'] = GUI()
            active = lv.screen_active()
        if _screen_state.get('labels') is not None:
            self.panel = _screen_state['panel']
            self.labels = _screen_state['labels']
            self.panel.set_style_bg_color(lv.color_hex(0x000000), 0)
            self.panel.set_style_bg_opa(255, 0)
            self.fill()
            return
        previous = _screen_state.get('panel')
        if previous is not None:
            previous.delete()
        self.panel = lv.obj(active)
        _screen_state['panel'] = self.panel
        self.panel.set_pos(0, 0)
        self.panel.set_size(240, 240)
        self.panel.set_style_pad_all(0, 0)
        self.panel.set_style_border_width(0, 0)
        self.panel.set_style_radius(0, 0)
        self.panel.set_style_bg_color(lv.color_hex(0x000000), 0)
        self.panel.set_style_bg_opa(255, 0)
        self.panel.set_style_shadow_width(0, 0)
        self.panel.remove_flag(lv.obj.FLAG.SCROLLABLE)
        self.labels = []
        for index in range(self.ROWS):
            label = lv.label(self.panel)
            label.set_pos(8, 8 + index * 24)
            label.set_size(224, 24)
            label.set_long_mode(lv.label.LONG_MODE.DOTS)
            label.set_style_pad_all(0, 0)
            label.set_style_text_color(lv.color_hex(0xffffff), 0)
            self.colors[index + 1] = 0xffffff
            for font_name in ('font_montserrat_16', 'font_montserrat_14', 'font_unscii_8'):
                if hasattr(lv, font_name):
                    label.set_style_text_font(getattr(lv, font_name), 0)
                    break
            label.set_text('')
            self.labels.append(label)
        _screen_state['labels'] = self.labels
    def fill(self, type=0):
        for row in range(1, self.ROWS + 1):
            self.pending[row] = ('', 0xffffff)
    def draw_label(self, text, row=1, color=0xffffff, wrap=False):
        row = int(row)
        if not 1 <= row <= self.ROWS:
            raise ValueError('Screen row must be 1..9')
        value = 'NOT CONNECTED' if isinstance(text, float) and text != text else str(text)
        if value.endswith(': nan'):
            value = value[:-3] + 'NOT CONNECTED'
        self.pending[row] = (value.replace('\n', ' ')[:160], color)
    def update(self):
        for row, (value, color) in self.pending.items():
            label = self.labels[row - 1]
            # Setting an unchanged LVGL style still invalidates its display area.
            if self.colors.get(row) != color:
                label.set_style_text_color(lv.color_hex(color), 0)
                self.colors[row] = color
            if label.get_text() != value:
                label.set_text(value)
        self.pending.clear()
        lv.timer_handler()

sample_count = None

"""Optional external sensors for block programs. No hardware access on import."""
_bp_sensor_cache = globals().get('_bp_sensor_cache', {})

class BPSensor:
    def __init__(self, kind, pin=5):
        self.kind, self.pin = kind, pin
        self.device = None
        self.status = 'not_connected'
        self.last_error = ''
        self._sample = None

    def _connect(self):
        if self.device is not None:
            return True
        try:
            if self.kind == 'light':
                from bh1750 import BH1750
                self.device = BH1750()
            elif self.kind == 'co2':
                from co2_sensors_jw01 import CO2SensorJW01
                # Old firmware accepts auto_start=False; explicit polling is new.
                self.device = CO2SensorJW01()
            elif self.kind == 'dht':
                import dht
                from mpython import Pin
                self.device = dht.DHT11(Pin(getattr(Pin, 'P' + str(self.pin))))
            else:
                raise ValueError('Unknown sensor kind')
            return True
        except Exception as error:
            self.status = 'not_connected'
            self.last_error = str(error)
            return False

    def _read(self, method):
        if not self._connect():
            return float('nan')
        try:
            value = getattr(self.device, method)()
            if value is None or (self.kind in ('light', 'co2') and value < 0):
                raise OSError('No sensor data')
            if self.kind == 'co2' and hasattr(self.device, 'is_data_fresh'):
                if not self.device.is_data_fresh() or value == 0:
                    raise OSError('No fresh CO2 data')
            self.status = 'ready'
            self.last_error = ''
            return value
        except Exception as error:
            self.status = 'not_connected'
            self.last_error = str(error)
            return float('nan')

    def measure(self):
        self._sample = None
        if not self._connect():
            return False
        try:
            self.device.measure()
            self._sample = (self.device.temperature(), self.device.humidity())
            self.status = 'ready'
            self.last_error = ''
            return True
        except Exception as error:
            self.status = 'not_connected'
            self.last_error = str(error)
            return False

    def temperature(self):
        return self._sample[0] if self._sample is not None else float('nan')

    def humidity(self):
        return self._sample[1] if self._sample is not None else float('nan')

    def read(self):
        return self._read('read')

    def read_co2_ppm(self):
        return self._read('read_co2_ppm')

    def is_connected(self):
        return self.status == 'ready'

def bp_sensor(kind, pin=5):
    key = (kind, pin)
    if key not in _bp_sensor_cache:
        _bp_sensor_cache[key] = BPSensor(kind, pin)
    return _bp_sensor_cache[key]


bot_screen = Screen240()
sample_count = 0
while True:
  try:
    environment_co2 = bp_sensor('co2')
    bot_screen.draw_label(text='CO2 ppm: ' + str(environment_co2.read_co2_ppm()), row=2, color=0xffffff, wrap=False)
  except Exception as sensor_error:
    bot_screen.draw_label(text='Sensor ERROR', row=2, color=0xffffff, wrap=False)
  sample_count = sample_count + 1
  bot_screen.draw_label(text='Sample ' + str(sample_count), row=1, color=0xffffff, wrap=False)
  bot_screen.update()
  import time
  time.sleep(2)
