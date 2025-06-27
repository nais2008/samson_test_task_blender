import django.apps

__all__ = ["Model3DConfig"]


class Model3DConfig(django.apps.AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.model3d"
    verbose_name = "model"
