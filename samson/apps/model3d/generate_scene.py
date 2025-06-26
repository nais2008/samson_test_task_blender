import argparse
import bpy
import sys
import json
from math import radians
from mathutils import Vector


def add_wall(x1, y1, x2, y2, height=2, thickness=0.1):
    # Преобразуем координаты концов отрезка в вектора
    p1 = Vector((x1, y1))
    p2 = Vector((x2, y2))

    # Определяем направление стенки
    direction = p2 - p1
    normal = direction.normalized()
    right_normal = Vector((-normal.y, normal.x)) * thickness / 2

    # Расчет координат вершин прямоугольника
    vertices = []
    vertices.append(Vector((p1.x + right_normal.x, p1.y + right_normal.y)))
    vertices.append(Vector((p1.x - right_normal.x, p1.y - right_normal.y)))
    vertices.append(Vector((p2.x - right_normal.x, p2.y - right_normal.y)))
    vertices.append(Vector((p2.x + right_normal.x, p2.y + right_normal.y)))

    # Приводим точки к 3D-пространству
    bottom_vertices = [Vector((v.x, v.y, 0)) for v in vertices]
    top_vertices = [Vector((v.x, v.y, height)) for v in vertices]

    # Объединение верхней и нижней части
    all_vertices = bottom_vertices + top_vertices

    # Определение граней
    faces = [
        [0, 1, 2, 3],       # Нижняя грань
        [4, 7, 6, 5],       # Верхняя грань
        [0, 4, 5, 1],       # Левая боковая сторона
        [1, 5, 6, 2],       # Передняя сторона
        [2, 6, 7, 3],       # Правая боковая сторона
        [3, 7, 4, 0],       # Задняя сторона
    ]

    # Создание сетки стены
    mesh = bpy.data.meshes.new("Wall")
    obj = bpy.data.objects.new("Wall", mesh)
    bpy.context.collection.objects.link(obj)

    # Обновление геометрии объекта
    mesh.from_pydata(all_vertices, [], faces)
    mesh.update()


def add_light():
    light_data = bpy.data.lights.new(name="light_2.90", type="SPOT")
    light_data.energy = 3

    light_object = bpy.data.objects.new(name="light_2.90", object_data=light_data)

    bpy.context.collection.objects.link(light_object)

    bpy.context.view_layer.objects.active = light_object

    light_object.location = (3, 3, 10)

    light_object.rotation_euler.rotate_axis("X", radians(-10))
    light_object.rotation_euler.rotate_axis("Y", radians(10))



def main():
    parser = argparse.ArgumentParser(description="Генерация 3D-сцены на основе JSON")
    parser.add_argument("--input", required=True, help="Путь к JSON-файлу сцены")
    parser.add_argument("--output", required=True, help="Путь для сохранения .glb-файла")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])

    bpy.ops.wm.read_factory_settings(use_empty=True)

    with open(args.input, "r", encoding="utf-8") as f:
        scene = json.load(f)[0]

    for light in scene.get("light", []):
        add_light(light)

    bpy.ops.export_scene.gltf(filepath=args.output, export_format="GLB")
    print(f"✅ Экспортировано в {args.output}")


if __name__ == "__main__":
    main()
