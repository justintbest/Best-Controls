import bpy

class VIEW3D_PT_move_to_active_collection(bpy.types.Panel):
    bl_label = "Collections"
    bl_idname = "VIEW3D_PT_move_to_active_collection"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Controls"

    def draw(self, context):
        active_coll = context.view_layer.active_layer_collection.collection
        self.layout.label(text=f"Active: {active_coll.name}")
        self.layout.operator("object.move_to_active_collection")
        self.layout.operator("object.move_to_active_object_collection")
