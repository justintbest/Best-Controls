import os

import bpy

from ..preferences import get_prefs


class OBJECT_OT_add_geo_nodes_asset(bpy.types.Operator):
    bl_idname = "object.add_geo_nodes_asset"
    bl_label = "Add Geometry Nodes Asset"
    bl_description = (
        "Append the Geometry Nodes group marked as an asset in the .blend file set in "
        "add-on preferences, and add it as a modifier on the selected objects"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        prefs = get_prefs(context)
        blend_path = bpy.path.abspath(prefs.asset_file)

        if not blend_path or not os.path.isfile(blend_path):
            self.report({'ERROR'}, "Set a valid .blend file in Best Controls preferences")
            return {'CANCELLED'}

        with bpy.data.libraries.load(blend_path, link=False, assets_only=True) as (data_from, data_to):
            available_names = list(data_from.node_groups)

        if not available_names:
            self.report({'ERROR'}, f"No Geometry Nodes asset found in {blend_path}")
            return {'CANCELLED'}

        asset_name = available_names[0]
        node_group = bpy.data.node_groups.get(asset_name)

        if node_group is None:
            with bpy.data.libraries.load(blend_path, link=False, assets_only=True) as (data_from, data_to):
                data_to.node_groups = [asset_name]
            node_group = data_to.node_groups[0]

        targets = context.selected_objects or [context.active_object]
        for obj in targets:
            mod = obj.modifiers.new(name=node_group.name, type='NODES')
            mod.node_group = node_group

        self.report({'INFO'}, f"Added '{node_group.name}' to {len(targets)} object(s)")
        return {'FINISHED'}
