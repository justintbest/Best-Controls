import bpy
import gpu
import blf
from gpu_extras.batch import batch_for_shader

BUTTON_W = 190
BUTTON_H = 26
PAD = 6
GROUP_GAP = 16
MARGIN = 20

GROUPS = [
    ("Collections", [
        ("Move to Active Collection", "object.move_to_active_collection", {}),
        ("Move to Active Object's Collection", "object.move_to_active_object_collection", {}),
    ]),
    ("Best Global Controls", [
        ("Remap Duplicates", "best.remap_duplicates", {}),
    ]),
    ("Objects", [
        ("Flip X", "object.flip_x", {}),
        ("Flip Camera X", "object.flip_camera_x", {}),
        ("GP to Mesh", "object.gp_to_mesh", {}),
        ("UV Active Quads", "object.uv_active_quads", {}),
        ("UV Active Quads Full", "object.uv_active_quads_full", {}),
    ]),
    ("Primitives", [
        ("Add Vertex", "object.add_single_vertex", {}),
        ("Add Plane", "object.add_single_plane", {}),
        ("Add Cube", "object.add_single_cube", {}),
        ("Add Grease Pencil", "object.add_gp_stroke", {}),
    ]),
]

_shader = gpu.shader.from_builtin('UNIFORM_COLOR')


def _draw_rect(x, y, w, h, color):
    coords = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    indices = [(0, 1, 2), (2, 3, 0)]
    batch = batch_for_shader(_shader, 'TRIS', {"pos": coords}, indices=indices)
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
        x = region.width - BUTTON_W - MARGIN
        y = region.height - 40
        buttons = []
        for group_label, items in GROUPS:
            y -= 18
            buttons.append(("HEADER", group_label, x, y, BUTTON_W, 0, None, None))
            for label, idname, kwargs in items:
                y -= BUTTON_H
                buttons.append(("BUTTON", label, x, y, BUTTON_W, BUTTON_H, idname, kwargs))
                y -= PAD
            y -= GROUP_GAP
        return buttons

    def draw_callback(self, context):
        region = context.region
        buttons = self.build_layout(region)
        mouse_x, mouse_y = self.mouse_pos

        for item in buttons:
            kind, label, x, y, w, h, idname, kwargs = item
            if kind == "HEADER":
                blf.position(0, x, y + 4, 0)
                blf.size(0, 13)
                blf.color(0, 1.0, 1.0, 1.0, 1.0)
                blf.draw(0, label)
            else:
                hovered = x <= mouse_x <= x + w and y <= mouse_y <= y + h
                color = (0.35, 0.35, 0.35, 0.9) if hovered else (0.18, 0.18, 0.18, 0.85)
                _draw_rect(x, y, w, h, color)
                blf.position(0, x + 8, y + 7, 0)
                blf.size(0, 12)
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
