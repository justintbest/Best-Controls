import bpy

from ..preferences import get_prefs


class VIEW3D_PT_best_assets(bpy.types.Panel):
    bl_label = "Assets"
    bl_idname = "VIEW3D_PT_best_assets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Controls"
    bl_order = -10

    def draw(self, context):
        layout = self.layout
        prefs = get_prefs(context)

        if not prefs.asset_entries:
            layout.label(text="No assets configured")
            layout.label(text="Add one in Add-on Preferences")
            return

        for entry in prefs.asset_entries:
            op = layout.operator("object.add_geo_nodes_asset", text=entry.name or "Asset")
            op.blend_path = entry.file_path
