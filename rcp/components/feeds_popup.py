from kivy.app import App
from kivy.logger import Logger
from kivy.properties import NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from rcp.components.home.elsbar import FEED_MODES

log = Logger.getChild(__name__)

class KeypadButton(Button):
    text_halign = "center"
    font_style = "bold"
    halign = "center"
    background_color = [0.2, 1, 0.2, 1]
    return_value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_height(self, instance, value):
        self.font_size = value / 4


class FeedsPopup(Popup):
    set_method = None
    container = None

    def __init__(self, **kwargs):
        self.app = App.get_running_app()
        super().__init__(**kwargs)
        self.title = f"Select Feed Mode"
        self.size_hint = (0.8, 0.3)
        self.auto_dismiss = False

        layout = BoxLayout(orientation="vertical")

        row1 = BoxLayout(orientation="horizontal")
        for mode in FEED_MODES:
            row1.add_widget(
                KeypadButton(text=mode.name, return_value=mode.id, on_release=self.confirm)
            )
        layout.add_widget(row1)
        self.add_widget(layout)
        self.callback_fn = None
        self.current_value = None

    def on_touch_down(self, touch):
        self.app.beep()
        return super().on_touch_down(touch)

    def show_with_callback(self, callback_fn, current_value=None):
        if current_value is not None:
            # Use the specified current value if passed
            self.current_value = float(current_value)

        self.callback_fn = callback_fn
        self.set_method = None
        self.container = None
        self.open()

    def confirm(self, instance: KeypadButton):
        try:
            value = instance.return_value
            self.callback_fn(value)
            self.dismiss()
        except Exception as e:
            log.error(e.__str__())
            return

    def cancel(self, *args, **kwargs):
        self.dismiss()
