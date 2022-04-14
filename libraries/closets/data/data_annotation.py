from os import path
import operator
import math
import re

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, FloatProperty

from snap import sn_types, sn_unit, sn_utils
from ..ops.drop_closet import PlaceClosetInsert
from .. import closet_props
from ..common import common_parts
from ..common import common_prompts
from .. import closet_paths
from .. import closet_props

OBJECT_DIR = closet_paths.get_closet_objects_path()
ANNOTATION = path.join(OBJECT_DIR, "Annotation.blend")

class Annotation(sn_types.Assembly):
    """ Annotation
    """

    type_assembly = "PRODUCT"
    placement_type = ""
    id_prompt = "sn_closets.annotation"
    drop_id = "sn_closets.annotation_drop"
    show_in_library = True
    category_name = "Products - Basic"
    mirror_y = True

    def update(self):
        self.obj_x.location.x = self.width
        self.obj_y.location.y = -self.depth if self.mirror_y else self.depth
        self.obj_z.location.z = self.height

        self.obj_bp.snap.export_as_subassembly = True
        self.obj_bp['IS_BP_ANNOTATION'] = True
        self.obj_bp['ID_PROMPT'] = self.id_prompt
        self.obj_bp['ID_DROP'] = self.drop_id
        self.obj_bp["ALLOW_PART_DELETE"] = True
        self.obj_bp.snap.placement_type = self.placement_type
        self.obj_bp.snap.type_group = self.type_assembly
        super().update()

    def draw(self):
        self.create_assembly()
        self.add_prompt("Label", "TEXT", "")
        annotation_obj = sn_types.Part(self.add_assembly_from_file(ANNOTATION))
        self.update()


class PROMPTS_Prompts_Annotation(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.annotation"
    bl_label = "Annotation Prompt"
    bl_options = {'UNDO'}

    annotation_label: StringProperty(name="Annotation Label",
                                    description="Set or change annotation text")

    assembly = None

    # NOTE It seems the smallest and simplest Assembly prompt on SNaP, 
    #      so if you are looking for an assembly it is a good one 
    #      to get started =)

    """ This is called everytime a change is made in the UI """
    def check(self, context):
        label = self.assembly.get_prompt("Label")
        if label:
            exec("label.set_value(str(self.annotation_label))")
        return True

    """ This is called when the OK button is clicked """
    def execute(self, context):
        return {'FINISHED'}

    """ This is called before the interface is displayed """
    def invoke(self, context, event):
        obj = bpy.data.objects[context.object.name]
        bp = sn_utils.get_annotation_bp(obj)
        self.assembly = Annotation(bp)
        label = self.assembly.get_prompt("Label").get_value()
        if label:
            exec("self.annotation_label = label")
        wm = context.window_manager
        dialog_width = sn_utils.get_prop_dialog_width(400)
        return wm.invoke_props_dialog(self, width=dialog_width)

    """ This is where you draw the interface """
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.prop(self, 'annotation_label')

class DROP_OPERATOR_Place_Annotation(Operator, PlaceClosetInsert):
    bl_idname = "sn_closets.annotation_drop"
    bl_label = "Place Annotation"
    bl_description = "This places the annotation."
    bl_options = {'UNDO'}

    def execute(self, context):
        self.draw_asset()
        self.get_insert(context)

        if self.insert is None:
            bpy.ops.snap.message_box(
                'INVOKE_DEFAULT',
                message="Could Not Find Insert Class: " + self.object_name)
            return {'CANCELLED'}

        self.exclude_objects = sn_utils.get_child_objects(self.insert.obj_bp)
        self.set_wire_and_xray(self.insert.obj_bp, True)
        if self.header_text:
            context.area.header_text_set(text=self.header_text)
        context.view_layer.update()  # THE SCENE MUST BE UPDATED FOR RAY CAST TO WORK
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def annotation_drop(self, context, event):
        selected_point, selected_obj, _ = sn_utils.get_selection_point(
            context, event, exclude_objects=self.exclude_objects)
        bpy.ops.object.select_all(action='DESELECT')
        self.asset.obj_bp.location = selected_point
        self.asset.obj_bp.parent = None

        if selected_obj:
            wall_bp = sn_utils.get_wall_bp(selected_obj)
            selected_assembly_bp = sn_utils.get_assembly_bp(selected_obj)
            selected_assembly = sn_types.Assembly(selected_assembly_bp)

            if wall_bp:
                self.asset.obj_bp.parent = wall_bp
                loc_pos = wall_bp.matrix_world.inverted() @ selected_point
                self.asset.obj_bp.location = loc_pos
                self.asset.obj_bp.rotation_euler.z = 0
                self.asset.obj_bp.rotation_euler.y = 0
                self.asset.obj_bp.rotation_euler.x = 0

            if selected_assembly and selected_assembly.obj_bp:
                if "IS_BP_PANEL" in selected_assembly.obj_bp:
                    assy_world_loc = (
                        selected_assembly.obj_bp.matrix_world[0][3],
                        selected_assembly.obj_bp.matrix_world[1][3],
                        selected_assembly.obj_bp.matrix_world[2][3])

                    assy_z_world_loc = (
                        selected_assembly.obj_z.matrix_world[0][3],
                        selected_assembly.obj_z.matrix_world[1][3],
                        selected_assembly.obj_z.matrix_world[2][3])

                    dist_to_bp = math.fabs(sn_utils.calc_distance(selected_point, assy_world_loc))
                    dist_to_z = math.fabs(sn_utils.calc_distance(selected_point, assy_z_world_loc))
                    loc_pos = selected_assembly.obj_bp.matrix_world.inverted() @ selected_point
                    self.asset.obj_bp.parent = selected_assembly.obj_bp
                    self.asset.obj_bp.location.x = loc_pos[0]
                    self.asset.obj_bp.location.z = 0
                    self.asset.obj_x.location.x = math.fabs(selected_assembly.obj_y.location.y)  # SET DEPTH

                    if selected_assembly.obj_z.location.z < 0:  # LEFT PANEL
                        if dist_to_bp > dist_to_z:  # PLACE ON RIGHT SIDE
                            self.asset.obj_bp.location.y = selected_assembly.obj_y.location.y
                            self.asset.obj_bp.rotation_euler.x = math.radians(90)
                            self.asset.obj_bp.rotation_euler.y = math.radians(0)
                            self.asset.obj_bp.rotation_euler.z = math.radians(90)
                            self.asset.obj_bp.location.z = selected_assembly.obj_z.location.z
                        else:  # PLACE ON LEFT SIDE
                            self.asset.obj_bp.location.y = 0
                            self.asset.obj_bp.rotation_euler.x = math.radians(90)
                            self.asset.obj_bp.rotation_euler.y = math.radians(180)
                            self.asset.obj_bp.rotation_euler.z = math.radians(90)
                            self.asset.obj_bp.location.z = 0
                    else:  # CENTER AND RIGHT PANEL
                        if dist_to_bp > dist_to_z:  # PLACE ON LEFT SIDE
                            self.asset.obj_bp.location.y = 0
                            self.asset.obj_bp.rotation_euler.x = math.radians(90)
                            self.asset.obj_bp.rotation_euler.y = math.radians(180)
                            self.asset.obj_bp.rotation_euler.z = math.radians(90)
                            self.asset.obj_bp.location.z = selected_assembly.obj_z.location.z
                        else:  # PLACE ON RIGHT SIDE
                            self.asset.obj_bp.location.y = selected_assembly.obj_y.location.y
                            self.asset.obj_bp.rotation_euler.x = math.radians(90)
                            self.asset.obj_bp.rotation_euler.y = math.radians(0)
                            self.asset.obj_bp.rotation_euler.z = math.radians(90)
                            self.asset.obj_bp.location.z = 0

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            bpy.context.window.cursor_set('DEFAULT')
            bpy.ops.object.select_all(action='DESELECT')
            sn_utils.set_wireframe(self.asset.obj_bp, False)
            context.view_layer.objects.active = self.asset.obj_bp
            self.asset.obj_bp.select_set(True)
            obj = self.asset.obj_bp

            if obj and "ID_PROMPT" in obj and obj["ID_PROMPT"] != "":
                id_prompt = obj["ID_PROMPT"]
                eval("bpy.ops." + id_prompt + "('INVOKE_DEFAULT')")
            else:
                bpy.ops.sn_closets.accessories('INVOKE_DEFAULT')
            for child in obj.children:
                if child.type == 'MESH':
                    child.lock_location[0] = True
                    child.lock_location[1] = True
                    child.lock_location[2] = True
            return self.finish(context)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        bpy.ops.object.select_all(action='DESELECT')
        context.area.tag_redraw()
        context.area.header_text_set(text=self.header_text)
        self.reset_selection()

        if self.event_is_cancel_command(event):
            context.area.header_text_set(None)
            return self.cancel_drop(context)

        if self.event_is_pass_through(event):
            return {'PASS_THROUGH'}

        return self.annotation_drop(context, event)

bpy.utils.register_class(PROMPTS_Prompts_Annotation)
bpy.utils.register_class(DROP_OPERATOR_Place_Annotation)
