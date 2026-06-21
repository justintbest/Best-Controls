import bpy
import math
import gpu
import blf
from gpu_extras.batch import batch_for_shader

FONT_SIZE = 9
TOOLTIP_FONT_SIZE = 12
BUTTON_H = 30
RADIUS = 8
GAP_Y = 6
MARGIN_TOP = 60
STRIP_WIDTH = 34
STRIP_MARGIN = 4

BUTTONS = [
    ("Move to Active Collection", "MAC", "object.move_to_active_collection", {}),
    ("Move to Active Object's Collection", "MAOC", "object.move_to_active_object_collection", {}),
    ("Remap Duplicates", "RD", "best.remap_duplicates", {}),
    ("Flip X", "FX", "object.flip_x", {}),
    ("Flip Camera X", "FCX", "object.flip_camera_x", {}),
    ("GP to Mesh", "G2M", "object.gp_to_mesh", {}),
    ("UV Active Quads", "UVQ", "object.uv_active_quads", {}),
    ("UV Active Quads Full", "UVF", "object.uv_active_quads_full", {}),
    ("Add Vertex", "+V", "object.add_single_vertex", {}),
    ("Add Plane", "+P", "object.add_single_plane", {}),
    ("Add Cube", "+C", "object.add_single_cube", {}),
    ("Add Grease Pencil", "+GP", "object.add_gp_stroke", {}),
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
        x = region.width - STRIP_WIDTH - STRIP_MARGIN
        w = STRIP_WIDTH
        y = region.height - MARGIN_TOP
        buttons = []
        for label, short, idname, kwargs in BUTTONS:
            y -= BUTTON_H
            buttons.append(("BUTTON", label, short, x, y, w, BUTTON_H, idname, kwargs))
            y -= GAP_Y
        return buttons

    def draw_callback(self, context):
        region = context.region
        buttons = self.build_layout(region)
        mouse_x, mouse_y = self.mouse_pos

        hovered_item = None
        for kind, label, short, x, y, w, h, idname, kwargs in buttons:
            hovered = x <= mouse_x <= x + w and y <= mouse_y <= y + h
            if hovered:
                hovered_item = (label, x, y, w, h)
            color = (0.32, 0.32, 0.32, 0.92) if hovered else (0.13, 0.13, 0.13, 0.85)
            _draw_pill(x, y, w, h, color)
            blf.size(0, FONT_SIZE)
            text_w = blf.dimensions(0, short)[0]
            blf.position(0, x + (w - text_w) / 2, y + (h - FONT_SIZE) / 2 + 1, 0)
            blf.color(0, 0.9, 0.9, 0.9, 1.0)
            blf.draw(0, short)

        if hovered_item:
            label, x, y, w, h = hovered_item
            blf.size(0, TOOLTIP_FONT_SIZE)
            text_w = blf.dimensions(0, label)[0]
            tip_pad = 8
            tip_w = text_w + 2 * tip_pad
            tip_x = x - tip_w - 6
            tip_y = y
            _draw_pill(tip_x, tip_y, tip_w, h, (0.08, 0.08, 0.08, 0.95))
            blf.position(0, tip_x + tip_pad, tip_y + (h - TOOLTIP_FONT_SIZE) / 2 + 1, 0)
            blf.color(0, 1.0, 1.0, 1.0, 1.0)
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
            for kind, label, short, x, y, w, h, idname, kwargs in buttons:
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
