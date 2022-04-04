import bpy
from bpy.types import Operator
import os
from snap import sn_xml

from snap import sn_utils

class SN_SCENE_OT_clear_2d_views(Operator):
    bl_idname = "sn_scene.clear_2d_views"
    bl_label = "Delete 2d View Scenes"
    bl_description = "Delete all 2d view scenes"
    bl_options = {'UNDO'}     

    def execute(self, context):

        for scene in bpy.data.scenes:
            is_pv = scene.snap.scene_type == 'PLAN_VIEW'
            is_elv = scene.snap.scene_type == 'ELEVATION'
            is_acc = scene.snap.scene_type == 'ACCORDION'
            is_island = scene.snap.scene_type == 'ISLAND'
            is_virt = scene.snap.scene_type == 'VIRTUAL'
            if is_elv or is_pv or is_acc or is_island or is_virt:
                context.window.scene = scene
                bpy.ops.scene.delete()

        for view in context.window_manager.snap.image_views:
            context.window_manager.snap.image_views.remove(0)

        # we need to remove any orphaned datablocks
        for obj in bpy.data.objects:

            # Profiles have no users, but most be preserved
            if obj.get('IS_MOLDING_PROFILE') is not None:
                continue
            if len(obj.users_scene) == 0:
                # first, remove mesh data, if its sole user is the object
                mesh = obj.data
                if obj.name in bpy.data.objects:
                    bpy.data.objects.remove(obj)

                if isinstance(mesh, bpy.types.Mesh) and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
                # finally, the object, if it still exists. (for some reason, it doesn't always...)
        return {'FINISHED'}


class SN_SCENE_OT_user_clear_2d_views(Operator):
    bl_idname = "sn_scene.user_clear_2d_views"
    bl_label = "Delete 2d View Scenes"
    bl_description = "Delete all 2d view scenes"
    bl_options = {'UNDO'}     

    PDF_TEMP_XML = "pdf_temp.xml"

    def remove_pdf_xml_file(self):
        proj_props = bpy.context.window_manager.sn_project
        proj_name = proj_props.projects[proj_props.project_index].name
        proj_dir = os.path.join(sn_xml.get_project_dir(), proj_name)
        proj_dir = proj_dir.replace("\\", "/")
        xml_4_pdf = f"{proj_dir}/{self.PDF_TEMP_XML}"
        if os.path.exists(xml_4_pdf):
            os.remove(xml_4_pdf)

    def execute(self, context):
        self.remove_pdf_xml_file()
        bpy.ops.sn_scene.clear_2d_views()
        for obj in bpy.data.objects:
            if obj.get('IS_VISDIM_A') or obj.get('IS_VISDIM_B'):
                # Preserve wall obstacle annotations
                obstacle_bp = sn_utils.get_obstacle_bp(obj)
                annotation = obj.get('IS_ANNOTATION')
                if obstacle_bp or annotation:
                    continue
                bpy.data.objects.remove(obj, do_unlink=True)
        return {'FINISHED'}


classes = (
    SN_SCENE_OT_clear_2d_views,
    SN_SCENE_OT_user_clear_2d_views,
)

register, unregister = bpy.utils.register_classes_factory(classes)
