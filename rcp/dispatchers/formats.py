from fractions import Fraction

from kivy.logger import Logger
from kivy.properties import (
    NumericProperty,
    StringProperty, ListProperty, ObjectProperty, BooleanProperty, DictProperty
)
from kivy.event import EventDispatcher

from rcp.dispatchers import SavingDispatcher

log = Logger.getChild(__name__)


class FormatsDispatcher(SavingDispatcher):
    _force_save = ['display_color', 'display_font', 'show_speed_label', 'show_numdec_panel']  # Add the new property
    metric_position = StringProperty("{:+0.3f}")
    metric_speed = StringProperty("{:+0.3f}")

    imperial_position = StringProperty("{:+0.4f}")
    imperial_speed = StringProperty("{:+0.4f}")

    angle_format = StringProperty("{:+0.1f}")
    angle_speed_format = StringProperty("{:+0.1f}")

    # Add the backlash property 
    backlash_amount = StringProperty("0.2")

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

    def get_backlash_display_value(self):
        """Return backlash value converted to current display units"""
        try:
            backlash_mm = float(self.backlash_amount)
            if self.current_format == "in":
                # Convert to inches with 4 decimal places for display
                return str(round(backlash_mm / 25.4, 4))
            return self.backlash_amount  # Already in mm
        except (ValueError, TypeError):
            return self.backlash_amount
    
    def set_backlash_from_display_value(self, display_value):
        """Set backlash value from display units, converting to mm if needed"""
        try:
            value = float(display_value)
            # If in inch mode, convert to mm
            if self.current_format == "in":
                value = value * 25.4
            
            self.backlash_amount = str(round(value, 3))  # Store as mm with 3 decimal places
            return True
        except ValueError:
            return False


class Formats(EventDispatcher):
    current_format = StringProperty("mm")
    formats_dict = DictProperty({"mm": 1.0, "in": 25.4})

    # Backlash is always stored in mm regardless of display units
    backlash_amount = StringProperty("0.2")  # in mm

    def __init__(self, **kw):
        super(Formats, self).__init__(**kw)
        from rcp.app import MainApp
        self.app = MainApp.get_running_app()
        self.load_formats()

    def load_formats(self):
        """Load formats from app settings"""
        app = self.app
        if hasattr(app, "application_settings") and "formats" in app.application_settings:
            formats_settings = app.application_settings["formats"]
            if "current_format" in formats_settings:
                self.current_format = formats_settings["current_format"]
            if "formats_dict" in formats_settings:
                self.formats_dict = formats_settings["formats_dict"]
            # Load backlash setting
            if "backlash_amount" in formats_settings:
                self.backlash_amount = formats_settings["backlash_amount"]
                Logger.info(f"Formats: Loaded backlash amount: {self.backlash_amount}")
            else:
                Logger.info(f"Formats: No backlash_amount in settings, using default: {self.backlash_amount}")

    def save_formats(self):
        """Save formats to app settings"""
        app = self.app
        if hasattr(app, "application_settings"):
            if not "formats" in app.application_settings:
                app.application_settings["formats"] = {}
            app.application_settings["formats"]["current_format"] = self.current_format
            app.application_settings["formats"]["formats_dict"] = self.formats_dict
            # Save backlash setting
            app.application_settings["formats"]["backlash_amount"] = self.backlash_amount
            Logger.info(f"Saving backlash amount: {self.backlash_amount}")
            app.save_settings()

    def get_backlash_display_value(self):
        """Return backlash value converted to current display units"""
        backlash_mm = float(self.backlash_amount)
        if self.current_format == "in":
            return str(round(backlash_mm / 25.4, 4))  # Convert to inches with 4 decimal places
        return self.backlash_amount  # Already in mm
    
    def set_backlash_from_display_value(self, display_value):
        """Set backlash value from display units, converting to mm if needed"""
        try:
            value = float(display_value)
            # If in inch mode, convert to mm
            if self.current_format == "in":
                value = value * 25.4
            
            self.backlash_amount = str(round(value, 3))  # Store as mm with 3 decimal places
            return True
        except ValueError:
            return False
