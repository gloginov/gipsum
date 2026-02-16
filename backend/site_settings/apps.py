from django.apps import AppConfig

class SiteSettingsConfig(AppConfig):  # Имя класса изменено
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'site_settings'  # Без apps. и без конфликта со встроенным settings
    verbose_name = 'Настройки сайта'