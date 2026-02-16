from django.db import models


class SiteSetting(models.Model):
    SETTING_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Text Area'),
        ('image', 'Image'),
        ('boolean', 'Boolean'),
        ('number', 'Number'),
    ]

    key = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=SETTING_TYPES, default='text')
    value = models.TextField(blank=True)
    image = models.ImageField(upload_to='settings/%Y/%m/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки'

    def __str__(self):
        return f"{self.name} ({self.key})"

    def get_value(self):
        if self.type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.type == 'number':
            try:
                return float(self.value)
            except ValueError:
                return 0
        elif self.type == 'image':
            return self.image.url if self.image else None
        return self.value