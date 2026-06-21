import bpy

class VIEW3D_PT_scene_custom_props_filtered(bpy.types.Panel):
    bl_label = "Best Global Controls"
    bl_idname = "VIEW3D_PT_scene_custom_props_filtered"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Controls"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("best.remap_duplicates")
        layout.separator()

        props = scene.keys()

        filtered_props = [
            p for p in props
            if p not in "_RNA_UI" and p.startswith("prop")
        ]

        if not filtered_props:
            layout.label(text="No matching properties")
            return

        for prop in filtered_props:
            layout.prop(scene, f'["{prop}"]', text=prop)
