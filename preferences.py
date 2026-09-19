import bpy


class BestControlsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    asset_file: bpy.props.StringProperty(
        name="Geometry Nodes Asset File",
        description="A .blend file containing a Geometry Nodes group marked as an asset",
        subtype='FILE_PATH',
    )

    def draw(self, context):
        self.layout.prop(self, "asset_file")


def get_prefs(context):
    return context.preferences.addons[__package__].preferences
