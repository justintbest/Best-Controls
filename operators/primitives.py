import bpy


class OBJECT_OT_add_single_vertex(bpy.types.Operator):
    bl_idname = "object.add_single_vertex"
    bl_label = "Add Vertex"
    bl_description = "Add a vertex at the 3D cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh = bpy.data.meshes.new("Vertex")
        mesh.from_pydata([(0, 0, 0)], [], [])
        mesh.update()
        obj = bpy.data.objects.new("Vertex", mesh)
        obj.location = context.scene.cursor.location.copy()
        context.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {'FINISHED'}


class OBJECT_OT_add_single_plane(bpy.types.Operator):
    bl_idname = "object.add_single_plane"
    bl_label = "Add Plane"
    bl_description = "Add a plane at the 3D cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(location=context.scene.cursor.location)
        return {'FINISHED'}


class OBJECT_OT_add_single_cube(bpy.types.Operator):
    bl_idname = "object.add_single_cube"
    bl_label = "Add Cube"
    bl_description = "Add a cube at the 3D cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(location=context.scene.cursor.location)
        return {'FINISHED'}


class OBJECT_OT_add_gp_stroke(bpy.types.Operator):
    bl_idname = "object.add_gp_stroke"
    bl_label = "Add Grease Pencil"
    bl_description = "Add a 2m straight grease pencil stroke centered on the 3D cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        gp_data = bpy.data.grease_pencils.new("GPStroke")
        gp_obj = bpy.data.objects.new("GPStroke", gp_data)
        gp_obj.location = context.scene.cursor.location.copy()
        context.collection.objects.link(gp_obj)

        mat = bpy.data.materials.new("GP Black")
        bpy.data.materials.create_gpencil_data(mat)
        mat.grease_pencil.show_stroke = True
        mat.grease_pencil.color = (0.0, 0.0, 0.0, 1.0)
        mat.grease_pencil.show_fill = False
        gp_data.materials.append(mat)

        layer = gp_data.layers.new("Layer")
        frame = layer.frames.new(context.scene.frame_current)

        if bpy.app.version >= (4, 3, 0):
            # GP v3 API (Blender 4.3+)
            drawing = frame.drawing
            drawing.add_strokes([2])
            stroke = drawing.strokes[0]
            stroke.material_index = 0
            stroke.points[0].position = (-1.0, 0.0, 0.0)
            stroke.points[1].position = (1.0, 0.0, 0.0)
        else:
            # GP v2 API (Blender < 4.3)
            stroke = frame.strokes.new()
            stroke.display_mode = '3DSPACE'
            stroke.points.add(count=2)
            stroke.points[0].co = (-1.0, 0.0, 0.0)
            stroke.points[1].co = (1.0, 0.0, 0.0)

        bpy.ops.object.select_all(action='DESELECT')
        gp_obj.select_set(True)
        context.view_layer.objects.active = gp_obj
        return {'FINISHED'}
