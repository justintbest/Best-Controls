import bpy

class VIEW3D_PT_best_objects(bpy.types.Panel):
    bl_label = "Objects"
    bl_idname = "VIEW3D_PT_best_objects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Controls"

    def draw(self, context):
        self.layout.operator("object.flip_x")
        self.layout.operator("object.flip_camera_x")
        self.layout.operator("object.gp_to_mesh")
        self.layout.operator("object.uv_active_quads")
        self.layout.operator("object.uv_active_quads_full")
