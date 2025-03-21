from keke import ktrace
from kivy.base import EventLoop
from kivy.logger import Logger, KivyFormatter
from kivy.core.window import Window
from fractions import Fraction
from kivy.lang import global_idmap
global_idmap['Fraction'] = Fraction

log = Logger.getChild(__name__)

Window.size = (1024, 600)
Window.show_cursor = True
for h in log.root.handlers:
    h.formatter = KivyFormatter('%(asctime)s - %(name)s:%(lineno)s-%(funcName)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    from rcp.app import MainApp
    # Monkeypatch to add more trace events
    EventLoop.idle = ktrace()(EventLoop.idle)
    MainApp().run()
