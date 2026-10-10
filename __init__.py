bl_info = {
    "name": "Preview Quads",
    "author": "maylog",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Preview Quads",
    "description": "Non-destructive triangulated-to-quad live preview tool",
    "tracker_url": "https://github.com/mayloglog/Preview-Quads",
}

import bpy
import bmesh

from bpy.app.translations import pgettext_iface as iface_


# --- Global state ---
_translations_dict = None


# --- i18n ---
def _get_translations_dict():
    """Lazy-load translations so a missing file does not break the add-on."""
    global _translations_dict
    if _translations_dict is None:
        try:
            from . import translations
            _translations_dict = translations.translations_dict
        except Exception:
            try:
                import translations
                _translations_dict = translations.translations_dict
            except Exception as e:
                print(f"[PreviewQuads] translations not loaded: {e}")
                _translations_dict = {}
    return _translations_dict


# --- Core update and conversion logic ---
def update_tris_to_quads_for_object(obj):
    if not obj or obj.type != 'MESH':
        return

    # 1. Record the source mesh name once
    if "source_mesh_name" not in obj:
        obj["source_mesh_name"] = obj.data.name

    source_mesh_name = obj["source_mesh_name"]
    if source_mesh_name not in bpy.data.meshes:
        return
    source_mesh = bpy.data.meshes[source_mesh_name]

    # 2. If preview is disabled, switch back to the source mesh
    if not obj.t2q_enable:
        if obj.data != source_mesh:
            obj.data = source_mesh
        return

    # 3. Read panel parameters
    angle_limit = obj.t2q_angle_limit
    shape_limit = obj.t2q_shape_limit
    cmp_uvs = obj.t2q_cmp_uvs
    cmp_vcols = obj.t2q_cmp_vcols
    cmp_seam = obj.t2q_cmp_seam
    cmp_sharp = obj.t2q_cmp_sharp
    cmp_materials = obj.t2q_cmp_materials

    # 4. Build BMesh from the latest source mesh and convert
    bm = bmesh.new()
    bm.from_mesh(source_mesh)

    bmesh.ops.join_triangles(
        bm,
        faces=bm.faces,
        cmp_seam=cmp_seam,
        cmp_sharp=cmp_sharp,
        cmp_uvs=cmp_uvs,
        cmp_vcols=cmp_vcols,
        cmp_materials=cmp_materials,
        angle_shape_threshold=shape_limit,
        angle_face_threshold=angle_limit,
    )

    # 5. Prepare or update the preview mesh
    eval_mesh_name = f"{source_mesh.name}_PreviewQuads_Eval"
    eval_mesh = bpy.data.meshes.get(eval_mesh_name)
    if not eval_mesh:
        eval_mesh = bpy.data.meshes.new(eval_mesh_name)
    else:
        eval_mesh.clear_geometry()

    bm.to_mesh(eval_mesh)
    bm.free()

    if obj.data != eval_mesh:
        obj.data = eval_mesh


# --- Apply operation ---
def apply_quads_to_source(obj):
    """Replace the source mesh with the current quad preview result."""
    if not obj or obj.type != 'MESH':
        return False
    if obj.mode != 'OBJECT':
        return False

    source_mesh_name = obj.get("source_mesh_name")
    if not source_mesh_name:
        return False
    source_mesh = bpy.data.meshes.get(source_mesh_name)
    if source_mesh is None:
        return False

    angle_limit = obj.t2q_angle_limit
    shape_limit = obj.t2q_shape_limit
    cmp_uvs = obj.t2q_cmp_uvs
    cmp_vcols = obj.t2q_cmp_vcols
    cmp_seam = obj.t2q_cmp_seam
    cmp_sharp = obj.t2q_cmp_sharp
    cmp_materials = obj.t2q_cmp_materials

    bm = bmesh.new()
    try:
        bm.from_mesh(source_mesh)
        bmesh.ops.join_triangles(
            bm,
            faces=bm.faces,
            cmp_seam=cmp_seam,
            cmp_sharp=cmp_sharp,
            cmp_uvs=cmp_uvs,
            cmp_vcols=cmp_vcols,
            cmp_materials=cmp_materials,
            angle_shape_threshold=shape_limit,
            angle_face_threshold=angle_limit,
        )
    except Exception as e:
        bm.free()
        print(f"[PreviewQuads] apply failed on '{obj.name}': {e}")
        return False

    # Overwrite the source mesh in place
    source_mesh.clear_geometry()
    bm.to_mesh(source_mesh)
    bm.free()
    source_mesh.update()

    # Remove the preview mesh if it exists
    eval_mesh_name = f"{source_mesh.name}_PreviewQuads_Eval"
    eval_mesh = bpy.data.meshes.get(eval_mesh_name)
    if eval_mesh is not None:
        if obj.data == eval_mesh:
            obj.data = source_mesh
        bpy.data.meshes.remove(eval_mesh)

    if obj.data != source_mesh:
        obj.data = source_mesh

    obj.t2q_enable = False
    return True


# Property update callback
def on_setting_update(self, context):
    update_tris_to_quads_for_object(self)


# --- UI panel ---
class VIEW3D_PT_PreviewQuadsPanel(bpy.types.Panel):
    bl_label = "Preview Quads"
    bl_idname = "VIEW3D_PT_preview_quads"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Preview Quads"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # 1. Target object selector
        layout.prop(scene, "t2q_target_object", text=iface_("Target Object"))

        obj = scene.t2q_target_object
        if not obj:
            layout.label(text=iface_("Select a mesh object with triangles"),
                         icon='INFO')
            return

        if obj.type != 'MESH':
            layout.label(text=iface_("Selected object must be a mesh"),
                         icon='ERROR')
            return

        layout.separator()

        # 2. Enable preview toggle
        layout.prop(obj, "t2q_enable", text=iface_("Enable Quad Preview"),
                    icon='MOD_DECIM')

        if obj.t2q_enable:
            box = layout.box()
            box.label(text=iface_("Triangles to Quads"), icon='PREFERENCES')

            box.prop(obj, "t2q_angle_limit", text="Max Face Angle")
            box.prop(obj, "t2q_shape_limit", text="Max Shape Angle")
            box.prop(obj, "t2q_face_weight", text="Topology Influence")

            box.separator()
            box.prop(obj, "t2q_cmp_uvs", text="Compare UVs")
            box.prop(obj, "t2q_cmp_vcols", text="Compare Color Attributes")
            box.prop(obj, "t2q_cmp_seam", text="Compare Seam")
            box.prop(obj, "t2q_cmp_sharp", text="Compare Sharp")
            box.prop(obj, "t2q_cmp_materials", text="Compare Materials")

        layout.separator()
        col = layout.column()
        col.enabled = (obj.mode == 'OBJECT' and obj.t2q_enable)
        col.operator("object.t2q_apply_quads", text=iface_("Apply Quads"),
                     icon='CHECKMARK')


# --- Operator: apply quads ---
class OBJECT_OT_T2QApplyQuads(bpy.types.Operator):
    bl_idname = "object.t2q_apply_quads"
    bl_label = "Apply Quads"
    bl_description = "Replace the source mesh with the current quad result"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.scene.t2q_target_object
        return (
            obj is not None
            and obj.type == 'MESH'
            and obj.mode == 'OBJECT'
        )

    def execute(self, context):
        obj = context.scene.t2q_target_object
        if obj is None:
            self.report({'ERROR'}, "No target object")
            return {'CANCELLED'}

        ok = apply_quads_to_source(obj)
        if not ok:
            self.report({'ERROR'}, "Failed to apply quads")
            return {'CANCELLED'}

        self.report({'INFO'}, iface_("Applied quads to '%s'") % obj.name)
        return {'FINISHED'}


# --- Registration ---
classes = (
    VIEW3D_PT_PreviewQuadsPanel,
    OBJECT_OT_T2QApplyQuads,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.t2q_target_object = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Target Object",
        description="Select a mesh object to preview as quads",
    )

    bpy.types.Object.t2q_enable = bpy.props.BoolProperty(
        name="Enable Preview", default=False, update=on_setting_update
    )
    bpy.types.Object.t2q_angle_limit = bpy.props.FloatProperty(
        name="Max Angle", default=3.1415927, min=0.0, max=3.1415927,
        subtype='ANGLE', update=on_setting_update,
    )
    bpy.types.Object.t2q_shape_limit = bpy.props.FloatProperty(
        name="Max Shape Angle", default=3.1415927, min=0.0, max=3.1415927,
        subtype='ANGLE', update=on_setting_update,
    )
    bpy.types.Object.t2q_face_weight = bpy.props.FloatProperty(
        name="Face Weight", default=1.1, min=0, max=2,
        update=on_setting_update,
    )
    bpy.types.Object.t2q_cmp_uvs = bpy.props.BoolProperty(
        name="Compare UVs", default=False, update=on_setting_update)
    bpy.types.Object.t2q_cmp_vcols = bpy.props.BoolProperty(
        name="Compare VCols", default=False, update=on_setting_update)
    bpy.types.Object.t2q_cmp_seam = bpy.props.BoolProperty(
        name="Compare Seam", default=False, update=on_setting_update)
    bpy.types.Object.t2q_cmp_sharp = bpy.props.BoolProperty(
        name="Compare Sharp", default=False, update=on_setting_update)
    bpy.types.Object.t2q_cmp_materials = bpy.props.BoolProperty(
        name="Compare Materials", default=False, update=on_setting_update)

    try:
        bpy.app.translations.register(__name__, _get_translations_dict())
    except Exception as e:
        print(f"[PreviewQuads] translations register failed: {e}")


def unregister():
    try:
        bpy.app.translations.unregister(__name__)
    except Exception:
        pass

    del bpy.types.Scene.t2q_target_object
    del bpy.types.Object.t2q_enable
    del bpy.types.Object.t2q_angle_limit
    del bpy.types.Object.t2q_shape_limit
    del bpy.types.Object.t2q_face_weight
    del bpy.types.Object.t2q_cmp_uvs
    del bpy.types.Object.t2q_cmp_vcols
    del bpy.types.Object.t2q_cmp_seam
    del bpy.types.Object.t2q_cmp_sharp
    del bpy.types.Object.t2q_cmp_materials

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()