from kivy.config import Config

Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from client.desktop.views.menu_screen import MenuScreen
from client.desktop.views.survey_screen import SurveyScreen
from client.desktop.views.results_screen import ResultsScreen


class FarApp(App):
    title = "FarApp"

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(SurveyScreen(name="survey"))
        sm.add_widget(ResultsScreen(name="results"))
        return sm


def main():
    FarApp().run()


if __name__ == "__main__":
    main()
