from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from client.desktop.views.menu_screen import MenuScreen


class FarApp(App):
    title = "FarApp"

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))

        return sm


def main():
    FarApp().run()


if __name__ == "__main__":
    main()
