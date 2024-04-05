import os
import time
import collections

from decimal import Decimal
from kivy.logger import Logger
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, ListProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App

from rotary_controller_python.dispatchers import SavingDispatcher

log = Logger.getChild(__name__)
kv_file = os.path.join(os.path.dirname(__file__), __file__.replace(".py", ".kv"))
if os.path.exists(kv_file):
    log.info(f"Loading KV file: {kv_file}")
    Builder.load_file(kv_file)


class CoordBar(BoxLayout, SavingDispatcher):
    device = ObjectProperty()
    input_index = NumericProperty(0)
    axis_name = StringProperty("?")
    ratio_num = NumericProperty(5)
    ratio_den = NumericProperty(1)
    sync_ratio_num = NumericProperty(360)
    sync_ratio_den = NumericProperty(100)
    sync_enable = BooleanProperty(False)
    position = NumericProperty(0)
    speed = NumericProperty(0.0)
    sync_button_color = ListProperty([0.3, 0.3, 0.3, 1])

    _skip_save = ["position", "formatted_axis_speed", "sync_enable"]

    def __init__(self, input_index, **kv):
        super().__init__(**kv)
        self.input_index = input_index

        self.speed_history = collections.deque(maxlen=5)
        self.previous_axis_time: float = 0
        self.previous_axis_pos: Decimal = Decimal(0)
        self.upload()
        self.app = App.get_running_app()

    def upload(self):
        props = self.get_our_properties()
        prop_names = [item.name for item in props]
        device_props = self.get_writeable_properties(type(self.device.scales[self.input_index]))
        matches = [item for item in prop_names if item in device_props]
        for item in matches:
            log.info(f"Writing scale settings for scale {self.input_index}: {item}={self.__getattribute__(item)}")
            self.device.scales[self.input_index].__setattr__(item, self.__getattribute__(item))

    def toggle_sync(self):
        running_app = App.get_running_app()
        self.sync_enable = not self.device.scales[self.input_index].sync_motion
        self.device.scales[self.input_index].sync_motion = self.sync_enable
        running_app.manual_full_update()

    def on_sync_ratio_num(self, instance, value):
        self.device.scales[instance.input_index].sync_ratio_num = int(value)

    def on_sync_ratio_den(self, instance, value):
        self.device.scales[instance.input_index].sync_ratio_den = int(value)

    def on_ratio_num(self, instance, value):
        self.device.scales[instance.input_index].ratio_num = int(value)

    def on_ratio_den(self, instance, value):
        self.device.scales[instance.input_index].ratio_den = int(value)

    def update_position(self):
        if not self.sync_enable:
            Factory.Keypad().show(self, 'new_position')

    @property
    def new_position(self):
        return None

    @new_position.setter
    def new_position(self, value):
        self.device.scales[self.input_index].position = int(float(value) * self.app.formats.factor * 1000)

