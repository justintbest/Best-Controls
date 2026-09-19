from .collections import (
    OBJECT_OT_move_to_active_collection,
    OBJECT_OT_move_to_active_object_collection,
)
from .transforms import (
    OBJECT_OT_add_copy_transforms_constraint,
    OBJECT_OT_copy_transforms_no_constraint,
    OBJECT_OT_reset_transforms,
)
from .mesh import MESH_OT_set_crease_one, MESH_OT_set_crease_zero, OBJECT_OT_uv_active_quads, OBJECT_OT_uv_active_quads_full
from .cleanup import BEST_OT_remap_duplicates, OBJECT_OT_make_single_user_quick
from .object_utils import (
    OBJECT_OT_flip_x,
    OBJECT_OT_flip_camera_x,
    OBJECT_OT_gp_to_mesh,
    OBJECT_OT_add_decimate_modifier,
)
from .primitives import (
    OBJECT_OT_add_single_vertex,
    OBJECT_OT_add_single_plane,
    OBJECT_OT_add_single_cube,
    OBJECT_OT_add_single_empty,
    OBJECT_OT_add_point_light,
    OBJECT_OT_add_area_light,
    OBJECT_OT_add_sun_light,
    OBJECT_OT_add_gp_stroke,
)
