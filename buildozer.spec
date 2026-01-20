[app]
title = WeatherApp
package.name = weatherapp
package.domain = org.vanz

source.dir = .
source.include_exts = py,kv,png,jpg

version = 0.1
requirements = python3,kivy,requests
orientation = portrait
android.permissions = INTERNET

[buildozer]
log_level = 2

[android]
android.api = 33
android.minapi = 21
android.ndk = 25b
android.skip_update = True
