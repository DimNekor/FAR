from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse, Line, Mesh
from kivy.properties import NumericProperty, ListProperty
from kivy.core.window import Window
import math
import random

from client.desktop.views import load_view_kv

load_view_kv("menu.kv")


class MenuScreen(Screen):
    time = NumericProperty(0)
    mouse_pos = ListProperty([0, 0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.neurons = []
        self.sparks = []
        self.signal_particles = []

        self._create_brain()
        self._setup_graphics()

        Clock.schedule_interval(self.update_animation, 1 / 60.0)
        Window.bind(mouse_pos=self._on_mouse_move)

        self.buttons = []
        self.button_hover_states = {}

    def on_kv_post(self, base_widget):
        self.buttons = [
            self.ids.btn_survey,
            self.ids.btn_results,
            self.ids.btn_settings,
        ]

        self.button_normal_colors = {
            self.ids.btn_survey: (0.15, 0.55, 0.8, 1),
            self.ids.btn_results: (0.25, 0.5, 0.7, 1),
            self.ids.btn_settings: (0.33, 0.43, 0.6, 1),
        }

        self.button_hover_colors = {
            self.ids.btn_survey: (0.22, 0.68, 0.92, 1),
            self.ids.btn_results: (0.32, 0.62, 0.82, 1),
            self.ids.btn_settings: (0.4, 0.52, 0.72, 1),
        }

    def _on_mouse_move(self, window, pos):
        self.mouse_pos = pos

        if hasattr(self, "button_color_refs"):
            for btn in self.buttons:
                if btn.collide_point(*pos):
                    # Hover
                    self.button_color_refs[btn].rgba = self.button_hover_colors[btn]
                else:
                    # Normal
                    self.button_color_refs[btn].rgba = self.button_normal_colors[btn]

    def _create_brain(self):
        # Создаем нейроны в форме мозга
        for _ in range(80):
            # Распределение в форме мозга с извилинами
            angle = random.uniform(0, 2 * math.pi)

            # Сложная форма мозга
            if random.random() < 0.5:
                # Левое полушарие
                base_x = -0.1
            else:
                # Правое полушарие
                base_x = 0.1

            # Добавляем извилины
            r_var = random.uniform(0.6, 1.0)

            # Разные слои мозга
            layer = random.choice(["outer", "middle", "inner"])
            if layer == "outer":
                radius = 0.55 * r_var
                color_base = (0.2, 0.5, 0.9)
            elif layer == "middle":
                radius = 0.35 * r_var
                color_base = (0.3, 0.6, 1.0)
            else:
                radius = 0.25 * r_var
                color_base = (0.4, 0.7, 1.0)

            x = 0.5 + base_x + radius * math.cos(angle)
            y = 0.5 + radius * math.sin(angle) * 0.8

            neuron = {
                "x": x,
                "y": y,
                "base_x": x,
                "base_y": y,
                "size": random.uniform(6, 12),
                "phase": random.uniform(0, 2 * math.pi),
                "activation": 0,
                "target_activation": 0,
                "color_base": color_base,
                "connections": [],
                "pulse_speed": random.uniform(1, 3),
            }
            self.neurons.append(neuron)

        # Создаем связи между близкими нейронами
        for i, n1 in enumerate(self.neurons):
            for j, n2 in enumerate(self.neurons):
                if i < j:
                    dist = math.sqrt(
                        (n1["x"] - n2["x"]) ** 2 + (n1["y"] - n2["y"]) ** 2
                    )
                    if dist < 0.1:
                        n1["connections"].append(j)

    def _setup_graphics(self):
        with self.canvas.before:
            self.conn_colors = []
            self.conn_lines = []
            for n1 in self.neurons:
                for _ in n1["connections"]:
                    col = Color(0.3, 0.5, 0.8, 0.2)
                    line = Line(points=[0, 0, 0, 0], width=1.5)
                    self.conn_colors.append(col)
                    self.conn_lines.append(line)

            # Нейроны
            self.neuron_colors = []
            self.neuron_shapes = []
            for neuron in self.neurons:
                col = Color(*neuron["color_base"], 0.8)
                ellipse = Ellipse()
                self.neuron_colors.append(col)
                self.neuron_shapes.append(ellipse)

            # Искры
            self.spark_colors = []
            self.spark_shapes = []
            for _ in range(40):
                col = Color(1, 1, 1, 0)
                ellipse = Ellipse()
                self.spark_colors.append(col)
                self.spark_shapes.append(ellipse)

            # Сигнальные частицы на связях
            self.signal_colors = []
            self.signal_shapes = []
            for _ in range(20):
                col = Color(1, 1, 1, 0)
                ellipse = Ellipse()
                self.signal_colors.append(col)
                self.signal_shapes.append(ellipse)

        self.bind(size=self._update_size)

        # Сохраняем ссылки на цвета кнопок ПОСЛЕ загрузки kv
        Clock.schedule_once(self._init_button_colors, 0.2)

    def _init_button_colors(self, dt):
        self.buttons = [
            self.ids.btn_survey,
            self.ids.btn_results,
            self.ids.btn_settings,
        ]

        self.button_color_refs = {}
        self.button_normal_colors = {
            self.ids.btn_survey: (0.15, 0.55, 0.8, 1),
            self.ids.btn_results: (0.25, 0.5, 0.7, 1),
            self.ids.btn_settings: (0.33, 0.43, 0.6, 1),
        }
        self.button_hover_colors = {
            self.ids.btn_survey: (0.25, 0.7, 0.95, 1),
            self.ids.btn_results: (0.35, 0.65, 0.85, 1),
            self.ids.btn_settings: (0.45, 0.55, 0.75, 1),
        }

        for btn in self.buttons:
            # Ищем основной Color в canvas.before (второй Color, после тени)
            color_count = 0
            for child in btn.canvas.before.children:
                if isinstance(child, Color):
                    color_count += 1
                    if (
                        color_count == 2
                    ):  # Основной цвет (первый - тень, второй - основной, третий - блик)
                        self.button_color_refs[btn] = child
                        break

    def _update_size(self, *args):
        pass

    def update_animation(self, dt):
        if self.width <= 0 or self.height <= 0:
            return
            
        self.time += dt
        t = self.time

        w, h = self.width, self.height

        # Мышь
        mx = self.mouse_pos[0] / w if w > 0 else 0.5
        my = self.mouse_pos[1] / h if h > 0 else 0.5

        breath = math.sin(t * 0.4) * 0.02
        sway = math.cos(t * 0.3) * 0.01

        # Обновляем нейроны
        conn_idx = 0
        for i, neuron in enumerate(self.neurons):
            dx = (neuron["base_x"] - 0.5) * breath
            dy = (neuron["base_y"] - 0.5) * breath
            wave_x = math.sin(t * 0.5 + neuron["base_y"] * 5) * 0.01
            wave_y = math.cos(t * 0.6 + neuron["base_x"] * 5) * 0.01

            neuron["x"] = neuron["base_x"] + dx + wave_x + sway
            neuron["y"] = neuron["base_y"] + dy + wave_y

            # Активация от мыши
            dist = math.sqrt((mx - neuron["x"]) ** 2 + (my - neuron["y"]) ** 2)
            if dist < 0.2:
                neuron["target_activation"] = 1 - (dist / 0.2)
            else:
                neuron["target_activation"] = 0

            # Плавное изменение активации
            neuron["activation"] += (
                (neuron["target_activation"] - neuron["activation"]) * dt * 8
            )

            # Размер нейрона с пульсацией
            pulse = math.sin(t * neuron["pulse_speed"] + neuron["phase"]) * 0.3
            size = neuron["size"] * (1 + pulse + neuron["activation"] * 0.8)

            px = neuron["x"] * w
            py = neuron["y"] * h

            # Проверка на валидность позиции и размера
            if size > 0 and w > 0 and h > 0:
                self.neuron_shapes[i].pos = (px - size / 2, py - size / 2)
                self.neuron_shapes[i].size = (size, size)

            # Цвет нейрона при активации
            base = neuron["color_base"]
            activation_glow = neuron["activation"]
            color = (
                min(1, base[0] + activation_glow * 0.6),
                min(1, base[1] + activation_glow * 0.4),
                min(1, base[2]),
            )
            self.neuron_colors[i].rgb = color
            self.neuron_colors[i].a = max(0, min(1, 0.6 + activation_glow * 0.4))  # Защита альфа-канала

            # Создаем искры при сильной активации
            if neuron["activation"] > 0.6:
                if random.random() < 0.3:
                    spark = {
                        "x": px,
                        "y": py,
                        "vx": random.uniform(-100, 100),
                        "vy": random.uniform(-100, 100),
                        "life": 0,
                        "max_life": random.uniform(0.3, 0.8),
                        "size": random.uniform(2, 5),
                        "color": random.choice(
                            [(1, 0.8, 0.2), (0.2, 0.8, 1), (1, 0.4, 0.6), (0.6, 1, 0.3)]
                        ),
                    }
                    self.sparks.append(spark)

            for j in neuron["connections"]:
                if j < len(self.neurons): 
                    target = self.neurons[j]

                    # Сигнал по связи
                    signal = (neuron["activation"] + target["activation"]) / 2
                    wave_signal = (math.sin(t * 4 + i * 0.1 + j * 0.1) + 1) / 2

                    x1 = neuron["x"] * w
                    y1 = neuron["y"] * h
                    x2 = target["x"] * w
                    y2 = target["y"] * h

                    if conn_idx < len(self.conn_lines):
                        self.conn_lines[conn_idx].points = [x1, y1, x2, y2]
                        
                        new_width = 1 + signal * 2
                        self.conn_lines[conn_idx].width = max(0.5, new_width)
                        
                        # Защита альфа-канала
                        alpha = max(0, min(1, 0.15 + signal * 0.5 * wave_signal))
                        self.conn_colors[conn_idx].a = alpha

                    conn_idx += 1

        # Обновляем искры с защитой от удаления во время итерации
        sparks_to_remove = []
        for spark in self.sparks:
            spark["life"] += dt
            spark["x"] += spark["vx"] * dt
            spark["y"] += spark["vy"] * dt
            spark["vy"] -= 50 * dt 

            if spark["life"] > spark["max_life"]:
                sparks_to_remove.append(spark)
        
        for spark in sparks_to_remove:
            if spark in self.sparks:
                self.sparks.remove(spark)

        # Отрисовываем искры 
        for i in range(min(40, len(self.spark_shapes))):
            if i < len(self.sparks):
                spark = self.sparks[i]
                progress = max(0, min(1, spark["life"] / spark["max_life"])) 
                alpha = 1 - progress
                size = max(0.1, spark["size"] * (1 - progress * 0.5))

                if size > 0:
                    self.spark_shapes[i].pos = (
                        spark["x"] - size / 2,
                        spark["y"] - size / 2,
                    )
                    self.spark_shapes[i].size = (size, size)
                self.spark_colors[i].rgb = spark["color"]
                self.spark_colors[i].a = max(0, min(1, alpha)) 
            else:
                self.spark_colors[i].a = 0

        # Создаем сигнальные частицы на связях
        self.signal_particles = []
        for neuron in self.neurons:
            for j in neuron["connections"]:
                if j < len(self.neurons) and random.random() < 0.05:
                    target = self.neurons[j]
                    progress = random.random()
                    x = neuron["x"] + (target["x"] - neuron["x"]) * progress
                    y = neuron["y"] + (target["y"] - neuron["y"]) * progress

                    self.signal_particles.append(
                        {
                            "x": x * w,
                            "y": y * h,
                            "life": 0,
                            "max_life": random.uniform(0.5, 1.5),
                            "size": random.uniform(2, 4),
                        }
                    )

        # Обновляем сигнальные частицы
        particles_to_remove = []
        for particle in self.signal_particles:
            particle["life"] += dt
            if particle["life"] > particle["max_life"]:
                particles_to_remove.append(particle)
        
        for particle in particles_to_remove:
            if particle in self.signal_particles:
                self.signal_particles.remove(particle)

        # Отрисовываем сигнальные частицы 
        for i in range(min(20, len(self.signal_shapes))):
            if i < len(self.signal_particles):
                particle = self.signal_particles[i]
                max_life = max(0.001, particle["max_life"])  
                alpha = 1 - (particle["life"] / max_life)
                size = max(0.1, particle["size"] * alpha)  

                if size > 0:
                    self.signal_shapes[i].pos = (
                        particle["x"] - size / 2,
                        particle["y"] - size / 2,
                    )
                    self.signal_shapes[i].size = (size, size)
                self.signal_colors[i].rgba = (0.6, 0.9, 1, max(0, min(1, alpha)))
            else:
                self.signal_colors[i].a = 0

    def go_to_survey(self):
        self.manager.current = "survey"

    def go_to_results(self):
        self.manager.current = "results"

    def go_to_settings(self):
        self.manager.current = "settings"
