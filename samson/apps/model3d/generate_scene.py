import bpy
import sys
import json
import math
import mathutils
import os
import json
import pathlib

BASE_DIR = pathlib.Path(__file__).parent.parent.parent  # Поднимаемся на 3 уровня вверх от generate_scene.py
MEDIA_ROOT = BASE_DIR / 'media'


def get_absolute_media_path(relative_path):
    try:
        clean_path = str(relative_path).lstrip('/').lstrip('\\').replace('./', '').replace('.\\', '')
        abs_path = os.path.join(MEDIA_ROOT, clean_path)

        if os.path.exists(abs_path):
            return abs_path
        return False
    except Exception as e:
        print(f"Ошибка при обработке пути: {e}")
        return False


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def create_textured_material(texture_path):
    material = bpy.data.materials.new(name="CustomTextureMaterial")
    material.use_nodes = True

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    output_node = next(
        (
            n
            for n in nodes
            if isinstance(n, bpy.types.ShaderNodeOutputMaterial)
        ),
        None,
    )
    if output_node:
        nodes.remove(output_node)

    new_output_node = nodes.new(type="ShaderNodeOutputMaterial")

    image_node = nodes.new("ShaderNodeTexImage")
    image_node.image = bpy.data.images.load(texture_path)

    principled_bsdf = nodes.get("Principled BSDF") or nodes.new(
        "ShaderNodeBsdfPrincipled",
    )

    mapping_node = nodes.new("ShaderNodeMapping")
    mapping_node.inputs["Scale"].default_value = (1.0, 1.0, 1.0)

    links.new(
        image_node.outputs["Color"], principled_bsdf.inputs["Base Color"],
    )
    links.new(
        principled_bsdf.outputs["BSDF"], new_output_node.inputs["Surface"],
    )

    return material


def find_room_bounds(walls):
    min_x = min([min(wall["x1"], wall["x2"]) for wall in walls])
    max_x = max([max(wall["x1"], wall["x2"]) for wall in walls])
    min_y = min([min(wall["y1"], wall["y2"]) for wall in walls])
    max_y = max([max(wall["y1"], wall["y2"]) for wall in walls])
    return (min_x, max_x, min_y, max_y)


def add_floor(min_x, max_x, min_y, max_y, floor_height=-0.1):
    vertices = [
        mathutils.Vector((min_x, min_y, floor_height)),
        mathutils.Vector((max_x, min_y, floor_height)),
        mathutils.Vector((max_x, max_y, floor_height)),
        mathutils.Vector((min_x, max_y, floor_height)),
    ]

    faces = [[0, 1, 2, 3]]

    mesh = bpy.data.meshes.new("FloorMesh")
    obj = bpy.data.objects.new("FloorObject", mesh)
    bpy.context.collection.objects.link(obj)

    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    uvs = []
    for vertex_idx in range(len(vertices)):
        u = (vertices[vertex_idx][0] - min_x) / (max_x - min_x)
        v = (vertices[vertex_idx][1] - min_y) / (max_y - min_y)
        uvs.append((u, v))

    face_uv_data = [(uvs[i], i) for i in range(4)]

    uv_layer = mesh.uv_layers.new(do_init=True)
    for loop_idx, (uv_coord, _) in enumerate(face_uv_data):
        uv_layer.data[loop_idx].uv = uv_coord

    return obj


def add_wall(x1, y1, x2, y2, height=5, thickness=0.2, texture_path=None):
    p1 = mathutils.Vector((x1, y1))
    p2 = mathutils.Vector((x2, y2))

    direction = p2 - p1
    length = direction.length
    normal = direction.normalized()
    right_normal = mathutils.Vector((-normal.y, normal.x)) * thickness / 2

    vertices = [
        mathutils.Vector((p1.x + right_normal.x, p1.y + right_normal.y, 0)),
        mathutils.Vector((p1.x - right_normal.x, p1.y - right_normal.y, 0)),
        mathutils.Vector((p2.x - right_normal.x, p2.y - right_normal.y, 0)),
        mathutils.Vector((p2.x + right_normal.x, p2.y + right_normal.y, 0)),
        mathutils.Vector((p1.x + right_normal.x, p1.y + right_normal.y, height)),
        mathutils.Vector((p1.x - right_normal.x, p1.y - right_normal.y, height)),
        mathutils.Vector((p2.x - right_normal.x, p2.y - right_normal.y, height)),
        mathutils.Vector((p2.x + right_normal.x, p2.y + right_normal.y, height)),
    ]

    faces = [
        [0, 1, 2, 3],
        [4, 7, 6, 5],
        [0, 4, 5, 1],
        [1, 5, 6, 2],
        [2, 6, 7, 3],
        [3, 7, 4, 0],
    ]

    mesh = bpy.data.meshes.new("Wall")
    obj = bpy.data.objects.new("Wall", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(vertices, [], faces)

    mesh.uv_layers.new(name="UVMap")
    uv_layer = mesh.uv_layers.active.data

    for poly in mesh.polygons:
        for loop_index in range(
            poly.loop_start, poly.loop_start + poly.loop_total
        ):
            vert_index = mesh.loops[loop_index].vertex_index
            vertex = vertices[vert_index]

            if poly.index in [0, 1]:
                u = (vertex.x - p1.x) / length
                v = (vertex.y - p1.y) / thickness
            else:
                if abs(normal.x) > abs(normal.y):
                    u = vertex.x / length
                else:
                    u = vertex.y / length
                v = vertex.z / height

            uv_layer[loop_index].uv = (u, v)

    texture = get_absolute_media_path(texture_path)

    if texture:
        material = create_textured_material(texture)
        obj.data.materials.append(material)
    else:
        print(f"Texture file not found: {texture_path}")
        material = bpy.data.materials.new(name="WallMaterial")
        material.diffuse_color = (0.8, 0.8, 0.8, 1)
        obj.data.materials.append(material)

    mesh.update()
    return obj


def add_light(light_data):
    light = bpy.data.lights.new(name="Light", type='POINT')
    light.energy = 1000
    light.color = (1.0, 1.0, 1.0)

    light_obj = bpy.data.objects.new(name="Light", object_data=light)
    light_obj.location = (
        light_data['cordinate']['x'],
        light_data['cordinate']['y'],
        light_data['cordinate']['z']
    )
    light_obj.rotation_euler = (
        math.radians(light_data['rotate']['x']),
        math.radians(light_data['rotate']['y']),
        math.radians(light_data['rotate']['z'])
    )

    bpy.context.collection.objects.link(light_obj)
    return light_obj


def load_and_place_model(url, coordinates):
    filepath = get_absolute_media_path(url)

    try:
        selected_before_import = set(bpy.context.selected_objects)

        bpy.ops.import_scene.gltf(filepath=filepath)

        new_objects = list(
            set(bpy.context.selected_objects).difference(
                selected_before_import
            )
        )

        if len(new_objects) > 0:
            root_obj = new_objects[0]

            rotate_value = math.radians(coordinates.get("rotate", 0))
            rotation_matrix = mathutils.Matrix.Rotation(rotate_value, 4, "Z")
            root_obj.matrix_world @= rotation_matrix

            x, y, z = (
                coordinates.get("x", 0),
                coordinates.get("y", 0),
                coordinates.get("z", 0),
            )
            root_obj.location = (x, y, z)

            return True
        else:
            print("Нет новых объектов после импорта")
            return False

    except Exception as e:
        print(f"Ошибка при импорте модели: {e}")
        return False


def export_scene(output_path):
    try:
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            export_format='GLB',
            export_cameras=True,
            export_lights=True
        )
        return True
    except Exception as e:
        print(f"Export error: {e}")
        return False


def generate_from_json(json_path, output_path):
    try:
        with open(json_path) as f:
            data = json.load(f)

        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        else:
            print("Ошибка: JSON должен быть массивом с хотя бы одним элементом")
            return False

        clear_scene()

        if 'objects' in data:
            for obj in data['objects']:
                if 'url' in obj and 'coordinates' in obj:
                    load_and_place_model(obj['url'], obj['coordinates'])

        if 'room' in data and 'contour' in data['room']:
            for wall in data['room']['contour']:
                texture_path = wall.get('texture')

                add_wall(
                    wall['x1'], wall['y1'], wall['x2'], wall['y2'],
                    height=5,
                    texture_path=texture_path
                )

        if 'light' in data:
            for light in data['light']:
                if 'cordinate' in light:
                    light_data = {
                        'cordinate': light['cordinate'],
                        'rotate': light['cordinate'].get('rotate', {'x': 0, 'y': 0, 'z': 0})
                    }
                    add_light(light_data)

        if 'room' in data and 'contour' in data['room']:
            room_bounds = find_room_bounds(data['room']['contour'])
            min_x, max_x, min_y, max_y = room_bounds

            if 'floor' in data:
                floor = add_floor(min_x, max_x, min_y, max_y)
                floor_texture = get_absolute_media_path(data['floor'])
                if floor_texture:
                    custom_material = create_textured_material(floor_texture)
                    floor.data.materials.clear()
                    floor.data.materials.append(custom_material)
                else:
                    print(f"Текстура пола не найдена: {data['floor']}")

        return export_scene(output_path)

    except Exception as e:
        print(f"Ошибка генерации: {e}")
        return False


def main():
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        if len(args) == 2:
            generate_from_json(args[0], args[1])
        else:
            print("Usage: blender --python script.py -- input.json output.glb")
    else:
        print("Please use blender --python script.py -- input.json output.glb")


if __name__ == "__main__":
    main()
