import os

from kivy.lang import Builder


def load_view_kv(filename):
    kv_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kv"))
    kv_file = os.path.join(kv_dir, filename)
    Builder.load_file(kv_file)
