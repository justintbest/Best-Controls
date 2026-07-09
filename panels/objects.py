import bpy

class VIEW3D_PT_best_objects(bpy.types.Panel):
    bl_label = "Objects"
    bl_idname = "VIEW3D_PT_best_objects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Controls"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.flip_x")
        layout.operator("object.flip_camera_x")
        layout.operator("view3d.camera_to_view", text="Align Camera to View")
        layout.operator("object.gp_to_mesh")
        layout.operator("object.uv_active_quads")
        layout.operator("object.uv_active_quads_full")

        layout.separator()
        row = layout.row(align=True)
        op = row.operator("object.add_decimate_modifier", text="Decimate 0.2")
        op.ratio = 0.2
        op = row.operator("object.add_decimate_modifier", text="Decimate 0.5")
        op.ratio = 0.5
