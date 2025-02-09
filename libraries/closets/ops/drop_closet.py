import os
import math
import time

import bpy
from bpy.types import Operator
from bpy.props import StringProperty
import re

from snap import sn_types
from snap import sn_utils


class PlaceClosetAsset():
    filepath: StringProperty(name="Filepath", default="Error")
    object_name: bpy.props.StringProperty(name="Object Name")
    obj_bp_name: bpy.props.StringProperty(name="Assembly Base Point", default="")

    asset = None
    selected_asset = None

    calculators = []

    drawing_plane = None
    next_wall = None
    current_wall = None
    previous_wall = None

    starting_point = ()
    placement = ''

    assembly = None
    obj = None
    include_objects = []
    exclude_objects = []
    selected_obj = None
    selected_point = None
    mouse_x = 0
    mouse_y = 0
    header_text = ""

    class_name = ""

    def invoke(self, context, event):
        self.object_selected_original_color = bpy.context.preferences.themes[0].view_3d.object_active.copy()
        self.active_object_original_color = bpy.context.preferences.themes[0].view_3d.object_selected.copy()
        self.reset_properties()
        if not self.obj_bp_name:
            self.get_asset(context)

        if self.asset or self.obj_bp_name:
            return self.execute(context)
        else:
            return self.cancel_drop(context)

    def reset_selection(self):
        self.current_wall = None
        self.selected_asset = None
        self.next_wall = None
        self.previous_wall = None
        self.placement = ''

    def reset_properties(self):
        self.asset = None
        self.selected_asset = None
        self.calculators = []
        self.drawing_plane = None
        self.next_wall = None
        self.current_wall = None
        self.previous_wall = None
        self.starting_point = ()
        self.placement = ''
        self.assembly = None
        self.obj = None
        self.exclude_objects = []
        self.class_name = ""

    def set_child_properties(self, obj):
        if "IS_DRAWERS_BP" in obj and obj["IS_DRAWERS_BP"]:
            assembly = sn_types.Assembly(obj)
            calculator = assembly.get_calculator('Front Height Calculator')
            if calculator:
                calculator.calculate()
                self.calculators.append(calculator)

        if "IS_BP_SPLITTER" in obj and obj["IS_BP_SPLITTER"]:
            assembly = sn_types.Assembly(obj)
            calculator = assembly.get_calculator('Opening Heights Calculator')
            if calculator:
                calculator.calculate()
                self.calculators.append(calculator)

        if "IS_VISDIM_A" in obj or "IS_VISDIM_B" in obj:
            obj.hide_viewport = False
            obj.hide_set(True)

        elif obj.type == 'EMPTY':
            obj.hide_viewport = True
        if obj.type == 'MESH':
            obj.display_type = 'WIRE'

        if self.drawing_plane and obj.name != self.drawing_plane.name:
            self.exclude_objects.append(obj)
        for child in obj.children:
            self.set_child_properties(child)

    def set_placed_properties(self, obj):
        if obj.type == 'MESH':
            obj.display_type = 'TEXTURED'
        for child in obj.children:
            self.set_placed_properties(child)

    def set_screen_defaults(self, context):
        context.window.cursor_set('DEFAULT')
        context.area.header_text_set(None)        

    def set_wire_and_xray(self, obj, turn_on):
        if turn_on:
            obj.display_type = 'WIRE'
        else:
            obj.display_type = 'TEXTURED'
        obj.show_in_front = turn_on
        for child in obj.children:
            self.set_wire_and_xray(child, turn_on)

    def hide_cages(self, context):
        for obj in context.visible_objects:
            if 'IS_CAGE' in obj and 'IS_OBSTACLE' not in obj.parent:
                obj.hide_viewport = True

    def get_asset(self, context):
        wm_props = context.window_manager.snap
        self.asset = wm_props.get_asset(self.filepath)

    def draw_asset(self):
        start_time = time.perf_counter()
        directory, file = os.path.split(self.filepath)
        filename, ext = os.path.splitext(file)

        if hasattr(self.asset, 'pre_draw'):
            self.asset.pre_draw()
        else:
            self.asset.draw()

        self.asset.set_name(filename)
        self.set_child_properties(self.asset.obj_bp)

        asset_name = self.asset.obj_bp.snap.name_object

        print("{} : Draw Time --- {} seconds --- Objects in scene: {} ({} visible)".format(
            asset_name,
            round(time.perf_counter() - start_time, 8),
            len(bpy.data.objects),
            len([ob for ob in bpy.context.view_layer.objects if ob.visible_get()])))

    def position_asset(self, context):
        pass

    def add_to_wall_collection(self, context):
        collections = bpy.data.collections
        scene_coll = context.scene.collection
        wall_name = ""
        wall_collections = [coll for coll in bpy.data.collections if coll.snap.type == "WALL"]

        if self.current_wall:
            wall_name = self.current_wall.obj_bp.snap.name_object
        elif self.asset and sn_utils.get_wall_bp(self.asset.obj_bp):
            wall_name = sn_utils.get_wall_bp(self.asset.obj_bp).snap.name_object
        if wall_name:
            if wall_name in collections:
                wall_coll = collections[wall_name]
                sn_utils.clear_assembly_wall_collections(self.asset.obj_bp, wall_collections, recursive=True)
                sn_utils.add_assembly_to_collection(self.asset.obj_bp, wall_coll, recursive=True)
                sn_utils.remove_assembly_from_collection(self.asset.obj_bp, scene_coll, recursive=True)

    def confirm_placement(self, context):
        pass

    def run_asset_calculators(self):
        for calculator in self.asset.obj_prompts.snap.calculators:
            calculator.calculate()

        inserts = []
        insert_bps = sn_utils.get_insert_bp_list(self.asset.obj_bp, inserts)

        for obj_bp in insert_bps:
            if "IS_BP_SPLITTER" in obj_bp and obj_bp["IS_BP_SPLITTER"]:
                assembly = sn_types.Assembly(obj_bp)
                calculator = assembly.get_calculator('Opening Heights Calculator')
                if calculator:
                    calculator.calculate()

            if "IS_DRAWERS_BP" in obj_bp and obj_bp["IS_DRAWERS_BP"]:
                assembly = sn_types.Assembly(obj_bp)
                calculator = assembly.get_calculator('Vertical Drawers Calculator')
                if calculator:
                    calculator.calculate()
                    self.calculators.append(calculator)

    def create_drawing_plane(self, context):
        bpy.ops.mesh.primitive_plane_add()
        plane = context.active_object
        plane['IS_DRAWING_PLANE'] = True
        plane.location = (0, 0, 0)
        self.drawing_plane = context.active_object
        self.drawing_plane.display_type = 'WIRE'
        self.drawing_plane.dimensions = (100, 100, 1)

    def event_is_place_next_point(self, event):
        if self.starting_point == ():
            return False
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return True
        elif event.type == 'NUMPAD_ENTER' and event.value == 'PRESS':
            return True
        elif event.type == 'RET' and event.value == 'PRESS':
            return True
        else:
            return False

    def event_is_place_first_point(self, event):
        if self.starting_point != ():
            return False
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return True
        elif event.type == 'NUMPAD_ENTER' and event.value == 'PRESS':
            return True
        elif event.type == 'RET' and event.value == 'PRESS':
            return True
        else:
            return False

    def event_is_cancel_command(self, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            return True
        else:
            return False

    def event_is_pass_through(self, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return True
        else:
            return False

    def cancel_drop(self, context):
        self.set_screen_defaults(context)
        if self.asset:
            sn_utils.delete_object_and_children(self.asset.obj_bp)
        if self.drawing_plane:
            sn_utils.delete_object_and_children(self.drawing_plane)
        self.hide_cages(context)
        return {'CANCELLED'}

    def refresh_data(self, hide=True):
        ''' For some reason matrix world doesn't evaluate correctly
            when placing cabinets next to this if object is hidden
            For now set x, y, z object to not be hidden.
        '''
        self.asset.obj_x.hide_viewport = hide
        self.asset.obj_y.hide_viewport = hide
        self.asset.obj_z.hide_viewport = hide
        self.asset.obj_x.empty_display_size = .001
        self.asset.obj_y.empty_display_size = .001
        self.asset.obj_z.empty_display_size = .001

    def finish(self, context):
        self.add_to_wall_collection(context)
        self.asset.update_dimensions()
        self.set_screen_defaults(context)
        if self.drawing_plane:
            sn_utils.delete_obj_list([self.drawing_plane])
        if self.asset.obj_bp:
            self.set_placed_properties(self.asset.obj_bp)
            context.view_layer.objects.active = self.asset.obj_bp
        self.hide_cages(context)
        bpy.ops.object.select_all(action='DESELECT')
        context.area.tag_redraw()
        bpy.ops.closet_materials.assign_materials()
        return {'FINISHED'}


class PlaceClosetInsert(PlaceClosetAsset):
    insert = None
    openings = []
    selected_opening = None
    show_openings = True
    header_text = "Place Insert   (Esc, Right Click) = Cancel Command  :  (Left Click) = Place Insert"
    adjacent_cant_be_deeper = False

    def execute(self, context):
        context.window.cursor_set('WAIT')

        if self.obj_bp_name in bpy.data.objects:
            obj_bp = bpy.data.objects[self.obj_bp_name]
            self.insert = sn_types.Assembly(obj_bp=obj_bp)
            self.asset = self.insert
        else:
            self.draw_asset()
            self.get_insert(context)

        if self.show_openings:
            self.show_openings()
            self.include_objects = self.openings

        if self.insert is None:
            bpy.ops.snap.message_box(
                'INVOKE_DEFAULT',
                message="Could Not Find Insert Class: " + self.object_name)
            return {'CANCELLED'}

        self.set_wire_and_xray(self.insert.obj_bp, True)
        self.run_asset_calculators()
        context.window.cursor_set('PAINT_BRUSH')
        if self.header_text:
            context.area.header_text_set(text=self.header_text)        
        context.view_layer.update()  # THE SCENE MUST BE UPDATED FOR RAY CAST TO WORK
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def set_wire_and_xray(self, obj, turn_on):
        if turn_on:
            obj.display_type = 'WIRE'
        else:
            obj.display_type = 'TEXTURED'
        obj.show_in_front = turn_on
        for child in obj.children:
            self.set_wire_and_xray(child, turn_on)

    def get_insert(self, context):
        if self.asset:
            self.insert = self.asset

        if not self.insert:
            print("Insert Not found.")
            self.cancel_drop(context)

        sn_utils.init_objects(self.insert.obj_bp)
        # self.default_z_loc = self.insert.obj_bp.location.z
        # self.default_height = self.insert.obj_z.location.z
        # self.default_depth = self.insert.obj_y.location.y

    def show_openings(self):
        # Clear  to avoid old/duplicate openings
        self.openings.clear()
        insert_type = self.insert.obj_bp.snap.placement_type
        insert_op_num = self.insert.obj_bp.sn_closets.opening_name

        for obj in bpy.context.scene.objects:
            # Check to avoid opening that is part of the dropped insert
            if sn_utils.get_parent_assembly_bp(obj) == self.insert.obj_bp:
                continue

            opening = None
            if obj.snap.type_group == 'OPENING':
                wall = sn_types.Wall(obj_bp=sn_utils.get_wall_bp(obj))

                # Ensure opening status is set correctly
                product_bp = sn_utils.get_closet_bp(obj)
                if product_bp:
                    op_num = obj.sn_closets.opening_name
                    op_inserts = [o for o in product_bp.children if o.snap.type_group == 'INSERT' and o.sn_closets.opening_name == op_num]
                    if not op_inserts:
                        obj.snap.interior_open = True
                        obj.snap.exterior_open = True

                wall_hidden = False
                collections = bpy.data.collections
                wall_bp = sn_utils.get_wall_bp(obj)
                if wall_bp:
                    wall_name = wall_bp.snap.name_object
                    if wall_name in collections:
                        wall_coll = collections[wall_name]
                        wall_hidden = wall_coll.hide_viewport
                if wall and sn_utils.get_wall_bp(obj) and wall_hidden:
                    continue
                if insert_type in ('INTERIOR', 'SPLITTER'):
                    opening = sn_types.Assembly(obj) if obj.snap.interior_open else None
                if insert_type == 'EXTERIOR':
                    opening = sn_types.Assembly(obj) if obj.snap.exterior_open else None
                if opening:
                    cage = opening.get_cage()
                    cage.display_type = 'WIRE'
                    cage.hide_select = False
                    cage.hide_viewport = False
                    self.openings.append(cage)

    def get_selected_opening(self):
        selected_obj_bp = sn_utils.get_assembly_bp(self.selected_obj)

        if self.selected_obj and selected_obj_bp.snap.type_group == 'OPENING':
            self.selected_opening = sn_types.Assembly(obj_bp=self.selected_obj.parent)
        else:
            self.selected_opening = None

    def set_opening_name(self, obj, name):
        obj.sn_closets.opening_name = name
        for child in obj.children:
            self.set_opening_name(child, name)

    def confirm_placement(self, context):
        self.insert.obj_bp.parent = self.selected_opening.obj_bp.parent
        self.insert.obj_bp.location = self.selected_opening.obj_bp.location
        self.insert.obj_bp.rotation_euler = self.selected_opening.obj_bp.rotation_euler
        if self.insert.obj_bp.snap.placement_type == 'INTERIOR':
            self.selected_opening.obj_bp.snap.interior_open = False
        if self.insert.obj_bp.snap.placement_type == 'EXTERIOR':
            self.selected_opening.obj_bp.snap.exterior_open = False
        if self.insert.obj_bp.snap.placement_type == 'SPLITTER':
            self.selected_opening.obj_bp.snap.interior_open = False
            self.selected_opening.obj_bp.snap.exterior_open = False

        sn_utils.copy_assembly_drivers(self.selected_opening, self.insert)
        self.set_opening_name(self.insert.obj_bp,
                              self.selected_opening.obj_bp.sn_closets.opening_name)
        self.set_wire_and_xray(self.insert.obj_bp, False)

        for obj in self.openings:
            obj.hide_viewport = True
            obj.hide_render = True
            obj.hide_select = True

    def position_asset(self, context):
        self.get_selected_opening()

        if self.selected_obj and self.selected_opening:
            self.selected_obj.select_set(True)
            if self.selected_opening.obj_bp.parent:
                self.insert.obj_bp.rotation_euler.z = self.selected_opening.obj_bp.rotation_euler.z
                if self.insert.obj_bp.parent is not self.selected_opening.obj_bp.parent:
                    self.insert.obj_bp.matrix_world = self.selected_opening.obj_bp.matrix_world
                    self.insert.obj_x.location.x = self.selected_opening.obj_x.location.x
                    self.insert.obj_y.location.y = self.selected_opening.obj_y.location.y
                    self.insert.obj_z.location.z = self.selected_opening.obj_z.location.z

    def is_between_deeper(self):
        # If the opening on either side is deeper, this returns true
        if not self.selected_opening:
            return False

        opening_num = [child.name for child in self.selected_opening.obj_bp.parent.children if 'Opening' in child.name]
        opening_num = list(sorted(opening_num))
        opening_num = opening_num.index(self.selected_opening.obj_bp.name)

        if opening_num is None:
            print('Unknown partition number selected')
            return None

        opening_num += 1
        pard_assembly = sn_types.Assembly(obj_bp=self.selected_opening.obj_bp.parent)
        depth_1_prompt = pard_assembly.get_prompt('Opening {} Depth'.format(opening_num - 1))
        depth_2_prompt = pard_assembly.get_prompt('Opening {} Depth'.format(opening_num + 1))
        product_bp = sn_utils.get_closet_bp(pard_assembly.obj_bp)
        product = sn_types.Assembly(product_bp)
        depth_current_prompt = product.get_prompt('Opening {} Depth'.format(opening_num))
        depth_1 = depth_1_prompt.get_value() if depth_1_prompt else 0
        depth_2 = depth_2_prompt.get_value() if depth_2_prompt else 0

        if not depth_current_prompt:
            return False

        depth_current = depth_current_prompt.get_value()

        if depth_current < depth_1 or depth_current < depth_2:
            return True
        else:
            False

    def modal(self, context, event):
        self.run_asset_calculators()
        bpy.ops.object.select_all(action='DESELECT')
        context.area.tag_redraw()
        self.reset_selection()

        if len(self.openings) == 0:
            bpy.ops.snap.message_box(
                'INVOKE_DEFAULT', message="There are no openings in this scene.")
            context.area.header_text_set(None)
            return self.cancel_drop(context)

        self.selected_point, self.selected_obj, _ = sn_utils.get_selection_point(
            context,
            event,
            objects=self.include_objects,
            exclude_objects=self.exclude_objects)

        self.position_asset(context)

        if self.adjacent_cant_be_deeper and self.is_between_deeper():
            bpy.context.preferences.themes[0].view_3d.object_active = (1, 0, 0)
            bpy.context.preferences.themes[0].view_3d.object_selected = (1, 0, 0)

        elif self.adjacent_cant_be_deeper:
            bpy.context.preferences.themes[0].view_3d.object_active = (0.14902, 1, 0.6)
            bpy.context.preferences.themes[0].view_3d.object_selected = (0.14902, 1, 0.6)

        if self.event_is_place_first_point(event) and self.selected_opening:
            bpy.context.preferences.themes[0].view_3d.object_active = self.object_selected_original_color
            bpy.context.preferences.themes[0].view_3d.object_selected = self.active_object_original_color

            if self.adjacent_cant_be_deeper and self.is_between_deeper():
                bpy.ops.snap.message_box(
                    'INVOKE_DEFAULT',
                    message="This assembly cannot be placed here because it can only \n "
                            "be placed in openings with equal left and right partition depths.")
                return self.cancel_drop(context)
            self.confirm_placement(context)
            return self.finish(context)



        if self.event_is_cancel_command(event):
            bpy.context.preferences.themes[0].view_3d.object_active = self.object_selected_original_color
            bpy.context.preferences.themes[0].view_3d.object_selected = self.active_object_original_color
            return self.cancel_drop(context)

        if self.event_is_pass_through(event):
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}


class SN_CLOSET_OT_drop(Operator, PlaceClosetAsset):
    bl_idname = "sn_closets.drop"
    bl_label = "Drag and Drop"
    bl_description = "This is called when an asset is dropped from the Product library"
    bl_options = {'UNDO'}

    filepath: StringProperty(name="Library Name")

    def execute(self, context):
        scene_props = context.scene.snap
        directory, file = os.path.split(self.filepath)
        filename, ext = os.path.splitext(file)

        libs = ("Product Library", "Kitchen Bath Library")

        if scene_props.active_library_name in libs:
            if hasattr(self.asset, 'drop_id'):
                drop_id = self.asset.drop_id
                eval('bpy.ops.{}("INVOKE_DEFAULT", filepath=self.filepath)'.format(drop_id))
                return {'FINISHED'}

            bpy.ops.sn_closets.place_closet_product('INVOKE_DEFAULT', filepath=self.filepath)

        return {'FINISHED'}


class SN_CLOSET_OT_place_product(Operator, PlaceClosetAsset):
    bl_idname = "sn_closets.place_closet_product"
    bl_label = "Place Closet Product"

    def position_asset(self, context):
        wall_bp = sn_utils.get_wall_bp(self.selected_obj)
        product_bp = sn_utils.get_closet_bp(self.selected_obj)

        if product_bp:
            self.selected_asset = sn_types.Assembly(product_bp)
            sel_asset_loc_x = self.selected_asset.obj_bp.matrix_world[0][3]
            sel_asset_loc_y = self.selected_asset.obj_bp.matrix_world[1][3]
            sel_asset_loc_z = self.selected_asset.obj_bp.matrix_world[2][3]

            sel_cabinet_world_loc = (sel_asset_loc_x,
                                     sel_asset_loc_y,
                                     sel_asset_loc_z)

            sel_cabinet_x_world_loc = (self.selected_asset.obj_x.matrix_world[0][3],
                                       self.selected_asset.obj_x.matrix_world[1][3],
                                       self.selected_asset.obj_x.matrix_world[2][3])

            dist_to_bp = sn_utils.calc_distance(self.selected_point, sel_cabinet_world_loc)
            dist_to_x = sn_utils.calc_distance(self.selected_point, sel_cabinet_x_world_loc)
            rot = self.selected_asset.obj_bp.rotation_euler.z
            x_loc = 0
            y_loc = 0

            if wall_bp:
                self.current_wall = sn_types.Assembly(wall_bp)
                rot += self.current_wall.obj_bp.rotation_euler.z

            if dist_to_bp < dist_to_x:
                self.placement = 'LEFT'
                add_x_loc = 0
                add_y_loc = 0
                x_loc = sel_asset_loc_x - math.cos(rot) * self.asset.obj_x.location.x + add_x_loc
                y_loc = sel_asset_loc_y - math.sin(rot) * self.asset.obj_x.location.x + add_y_loc

            else:
                self.placement = 'RIGHT'
                x_loc = sel_asset_loc_x + math.cos(rot) * self.selected_asset.obj_x.location.x
                y_loc = sel_asset_loc_y + math.sin(rot) * self.selected_asset.obj_x.location.x

            self.asset.obj_bp.rotation_euler.z = rot
            self.asset.obj_bp.location.x = x_loc
            self.asset.obj_bp.location.y = y_loc

        elif wall_bp:
            self.placement = 'WALL'
            self.current_wall = sn_types.Wall(wall_bp)
            self.asset.obj_bp.rotation_euler = self.current_wall.obj_bp.rotation_euler
            self.asset.obj_bp.location.x = self.selected_point[0]
            self.asset.obj_bp.location.y = self.selected_point[1]
            wall_mesh = self.current_wall.get_wall_mesh()
            wall_mesh.select_set(True)

        else:
            self.asset.obj_bp.location.x = self.selected_point[0]
            self.asset.obj_bp.location.y = self.selected_point[1]

    def confirm_placement(self, context):
        if self.current_wall:
            x_loc = sn_utils.calc_distance(
                (
                    self.asset.obj_bp.location.x,
                    self.asset.obj_bp.location.y,
                    0),
                (
                    self.current_wall.obj_bp.matrix_local[0][3],
                    self.current_wall.obj_bp.matrix_local[1][3],
                    0))

            self.asset.obj_bp.location = (0, 0, self.asset.obj_bp.location.z)
            self.asset.obj_bp.rotation_euler = (0, 0, 0)
            self.asset.obj_bp.parent = self.current_wall.obj_bp
            self.asset.obj_bp.location.x = x_loc

        if self.placement == 'LEFT':
            self.asset.obj_bp.parent = self.selected_asset.obj_bp.parent
            constraint_obj = self.asset.obj_x
            constraint = self.selected_asset.obj_bp.constraints.new('COPY_LOCATION')
            constraint.target = constraint_obj
            constraint.use_x = True
            constraint.use_y = True
            constraint.use_z = False

        if self.placement == 'RIGHT':
            self.asset.obj_bp.parent = self.selected_asset.obj_bp.parent
            constraint_obj = self.selected_asset.obj_x
            constraint = self.asset.obj_bp.constraints.new('COPY_LOCATION')
            constraint.target = constraint_obj
            constraint.use_x = True
            constraint.use_y = True
            constraint.use_z = False

        if hasattr(self.asset, 'pre_draw'):
            self.asset.draw()
        self.set_child_properties(self.asset.obj_bp)

        for cal in self.calculators:
            cal.calculate()

        self.refresh_data(False)

    def execute(self, context):
        self.create_drawing_plane(context)
        self.draw_asset()
        self.run_asset_calculators()
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def validate_placement(self, context):
        if self.selected_obj is None:
            return False

        valid_placement = True
        floor = self.selected_obj.sn_roombuilder.is_floor
        drawing_plane = 'IS_DRAWING_PLANE' in self.selected_obj
        closet = None
        island = sn_utils.get_island_bp(self.asset.obj_bp)

        if self.asset.obj_bp.get("product_type"):
            closet = self.asset.obj_bp['product_type'] == "Closet"

        # Only validate if room has been created and file has been saved, allow free placement if no existing room
        if bpy.data.is_saved:
            # Check if current asset is a hang section
            if closet and not island:
                if floor or drawing_plane:
                    valid_placement = False

        return valid_placement

    def modal(self, context, event):
        self.run_asset_calculators()
        bpy.ops.object.select_all(action='DESELECT')
        context.area.tag_redraw()
        self.reset_selection()

        self.selected_point, self.selected_obj, _ = sn_utils.get_selection_point(
            context,
            event,
            objects=self.include_objects,
            exclude_objects=self.exclude_objects)

        self.position_asset(context)

        if self.event_is_place_first_point(event):
            if self.validate_placement(context):
                self.confirm_placement(context)
                return self.finish(context)

        if event.type == 'RIGHTMOUSE' and self.asset.obj_bp.get("IS_BP_CABINET"):
            wall_bp = sn_utils.get_wall_bp(self.selected_obj)
            if wall_bp:
                x_loc = sn_utils.calc_distance((self.asset.obj_bp.location.x,self.asset.obj_bp.location.y,0),
                                        (wall_bp.matrix_local[0][3],wall_bp.matrix_local[1][3],0))
                self.asset.obj_bp.location = (0,0,self.asset.obj_bp.location.z)
                self.asset.obj_bp.rotation_euler = (0,0,0)
                self.asset.obj_bp.parent = wall_bp
                self.asset.obj_bp.location.x = x_loc
                bpy.ops.sn_general.product_placement_options('INVOKE_DEFAULT',object_name=self.asset.obj_bp.name)
                bpy.ops.closet_materials.assign_materials()
                self.set_wire_and_xray(self.asset.obj_bp, False)  
                bpy.context.window.cursor_set('DEFAULT')
                return self.finish(context) 

        if self.event_is_cancel_command(event):
            return self.cancel_drop(context)

        if self.event_is_pass_through(event):
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}


class SN_CLOSET_OT_place_insert(Operator, PlaceClosetInsert):
    bl_idname = "sn_closets.drop_insert"
    bl_label = "Place Closet Insert"

    def execute(self, context):
        return super().execute(context)


classes = (
    SN_CLOSET_OT_drop,
    SN_CLOSET_OT_place_product,
    SN_CLOSET_OT_place_insert
)

register, unregister = bpy.utils.register_classes_factory(classes)