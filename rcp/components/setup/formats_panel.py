import os
from kivy.app import App
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ObjectProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from rcp.components.forms.string_item import StringItem

log = Logger.getChild(__name__)
kv_file = os.path.join(os.path.dirname(__file__), "formats_panel.kv")
if os.path.exists(kv_file):
    log.info(f"Loading KV file: {kv_file}")
    Builder.load_file(kv_file)

class FormatsPanel(BoxLayout):
    formats = ObjectProperty()
    available_fonts = ListProperty([])
    
    def __init__(self, formats, **kv):
        from rcp.app import MainApp
        self.app: MainApp = MainApp.get_running_app()
        self.formats = formats
        
        # Make sure display_font is set in formats
        if not hasattr(self.formats, 'display_font') or not self.formats.display_font:
            self.formats.display_font = "fonts/drofonts/DS-DIGIB.ttf"
            
        super().__init__(**kv)
        self.ids['grid_layout'].bind(minimum_height=self.ids['grid_layout'].setter('height'))
        self.load_available_fonts()
        
        # Schedule UI update after initialization
        Clock.schedule_once(self.update_font_spinner, 0.5)
        
    def load_available_fonts(self):
        """Load all available fonts from the fonts directory"""
        fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fonts/drofonts')
        if os.path.exists(fonts_dir):
            font_files = [f for f in os.listdir(fonts_dir) if f.endswith(('.ttf', '.TTF', '.otf', '.OTF'))]
            self.available_fonts = sorted(font_files)
            log.info(f"Loaded {len(self.available_fonts)} fonts")
        else:
            log.error(f"Font directory not found: {fonts_dir}")
            
    def update_font_spinner(self, dt):
        """Update the font spinner with the current selection"""
        if hasattr(self.ids, 'font_spinner'):
            # Extract just the filename from the full path
            current_font = self.formats.display_font.split('/')[-1]
            log.info(f"Setting spinner to current font: {current_font} from {self.formats.display_font}")
            
            # Verify font exists in available fonts
            if current_font in self.available_fonts:
                self.ids.font_spinner.text = current_font
            else:
                log.warning(f"Current font {current_font} not in available fonts: {self.available_fonts}")
                # Set to default if available
                if "DS-DIGIB.ttf" in self.available_fonts:
                    self.ids.font_spinner.text = "DS-DIGIB.ttf"
                    self.formats.display_font = "fonts/drofonts/DS-DIGIB.ttf"
                elif self.available_fonts:
                    # Use first available font
                    self.ids.font_spinner.text = self.available_fonts[0]
                    self.formats.display_font = f"fonts/drofonts/{self.available_fonts[0]}"
                    
    def on_font_selected(self, font_name):
        """Handle font selection change"""
        if font_name in self.available_fonts:
            self.formats.display_font = f"fonts/drofonts/{font_name}"
            log.info(f"Selected font: {self.formats.display_font}")
    
    def on_backlash_change(self, instance, value):
        """
        Handle backlash amount change with direct property setting
        """
        try:
            # Validate first
            backlash_value = float(value.strip())
            
            # Convert if in inches
            if self.formats.current_format == "in":
                backlash_value = backlash_value * 25.4  # Convert to mm
                
            # Store as mm with proper formatting
            self.formats.backlash_amount = str(round(backlash_value, 3))
            
            # Save settings
            if hasattr(self.formats, 'save_formats'):
                self.formats.save_formats()
            
            log.info(f"Backlash amount set to: {self.formats.backlash_amount} mm")
            
        except ValueError:
            # If not a valid float, revert to previous value
            log.warning(f"Invalid backlash value: {value}")
            # Try to show the value in current display units
            if hasattr(self.formats, 'get_backlash_display_value'):
                instance.value = self.formats.get_backlash_display_value()
            else:
                # Fallback: show raw value
                instance.value = self.formats.backlash_amount
                
        except Exception as e:
            log.error(f"Error updating backlash: {e}")
            import traceback
            log.error(traceback.format_exc())
