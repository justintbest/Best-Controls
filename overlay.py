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
    ("Flip Camera X", "FCX", "object.flip_camera_x", {}),
    ("Align Cam", "ACV", "view3d.camera_to_view", {}),
    ("Move to Coll.", "MAC", "object.move_to_active_collection", {}),
    ("Move to Obj.", "MAOC", "object.move_to_active_object_collection", {}),
    ("Remap Dupes", "RD", "best.remap_duplicates", {}),
    ("Flip X", "FX", "object.flip_x", {}),
    ("GP to Mesh", "G2M", "object.gp_to_mesh", {}),
    ("UV Act Quads", "UVQ", "object.uv_active_quads", {}),
    ("UV Quads Full", "UVF", "object.uv_active_quads_full", {}),
    ("Dec 0.2", "D2", "object.add_decimate_modifier", {"ratio": 0.2}),
    ("Dec 0.5", "D5", "object.add_decimate_modifier", {"ratio": 0.5}),
]

REFERENCE_LABEL = "Flip Camera X"

ORANGE_BUTTON_LABELS = {"Flip Camera X", "Align Cam"}

ADD_BUTTONS = [
    ("Vertex", "object.add_single_vertex", {}),
    ("Plane", "object.add_single_plane", {}),
    ("Cube", "object.add_single_cube", {}),
    ("GP", "object.add_gp_stroke", {}),
    ("Empty", "object.add_single_empty", {}),
    ("Point", "object.add_point_light", {}),
    ("Area", "object.add_area_light", {}),
    ("Sun", "object.add_sun_light", {}),
]

YELLOW_ADD_BUTTON_LABELS = {"Point", "Area", "Sun"}

ADD_BUTTON_WIDTH_FACTOR = 0.7
ADD_BUTTON_GAP_X = 6

_shader = gpu.shader.from_builtin('UNIFORM_COLOR')

_SDF_VERT = """
uniform mat4 ModelViewProjectionMatrix;
in vec2 pos;
in vec2 local;
out vec2 v_local;
void main()
{
    gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
    v_local = local;
}
"""

_SDF_FRAG = """
uniform vec4 color;
uniform vec2 halfSize;
uniform float radius;
in vec2 v_local;
out vec4 fragColor;
void main()
{
    vec2 d = abs(v_local) - (halfSize - vec2(radius));
    float dist = length(max(d, 0.0)) - radius;
    float alpha = 1.0 - smoothstep(-1.0, 1.0, dist);
    fragColor = vec4(color.rgb, color.a * alpha);
}
"""

_sdf_shader = gpu.types.GPUShader(_SDF_VERT, _SDF_FRAG)

_CAPSULE_FRAG = """
uniform vec4 color;
uniform vec2 p1;
uniform vec2 p2;
uniform float radius;
in vec2 v_local;
out vec4 fragColor;
void main()
{
    vec2 pa = v_local - p1;
    vec2 ba = p2 - p1;
    float h = clamp(dot(pa, ba) / max(dot(ba, ba), 0.0001), 0.0, 1.0);
    float dist = length(pa - ba * h) - radius;
    float alpha = 1.0 - smoothstep(-0.75, 0.75, dist);
    fragColor = vec4(color.rgb, color.a * alpha);
}
"""

_capsule_shader = gpu.types.GPUShader(_SDF_VERT, _CAPSULE_FRAG)


def _ui_scale():
    prefs = bpy.context.preferences
    return prefs.view.ui_scale * prefs.system.pixel_size


def _draw_rounded_quad(x, y, w, h, radius, color):
    half_w, half_h = w / 2, h / 2
    cx, cy = x + half_w, y + half_h
    pos = [(cx - half_w, cy - half_h), (cx + half_w, cy - half_h),
           (cx + half_w, cy + half_h), (cx - half_w, cy + half_h)]
    local = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
    indices = [(0, 1, 2), (2, 3, 0)]
    batch = batch_for_shader(_sdf_shader, 'TRIS', {"pos": pos, "local": local}, indices=indices)
    gpu.state.blend_set('ALPHA')
    _sdf_shader.bind()
    _sdf_shader.uniform_float("color", color)
    _sdf_shader.uniform_float("halfSize", (half_w, half_h))
    _sdf_shader.uniform_float("radius", min(radius, half_w, half_h))
    batch.draw(_sdf_shader)
    gpu.state.blend_set('NONE')


def _draw_pill(x, y, w, h, color):
    _draw_rounded_quad(x, y, w, h, RADIUS, color)


def _draw_circle(cx, cy, radius, color):
    _draw_rounded_quad(cx - radius, cy - radius, radius * 2, radius * 2, radius, color)


def _draw_capsule_local(p1, p2, radius, cx, cy, scale, color):
    pad = radius + 1.5
    minx = min(p1[0], p2[0]) - pad
    maxx = max(p1[0], p2[0]) + pad
    miny = min(p1[1], p2[1]) - pad
    maxy = max(p1[1], p2[1]) + pad
    local = [(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)]
    pos = [(cx + lx * scale, cy + ly * scale) for lx, ly in local]
    indices = [(0, 1, 2), (2, 3, 0)]
    batch = batch_for_shader(_capsule_shader, 'TRIS', {"pos": pos, "local": local}, indices=indices)
    gpu.state.blend_set('ALPHA')
    _capsule_shader.bind()
    _capsule_shader.uniform_float("color", color)
    _capsule_shader.uniform_float("p1", p1)
    _capsule_shader.uniform_float("p2", p2)
    _capsule_shader.uniform_float("radius", radius)
    batch.draw(_capsule_shader)
    gpu.state.blend_set('NONE')


class VIEW3D_OT_best_controls_overlay(bpy.types.Operator):
    bl_idname = "view3d.best_controls_overlay"
    bl_label = "Best Controls Overlay"
    bl_options = {'INTERNAL'}

    _handle = None
    _running = False

    @staticmethod
    def _ui_region_width(area):
        if area is None:
            return 0
        ui_region = next((r for r in area.regions if r.type == 'UI'), None)
        return ui_region.width if ui_region else 0

    def build_layout(self, region, ui_width=0):
        s = _ui_scale()
        font_size = round(FONT_SIZE * s)
        button_h = BUTTON_H * s
        gap_y = GAP_Y * s
        top_offset = TOP_OFFSET * s
        strip_margin = STRIP_MARGIN * s
        text_pad = TEXT_PAD * s
        add_gap_x = ADD_BUTTON_GAP_X * s

        blf.size(0, font_size)
        right_edge = region.width - strip_margin - ui_width
        w = blf.dimensions(0, REFERENCE_LABEL)[0] + 2 * text_pad
        x = right_edge - w
        y = region.height - top_offset
        buttons = []
        for label, short, idname, kwargs in BUTTONS:
            y -= button_h
            buttons.append(("BUTTON", label, short, x, y, w, button_h, idname, kwargs))
            y -= gap_y

        left_edge = min(b[3] for b in buttons)
        row_step = button_h + gap_y
        add_w = w * ADD_BUTTON_WIDTH_FACTOR
        add_x = left_edge - add_gap_x - add_w
        top_row_y = region.height - top_offset - button_h
        add_buttons = []
        for i, (label, idname, kwargs) in enumerate(ADD_BUTTONS):
            ay = top_row_y - i * row_step
            add_buttons.append(("ADD", label, add_x, ay, add_w, button_h, idname, kwargs))

        return buttons, add_buttons, font_size, text_pad, s

    def draw_callback(self, context):
        region = bpy.context.region
        ui_width = self._ui_region_width(bpy.context.area)
        buttons, add_buttons, font_size, text_pad, s = self.build_layout(region, ui_width)
        mouse_x, mouse_y = self.mouse_pos

        for kind, label, short, x, y, w, h, idname, kwargs in buttons:
            hovered = x <= mouse_x <= x + w and y <= mouse_y <= y + h
            if label in ORANGE_BUTTON_LABELS:
                color = (0.18, 0.12, 0.07, 1.0) if hovered else (0.10, 0.07, 0.04, 1.0)
            else:
                color = (0.10, 0.10, 0.10, 1.0) if hovered else (0.02, 0.02, 0.02, 1.0)
            _draw_pill(x, y, w, h, color)
            blf.size(0, font_size)
            text_w = blf.dimensions(0, label)[0]
            blf.position(0, x + (w - text_w) / 2, y + (h - font_size) / 2 + 1, 0)
            blf.color(0, 0.9, 0.9, 0.9, 1.0)
            blf.draw(0, label)

        for kind, label, x, y, w, h, idname, kwargs in add_buttons:
            hovered = x <= mouse_x <= x + w and y <= mouse_y <= y + h
            if label in YELLOW_ADD_BUTTON_LABELS:
                color = (0.20, 0.16, 0.03, 1.0) if hovered else (0.11, 0.09, 0.01, 1.0)
            else:
                color = (0.12, 0.16, 0.21, 1.0) if hovered else (0.06, 0.09, 0.13, 1.0)
            _draw_pill(x, y, w, h, color)
            blf.size(0, font_size)
            text_w = blf.dimensions(0, label)[0]
            blf.position(0, x + (w - text_w) / 2, y + (h - font_size) / 2 + 1, 0)
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
            ui_width = self._ui_region_width(context.area)
            buttons, add_buttons, _, _, _ = self.build_layout(context.region, ui_width)

            for kind, label, short, x, y, w, h, idname, kwargs in buttons:
                if x <= mx <= x + w and y <= my <= y + h:
                    self._invoke_op(idname, kwargs)
                    return {'RUNNING_MODAL'}

            for kind, label, x, y, w, h, idname, kwargs in add_buttons:
                if x <= mx <= x + w and y <= my <= y + h:
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
