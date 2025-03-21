import os
from fractions import Fraction

from kivy.factory import Factory
from kivy.logger import Logger
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from pydantic import BaseModel

from rcp.components.home.coordbar import CoordBar
from rcp import feeds
from rcp.dispatchers import SavingDispatcher


class FeedMode(BaseModel):
    id: int
    name: str

log = Logger.getChild(__name__)

kv_file = os.path.join(os.path.dirname(__file__), __file__.replace(".py", ".kv"))
if os.path.exists(kv_file):
    log.info(f"Loading KV file: {kv_file}")
    Builder.load_file(kv_file)


class ElsBar(BoxLayout, SavingDispatcher):
    feed_button = ObjectProperty(None)
    feed_ratio = ObjectProperty(None)

    mode_name = StringProperty(":(")
    feed_name = StringProperty(":(")
    current_feeds_index = NumericProperty(0)
    
    # New properties for thread length control
    thread_length = NumericProperty(10.0)  # Default thread length in mm/inch (based on current format)
    cycle_active = BooleanProperty(False)
    cycle_state = NumericProperty(0)  # 0=idle, 1=cutting, 2=waiting, 3=returning_past, 4=returning_exact
    cycle_start_position = NumericProperty(0)
    
    _skip_save = [
        "position",
        "x", "y",
        "minimum_width",
        "minimum_height",
        "width", "height",
        "cycle_active", "cycle_state", "cycle_start_position"
    ]

    def __init__(self, **kwargs):
        from rcp.app import MainApp
        self.app: MainApp = MainApp.get_running_app()
        super().__init__(**kwargs)
        if not self.mode_name in feeds.table.keys():
            self.mode_name = next(iter(feeds.table.keys()))
        self.current_feeds_table = feeds.table[self.mode_name]
        self.update_feeds_ratio(self, None)
        self.bind(current_feeds_index=self.update_feeds_ratio)
        
        # Add binding to servo status to detect when motion completes
        if hasattr(self.app, 'servo'):
            self.app.servo.bind(disableControls=self.on_servo_status_change)
        
        # Add binding to format changes to update thread length units
        self.app.formats.bind(current_format=self.on_format_change)
        
    # Add property getter for backlash amount
    @property
    def backlash_amount(self):
        """
        Get backlash amount from formats settings in mm
        Backlash is always stored as mm in the settings
        """
        try:
            return float(self.app.formats.backlash_amount)
        except (ValueError, AttributeError):
            return 0.2

    def get_backlash_in_current_units(self):
        """
        Get the backlash amount converted to current display units
        for UI display purposes only
        """
        backlash_mm = self.backlash_amount
        
        # Convert to current units if necessary
        if self.app.formats.current_format == "in":
            return backlash_mm / 25.4  # Convert mm to inches
        return backlash_mm  # Already in mm

    def update_current_position(self):
        Factory.Keypad().show_with_callback(self.servo.set_current_position, self.servo.scaledPosition)

    def set_feed_ratio(self, table_name, index):
        table_instance = feeds.table[table_name]
        self.mode_name = table_name
        self.current_feeds_table = table_instance
        self.current_feeds_index = index

    def update_feeds_ratio(self, instance, value):
        ratio = self.current_feeds_table[self.current_feeds_index].ratio
        spindle_scale: CoordBar = self.app.get_spindle_scale()
        if spindle_scale is not None:
            spindle_scale.syncRatioNum = ratio.numerator
            spindle_scale.syncRatioDen = ratio.denominator
        self.feed_name = self.current_feeds_table[self.current_feeds_index].name
        log.info(f"Configured ratio is: {ratio.numerator}/{ratio.denominator}")

    def next_feed(self):
        if self.current_feeds_index < len(self.current_feeds_table) -1:
            self.current_feeds_index = (self.current_feeds_index + 1)

    def previous_feed(self):
        if self.current_feeds_index > 0:
            self.current_feeds_index = (self.current_feeds_index - 1)

    def set_thread_length(self, value):
        """Set the thread length from keypad input"""
        # Value is already in current display units, so set directly
        self.thread_length = value
        log.info(f"Thread length set to {self.thread_length} {self.app.formats.current_format}")
    
    def show_thread_length_keypad(self):
        """Show keypad to set thread length"""
        Factory.Keypad().show_with_callback(self.set_thread_length, self.thread_length)
    
    def start_thread_cycle(self):
        """Start the threading cycle"""
        if not self.app.connected or not self.app.servo.elsMode:
            return
            
        if self.cycle_active:
            # If cycle is active but waiting for button press
            if self.cycle_state == 2:  # waiting state
                # Start return movement with backlash compensation
                self.cycle_state = 3  # returning_past state
                
                # Get backlash amount in mm
                backlash_mm = self.backlash_amount
                
                # Convert backlash to machine units if necessary
                # The servo position is always in the machine's native units,
                # so we need to ensure backlash uses the same units
                backlash_machine_units = backlash_mm
                if hasattr(self.app.servo, 'positionScale') and self.app.servo.positionScale != 1.0:
                    backlash_machine_units = backlash_mm / self.app.servo.positionScale
                
                # The direction depends on which way we were cutting
                direction = self.app.servo.direction / abs(self.app.servo.direction)  # Get +1 or -1
                backlash_position = self.cycle_start_position - (direction * backlash_machine_units)
                
                # Move past the starting position to take up backlash
                self.app.servo.servoEnable = 1  # Enable servo
                self.app.device['servo']['position'] = backlash_position
                
            elif self.cycle_state == 0:  # If cycle is in idle state after returning
                # Start a new cutting pass
                self.cycle_state = 1  # cutting state
                self.cycle_start_position = self.app.servo.position
                self.app.servo.servoEnable = 1  # Enable servo
        else:
            # Start new cycle
            self.cycle_active = True
            self.cycle_state = 1  # cutting state
            self.cycle_start_position = self.app.servo.position
            self.app.servo.servoEnable = 1  # Enable servo
            
            # Start monitoring thread length
            Clock.schedule_interval(self.monitor_thread_progress, 0.1)
    
    def stop_thread_cycle(self):
        """Stop the active threading cycle"""
        if self.cycle_active:
            self.cycle_active = False
            self.cycle_state = 0  # idle state
            Clock.unschedule(self.monitor_thread_progress)
            self.app.servo.servoEnable = 0  # Disable servo
    
    def monitor_thread_progress(self, dt):
        """Monitor threading progress and handle state changes"""
        if not self.cycle_active:
            return
            
        if self.cycle_state == 1:  # cutting state
            # Calculate distance traveled using scaled position
            distance = abs(self.app.servo.scaledPosition - 
                          (self.cycle_start_position * Fraction(self.app.servo.ratioNum, 
                                                              self.app.servo.ratioDen)))
            
            # The visual indicator will update automatically
            # through the property binding in the KV file
            
            # If we've reached the target length
            if distance >= self.thread_length:
                self.cycle_state = 2  # waiting state
                self.app.servo.servoEnable = 0  # Stop motion

    def on_servo_status_change(self, instance, value):
        """Handle servo status changes"""
        if not self.cycle_active:
            return
            
        # If servo is no longer disabled (movement completed)
        if not value:
            if self.cycle_state == 3:  # If we just finished moving past the starting position
                # Now move to the exact starting position
                self.cycle_state = 4  # returning_exact state
                self.app.servo.servoEnable = 1  # Enable servo
                self.app.device['servo']['position'] = self.cycle_start_position
                
            elif self.cycle_state == 4:  # If we just finished the final move to starting position
                # Cycle completed - go to idle state ready for next pass
                self.cycle_state = 0

    def on_format_change(self, instance, value):
        """Handle unit format changes by converting thread length to new units"""
        # Get the factor from the formats dispatcher
        factor = 1.0
        if hasattr(instance, 'formats_dict') and value.lower() in instance.formats_dict:
            factor = instance.formats_dict[value.lower()]
        
        # For metric to imperial (mm to inches)
        if value.lower() == "in":
            # Convert from mm to inches
            self.thread_length = self.thread_length / 25.4
        # For imperial to metric (inches to mm)
        elif value.lower() == "mm" and self.thread_length < 100:  
            # Assume small values are in inches and need conversion to mm
            # The < 100 check helps avoid multiple conversions
            self.thread_length = self.thread_length * 25.4
        
        log.info(f"Thread length converted to {self.thread_length} {value}")

    def get_scaled_cycle_position(self):
        """Calculate the current position in the threading cycle, scaled to the current ratio"""
        if not self.cycle_active:
            return 0
        
        # Use Fraction to handle precise ratio calculations
        from fractions import Fraction
        position_fraction = abs(self.app.servo.scaledPosition - 
                      (self.cycle_start_position * Fraction(self.app.servo.ratioNum, 
                                                          self.app.servo.ratioDen)))
        
        # Convert Fraction to float before returning
        return float(position_fraction)