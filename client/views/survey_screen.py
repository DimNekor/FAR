from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.checkbox import CheckBox

from datetime import datetime
import random
import os
import json
import time
import sys
from pathlib import Path

from client.views import load_view_kv
from client.models.database import Database

load_view_kv("survey.kv")


class SurveyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.db = Database()

        self.state = "id_input"
        self.participant_id = ""
        self.user_id = None
        self.session_id = None
        self.images = []
        self.current_image_index = 0
        self.results = []
        self.image_timer = 10
        self.fixation_timer = 3
        self.time_left = 0
        self.image_start_time = 0

        self.layout = BoxLayout(orientation="vertical")
        self.add_widget(self.layout)

        self._load_images()
        self._show_id_input()

    def _load_images(self):        
        if getattr(sys, 'frozen', False):
            if sys.platform == "win32":
                base = Path(os.environ.get("APPDATA", ".")) / "FAR"
            else:
                base = Path.home() / ".config" / "FAR"
            image_dir = str(base / "images")
        else:
            image_dir = "static/images/"
        
        self.images = []

        real_images = []
        fake_images = []

        if os.path.exists(image_dir):
            for filename in os.listdir(image_dir):
                if filename.endswith((".png", ".jpg", ".jpeg")):
                    if filename.startswith("real"):
                        real_images.append(os.path.join(image_dir, filename))
                    elif filename.startswith("fake"):
                        fake_images.append(os.path.join(image_dir, filename))

        if len(real_images) >= 25 and len(fake_images) >= 25:
            selected_real = random.sample(real_images, 25)
            selected_fake = random.sample(fake_images, 25)

            self.images = selected_real + selected_fake
            random.shuffle(self.images)

            self.images = real_images + fake_images
            random.shuffle(self.images)

    def _clear_layout(self):
        self.layout.clear_widgets()

    def _show_id_input(self):
        self._clear_layout()
        self.state = "id_input"

        from kivy.uix.floatlayout import FloatLayout
        from kivy.uix.boxlayout import BoxLayout
        from kivy.graphics import Color, Line, Rectangle
        from kivy.uix.checkbox import CheckBox

        float_layout = FloatLayout()
        self.layout.add_widget(float_layout)

        # Основной контейнер
        container = BoxLayout(
            orientation="vertical",
            size_hint=(0.6, 0.7),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            spacing=15,
            padding=30,
        )

        # Рамка и фон
        def update_rect(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0.3, 0.3, 0.3, 1)
                Line(
                    rectangle=(instance.x, instance.y, instance.width, instance.height),
                    width=2,
                )
                Color(0.95, 0.95, 0.95, 1)
                Rectangle(pos=instance.pos, size=instance.size)

        container.bind(pos=update_rect, size=update_rect)

        # Заголовок
        title = Label(
            text="Регистрация участника",
            font_size=26,
            bold=True,
            color=(0.1, 0.1, 0.3, 1),
            size_hint=(1, 0.12),
            halign="center",
            valign="middle",
        )
        container.add_widget(title)

        # Поле ID
        id_box = BoxLayout(orientation="vertical", size_hint=(1, 0.22), spacing=8)

        id_label = Label(
            text="Введите ваш ID (почта, телефон, ФИО или другой идентификатор):",
            font_size=16,
            color=(0, 0, 0, 1),
            size_hint=(1, 0.4),
            halign="left",
            valign="bottom",
        )
        id_box.add_widget(id_label)

        self.id_input = TextInput(
            text="",
            font_size=16,
            size_hint=(1, 0.5),
            multiline=False,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            padding=(10, 10),
        )
        id_box.add_widget(self.id_input)
        container.add_widget(id_box)

        sex_box = BoxLayout(orientation="vertical", size_hint=(1, 0.2), spacing=5)

        sex_label = Label(
            text="Укажите ваш пол:",
            font_size=15,
            color=(0, 0, 0, 1),
            size_hint=(1, 0.4),
            halign="left",
            valign="bottom",
        )
        sex_box.add_widget(sex_label)

        # Контейнер для флажков пола
        sex_checkboxes = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.5), spacing=30
        )

        # Флажок Мужской
        male_box = BoxLayout(orientation="horizontal", spacing=5)
        self.checkbox_male = CheckBox(
            group="sex",
            size_hint=(None, None),
            size=(40, 40),
            active=True,  # По умолчанию выбран мужской
        )
        male_label = Label(
            text="Мужской",
            font_size=16,
            color=(0, 0, 0, 1),
            size_hint=(None, None),
            size=(100, 40),
            halign="left",
            valign="middle",
        )
        male_box.add_widget(self.checkbox_male)
        male_box.add_widget(male_label)

        # Флажок Женский
        female_box = BoxLayout(orientation="horizontal", spacing=5)
        self.checkbox_female = CheckBox(
            group="sex",
            size_hint=(None, None),
            size=(40, 40),
            active=False,
        )
        female_label = Label(
            text="Женский",
            font_size=16,
            color=(0, 0, 0, 1),
            size_hint=(None, None),
            size=(100, 40),
            halign="left",
            valign="middle",
        )
        female_box.add_widget(self.checkbox_female)
        female_box.add_widget(female_label)

        sex_checkboxes.add_widget(male_box)
        sex_checkboxes.add_widget(female_box)
        sex_box.add_widget(sex_checkboxes)
        container.add_widget(sex_box)

        # Выбор ДО/ПОСЛЕ
        timing_box = BoxLayout(orientation="vertical", size_hint=(1, 0.3), spacing=10)

        timing_label = Label(
            text="Укажите, когда проводится опрос:",
            font_size=15,
            color=(0, 0, 0, 1),
            size_hint=(1, 0.3),
            halign="left",
            valign="bottom",
        )
        timing_box.add_widget(timing_label)

        # Контейнер для флажков
        checkboxes_box = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.5), spacing=30
        )

        from kivy.uix.checkbox import CheckBox

        # Флажок ДО
        before_box = BoxLayout(orientation="horizontal", spacing=5)
        self.checkbox_before = CheckBox(
            group="timing",
            size_hint=(None, None),
            size=(40, 40),
            active=True,  # По умолчанию выбрано ДО
        )
        before_label = Label(
            text="ДО физической нагрузки",
            font_size=16,
            color=(0, 0, 0, 1),
            size_hint=(None, None),
            size=(200, 40),
            halign="left",
            valign="middle",
        )
        before_box.add_widget(self.checkbox_before)
        before_box.add_widget(before_label)

        # Флажок ПОСЛЕ
        after_box = BoxLayout(orientation="horizontal", spacing=5)
        self.checkbox_after = CheckBox(
            group="timing", size_hint=(None, None), size=(40, 40), active=False
        )
        after_label = Label(
            text="ПОСЛЕ физической нагрузки",
            font_size=16,
            color=(0, 0, 0, 1),
            size_hint=(None, None),
            size=(220, 40),
            halign="left",
            valign="middle",
        )
        after_box.add_widget(self.checkbox_after)
        after_box.add_widget(after_label)

        checkboxes_box.add_widget(before_box)
        checkboxes_box.add_widget(after_box)
        timing_box.add_widget(checkboxes_box)
        container.add_widget(timing_box)

        # Кнопка Продолжить
        submit_btn = Button(
            text="Продолжить",
            font_size=18,
            size_hint=(0.5, 0.1),
            pos_hint={"center_x": 0.5},
            background_color=(0.3, 0.5, 0.7, 1),
            color=(1, 1, 1, 1),
        )
        submit_btn.bind(on_release=self._on_id_submit)
        container.add_widget(submit_btn)

        float_layout.add_widget(container)

    def _on_id_submit(self, instance):
        self.participant_id = self.id_input.text.strip()

        if hasattr(self, "checkbox_male") and self.checkbox_male.active:
            self.sex = "male"
        else:
            self.sex = "female"

        if self.participant_id:
            # Определяем ДО или ПОСЛЕ
            if self.checkbox_before.active:
                self.timing = "before"
            else:
                self.timing = "after"

            try:
                self.user_id = self.db.create_users(self.participant_id, self.sex)
                self.session_id = self.db.create_session(self.user_id, self.timing)
            except Exception as e:
                print(f"Ошибка при создании пользователя/сессии: {e}")
                return

            self._show_instruction()
        else:
            self.id_input.background_color = (1, 0.8, 0.8, 1)

    def _show_instruction(self):
        self._clear_layout()
        self.state = "instruction"

        from kivy.uix.floatlayout import FloatLayout
        from kivy.uix.boxlayout import BoxLayout
        from kivy.graphics import Color, Line, Rectangle

        float_layout = FloatLayout()
        self.layout.add_widget(float_layout)

        # Основной контейнер
        main_container = BoxLayout(
            orientation="vertical",
            size_hint=(0.8, 0.75),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            spacing=0,
        )

        # Рамка для всего контейнера
        with main_container.canvas.before:
            Color(0.3, 0.3, 0.3, 1)
            self.border_rect = Line(rectangle=(0, 0, 0, 0), width=2)
            Color(0.95, 0.95, 0.95, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=(0, 0))

        def update_main_rect(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0.3, 0.3, 0.3, 1)
                Line(
                    rectangle=(instance.x, instance.y, instance.width, instance.height),
                    width=2,
                )
                Color(0.95, 0.95, 0.95, 1)
                Rectangle(pos=instance.pos, size=instance.size)

        main_container.bind(pos=update_main_rect, size=update_main_rect)

        # Заголовок
        title_label = Label(
            text="Инструкция FAR",
            font_size=28,
            bold=True,
            color=(0.1, 0.1, 0.3, 1),
            size_hint=(1, 0.15),
            halign="center",
            valign="middle",
            padding=(0, 10),
        )

        # Линия под заголовком
        separator = BoxLayout(size_hint=(1, 0.02), padding=(20, 0))
        with separator.canvas.before:
            Color(0.3, 0.3, 0.3, 1)
            Line(
                points=[
                    separator.x,
                    separator.y,
                    separator.x + separator.width,
                    separator.y,
                ],
                width=1,
            )

        def update_separator(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0.5, 0.5, 0.5, 1)
                Line(
                    points=[
                        instance.x + 20,
                        instance.y + instance.height / 2,
                        instance.x + instance.width - 20,
                        instance.y + instance.height / 2,
                    ],
                    width=1,
                )

        separator.bind(pos=update_separator, size=update_separator)

        # Текст инструкции
        instruction_text = (
            "Сейчас перед Вами на экране появится серый фон с точкой фиксации, "
            "на которой Вам нужно сконцентрировать взгляд, далее будут последовательно "
            "предъявляться изображения. Вы должны будете решить, изображение настоящее "
            "или сгенерированное ИИ.\n\n"
            "Время предъявления ограничено (10 секунд), "
            "поэтому, пожалуйста, постарайтесь выбрать оптимальный режим соотношения "
            "скорости и качества оценки.\n\n"
            "Если Вы считаете, что изображение сгенерировано ИИ, "
            "то нажмите правую кнопку мыши, если настоящее - левую.\n\n"
            'Для начала нажмите "ПРОБЕЛ".'
        )

        instruction_label = Label(
            text=instruction_text,
            font_size=25,
            color=(0, 0, 0, 1),
            size_hint=(1, 0.83),
            halign="left",
            valign="top",
            padding=(25, 15),
        )

        def set_text_size(instance, value):
            instance.text_size = (instance.width - 50, None)

        instruction_label.bind(size=set_text_size)

        main_container.add_widget(title_label)
        main_container.add_widget(separator)
        main_container.add_widget(instruction_label)
        float_layout.add_widget(main_container)

        Window.bind(on_key_down=self._on_instruction_key)

    def _on_instruction_key(self, window, key, scancode, codepoint, modifier):
        if key == 32:
            Window.unbind(on_key_down=self._on_instruction_key)
            self._show_fixation()

    def _show_fixation(self):
        self._clear_layout()
        self.state = "fixation"

        fixation_label = Label(
            text="+",
            font_size=72,
            color=(0, 0, 0, 1),
            size_hint=(1, 1),
            halign="center",
            valign="middle",
        )
        self.layout.add_widget(fixation_label)

        self.time_left = self.fixation_timer
        Clock.schedule_interval(self._fixation_timer, 1.0)

    def _fixation_timer(self, dt):
        self.time_left -= 1
        if self.time_left <= 0:
            Clock.unschedule(self._fixation_timer)
            self._show_image()

    def _show_image(self):
        self._clear_layout()
        self.state = "image"

        if self.current_image_index >= len(self.images):
            self._show_end()
            return

        self.layout.clear_widgets()

        from kivy.uix.floatlayout import FloatLayout

        float_layout = FloatLayout()
        self.layout.add_widget(float_layout)

        image_path = self.images[self.current_image_index]

        img = Image(
            source=image_path,
            size_hint=(None, None),
            size=(400, 400),
            pos_hint={"center_x": 0.5, "center_y": 0.5},  # Точный центр экрана
            fit_mode="contain",
        )
        float_layout.add_widget(img)

        self.image_start_time = time.time()

        self.time_left = self.image_timer
        self.image_event = Clock.schedule_interval(self._image_timer, 1.0)

        Window.bind(on_mouse_down=self._on_image_click)

    def _image_timer(self, dt):
        self.time_left -= 1
        if self.time_left <= 0:
            image_name = self.images[self.current_image_index]
            true_class = 1 if "real" in image_name else 0

            try:
                self.db.add_image(
                    session_id=self.session_id,
                    image_name=image_name,
                    reaction_time=self.image_timer,
                    true_class=true_class,
                    predicted_class=-1,
                )
            except Exception as e:
                print(f"Ошибка при сохранении таймаута: {e}")

            self.results.append(
                {
                    "image": image_name,
                    "response": "timeout",
                    "time": self.image_timer,
                    "true_class": true_class,
                    "predicted_class": -1,
                }
            )
            print(self.results)
            self._next_image()

    def _on_image_click(self, window, x, y, button, modifiers):
        if self.state != "image":
            return

        response = None
        predicted_class = 0
        if button == "left":
            response = "real"
            predicted_class = 1
        elif button == "right":
            response = "fake"

        if response:
            reaction_time = time.time() - self.image_start_time

            image_name = self.images[self.current_image_index]
            true_class = 1 if "real" in image_name else 0

            try:
                self.db.add_image(
                    session_id=self.session_id,
                    image_name=image_name,
                    reaction_time=round(reaction_time, 3),
                    true_class=true_class,
                    predicted_class=predicted_class,
                )
            except Exception as e:
                print(f"Ошибка при сохранении результата: {e}")

            self.results.append(
                {
                    "image": self.images[self.current_image_index],
                    "response": response,
                    "time": round(reaction_time, 3),
                    "true_class": true_class,
                    "predicted_class": predicted_class,
                }
            )
            self._next_image()

    def _next_image(self):
        Clock.unschedule(self._image_timer)
        Window.unbind(on_mouse_down=self._on_image_click)

        self.current_image_index += 1

        if self.current_image_index < len(self.images):
            self._show_fixation()
        else:
            self._show_end()

    def _show_end(self):
        self._clear_layout()
        self.state = "end"

        self._save_results()

        end_label = Label(
            text="Спасибо за участие!",
            font_size=32,
            color=(0, 0, 0, 1),
            size_hint=(1, 1),
            halign="center",
            valign="middle",
        )
        self.layout.add_widget(end_label)

        Clock.schedule_once(self._go_to_menu, 3)

    def _save_results(self):
        results = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "sex": self.sex,
            "timing": self.timing,
            "date": datetime.now().isoformat(),
            "responses": self.results,
        }

        backup_dir = "backup_results/"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        filename = f"{backup_dir}results_{self.participant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)

        print(f"Резервная копия сохранена в {filename}")

    def _go_to_menu(self, dt):
        if self.manager:
            self.manager.current = "menu"

    def on_leave(self, *args):
        Clock.unschedule(self._fixation_timer)
        Clock.unschedule(self._image_timer)
        Window.unbind(on_mouse_down=self._on_image_click)
        Window.unbind(on_key_down=self._on_instruction_key)
