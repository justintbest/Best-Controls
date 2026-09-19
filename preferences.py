import bpy


class BestControlsAssetEntry(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="Asset")
    file_path: bpy.props.StringProperty(
        name="File",
        description="A .blend file containing a Geometry Nodes group marked as an asset",
        subtype='FILE_PATH',
    )


class BEST_UL_asset_entries(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False)
        row.prop(item, "file_path", text="")


class BEST_OT_add_asset_entry(bpy.types.Operator):
    bl_idname = "best.add_asset_entry"
    bl_label = "Add Asset Entry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = get_prefs(context)
        entry = prefs.asset_entries.add()
        entry.name = "Asset"
        prefs.active_asset_index = len(prefs.asset_entries) - 1
        return {'FINISHED'}


class BEST_OT_remove_asset_entry(bpy.types.Operator):
    bl_idname = "best.remove_asset_entry"
    bl_label = "Remove Asset Entry"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(get_prefs(context).asset_entries)

    def execute(self, context):
        prefs = get_prefs(context)
        prefs.asset_entries.remove(prefs.active_asset_index)
        prefs.active_asset_index = max(0, min(prefs.active_asset_index, len(prefs.asset_entries) - 1))
        return {'FINISHED'}


class BestControlsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    asset_entries: bpy.props.CollectionProperty(type=BestControlsAssetEntry)
    active_asset_index: bpy.props.IntProperty()

    def draw(self, context):
        layout = self.layout
        layout.label(text="Geometry Nodes Assets")

        row = layout.row()
        row.template_list(
            "BEST_UL_asset_entries", "",
            self, "asset_entries",
            self, "active_asset_index",
        )

        col = row.column(align=True)
        col.operator("best.add_asset_entry", text="", icon='ADD')
        col.operator("best.remove_asset_entry", text="", icon='REMOVE')


def get_prefs(context):
    return context.preferences.addons[__package__].preferences
