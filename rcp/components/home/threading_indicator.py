from kivy.uix.button import Button
from kivy.properties import NumericProperty, BooleanProperty
from kivy.graphics import Color, Rectangle, Line, Ellipse, Triangle
from kivy.logger import Logger
from fractions import Fraction

log = Logger.getChild(__name__)

class ThreadingIndicator(Button):
    """Visual indicator for threading operations showing position and cycle state"""
    thread_length = NumericProperty(10.0)
    current_position = NumericProperty(0.0)
    cycle_state = NumericProperty(0)  # 0=idle, 1=cutting, 2=waiting, 3=returning_past, 4=returning_exact
    cycle_active = BooleanProperty(False)
    right_to_left = BooleanProperty(True)  # Add property to track direction
    
    def __init__(self, **kwargs):
        super(ThreadingIndicator, self).__init__(**kwargs)
        self.background_normal = ''  # Remove button background
        self.background_down = ''    # Remove button press effect
        self.bind(pos=self.update_graphics)
        self.bind(size=self.update_graphics)
        self.bind(thread_length=self.update_graphics)
        self.bind(current_position=self.update_graphics)
        self.bind(cycle_state=self.update_graphics)
        self.bind(cycle_active=self.update_graphics)
        
    def update_graphics(self, *args):
        # Ensure we have valid dimensions before drawing
        if self.width <= 0 or self.height <= 0:
            return
            
        self.canvas.clear()
        
        with self.canvas:
            # Set dimensions and positions within the widget's own coordinate space
            bar_height = min(self.height * 0.6, 15)
            x_margin = self.width * 0.05
            bar_width = self.width - (2 * x_margin)
            bar_y = (self.height - bar_height) / 2
            
            # Calculate position indicator - inverted for right to left operation
            progress = min(1.0, max(0.0, abs(self.current_position) / self.thread_length)) if self.thread_length > 0 else 0
            # Invert the position to go from right to left
            position_x = x_margin + bar_width - (progress * bar_width) if self.right_to_left else x_margin + (progress * bar_width)
            
            # Background color based on state
            if self.cycle_active:
                if self.cycle_state == 1:  # cutting
                    Color(0.2, 0.7, 0.2, 1)  # Green for cutting
                elif self.cycle_state == 2:  # waiting
                    Color(0.7, 0.7, 0.2, 1)  # Yellow for waiting
                elif self.cycle_state in (3, 4):  # returning
                    Color(0.2, 0.2, 0.7, 1)  # Blue for returning
            else:
                Color(0.15, 0.15, 0.15, 1)  # Dark gray for inactive
                
            # Draw background bar - IMPORTANT: Use self.pos[0] and self.pos[1]
            Rectangle(
                pos=(self.pos[0] + x_margin, self.pos[1] + bar_y), 
                size=(bar_width, bar_height)
            )
            
            # Draw start and end markers
            Color(1, 1, 1, 1)
            marker_width = min(bar_height * 0.3, 5)
            
            # Start marker
            Rectangle(
                pos=(self.pos[0] + x_margin, self.pos[1] + bar_y), 
                size=(marker_width, bar_height)
            )
            
            # End marker
            Rectangle(
                pos=(self.pos[0] + x_margin + bar_width - marker_width, self.pos[1] + bar_y), 
                size=(marker_width, bar_height)
            )
            
            # Position indicator
            Color(1, 0.7, 0, 1)  # Orange triangle
            indicator_size = min(bar_height * 1.6, 30)
            
            # Define triangle points (pointing up)
            triangle_x = self.pos[0] + position_x
            triangle_y = self.pos[1] + bar_y + bar_height/2
            
            # Define three points for triangle: bottom left, bottom right, top middle
            triangle_points = [
                triangle_x - indicator_size/2, triangle_y - indicator_size/3,  # bottom left
                triangle_x + indicator_size/2, triangle_y - indicator_size/3,  # bottom right
                triangle_x, triangle_y + indicator_size*2/3  # top middle
            ]
            
            # Draw triangle
            Triangle(points=triangle_points)
            
    def toggle_direction(self):
        """Toggle the indicator direction between right-to-left and left-to-right"""
        self.right_to_left = not self.right_to_left
        log.info(f"Threading indicator direction: {'right-to-left' if self.right_to_left else 'left-to-right'}")
        
    def on_release(self):
        """Handle button press to toggle direction"""
        self.toggle_direction()