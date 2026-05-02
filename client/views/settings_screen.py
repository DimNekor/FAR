# client/desktop/views/settings_screen.py

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.clock import Clock

import os
import shutil
import threading
from datetime import datetime
from pathlib import Path

# Импортируем API клиент
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
# from api.client import APIClient, UpdateInfo, SyncResult

from client.views import load_view_kv

load_view_kv("settings.kv")


class SettingsScreen(Screen):
    main_layout = ObjectProperty(None)
    connection_status_text = StringProperty("Проверка...")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Инициализация API клиента
        config_path = Path(__file__).parent.parent / "config.json"
        # self.api = APIClient(config_path)
        self.api = None
        # Пути
        self.db_path = Path(__file__).parent / "research_data.db"
        self.backup_dir = Path(__file__).parent.parent / "backups"

        # Создаем директорию для бэкапов
        self.backup_dir.mkdir(exist_ok=True)

        # Флаг для предотвращения повторных проверок
        self._checking = False

    def on_enter(self):
        """Вызывается при входе на экран"""
        if not self._checking:
            self._check_connection()

    def _check_connection(self):
        """Проверка подключения к VPS"""
        self._checking = True
        self.ids.connection_status.text = "Проверка..."
        self.ids.connection_status.color = (0.8, 0.6, 0.2, 1)

        def check():
            is_available, message = self.api.check_health()

            def update_ui(dt):
                if is_available:
                    self.ids.connection_status.text = "Подключено"
                    self.ids.connection_status.color = (0.3, 0.8, 0.3, 1)
                else:
                    self.ids.connection_status.text = "Не подключено"
                    self.ids.connection_status.color = (0.8, 0.3, 0.3, 1)
                self._checking = False

            Clock.schedule_once(update_ui, 0)

        threading.Thread(target=check, daemon=True).start()

    def check_updates(self):
        """Проверка наличия обновлений"""
        content = BoxLayout(orientation="vertical", spacing=15, padding=20)

        status_label = Label(
            text="Проверка обновлений...",
            font_size=16,
            size_hint=(1, 0.3),
            color=(0.2, 0.2, 0.5, 1),
        )
        content.add_widget(status_label)

        progress = ProgressBar(max=100, size_hint=(1, 0.1))
        content.add_widget(progress)

        info_label = Label(
            text="Подключение к серверу...",
            font_size=14,
            size_hint=(1, 0.4),
            color=(0.3, 0.3, 0.3, 1),
            halign="center",
        )
        content.add_widget(info_label)

        buttons_box = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.2), spacing=10
        )

        close_btn = Button(text="Закрыть", background_color=(0.7, 0.3, 0.3, 1))

        update_btn = Button(
            text="Обновить", background_color=(0.2, 0.7, 0.3, 1), disabled=True
        )

        buttons_box.add_widget(close_btn)
        buttons_box.add_widget(update_btn)
        content.add_widget(buttons_box)

        popup = Popup(
            title="Обновление приложения",
            content=content,
            size_hint=(0.7, 0.6),
            auto_dismiss=False,
        )

        update_info_holder = {"update": None}

        def close_popup(instance):
            popup.dismiss()

        def on_update(instance):
            if update_info_holder["update"]:
                popup.dismiss()
                self._perform_update(update_info_holder["update"])

        close_btn.bind(on_release=close_popup)
        update_btn.bind(on_release=on_update)

        def check():
            # Шаг 1: Проверка подключения
            Clock.schedule_once(lambda dt: setattr(progress, "value", 30), 0)
            Clock.schedule_once(
                lambda dt: setattr(status_label, "text", "Подключение к серверу..."), 0
            )
            Clock.schedule_once(
                lambda dt: setattr(info_label, "text", "Установка соединения..."), 0
            )

            is_available, message = self.api.check_health()

            if not is_available:

                def update_error(dt):
                    progress.value = 100
                    status_label.text = "Ошибка подключения"
                    info_label.text = message
                    close_btn.text = "OK"

                Clock.schedule_once(update_error, 0.5)
                return

            # Шаг 2: Поиск обновлений
            Clock.schedule_once(lambda dt: setattr(progress, "value", 60), 0.5)
            Clock.schedule_once(
                lambda dt: setattr(status_label, "text", "Поиск обновлений..."), 0.5
            )
            Clock.schedule_once(
                lambda dt: setattr(info_label, "text", "Сравнение версий..."), 0.5
            )

            update_info = self.api.check_updates()

            # Шаг 3: Результат
            def show_result(dt):
                progress.value = 100

                if update_info:
                    status_label.text = "Доступно обновление!"
                    info_label.text = (
                        f"Версия: {update_info.version}\n"
                        f"Дата: {update_info.release_date}\n"
                        f"Размер: {update_info.file_size // 1024} KB\n\n"
                        f"Изменения:\n{update_info.changelog[:200]}"
                    )
                    update_btn.disabled = False
                    update_info_holder["update"] = update_info
                else:
                    status_label.text = "Обновлений нет"
                    info_label.text = "У вас последняя версия приложения"
                    close_btn.text = "OK"

            Clock.schedule_once(show_result, 1.0)

        threading.Thread(target=check, daemon=True).start()
        popup.open()

    def _perform_update(self, update_info):
        """Выполнение обновления"""
        content = BoxLayout(orientation="vertical", spacing=15, padding=20)

        status_label = Label(
            text="Загрузка обновления...",
            font_size=16,
            size_hint=(1, 0.3),
            color=(0.2, 0.2, 0.5, 1),
        )
        content.add_widget(status_label)

        progress = ProgressBar(max=100, size_hint=(1, 0.1))
        content.add_widget(progress)

        detail_label = Label(
            text="0%", font_size=14, size_hint=(1, 0.4), color=(0.3, 0.3, 0.3, 1)
        )
        content.add_widget(detail_label)

        close_btn = Button(
            text="Отмена", size_hint=(1, 0.2), background_color=(0.7, 0.3, 0.3, 1)
        )
        content.add_widget(close_btn)

        popup = Popup(
            title="Обновление",
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=False,
        )

        cancel_flag = {"cancel": False}

        def on_cancel(instance):
            cancel_flag["cancel"] = True
            popup.dismiss()

        def on_complete(instance):
            popup.dismiss()
            # В будущем: перезапуск приложения
            self._show_popup(
                "Информация", "Для завершения обновления перезапустите приложение"
            )

        close_btn.bind(on_release=on_cancel)

        def update():
            def progress_callback(percent):
                if not cancel_flag["cancel"]:
                    Clock.schedule_once(
                        lambda dt, p=percent: setattr(progress, "value", p), 0
                    )
                    Clock.schedule_once(
                        lambda dt, p=percent: setattr(
                            detail_label, "text", f"Загружено {p}%"
                        ),
                        0,
                    )

            filepath = self.api.download_update(update_info, progress_callback)

            def finish_update(dt):
                if filepath:
                    status_label.text = "Обновление загружено!"
                    detail_label.text = f"Файл сохранен:\n{filepath}"
                    close_btn.text = "OK"
                    close_btn.background_color = (0.2, 0.7, 0.3, 1)
                    close_btn.unbind(on_release=on_cancel)
                    close_btn.bind(on_release=on_complete)
                else:
                    status_label.text = "Ошибка загрузки"
                    detail_label.text = "Не удалось загрузить обновление"

            Clock.schedule_once(finish_update, 0)

        popup.open()
        threading.Thread(target=update, daemon=True).start()

    def update_app(self):
        """Кнопка 'Обновить сейчас' - проверяет обновления и предлагает установить"""
        content = BoxLayout(orientation="vertical", spacing=15, padding=20)

        warning_label = Label(
            text="⚠ Внимание!\n\nПри обновлении приложение будет перезапущено.\n"
            "Убедитесь, что все данные сохранены.\n\n"
            "Проверить наличие обновлений?",
            font_size=16,
            size_hint=(1, 0.6),
            color=(0.8, 0.3, 0.3, 1),
            halign="center",
        )
        content.add_widget(warning_label)

        buttons_box = BoxLayout(
            orientation="horizontal", spacing=10, size_hint=(1, 0.4)
        )

        cancel_btn = Button(text="Отмена", background_color=(0.7, 0.3, 0.3, 1))

        check_btn = Button(text="Проверить", background_color=(0.2, 0.7, 0.3, 1))

        buttons_box.add_widget(cancel_btn)
        buttons_box.add_widget(check_btn)
        content.add_widget(buttons_box)

        popup = Popup(
            title="Обновление приложения", content=content, size_hint=(0.7, 0.5)
        )

        def on_cancel(instance):
            popup.dismiss()

        def on_check(instance):
            popup.dismiss()
            self.check_updates()

        cancel_btn.bind(on_release=on_cancel)
        check_btn.bind(on_release=on_check)

        popup.open()

    def export_database(self):
        """Экспорт базы данных"""
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        content.add_widget(
            Label(
                text="Выберите папку для экспорта базы данных:",
                size_hint=(1, 0.1),
                bold=True,
            )
        )

        file_chooser = FileChooserListView(
            dirselect=True,
            size_hint=(1, 0.6),
            path=os.path.expanduser("~"),
            filters=[""],
            multiselect=False,
        )
        content.add_widget(file_chooser)

        filename_box = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.1), spacing=10
        )
        filename_box.add_widget(Label(text="Имя файла:", size_hint=(0.3, 1)))

        default_name = (
            f"research_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        filename_input = TextInput(
            text=default_name, size_hint=(0.7, 1), multiline=False
        )
        filename_box.add_widget(filename_input)
        content.add_widget(filename_box)

        # Добавляем опцию экспорта на сервер
        server_export_box = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.1), spacing=10
        )
        from kivy.uix.checkbox import CheckBox

        server_checkbox = CheckBox(size_hint=(0.1, 1), active=False)
        server_export_box.add_widget(server_checkbox)
        server_export_box.add_widget(
            Label(text="Также отправить на сервер", size_hint=(0.9, 1), halign="left")
        )
        content.add_widget(server_export_box)

        buttons_box = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.1), spacing=10
        )

        cancel_btn = Button(text="Отмена", background_color=(0.7, 0.3, 0.3, 1))

        export_btn = Button(text="Экспортировать", background_color=(0.2, 0.7, 0.3, 1))

        buttons_box.add_widget(cancel_btn)
        buttons_box.add_widget(export_btn)
        content.add_widget(buttons_box)

        popup = Popup(
            title="Экспорт базы данных", content=content, size_hint=(0.8, 0.7)
        )

        def on_cancel(instance):
            popup.dismiss()

        def on_export(instance):
            selected_path = file_chooser.path
            filename = filename_input.text.strip()

            if not filename:
                self._show_popup("Ошибка", "Введите имя файла")
                return

            if not filename.endswith(".db"):
                filename += ".db"

            export_path = os.path.join(selected_path, filename)

            try:
                if self.db_path.exists():
                    shutil.copy2(self.db_path, export_path)

                    message = f"База данных экспортирована в:\n{export_path}"

                    # Если выбрана опция отправки на сервер
                    if server_checkbox.active:
                        if self.api.export_database_to_server(self.db_path):
                            message += "\n\nБаза данных отправлена на сервер"
                        else:
                            message += "\n\nНе удалось отправить на сервер"

                    self._show_popup("Успех", message)
                    popup.dismiss()
                else:
                    self._show_popup("Ошибка", "Файл базы данных не найден")
            except Exception as e:
                self._show_popup("Ошибка", f"Ошибка при экспорте:\n{str(e)}")

        cancel_btn.bind(on_release=on_cancel)
        export_btn.bind(on_release=on_export)

        popup.open()

    def sync_database(self):
        """Синхронизация базы данных с VPS"""
        # Создаем бэкап перед синхронизацией
        if self.api.config.get("backup_before_sync", True):
            self._create_backup()

        content = BoxLayout(orientation="vertical", spacing=15, padding=20)

        status_label = Label(
            text="Подготовка к синхронизации...",
            font_size=16,
            size_hint=(1, 0.3),
            color=(0.2, 0.2, 0.5, 1),
        )
        content.add_widget(status_label)

        progress = ProgressBar(max=100, size_hint=(1, 0.1))
        content.add_widget(progress)

        detail_label = Label(
            text="",
            font_size=14,
            size_hint=(1, 0.4),
            color=(0.3, 0.3, 0.3, 1),
            halign="center",
        )
        content.add_widget(detail_label)

        close_btn = Button(
            text="Отмена", size_hint=(1, 0.2), background_color=(0.7, 0.3, 0.3, 1)
        )
        content.add_widget(close_btn)

        popup = Popup(
            title="Синхронизация базы данных",
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=False,
        )

        cancel_flag = {"cancel": False}

        def on_cancel(instance):
            cancel_flag["cancel"] = True
            popup.dismiss()

        def on_complete(instance):
            popup.dismiss()

        close_btn.bind(on_release=on_cancel)

        def sync():
            def progress_callback(percent, message):
                if not cancel_flag["cancel"]:
                    Clock.schedule_once(
                        lambda dt, p=percent: setattr(progress, "value", p), 0
                    )
                    Clock.schedule_once(
                        lambda dt, m=message: setattr(status_label, "text", m), 0
                    )

            def detail_callback(message):
                if not cancel_flag["cancel"]:
                    Clock.schedule_once(
                        lambda dt, m=message: setattr(detail_label, "text", m), 0
                    )

            # Шаг 1: Проверка подключения
            progress_callback(10, "Проверка подключения к серверу...")
            detail_callback("Установка соединения...")

            is_available, message = self.api.check_health()

            if not is_available:

                def show_error(dt):
                    status_label.text = "Ошибка подключения"
                    detail_label.text = message
                    close_btn.text = "Закрыть"
                    close_btn.unbind(on_release=on_cancel)
                    close_btn.bind(on_release=on_complete)

                Clock.schedule_once(show_error, 0)
                return

            # Шаг 2: Синхронизация
            detail_callback("Синхронизация данных...")

            result = self.api.sync_database(self.db_path, progress_callback)

            # Шаг 3: Результат
            def show_result(dt):
                progress.value = 100

                if result.success:
                    status_label.text = "Синхронизация завершена!"
                    detail_text = (
                        f"Отправлено записей: {result.records_sent}\n"
                        f"Получено записей: {result.records_received}"
                    )
                    close_btn.background_color = (0.2, 0.7, 0.3, 1)
                else:
                    status_label.text = "Ошибка синхронизации"
                    detail_text = result.message
                    close_btn.background_color = (0.8, 0.3, 0.3, 1)

                detail_label.text = detail_text
                close_btn.text = "Закрыть"
                close_btn.unbind(on_release=on_cancel)
                close_btn.bind(on_release=on_complete)

            Clock.schedule_once(show_result, 0)

        popup.open()
        threading.Thread(target=sync, daemon=True).start()

    def _create_backup(self):
        """Создание резервной копии базы данных"""
        if not self.db_path.exists():
            return None

        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = self.backup_dir / backup_name

        try:
            shutil.copy2(self.db_path, backup_path)
            print(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Backup error: {e}")
            return None

    def _show_popup(self, title, message):
        """Показать всплывающее окно с сообщением"""
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=message, halign="center"))

        close_btn = Button(
            text="OK", size_hint=(1, 0.3), background_color=(0.3, 0.5, 0.7, 1)
        )
        content.add_widget(close_btn)

        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))

        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def go_to_menu(self):
        """Возврат в главное меню"""
        self.api.close()  # Закрываем сессию API
        if self.manager:
            self.manager.current = "menu"
