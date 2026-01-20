from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from random import choice
import requests
from datetime import datetime
from kivy.graphics import Color, Rectangle

API_KEY = "bbc75e5ff6f517935e16293103ded9dc"

class WeatherApp(App):
    city = "Jakarta"
    current_temp_display = None

    def build(self):
        self.root = Builder.load_file("weather.kv")

        # Dropdown menu
        self.menu_dropdown = DropDown()
        for screen_name in ["dashboard","stats"]:
            btn = Button(text=screen_name.capitalize(), size_hint_y=None, height=dp(40))
            btn.bind(on_release=self.get_menu_callback(screen_name))
            self.menu_dropdown.add_widget(btn)

        # Background rectangle dinamis
        self.dashboard = self.root.get_screen("dashboard")
        with self.dashboard.canvas.before:
            self.bg_color = Color(0.1,0.2,0.3,1)
            self.bg_rect = Rectangle(pos=self.dashboard.pos, size=self.dashboard.size)
        self.dashboard.bind(size=self.update_bg_rect, pos=self.update_bg_rect)

        return self.root

    def update_bg_rect(self, *args):
        self.bg_rect.pos = self.dashboard.pos
        self.bg_rect.size = self.dashboard.size

    def get_menu_callback(self, screen_name):
        def callback(instance):
            self.root.current = screen_name
            self.menu_dropdown.dismiss()
            self.refresh()
        return callback

    def search_city(self):
        city_input = self.dashboard.ids.city_input
        city = city_input.text.strip()
        if city:
            self.city = city
            self.refresh()
            city_input.text = ""

    def on_start(self):
        Clock.schedule_interval(self.animate_temp, 5)
        Clock.schedule_once(lambda dt: self.refresh(), 1)
        Clock.schedule_interval(lambda dt: self.update_time(), 1)
        Clock.schedule_interval(lambda dt: self.update_background(), 60)

    def update_time(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.dashboard.ids.time_label.text = f"Jam: {now}"

    def update_background(self):
        desc = self.dashboard.ids.desc.text.lower()
        if "hujan" in desc:
            self.bg_color.rgba = (0.1,0.1,0.3,1)
        elif "berawan" in desc:
            self.bg_color.rgba = (0.3,0.3,0.4,1)
        else:
            self.bg_color.rgba = (0.1,0.5,0.8,1)

    def refresh(self):
        self.get_weather()
        self.get_forecast()
        self.get_hourly_forecast()
        self.update_stats()

    def get_weather(self):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={API_KEY}&units=metric&lang=id"
            data = requests.get(url, timeout=10).json()
            if data.get("cod") != 200:
                self.dashboard.ids.city.text = self.city
                self.dashboard.ids.temp.text = "-- °C"
                self.dashboard.ids.desc.text = "Kota tidak tersedia"
                self.set_default_stats()
                return

            temp = int(data["main"]["temp"])
            desc = data["weather"][0]["description"].capitalize()
            humidity = data["main"]["humidity"]
            pressure = data["main"]["pressure"]
            wind_speed = data["wind"]["speed"]

            self.dashboard.ids.city.text = self.city
            self.dashboard.ids.temp.text = f"{temp} °C"
            self.dashboard.ids.desc.text = desc

            # Statistik
            self.stat_temp = temp
            self.stat_pressure = pressure
            self.stat_humidity = humidity
            self.stat_wind = wind_speed

            # Tips bencana sederhana
            if "hujan" in desc.lower():
                self.disaster_health = "Tetap di rumah saat hujan deras"
                self.disaster_flood = "Siapkan perahu darurat"
                self.disaster_wave = "Jangan berenang saat laut bergelombang tinggi"
            elif "petir" in desc.lower():
                self.disaster_health = "Hindari penggunaan listrik berlebihan"
                self.disaster_flood = "Siapkan tempat aman untuk evakuasi"
                self.disaster_wave = "Tidak aman di luar rumah"
            else:
                self.disaster_health = "Cuaca normal"
                self.disaster_flood = "Risiko banjir rendah"
                self.disaster_wave = "Laut tenang"

        except:
            self.set_default_stats()

    def set_default_stats(self):
        self.stat_temp=self.stat_pressure=self.stat_humidity=self.stat_wind=0
        self.disaster_health=self.disaster_flood=self.disaster_wave="Data tidak tersedia"

    def get_forecast(self):
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={self.city}&appid={API_KEY}&units=metric&lang=id"
            data = requests.get(url, timeout=10).json()
            if data.get("cod") != "200": return

            box = self.dashboard.ids.forecast_box
            box.clear_widgets()
            used = set()
            for item in data["list"]:
                date = item["dt_txt"].split(" ")[0]
                if date in used: continue
                used.add(date)

                day = datetime.strptime(date,"%Y-%m-%d").strftime("%a %d/%m")
                temp = int(item["main"]["temp"])
                weather_main = item["weather"][0]["main"].lower()

                if "rain" in weather_main:
                    condition = "Hujan"
                elif "thunderstorm" in weather_main:
                    condition = "Hujan Petir"
                elif "cloud" in weather_main:
                    condition = "Berawan"
                else:
                    condition = "Cerah"

                row = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(80), padding=dp(5))
                row.add_widget(Label(text=day, font_size="14sp", color=(1,1,1,1), size_hint_y=None, height=dp(20)))
                row.add_widget(Label(text=f"{temp}°C", color=(1,1,1,1), font_size="14sp"))
                row.add_widget(Label(text=condition, color=(1,1,0.6,1), font_size="12sp"))
                box.add_widget(row)

                if len(used) == 5: break
        except:
            pass

    def get_hourly_forecast(self):
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={self.city}&appid={API_KEY}&units=metric&lang=id"
            data = requests.get(url, timeout=10).json()
            if data.get("cod") != "200": return

            box = self.dashboard.ids.hourly_box
            box.clear_widgets()
            today = datetime.now().strftime("%Y-%m-%d")

            for item in data["list"]:
                date, time_str = item["dt_txt"].split(" ")
                if date != today: continue

                temp = int(item["main"]["temp"])
                weather_main = item["weather"][0]["main"].lower()
                if "rain" in weather_main:
                    condition = "Hujan"
                elif "thunderstorm" in weather_main:
                    condition = "Hujan Petir"
                elif "cloud" in weather_main:
                    condition = "Berawan"
                else:
                    condition = "Cerah"

                row = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(60), padding=dp(5))
                row.add_widget(Label(text=time_str[:5], font_size="12sp", color=(1,1,1,1), size_hint_y=None, height=dp(15)))
                row.add_widget(Label(text=f"{temp}°C", color=(1,1,1,1), font_size="12sp"))
                row.add_widget(Label(text=condition, color=(1,1,0.6,1), font_size="10sp"))
                box.add_widget(row)

        except:
            pass

    def update_stats(self):
        stats = self.root.get_screen("stats")
        stats.ids.stat_temp.text = f"Suhu Udara: {self.stat_temp} °C"
        stats.ids.stat_pressure.text = f"Tekanan Udara: {self.stat_pressure} hPa"
        stats.ids.stat_humidity.text = f"Kelembapan Udara: {self.stat_humidity} %"
        stats.ids.stat_wind.text = f"Angin: {self.stat_wind} m/s"
        stats.ids.disaster_health.text = f"Tips Kesehatan: {self.disaster_health}"
        stats.ids.disaster_flood.text = f"Tips Banjir: {self.disaster_flood}"
        stats.ids.disaster_wave.text = f"Tips Gelombang: {self.disaster_wave}"

    def animate_temp(self, dt):
        dashboard = self.dashboard
        if hasattr(self, 'stat_temp') and self.stat_temp is not None:
            if self.current_temp_display is None:
                self.current_temp_display = self.stat_temp
            change = choice([-1,0,1])
            self.current_temp_display += change
            dashboard.ids.temp.text = f"{self.current_temp_display} °C"


if __name__=="__main__":
    WeatherApp().run()
