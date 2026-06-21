bl_info = {
    "name": "Best Controls",
    "author": "Justin Best",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Best Controls",
    "description": "Best Controls panel: transforms, mesh tools, cleanup, and collections",
    "category": "3D View",
}

import bpy

from . operators import (
    OBJECT_OT_move_to_active_collection,
    OBJECT_OT_move_to_active_object_collection,
    OBJECT_OT_add_copy_transforms_constraint,
    OBJECT_OT_copy_transforms_no_constraint,
    OBJECT_OT_reset_transforms,
    MESH_OT_set_crease_one,
    MESH_OT_set_crease_zero,
    BEST_OT_remap_duplicates,
    OBJECT_OT_make_single_user_quick,
    OBJECT_OT_flip_x,
    OBJECT_OT_flip_camera_x,
    OBJECT_OT_gp_to_mesh,
    OBJECT_OT_uv_active_quads,
    OBJECT_OT_uv_active_quads_full,
    OBJECT_OT_add_single_vertex,
    OBJECT_OT_add_single_plane,
    OBJECT_OT_add_single_cube,
    OBJECT_OT_add_single_empty,
    OBJECT_OT_add_gp_stroke,
    OBJECT_OT_add_decimate_modifier,
)
from .panels import (
    VIEW3D_PT_move_to_active_collection,
    VIEW3D_PT_scene_custom_props_filtered,
    VIEW3D_PT_best_objects,
    VIEW3D_PT_best_primitives,
)
from . import overlay

classes = (
    OBJECT_OT_move_to_active_collection,
    OBJECT_OT_move_to_active_object_collection,
    OBJECT_OT_add_copy_transforms_constraint,
    OBJECT_OT_copy_transforms_no_constraint,
    OBJECT_OT_reset_transforms,
    MESH_OT_set_crease_one,
    MESH_OT_set_crease_zero,
    BEST_OT_remap_duplicates,
    OBJECT_OT_make_single_user_quick,
    OBJECT_OT_flip_x,
    OBJECT_OT_flip_camera_x,
    OBJECT_OT_gp_to_mesh,
    OBJECT_OT_uv_active_quads,
    OBJECT_OT_uv_active_quads_full,
    OBJECT_OT_add_single_vertex,
    OBJECT_OT_add_single_plane,
    OBJECT_OT_add_single_cube,
    OBJECT_OT_add_single_empty,
    OBJECT_OT_add_gp_stroke,
    OBJECT_OT_add_decimate_modifier,
    VIEW3D_PT_move_to_active_collection,
    VIEW3D_PT_scene_custom_props_filtered,
    VIEW3D_PT_best_objects,
    VIEW3D_PT_best_primitives,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    overlay.register()

def unregister():
    overlay.unregister()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
