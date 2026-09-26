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

from mpython import MPythonPin, PinMode


bot_screen = Screen240()
from machine import Pin
pin2 = Pin(2, Pin.OUT)
while True:
  soil_1 = MPythonPin(0, PinMode.ANALOG)
  bot_screen.draw_label(text='Soil P0: ' + str(soil_1.read_analog()), row=8, color=0xffffff, wrap=False)
  bot_screen.update()
  import time
  time.sleep(2)
  pin2.value(1)
  import time
  time.sleep(1)
  pin2.value(0)
  import time
  time.sleep(1)
