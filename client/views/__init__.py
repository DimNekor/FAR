import os
import sys

from kivy.lang import Builder


def load_view_kv(filename):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    kv_file = os.path.join(base_path, "kv", filename)
    Builder.load_file(kv_file)
