import bpy
import math
import gpu
import blf
from gpu_extras.batch import batch_for_shader

FONT_SIZE = 12
BUTTON_H = 28
RADIUS = 14
H_PAD = 16
GAP_X = 8
GAP_Y = 8
MARGIN = 24
MAX_ROW_WIDTH = 640

BUTTONS = [
    ("Move to Active Collection", "object.move_to_active_collection", {}),
    ("Move to Active Object's Collection", "object.move_to_active_object_collection", {}),
    ("Remap Duplicates", "best.remap_duplicates", {}),
    ("Flip X", "object.flip_x", {}),
    ("Flip Camera X", "object.flip_camera_x", {}),
    ("GP to Mesh", "object.gp_to_mesh", {}),
    ("UV Active Quads", "object.uv_active_quads", {}),
    ("UV Active Quads Full", "object.uv_active_quads_full", {}),
    ("Add Vertex", "object.add_single_vertex", {}),
    ("Add Plane", "object.add_single_plane", {}),
    ("Add Cube", "object.add_single_cube", {}),
    ("Add Grease Pencil", "object.add_gp_stroke", {}),
]

_shader = gpu.shader.from_builtin('UNIFORM_COLOR')


def _rounded_rect_verts(x, y, w, h, r, segments=6):
    r = min(r, w / 2, h / 2)
    corners = [
        (x + w - r, y + r, -90, 0),
        (x + w - r, y + h - r, 0, 90),
        (x + r, y + h - r, 90, 180),
        (x + r, y + r, 180, 270),
    ]
    verts = []
    for cx, cy, a0, a1 in corners:
        for i in range(segments + 1):
            t = math.radians(a0 + (a1 - a0) * i / segments)
            verts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return verts


def _draw_pill(x, y, w, h, color):
    verts = _rounded_rect_verts(x, y, w, h, RADIUS)
    batch = batch_for_shader(_shader, 'TRI_FAN', {"pos": verts})
    gpu.state.blend_set('ALPHA')
    _shader.uniform_float("color", color)
    batch.draw(_shader)
    gpu.state.blend_set('NONE')


class VIEW3D_OT_best_controls_overlay(bpy.types.Operator):
    bl_idname = "view3d.best_controls_overlay"
    bl_label = "Best Controls Overlay"
    bl_options = {'INTERNAL'}

    _handle = None
    _running = False

    def build_layout(self, region):
        blf.size(0, FONT_SIZE)
        max_row_w = min(region.width - 2 * MARGIN, MAX_ROW_WIDTH)

        rows = []
        row = []
        row_w = 0
        for label, idname, kwargs in BUTTONS:
            text_w = blf.dimensions(0, label)[0]
            btn_w = text_w + 2 * H_PAD
            extra = GAP_X if row else 0
            if row and row_w + extra + btn_w > max_row_w:
                rows.append(row)
                row = []
                row_w = 0
                extra = 0
            row.append((label, idname, kwargs, btn_w))
            row_w += extra + btn_w
        if row:
            rows.append(row)

        buttons = []
        y = MARGIN
        for row in reversed(rows):
            x = MARGIN
            for label, idname, kwargs, btn_w in row:
                buttons.append(("BUTTON", label, x, y, btn_w, BUTTON_H, idname, kwargs))
                x += btn_w + GAP_X
            y += BUTTON_H + GAP_Y
        return buttons

    def draw_callback(self, context):
        region = context.region
        buttons = self.build_layout(region)
        mouse_x, mouse_y = self.mouse_pos

        for kind, label, x, y, w, h, idname, kwargs in buttons:
            hovered = x <= mouse_x <= x + w and y <= mouse_y <= y + h
            color = (0.32, 0.32, 0.32, 0.92) if hovered else (0.13, 0.13, 0.13, 0.85)
            _draw_pill(x, y, w, h, color)
            blf.position(0, x + H_PAD, y + (h - FONT_SIZE) / 2 + 1, 0)
            blf.size(0, FONT_SIZE)
            blf.color(0, 0.9, 0.9, 0.9, 1.0)
            blf.draw(0, label)

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            mx, my = event.mouse_region_x, event.mouse_region_y
            buttons = self.build_layout(context.region)
            for kind, label, x, y, w, h, idname, kwargs in buttons:
                if kind != "BUTTON":
                    continue
                if x <= mx <= x + w and y <= my <= y + h:
                    op_cat, op_name = idname.split(".")
                    try:
                        getattr(getattr(bpy.ops, op_cat), op_name)(**kwargs)
                    except Exception as exc:
                        self.report({'WARNING'}, str(exc))
                    return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if VIEW3D_OT_best_controls_overlay._running:
            return {'CANCELLED'}

        self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        VIEW3D_OT_best_controls_overlay._handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback, (context,), 'WINDOW', 'POST_PIXEL'
        )
        VIEW3D_OT_best_controls_overlay._running = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if VIEW3D_OT_best_controls_overlay._handle:
            bpy.types.SpaceView3D.draw_handler_remove(VIEW3D_OT_best_controls_overlay._handle, 'WINDOW')
            VIEW3D_OT_best_controls_overlay._handle = None
        VIEW3D_OT_best_controls_overlay._running = False


def _autostart():
    if VIEW3D_OT_best_controls_overlay._running:
        return None
    wm = bpy.context.window_manager
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            if region is None:
                continue
            override = {'window': window, 'screen': window.screen, 'area': area, 'region': region}
            with bpy.context.temp_override(**override):
                bpy.ops.view3d.best_controls_overlay('INVOKE_DEFAULT')
            return None
    return 0.5


def register():
    bpy.utils.register_class(VIEW3D_OT_best_controls_overlay)
    bpy.app.timers.register(_autostart, first_interval=0.5)


def unregister():
    if VIEW3D_OT_best_controls_overlay._running:
        VIEW3D_OT_best_controls_overlay._handle and bpy.types.SpaceView3D.draw_handler_remove(
            VIEW3D_OT_best_controls_overlay._handle, 'WINDOW'
        )
        VIEW3D_OT_best_controls_overlay._handle = None
        VIEW3D_OT_best_controls_overlay._running = False
    bpy.utils.unregister_class(VIEW3D_OT_best_controls_overlay)
