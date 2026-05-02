from kivy.config import Config

Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from client.views.menu_screen import MenuScreen
from client.views.survey_screen import SurveyScreen
from client.views.results_screen import ResultsScreen
from client.views.settings_screen import SettingsScreen


class FarApp(App):
    title = "FarApp"

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(SurveyScreen(name="survey"))
        sm.add_widget(ResultsScreen(name="results"))
        sm.add_widget(SettingsScreen(name="settings"))
        return sm


def main():
    FarApp().run()


if __name__ == "__main__":
    main()
