import bpy


class VIEW3D_PT_best_assets(bpy.types.Panel):
    bl_label = "Assets"
    bl_idname = "VIEW3D_PT_best_assets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Controls"

    def draw(self, context):
        self.layout.operator("object.add_geo_nodes_asset")
