import bpy


class BestControlsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    asset_folder: bpy.props.StringProperty(
        name="Geometry Nodes Asset Folder",
        description="Folder containing a .blend file with a Geometry Nodes group marked as an asset",
        subtype='DIR_PATH',
    )

    def draw(self, context):
        self.layout.prop(self, "asset_folder")


def get_prefs(context):
    return context.preferences.addons[__package__].preferences
