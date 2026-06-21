import bpy
import math
import gpu
import blf
from gpu_extras.batch import batch_for_shader

FONT_SIZE = 10
BUTTON_H = 22
RADIUS = 11
GAP_Y = 5
TOP_OFFSET = 290
STRIP_MARGIN = 4
TEXT_PAD = 10

BUTTONS = [
    ("Move to Coll.", "MAC", "object.move_to_active_collection", {}),
    ("Move to Obj.", "MAOC", "object.move_to_active_object_collection", {}),
    ("Remap Dupes", "RD", "best.remap_duplicates", {}),
    ("Flip X", "FX", "object.flip_x", {}),
    ("Flip Camera X", "FCX", "object.flip_camera_x", {}),
    ("GP to Mesh", "G2M", "object.gp_to_mesh", {}),
    ("UV Act Quads", "UVQ", "object.uv_active_quads", {}),
    ("UV Quads Full", "UVF", "object.uv_active_quads_full", {}),
    ("Dec 0.2", "D2", "object.add_decimate_modifier", {"ratio": 0.2}),
    ("Dec 0.5", "D5", "object.add_decimate_modifier", {"ratio": 0.5}),
]

REFERENCE_LABEL = "Flip Camera X"

ADD_BUTTONS = [
    ("Add Vertex", "V", "object.add_single_vertex", {}),
    ("Add Plane", "P", "object.add_single_plane", {}),
    ("Add Cube", "C", "object.add_single_cube", {}),
    ("Add Grease Pencil", "G", "object.add_gp_stroke", {}),
]

ICON_SEGMENTS = {
    'P': [
        ((-5, -4), (5, -4)), ((5, -4), (5, 4)),
        ((5, 4), (-5, 4)), ((-5, 4), (-5, -4)),
    ],
    'C': [
        ((-5, -5), (1, -5)), ((1, -5), (1, 1)),
        ((1, 1), (-5, 1)), ((-5, 1), (-5, -5)),
        ((-1, -1), (5, -1)), ((5, -1), (5, 5)),
        ((5, 5), (-1, 5)), ((-1, 5), (-1, -1)),
        ((-5, -5), (-1, -1)), ((1, -5), (5, -1)),
        ((1, 1), (5, 5)), ((-5, 1), (-1, 5)),
    ],
    'G': [
        ((-6, -3), (-2, 4)), ((-2, 4), (2, -4)), ((2, -4), (6, 3)),
    ],
}

CIRCLE_D = 22
CIRCLE_GAP_Y = 5
CIRCLE_GAP_X = 6

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


def _draw_circle(cx, cy, radius, color, segments=20):
    verts = [(cx, cy)]
    for i in range(segments + 1):
        t = math.radians(360 * i / segments)
        verts.append((cx + radius * math.cos(t), cy + radius * math.sin(t)))
    batch = batch_for_shader(_shader, 'TRI_FAN', {"pos": verts})
    gpu.state.blend_set('ALPHA')
    _shader.uniform_float("color", color)
    batch.draw(_shader)
    gpu.state.blend_set('NONE')


def _draw_icon(code, cx, cy, scale=1.0):
    if code == 'V':
        _draw_circle(cx, cy, 2.2 * scale, (1.0, 1.0, 1.0, 1.0), segments=10)
        return

    segments = ICON_SEGMENTS.get(code)
    if not segments:
        return
    verts = []
    for (x1, y1), (x2, y2) in segments:
        verts.append((cx + x1 * scale, cy + y1 * scale))
        verts.append((cx + x2 * scale, cy + y2 * scale))
    batch = batch_for_shader(_shader, 'LINES', {"pos": verts})
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(1.5)
    _shader.uniform_float("color", (1.0, 1.0, 1.0, 1.0))
    batch.draw(_shader)
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')


class VIEW3D_OT_best_controls_overlay(bpy.types.Operator):
    bl_idname = "view3d.best_controls_overlay"
    bl_label = "Best Controls Overlay"
    bl_options = {'INTERNAL'}

    _handle = None
    _running = False

    def build_layout(self, region):
        blf.size(0, FONT_SIZE)
        right_edge = region.width - STRIP_MARGIN
        w = blf.dimensions(0, REFERENCE_LABEL)[0] + 2 * TEXT_PAD
        x = right_edge - w
        y = region.height - TOP_OFFSET
        buttons = []
        for label, short, idname, kwargs in BUTTONS:
            y -= BUTTON_H
            buttons.append(("BUTTON", label, short, x, y, w, BUTTON_H, idname, kwargs))
            y -= GAP_Y

        left_edge = min(b[3] for b in buttons)
        circles = []
        cy = region.height - TOP_OFFSET - BUTTON_H / 2 + CIRCLE_D / 2
        for label, short, idname, kwargs in ADD_BUTTONS:
            cy -= CIRCLE_D
            cx = left_edge - CIRCLE_GAP_X - CIRCLE_D / 2
            circles.append(("CIRCLE", label, short, cx, cy, CIRCLE_D, idname, kwargs))
            cy -= CIRCLE_GAP_Y

        return buttons, circles

    def draw_callback(self, context):
        region = context.region
        buttons, circles = self.build_layout(region)
        mouse_x, mouse_y = self.mouse_pos

        for kind, label, short, x, y, w, h, idname, kwargs in buttons:
            hovered = x <= mouse_x <= x + w and y <= mouse_y <= y + h
            color = (0.32, 0.32, 0.32, 0.92) if hovered else (0.13, 0.13, 0.13, 0.85)
            _draw_pill(x, y, w, h, color)
            blf.size(0, FONT_SIZE)
            blf.position(0, x + TEXT_PAD, y + (h - FONT_SIZE) / 2 + 1, 0)
            blf.color(0, 0.9, 0.9, 0.9, 1.0)
            blf.draw(0, label)

        for kind, label, short, cx, cy, d, idname, kwargs in circles:
            r = d / 2
            hovered = (mouse_x - cx) ** 2 + (mouse_y - cy) ** 2 <= r * r
            color = (0.25, 0.55, 0.95, 1.0) if hovered else (0.13, 0.42, 0.85, 0.95)
            _draw_circle(cx, cy, r, color)
            _draw_icon(short, cx, cy)

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            mx, my = event.mouse_region_x, event.mouse_region_y
            buttons, circles = self.build_layout(context.region)

            for kind, label, short, x, y, w, h, idname, kwargs in buttons:
                if x <= mx <= x + w and y <= my <= y + h:
                    self._invoke_op(idname, kwargs)
                    return {'RUNNING_MODAL'}

            for kind, label, short, cx, cy, d, idname, kwargs in circles:
                r = d / 2
                if (mx - cx) ** 2 + (my - cy) ** 2 <= r * r:
                    self._invoke_op(idname, kwargs)
                    return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def _invoke_op(self, idname, kwargs):
        op_cat, op_name = idname.split(".")
        try:
            getattr(getattr(bpy.ops, op_cat), op_name)(**kwargs)
        except Exception as exc:
            self.report({'WARNING'}, str(exc))

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
