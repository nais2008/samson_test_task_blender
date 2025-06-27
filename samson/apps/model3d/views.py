import json
import logging
import os
import pathlib
import subprocess
import tempfile

import django.core.files
import django.http
import django.views.decorators.csrf
import django.views.decorators.http

import apps.model3d.models

__all__ = ["generate_3d_scene"]

logger = logging.getLogger(__name__)


@django.views.decorators.http.require_POST
@django.views.decorators.csrf.csrf_exempt
def generate_3d_scene(request):
    try:
        json_data = request.body.decode("utf-8")
        data = json.loads(json_data)

        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".json", delete=False,
        ) as tmp_json:
            json.dump(data, tmp_json)
            tmp_json_path = tmp_json.name

        model_3d = apps.model3d.models.Model3D()

        with pathlib.Path.open(tmp_json_path, "rb") as f:
            model_3d.json_data.save(
                f"scene_{model_3d.id}.json", django.core.files.File(f),
            )

        with tempfile.NamedTemporaryFile(
            suffix=".glb", delete=False,
        ) as tmp_glb:
            output_path = tmp_glb.name

        current_dir = pathlib.Path(__file__).parent
        blender_script_path = str(current_dir / "generate_scene.py")

        blender_cmd = [
            django.conf.settings.BLENDER_PATH,
            "--background",
            "--python",
            blender_script_path,
            "--",
            tmp_json_path,
            output_path,
        ]

        try:
            subprocess.run(
                blender_cmd, capture_output=True, text=True, check=True,
            )

            if (
                not os.path.exists(output_path)
                or os.path.getsize(output_path) == 0
            ):
                raise Exception(
                    "Blender не создал выходной файл или файл пуст",
                )

            with pathlib.Path.open(output_path, "rb") as f:
                model_3d.scene_file.save(
                    f"scene_{model_3d.id}.glb", django.core.files.File(f),
                )

            model_3d.save()

            response_data = {
                "status": "success",
                "model_id": model_3d.id,
                "scene_file_url": model_3d.scene_file.url,
            }

            return django.http.JsonResponse(response_data, status=201)

        except subprocess.CalledProcessError as e:
            logger.error(f"Blender process failed: {e.stderr}")
            return django.http.JsonResponse(
                {
                    "status": "error",
                    "message": "Ошибка генерации 3D-сцены",
                    "details": e.stderr,
                },
                status=500,
            )

        except Exception as e:
            logger.error(f"Scene generation error: {str(e)}")
            return django.http.JsonResponse(
                {"status": "error", "message": str(e)}, status=500,
            )

        finally:
            try:
                os.unlink(tmp_json_path)
            except BaseException:
                pass

            try:
                os.unlink(output_path)
            except BaseException:
                pass

    except json.JSONDecodeError:
        return django.http.JsonResponse(
            {"status": "error", "message": "Невалидный JSON"}, status=400,
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return django.http.JsonResponse(
            {"status": "error", "message": "Внутренняя ошибка сервера"},
            status=500,
        )
