import bpy
import bmesh


class OBJECT_OT_add_decimate_modifier(bpy.types.Operator):
    bl_idname = "object.add_decimate_modifier"
    bl_label = "Add Decimate Modifier"
    bl_description = "Add a Decimate modifier to the active object with the given ratio"
    bl_options = {'REGISTER', 'UNDO'}

    ratio: bpy.props.FloatProperty(name="Ratio", default=0.5, min=0.0, max=1.0)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        mod = context.active_object.modifiers.new(name="Decimate", type='DECIMATE')
        mod.ratio = self.ratio
        return {'FINISHED'}


class OBJECT_OT_flip_x(bpy.types.Operator):
    bl_idname = "object.flip_x"
    bl_label = "Flip X"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            obj.scale.x *= -1
        return {'FINISHED'}


class OBJECT_OT_flip_camera_x(bpy.types.Operator):
    bl_idname = "object.flip_camera_x"
    bl_label = "Flip Camera X"
    bl_description = "Flip the X scale of the active scene camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None

    def execute(self, context):
        cam = context.scene.camera
        cam.scale.x *= -1
        return {'FINISHED'}


class OBJECT_OT_gp_to_mesh(bpy.types.Operator):
    bl_idname = "object.gp_to_mesh"
    bl_label = "GP to Mesh"
    bl_description = "Convert all Grease Pencil strokes to a single mesh object and delete the GP object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'GPENCIL'

    def execute(self, context):
        gp_obj = context.active_object
        world_matrix = gp_obj.matrix_world
        gp_collections = list(gp_obj.users_collection)

        bm = bmesh.new()
        stroke_count = 0

        for layer in gp_obj.data.layers:
            frame = layer.active_frame
            if frame is None:
                continue

            for stroke in frame.strokes:
                pts = stroke.points
                if len(pts) < 2:
                    continue

                verts = [bm.verts.new(p.co) for p in pts]

                for j in range(len(verts) - 1):
                    bm.edges.new((verts[j], verts[j + 1]))

                if stroke.use_cyclic:
                    bm.edges.new((verts[-1], verts[0]))
                    if len(verts) >= 3:
                        try:
                            bm.faces.new(verts)
                        except ValueError:
                            pass

                stroke_count += 1

        if stroke_count == 0:
            bm.free()
            self.report({'WARNING'}, "No strokes found - nothing converted.")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new(gp_obj.name)
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()

        new_obj = bpy.data.objects.new(gp_obj.name, mesh)
        for col in gp_collections:
            col.objects.link(new_obj)
        new_obj.matrix_world = world_matrix

        bpy.data.objects.remove(gp_obj, do_unlink=True)

        self.report({'INFO'}, f"Converted {stroke_count} stroke(s) into '{new_obj.name}'")
        return {'FINISHED'}
