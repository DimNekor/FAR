from kivy.uix.screenmanager import Screen

from client.desktop.views import load_view_kv

load_view_kv("menu.kv")


class MenuScreen(Screen):
    def go_to_survey(self):
        self.manager.current = "survey"

    def go_to_results(self):
        self.manager.current = "results"

    def go_to_settings(self):
        self.manager.current = "settings"
