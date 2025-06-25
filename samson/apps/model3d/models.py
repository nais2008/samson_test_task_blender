import django.db.models

__all__ = []


class Model3D(django.db.models.Model):
    created_at = django.db.models.DateTimeField(
        "created at",
        help_text="date and time create",
        auto_now_add=True,
    )
    json_data = django.db.models.JSONField(
        "data json",
        default="[]",
    )
    scene_file = django.db.models.FileField(
        "scene file",
        help_text="scene file path",
        upload_to="3d_models/",
    )

    def __str__(self):
        if len(self.scene_file) > 25:
            return f"{self.scene_file[:25]}..."

        return self.scene_file


class LightType(django.db.models.Model):
    class TypeLight(django.db.models.TextChoices):
        POINT = "point light", "точечный свет"
        SPOT = "spot light", "прожектор"
        SUN = "sun light", "солнечный свет"
        AREA = "area light", "плоский свет"

    type_light = django.db.models.CharField(
        "type light",
        help_text="type light in scene",
        choices=TypeLight.choices,
        default=TypeLight.POINT,
        max_length=150,
    )


class Texture(django.db.models.Model):
    texture_path = django.db.models.ImageField(
        "texture path",
        help_text="path to texture",
        upload_to="texture/",
    )
