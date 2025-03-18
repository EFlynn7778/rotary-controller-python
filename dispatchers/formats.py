from fractions import Fraction

from kivy.logger import Logger
from kivy.properties import (
    NumericProperty,
    StringProperty, ListProperty, ObjectProperty, BooleanProperty,
)

from rcp.dispatchers import SavingDispatcher

log = Logger.getChild(__name__)


class FormatsDispatcher(SavingDispatcher):
    _force_save = ['display_color', 'display_font', 'show_speed_label', 'show_numdec_panel']  # Add the new property
    metric_position = StringProperty("{:+0.3f}")
    metric_speed = StringProperty("{:+0.3f}")

    imperial_position = StringProperty("{:+0.4f}")
    imperial_speed = StringProperty("{:+0.4f}")

    angle_format = StringProperty("{:+0.1f}")
    angle_speed_format = StringProperty("{:+0.1f} r")

    current_format = StringProperty("MM")
    speed_format = StringProperty()
    position_format = StringProperty()
    factor = ObjectProperty(Fraction(1, 1))

    display_color = ListProperty([1, 1, 1, 1])
    accept_color = ListProperty([0.2, 1, 0.2, 1])
    cancel_color = ListProperty([1, 0.2, 0.2, 1])

    volume = NumericProperty(0.2)
    display_font = StringProperty('display_font')
    show_speed_label = BooleanProperty(True)  # New property to toggle speed label visibility
    show_numdec_panel = BooleanProperty(True)  # New property to toggle speed label visibility

    def __init__(self, **kv):
        # Get the display_font before calling super().__init__
        # to ensure we don't overwrite the loaded value
        display_font = kv.get('display_font', "fonts/drofonts/Calculator.ttf")
        
        super().__init__(**kv)
        
        # Only set if not already loaded from saved settings
        if not self.display_font or self.display_font == "fonts/drofonts/DS-DIGIB.ttf":
            self.display_font = display_font
            
        log.info(f"Initialized FormatsDispatcher with display_font: {self.display_font}")
        
        self.bind(current_format=self.update_format)
        self.update_format()

    def update_format(self, *args, **kv):
        if self.current_format == "MM":
            self.speed_format = f"{self.metric_speed} M/min"
            self.position_format = self.metric_position
            self.factor = Fraction(1, 1)
        else:
            self.speed_format = f"{self.imperial_speed} Ft/min"
            self.position_format = self.imperial_position
            self.factor = Fraction(10, 254)

    def toggle(self, *_):
        if self.current_format == "MM":
            self.current_format = "IN"
        else:
            self.current_format = "MM"
