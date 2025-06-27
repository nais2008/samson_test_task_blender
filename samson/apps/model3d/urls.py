import django.urls

import apps.model3d.views

app_name = "model3d"

urlpatterns = [
    django.urls.path(
        "generate-scene/",
        apps.model3d.views.generate_3d_scene,
        name="generate-scane",
    )
]

