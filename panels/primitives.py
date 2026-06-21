import bpy


class VIEW3D_PT_best_primitives(bpy.types.Panel):
    bl_label = "Primitives"
    bl_idname = "VIEW3D_PT_best_primitives"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Controls"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.add_single_vertex")
        layout.operator("object.add_single_plane")
        layout.operator("object.add_single_cube")
        layout.operator("object.add_gp_stroke")
