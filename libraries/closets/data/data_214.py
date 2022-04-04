import os
from os import path
import math
import time

import bpy
from bpy.types import Operator
from bpy.props import (
    FloatProperty,
    StringProperty,
    EnumProperty,
    BoolProperty)

from snap import sn_types, sn_unit, sn_utils
from snap.sn_unit import inch
from . import data_closet_splitters
from .. import closet_props
from ..common import common_lists
from ..common import common_parts
from ..common import common_prompts

SHELF_OPENING_MIN_HEIGHT = 124  # milllimeters 4H opening space

opening_height_ppt = None
shelf_stack_assembly = None


def update_product_height(self, context):
    # THIS IS A HACK!
    # FOR SOME REASON THE FORMULAS IN THE PRODUCT WILL NOT
    # RECALCULATE WHEN THE PANEL HEIGHT IS CHANGED
    obj_product_bp = sn_utils.get_bp(context.active_object, 'PRODUCT')
    product = sn_types.Assembly(obj_product_bp)
    if product:
        product.obj_z.location.z = product.obj_z.location.z


def get_opening_heights(end_hole_amt=76):
    start = SHELF_OPENING_MIN_HEIGHT
    start_hole_amt = 4
    opening_heights = data_closet_splitters.OpeningHeights(start, start_hole_amt, end_hole_amt)
    heights_iter = iter(opening_heights)
    opening_heights = list(heights_iter)

    return opening_heights


class Shelf_Stack(sn_types.Assembly):

    type_assembly = "INSERT"
    id_prompt = "sn_closets.vertical_splitters"
    drop_id = "sn_closets.insert_vertical_splitters_drop"
    placement_type = "SPLITTER"
    show_in_library = True
    category_name = "Products - Shelves"
    mirror_y = False
    calculator = None
    calculator_name = "Opening Heights Calculator"
    calculator_obj_name = "Shelf Stack Calc Distance Obj"

    splitters = []
    openings = []

    def __init__(self, obj_bp=None):
        super().__init__(obj_bp=obj_bp)
        self.splitters = []
        self.openings = []
        self.get_shelves()
        self.calculator = self.get_calculator(self.calculator_name)

    def get_shelves(self):
        for child in self.obj_bp.children:
            if child.get("IS_STACK_SHELF"):
                shelf = sn_types.Assembly(child)
                self.splitters.append(shelf)
            if child.snap.type_group == 'OPENING':
                opening = sn_types.Assembly(child)
                self.openings.append(opening)

    def add_prompts(self):
        self.add_prompt("Adj Shelf Setback", 'DISTANCE', sn_unit.inch(0.25))
        self.add_prompt("Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Left Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Right Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Top Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Bottom Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Extend Top Amount", 'DISTANCE', sn_unit.inch(0))
        self.add_prompt("Extend Bottom Amount", 'DISTANCE', sn_unit.inch(0))
        self.add_prompt("Remove Bottom Shelf", 'CHECKBOX', False)
        self.add_prompt("Shelf Quantity", 'QUANTITY', 5)
        self.add_prompt("Shelf Backing Setback", 'DISTANCE', 0)
        self.add_prompt("Parent Has Bottom KD", 'CHECKBOX', False)
        self.add_prompt('Hide', 'CHECKBOX', False)
        self.add_prompt("Thick Adjustable Shelves", 'CHECKBOX', bpy.context.scene.sn_closets.closet_defaults.thick_adjustable_shelves)
        self.add_prompt('Individual Shelf Setbacks', 'CHECKBOX', False)

    def add_calculator(self, amt):
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Thickness = self.get_prompt('Thickness').get_var("Thickness")

        self.obj_prompts.snap.remove_calculator(self.calculator_name, self.calculator_obj_name)
        calc_distance_obj = self.add_empty(self.calculator_obj_name)
        calc_distance_obj.empty_display_size = .001
        self.calculator = self.obj_prompts.snap.add_calculator(self.calculator_name, calc_distance_obj)
        self.calculator.set_total_distance("Height-Thickness*{}".format(str(amt - 1)), [Height, Thickness])

        for i in range(1, amt + 1):
            calc_prompt = self.calculator.add_calculator_prompt("Opening " + str(i) + " Height")
            calc_prompt.equal = True

    # def add_insert(self, insert, index, z_loc_vars=[], z_loc_expression=""):
        # Width = self.obj_x.snap.get_var('location.x', 'Width')
        # Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        # open_prompt = eval("self.calculator.get_calculator_prompt('Opening {} Height')".format(str(index)))
        # open_var = eval("open_prompt.get_var(self.calculator.name, 'Opening_{}_Height')".format(str(index)))
        # z_dim_expression = "Opening_" + str(index) + "_Height"

        # if insert:
        #     if not insert.obj_bp:
        #         insert.draw()
        #     insert.obj_bp.parent = self.obj_bp

        #     if index == self.vertical_openings:
        #         insert.loc_z(z_loc_expression, z_loc_vars)

        #     insert.dim_x('Width', [Width])
        #     insert.dim_y('Depth', [Depth])
        #     insert.dim_z(z_dim_expression, [open_var])

        #     if index == 1:
        #         # ALLOW DOOR TO EXTEND TO TOP OF VALANCE
        #         extend_top_amount = insert.get_prompt("Extend Top Amount")
        #         if extend_top_amount:
        #             Extend_Top_Amount = self.get_prompt("Extend Top Amount")
        #             Extend_Top_Amount.set_formula('Extend_Top_Amount', [Extend_Top_Amount])

        #     if index == self.vertical_openings:
        #         # ALLOW DOOR TO EXTEND TO BOTTOM OF VALANCE
        #         extend_bottom_amount = insert.get_prompt("Extend Bottom Amount")
        #         if extend_bottom_amount:
        #             Extend_Bottom_Amount = self.get_prompt("Extend Bottom Amount")
        #             Extend_Bottom_Amount.set_formula('Extend_Bottom_Amount', [Extend_Bottom_Amount])

    def get_opening(self, index):
        opening = common_parts.add_opening(self)
        exterior = eval('self.exterior_' + str(index))
        interior = eval('self.interior_' + str(index))

        if interior:
            opening.obj_bp.snap.interior_open = False

        if exterior:
            opening.obj_bp.snap.exterior_open = False

        return opening

    def add_splitters(self, amt=5):
        self.splitters = []
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Thickness = self.get_prompt('Thickness').get_var("Thickness")
        Remove_Bottom_Shelf = self.get_prompt('Remove Bottom Shelf').get_var("Remove_Bottom_Shelf")
        Shelf_Quantity = self.get_prompt('Shelf Quantity').get_var("Shelf_Quantity")
        Shelf_Backing_Setback = self.get_prompt('Shelf Backing Setback').get_var("Shelf_Backing_Setback")
        Parent_Has_Bottom_KD = self.get_prompt('Parent Has Bottom KD').get_var("Parent_Has_Bottom_KD")
        Individual_Shelf_Setbacks = self.get_prompt("Individual Shelf Setbacks").get_var()
        parent_hide = self.get_prompt('Hide').get_var()
        previous_splitter = None
        TAS = self.get_prompt("Thick Adjustable Shelves").get_var('TAS')

        self.add_calculator(amt)
        for i in range(1, amt + 1):
            self.add_prompt("Shelf " + str(i) + " Setback", 'DISTANCE', sn_unit.inch(0.25))
            Shelf_Setback = self.get_prompt("Shelf " + str(i) + " Setback").get_var("Shelf_Setback")
            height_prompt = eval("self.calculator.get_calculator_prompt('Opening {} Height')".format(str(i)))
            opening_height = eval("height_prompt.get_var(self.calculator.name, 'opening_{}_height')".format(str(i)))

            splitter = common_parts.add_shelf(self)
            splitter.obj_bp["IS_STACK_SHELF"] = True
            self.splitters.append(splitter)
            Is_Locked_Shelf = splitter.get_prompt('Is Locked Shelf').get_var('Is_Locked_Shelf')
            IBEKD = splitter.get_prompt('Is Bottom Exposed KD').get_var('IBEKD')
            Adj_Shelf_Setback = splitter.get_prompt('Adj Shelf Setback').get_var('Adj_Shelf_Setback')
            Locked_Shelf_Setback = splitter.get_prompt('Locked Shelf Setback').get_var('Locked_Shelf_Setback')
            Adj_Shelf_Clip_Gap = splitter.get_prompt('Adj Shelf Clip Gap').get_var('Adj_Shelf_Clip_Gap')
            Shelf_Setback_All = self.get_prompt("Adj Shelf Setback").get_var('Shelf_Setback_All')

            splitter.loc_x('IF(Is_Locked_Shelf,0,Adj_Shelf_Clip_Gap)', [Is_Locked_Shelf, Adj_Shelf_Clip_Gap])
            splitter.loc_y('Depth-Shelf_Backing_Setback', [Depth, Shelf_Backing_Setback])

            if previous_splitter:
                if i != amt:  # Not last Shelf
                    Previous_Z_Loc = previous_splitter.obj_bp.snap.get_var("location.z", "Previous_Z_Loc")
                    splitter.loc_z('Previous_Z_Loc-opening_{}_height-Thickness'.format(str(i)), [Previous_Z_Loc, opening_height, Thickness])
                else:
                    is_locked_shelf = splitter.get_prompt("Is Locked Shelf")
                    is_locked_shelf.set_value(True)
                    hide = splitter.get_prompt("Hide")
                    hide.set_formula(
                        'IF(Remove_Bottom_Shelf,True,IF(Parent_Has_Bottom_KD,True,False)) or Hide',
                        [Remove_Bottom_Shelf, Parent_Has_Bottom_KD, parent_hide])
                    splitter.get_prompt("Is Forced Locked Shelf").set_value(value=True)

                    IBEKD = splitter.get_prompt('Is Bottom Exposed KD').get_var('IBEKD')
                    splitter.loc_y('Depth', [Depth])
                    # bottom_shelf.loc_z('IF(AND(TAS,IBEKD==False), INCH(0.25), 0)', [TAS, IBEKD, Thickness])
                    splitter.dim_x('Width', [Width])
                    splitter.dim_y('-Depth', [Depth])
                    # bottom_shelf.dim_z('IF(AND(TAS,IBEKD==False), INCH(1),Thickness) *-1', [Thickness, TAS, IBEKD])
                    splitter.dim_z('-Thickness', [Thickness, TAS, IBEKD])
            else:
                splitter.loc_z('Height-opening_{}_height'.format(str(i)), [Height, opening_height])

            splitter.dim_x(
                'Width-IF(Is_Locked_Shelf,0,Adj_Shelf_Clip_Gap*2)',
                [Width, Is_Locked_Shelf, Adj_Shelf_Clip_Gap])
            splitter.dim_y(
                '-Depth+IF(Is_Locked_Shelf,Locked_Shelf_Setback,Adj_Shelf_Setback)+Shelf_Backing_Setback',
                [Depth, Locked_Shelf_Setback, Is_Locked_Shelf, Adj_Shelf_Setback, Shelf_Backing_Setback])
            splitter.dim_z('IF(AND(TAS,IBEKD==False), INCH(1),Thickness) *-1', [Thickness, TAS, IBEKD])
            splitter.get_prompt("Adj Shelf Setback").set_formula(
                'IF(Individual_Shelf_Setbacks,Shelf_Setback,Shelf_Setback_All)',
                [Shelf_Setback, Shelf_Setback_All, Individual_Shelf_Setbacks])

            opening = common_parts.add_opening(self)
            opening.obj_bp.sn_closets.opening_name = str(i)
            self.openings.append(opening)

            if previous_splitter:
                if i != amt + 1:  # Not last opening
                    opening_z_loc = previous_splitter.obj_bp.snap.get_var("location.z", "opening_z_loc")
                    opening.loc_z('opening_z_loc', [opening_z_loc])
                    opening.dim_z('opening_{}_height'.format(str(i)), [opening_height, Thickness])
            else:
                opening.dim_z('opening_{}_height'.format(str(i)), [opening_height])

            opening.dim_x('Width', [Width])
            opening.dim_y('Depth', [Depth])
            previous_splitter = splitter

        for splitter in self.splitters:
            sn_utils.update_obj_driver_expressions(splitter.obj_bp)

    def update(self):
        super().update()
        self.obj_bp.snap.export_as_subassembly = True

        self.obj_bp['IS_BP_SPLITTER'] = True
        props = self.obj_bp.sn_closets
        props.is_splitter_bp = True  # TODO: remove

    def draw(self):
        self.create_assembly()
        hide_prompt = self.add_prompt('Hide', 'CHECKBOX', False)
        self.hide_var = hide_prompt.get_var()
        self.add_prompts()
        self.add_splitters()
        self.update()


class PROMPTS_Vertical_Splitter_Prompts_214(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.vertical_splitters_214"
    bl_label = "Shelf Prompts"
    bl_description = "This shows all of the available vertical splitter options"
    bl_options = {'UNDO'}

    object_name: bpy.props.StringProperty(name="Object Name")

    shelf_quantity: bpy.props.EnumProperty(name="Shelf Quantity",
                                           items=[('1', "1", '1'),
                                                  ('2', "2", '2'),
                                                  ('3', "3", '3'),
                                                  ('4', "4", '4'),
                                                  ('5', "5", '5'),
                                                  ('6', "6", '6'),
                                                  ('7', "7", '7'),
                                                  ('8', "8", '8'),
                                                  ('9', "9", '9'),
                                                  ('10', "10", '10'),
                                                  ('11', "11", '11'),
                                                  ('12', "12", '12'),
                                                  ('13', "13", '13'),
                                                  ('14', "14", '14'),
                                                  ('15', "15", '15')],
                                           default='5')

    assembly = None
    cur_shelf_height = None

    def update_shelves(self):
        shelf_amt_changed = len(self.assembly.splitters) != int(self.shelf_quantity)

        if shelf_amt_changed:
            for i, assembly in enumerate(self.assembly.splitters):
                sn_utils.delete_object_and_children(assembly.obj_bp)
                setback_ppt = self.assembly.get_prompt("Shelf " + str(i + 1) + " Setback")

                if setback_ppt:
                    bpy.ops.sn_prompt.delete_prompt(
                        obj_name=self.assembly.obj_prompts.name,
                        prompt_name=setback_ppt.name)

            self.assembly.splitters.clear()
            for assembly in self.assembly.openings:
                sn_utils.delete_object_and_children(assembly.obj_bp)
            self.assembly.openings.clear()
            self.assembly.add_splitters(amt=int(self.shelf_quantity))

        self.assembly.update()
        shelf = self.assembly.splitters[0]
        for child in shelf.obj_bp.children:
            if child.type == 'MESH':
                bpy.context.view_layer.objects.active = child

    def closest_hole_amt(self, opening_heights, height):
        return opening_heights[min(range(len(opening_heights)), key=lambda i: abs(opening_heights[i] - height))]

    def update_opening_heights(self):
        for i in range(1, int(self.shelf_quantity) + 1):
            opening_height = self.assembly.get_prompt("Opening " + str(i) + " Height")
            if opening_height:
                if not opening_height.equal:
                    op_heights = [float(height[0]) for height in get_opening_heights()]
                    height = opening_height.get_value()
                    closest_hole_amt = self.closest_hole_amt(op_heights, sn_unit.meter_to_millimeter(height))
                    opening_height.set_value(sn_unit.millimeter(closest_hole_amt))

    def check(self, context):
        self.set_prompts_from_properties()
        self.update_shelves()
        self.update_openings()
        self.update_opening_heights()

        opening = self.assembly.obj_bp.sn_closets.opening_name
        parent_obj = self.assembly.obj_bp.parent
        parent_assembly = sn_types.Assembly(parent_obj)
        parent_remove_bottom_shelf = parent_assembly.get_prompt('Remove Bottom Hanging Shelf ' + str(opening))
        floor = parent_assembly.get_prompt("Opening " + str(opening) + " Floor Mounted")
        remove_bottom_shelf = self.assembly.get_prompt("Remove Bottom Shelf")
        parent_has_bottom_kd = self.assembly.get_prompt("Parent Has Bottom KD")
        prompts = [floor, parent_remove_bottom_shelf, remove_bottom_shelf, parent_has_bottom_kd]

        if all(prompts):
            if parent_remove_bottom_shelf.get_value() or floor.get_value():
                parent_has_bottom_kd.set_value(True)
                remove_bottom_shelf.set_value(True)
            else:
                parent_remove_bottom_shelf.set_value(False)
                parent_has_bottom_kd.set_value(False)

        self.run_calculators(self.assembly.obj_bp)
        closet_props.update_render_materials(self, context)
        return True

    def update_openings(self):
        '''This should be called in the check function before set_prompts_from_properties
           updates which openings are available based on the value of shelf_quantity
        '''
        shelf_quantity = self.assembly.get_prompt("Shelf Quantity")
        if (shelf_quantity):
            if shelf_quantity.get_value() != int(self.shelf_quantity):
                for child in self.assembly.obj_bp.children:
                    if child.snap.type_group == 'OPENING':
                        if int(child.sn_closets.opening_name) > int(self.shelf_quantity) + 1:
                            child.snap.interior_open = False
                            child.snap.exterior_open = False
                        else:
                            shares_location = False
                            for cchild in self.assembly.obj_bp.children:
                                if cchild.snap.type_group != 'OPENING':
                                    if cchild.location == child.location:
                                        shares_location = True
                            if not shares_location:
                                child.snap.interior_open = True
                                child.snap.exterior_open = True

    def set_prompts_from_properties(self):
        ''' This should be called in the check function to set the prompts
            to the same values as the class properties
        '''
        shelf_quantity = self.assembly.get_prompt("Shelf Quantity")
        if shelf_quantity:
            shelf_quantity.set_value(int(self.shelf_quantity))

    def set_properties_from_prompts(self):
        ''' This should be called in the invoke function to set the class properties
            to the same values as the prompts
        '''
        shelf_quantity = self.assembly.get_prompt("Shelf Quantity")
        if shelf_quantity:
            self.shelf_quantity = str(shelf_quantity.get_value())

    def get_splitter(self, obj_bp):
        ''' Gets the splitter based on selection
        '''
        props = self.obj_bp.sn_closets
        if props.is_splitter_bp:
            return sn_types.Assembly(obj_bp)
        if obj_bp.parent:
            return self.get_splitter(obj_bp.parent)

    def invoke(self, context, event):
        self.assembly = Shelf_Stack(self.get_insert().obj_bp)
        self.set_properties_from_prompts()
        self.calculators = []
        heights_calc = self.assembly.get_calculator('Opening Heights Calculator')
        if heights_calc:
            self.calculators.append(heights_calc)
        self.run_calculators(self.assembly.obj_bp)

        opening = self.assembly.obj_bp.sn_closets.opening_name
        parent_obj = self.assembly.obj_bp.parent
        parent_assembly = sn_types.Assembly(parent_obj)
        # TODO: If parent_remove_bottom_shelf True bottom KD IS enabled. This prompt is named incorrectly
        parent_remove_bottom_shelf = parent_assembly.get_prompt('Remove Bottom Hanging Shelf ' + str(opening))
        door_type = parent_assembly.get_prompt("Door Type")
        floor = parent_assembly.get_prompt("Opening " + str(opening) + " Floor Mounted")
        remove_bottom_shelf = self.assembly.get_prompt("Remove Bottom Shelf")
        parent_has_bottom_kd = self.assembly.get_prompt("Parent Has Bottom KD")
        prompts = [floor, parent_remove_bottom_shelf, remove_bottom_shelf, parent_has_bottom_kd]

        if all(prompts):
            if parent_remove_bottom_shelf.get_value() or floor.get_value():
                parent_has_bottom_kd.set_value(True)
                remove_bottom_shelf.set_value(True)
            else:
                parent_remove_bottom_shelf.set_value(False)
                parent_has_bottom_kd.set_value(False)
        elif door_type:
            if door_type.get_value() == 0:
                remove_bottom_shelf.set_value(True)

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)

    def execute(self, context):
        return {'FINISHED'}

    def get_number_of_equal_heights(self):
        shelf_qty = self.assembly.get_prompt("Shelf Quantity")
        number_of_equal_heights = 0

        for i in range(1, shelf_qty.get_value() + 1):
            calculator = self.assembly.get_calculator('Opening Heights Calculator')
            height = eval("calculator.get_calculator_prompt('Opening {} Height')".format(str(i)))

            if height:
                number_of_equal_heights += 1 if height.equal else 0
            else:
                break

        return number_of_equal_heights

    def draw_splitter_heights(self, layout):
        shelf_qty = self.assembly.get_prompt("Shelf Quantity")
        idv_shelf_setbacks = self.assembly.get_prompt("Individual Shelf Setbacks")

        props = bpy.context.scene.sn_closets
        opening_heights = get_opening_heights()

        col = layout.column(align=True)
        box = col.box()
        box.label(text="Opening Heights:")

        # for i in range(1, shelf_qty.get_value() + 1):
        for i, shelf in enumerate(self.assembly.splitters):
            calculator = self.assembly.get_calculator('Opening Heights Calculator')
            height = eval("calculator.get_calculator_prompt('Opening {} Height')".format(str(i + 1)))
            setback = self.assembly.get_prompt("Shelf " + str(i + 1) + " Setback")
            is_locked_shelf = shelf.get_prompt("Is Locked Shelf")

            if height:
                row = box.row()
                row.label(text="Opening " + str(i + 1) + ":")
                if not height.equal:
                    row.prop(height, 'equal', text="")
                else:
                    if self.get_number_of_equal_heights() != 1:
                        row.prop(height, 'equal', text="")
                    else:
                        row.label(text="", icon='BLANK1')
                if height.equal:
                    row.label(text=str(round(sn_unit.meter_to_active_unit(height.distance_value), 3)) + '"')
                else:
                    label = ""
                    for opening_height in opening_heights:
                        if float(opening_height[0]) == round(sn_unit.meter_to_millimeter(height.distance_value), 1):
                            label = opening_height[1]
                    row.menu("SNAP_MT_Opening_{}_Heights".format(str(i + 1)), text=label)

            if setback and idv_shelf_setbacks and is_locked_shelf:
                if idv_shelf_setbacks.get_value() and not is_locked_shelf.get_value():
                    row = box.row()
                    row.label(text="Shelf " + str(i + 1) + " Setback")
                    row.prop(setback, 'distance_value', text="")

    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                box = layout.box()
                row = box.row()
                adj_shelf_setback = self.assembly.get_prompt("Adj Shelf Setback")
                shelf_quantity = self.assembly.get_prompt("Shelf Quantity")
                idv_shelf_setbacks = self.assembly.get_prompt("Individual Shelf Setbacks")

                if shelf_quantity:
                    col = box.column(align=True)
                    row = col.row()
                    row.label(text="Qty:")
                    row.prop(self, "shelf_quantity", expand=True)

                if adj_shelf_setback:
                    col = box.column(align=True)
                    row = col.row()
                    adj_shelf_setback.draw(row, allow_edit=False)

                if idv_shelf_setbacks:
                    col = box.column(align=True)
                    row = col.row()
                    idv_shelf_setbacks.draw(row, allow_edit=False)

                self.draw_splitter_heights(box)

                remove_bottom_shelf = self.assembly.get_prompt('Remove Bottom Shelf')
                if remove_bottom_shelf:
                    box.prop(remove_bottom_shelf, "checkbox_value", text=remove_bottom_shelf.name)


class L_Shelves(sn_types.Assembly):

    """
    This L Shelf Includes a Back Spine for support and is hanging first
    """

    category_name = ""
    type_assembly = "PRODUCT"
    id_prompt = "sn_closets.l_shelves"
    show_in_library = True
    placement_type = 'CORNER'

    def pre_draw(self):
        self.create_assembly()
        hide_prompt = self.add_prompt('Hide', 'CHECKBOX', False)
        self.hide_var = hide_prompt.get_var()
        self.obj_x.location.x = self.width
        self.obj_y.location.y = -self.depth
        self.obj_z.location.z = self.height

        props = bpy.context.scene.sn_closets

        self.add_prompt("Panel Height", 'DISTANCE', sn_unit.millimeter(2003))
        self.add_prompt("Back Inset", 'DISTANCE', sn_unit.inch(.25))
        self.add_prompt("Spine Width", 'DISTANCE', sn_unit.inch(1))
        self.add_prompt("Spine Y Location", 'DISTANCE', sn_unit.inch(2.1))
        self.add_prompt("Cleat Height", 'DISTANCE', sn_unit.inch(3.64))
        self.add_prompt("Left Depth", 'DISTANCE', sn_unit.inch(12))
        self.add_prompt("Right Depth", 'DISTANCE', sn_unit.inch(12))
        self.add_prompt("Shelf Quantity", 'QUANTITY', 3)
        self.add_prompt("Add Top KD", 'CHECKBOX', True)  # export=True
        self.add_prompt("Hide Toe Kick", 'CHECKBOX', False)  # export=True
        self.add_prompt("Add Backing", 'CHECKBOX', False)  # export=True
        self.add_prompt("Is Hanging", 'CHECKBOX', False)  # export=True
        self.add_prompt("Remove Left Side", 'CHECKBOX', False)  # export=True
        self.add_prompt("Remove Right Side", 'CHECKBOX', False)  # export=True
        self.add_prompt("Force Double Doors", 'CHECKBOX', False)  # export=True
        self.add_prompt("Door", 'CHECKBOX', False)  # export=True
        self.add_prompt("Door Pull Height", 'DISTANCE', sn_unit.inch(36))
        self.add_prompt("Backing Thickness", 'DISTANCE', sn_unit.inch(0.75))

        self.add_prompt("Door Type", 'COMBOBOX', 0, ["Reach Back", "Lazy Susan"])
        self.add_prompt("Open Door", 'PERCENTAGE', 0)
        self.add_prompt("Door Rotation", 'QUANTITY', 120)
        self.add_prompt("Half Open", 'PERCENTAGE', 0.5)
        self.add_prompt("Pull Type", 'COMBOBOX', 1, ["Base", "Tall", "Upper"])
        self.add_prompt("Pull Location", 'COMBOBOX', 0, ["Pull on Left Door", "Pull on Right Door"])

        self.add_prompt("Add Top Shelf", 'CHECKBOX', False)
        self.add_prompt("Exposed Left", 'CHECKBOX', False)
        self.add_prompt("Exposed Right", 'CHECKBOX', False)
        self.add_prompt("Top Shelf Overhang", 'DISTANCE', sn_unit.inch(0.5))
        self.add_prompt("Extend Left", 'DISTANCE', 0)
        self.add_prompt("Extend Right", 'DISTANCE', 0)

        self.add_prompt("Add Left Filler", 'CHECKBOX', False)
        self.add_prompt("Add Right Filler", 'CHECKBOX', False)
        self.add_prompt("Left Side Wall Filler", 'DISTANCE', 0.0)
        self.add_prompt("Right Side Wall Filler", 'DISTANCE', 0.0)
        self.add_prompt("Add Capping Left Filler", 'CHECKBOX', False)
        self.add_prompt("Add Capping Right Filler", 'CHECKBOX', False)
        self.add_prompt("Left Filler Setback Amount", 'DISTANCE', 0.0)
        self.add_prompt("Right Filler Setback Amount", 'DISTANCE', 0.0)
        self.add_prompt("Edge Bottom of Left Filler", 'CHECKBOX', False)
        self.add_prompt("Edge Bottom of Right Filler", 'CHECKBOX', False)

        for i in range(1, 11):
            self.add_prompt("Shelf " + str(i) + " Height", 'DISTANCE', sn_unit.millimeter(653.034))

        common_prompts.add_toe_kick_prompts(self)
        common_prompts.add_thickness_prompts(self)
        common_prompts.add_door_prompts(self)
        common_prompts.add_door_pull_prompts(self)

        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Panel_Height = self.get_prompt('Panel Height').get_var('Panel_Height')
        Left_Depth = self.get_prompt('Left Depth').get_var('Left_Depth')
        Right_Depth = self.get_prompt('Right Depth').get_var('Right_Depth')
        Shelf_Thickness = self.get_prompt('Shelf Thickness').get_var('Shelf_Thickness')
        PT = self.get_prompt('Panel Thickness').get_var("PT")
        Toe_Kick_Height = self.get_prompt('Toe Kick Height').get_var('Toe_Kick_Height')
        Toe_Kick_Setback = self.get_prompt('Toe Kick Setback').get_var('Toe_Kick_Setback')
        Hide_Toe_Kick = self.get_prompt('Hide Toe Kick').get_var('Hide_Toe_Kick')
        Shelf_Quantity = self.get_prompt('Shelf Quantity').get_var('Shelf_Quantity')
        Add_Backing = self.get_prompt('Add Backing').get_var('Add_Backing')
        Back_Inset = self.get_prompt('Back Inset').get_var('Back_Inset')
        DT = self.get_prompt('Door Type').get_var('DT')
        Add_Top = self.get_prompt('Add Top KD').get_var('Add_Top')
        Backing_Thickness = self.get_prompt('Backing Thickness').get_var('Backing_Thickness')
        Is_Hanging = self.get_prompt('Is Hanging').get_var('Is_Hanging')
        RLS = self.get_prompt('Remove Left Side').get_var("RLS")
        RRS = self.get_prompt('Remove Right Side').get_var("RRS")
        Spine_Width = self.get_prompt('Spine Width').get_var('Spine_Width')
        Spine_Y_Location = self.get_prompt('Spine Y Location').get_var('Spine_Y_Location')
        Cleat_Height = self.get_prompt('Cleat Height').get_var('Cleat_Height')
        Door = self.get_prompt('Door').get_var('Door')
        Door_Pull_Height = self.get_prompt('Door Pull Height').get_var('Door_Pull_Height')
        Pull_Location = self.get_prompt("Pull Location").get_var('Pull_Location')
        Open = self.get_prompt("Open Door").get_var('Open')
        Rotation = self.get_prompt("Door Rotation").get_var('Rotation')
        Half = self.get_prompt("Half Open").get_var('Half')
        Pull_Type = self.get_prompt("Pull Type").get_var('Pull_Type')
        Base_Pull_Location = self.get_prompt("Base Pull Location").get_var('Base_Pull_Location')
        Tall_Pull_Location = self.get_prompt("Tall Pull Location").get_var('Tall_Pull_Location')
        Upper_Pull_Location = self.get_prompt("Upper Pull Location").get_var('Upper_Pull_Location')
        World_Z = self.obj_bp.snap.get_var('matrix_world[2][3]', 'World_Z')
        Add_Top_Shelf = self.get_prompt('Add Top Shelf').get_var('Add_Top_Shelf')
        Exposed_Left = self.get_prompt('Exposed Left').get_var('Exposed_Left')
        Exposed_Right = self.get_prompt('Exposed Right').get_var('Exposed_Right')
        Top_Shelf_Overhang = self.get_prompt('Top Shelf Overhang').get_var('Top_Shelf_Overhang')
        Left_Side_Wall_Filler = self.get_prompt('Left Side Wall Filler').get_var('Left_Side_Wall_Filler')
        Panel_Thickness = self.get_prompt('Panel Thickness').get_var('Panel_Thickness')
        Left_Filler_Setback_Amount = self.get_prompt('Left Filler Setback Amount').get_var()
        Edge_Bottom_of_Left_Filler = self.get_prompt("Edge Bottom of Left Filler").get_var()
        Add_Capping_Left_Filler = self.get_prompt("Add Capping Left Filler").get_var()
        Right_Side_Wall_Filler = self.get_prompt('Right Side Wall Filler').get_var('Right_Side_Wall_Filler')
        Right_Filler_Setback_Amount = self.get_prompt('Right Filler Setback Amount').get_var()
        Edge_Bottom_of_Right_Filler = self.get_prompt("Edge Bottom of Right Filler").get_var()
        Add_Capping_Right_Filler = self.get_prompt("Add Capping Right Filler").get_var()
        Extend_Left = self.get_prompt('Extend Left').get_var('Extend_Left')
        Extend_Right = self.get_prompt('Extend Right').get_var('Extend_Right')

        top = common_parts.add_l_shelf(self)
        top.loc_z('(Height+IF(Is_Hanging,0,Toe_Kick_Height))', [Height, Toe_Kick_Height, Is_Hanging])
        top.dim_x('Width-IF(RRS,0,PT)', [Width, RRS, PT])
        top.dim_y('Depth+IF(RLS,0,PT)', [Depth, PT, RLS])
        top.dim_z('-Shelf_Thickness', [Shelf_Thickness])
        top.get_prompt('Left Depth').set_formula('Left_Depth', [Left_Depth])
        top.get_prompt('Right Depth').set_formula('Right_Depth', [Right_Depth])
        top.get_prompt("Is Locked Shelf").set_value(True)
        top.get_prompt('Hide').set_formula('IF(Add_Top,False,True)', [Add_Top])

        left_top_shelf = common_parts.add_plant_on_top(self)
        left_top_shelf.set_name('Topshelf')
        left_top_shelf.loc_y(
            'Depth-Left_Side_Wall_Filler-Extend_Left', [Depth, Left_Side_Wall_Filler, Extend_Left])
        left_top_shelf.loc_z('(Height+IF(Is_Hanging,0,Toe_Kick_Height))+PT', [Height, Toe_Kick_Height, Is_Hanging, PT])
        left_top_shelf.dim_x(
            '(Depth+Right_Depth+Top_Shelf_Overhang-Extend_Left)*-1+Left_Side_Wall_Filler',
            [Right_Depth, RRS, PT, Depth,
             Top_Shelf_Overhang, Left_Side_Wall_Filler, Extend_Left])
        left_top_shelf.dim_y('-Left_Depth-Top_Shelf_Overhang', [Depth, PT, RLS, Left_Depth, Top_Shelf_Overhang])
        left_top_shelf.dim_z('-Shelf_Thickness', [Shelf_Thickness])
        left_top_shelf.rot_z(value=math.radians(90))
        left_top_shelf.get_prompt('Exposed Left').set_formula('Exposed_Left', [Exposed_Left])
        left_top_shelf.get_prompt('Hide').set_formula('IF(Add_Top_Shelf,False,True)', [Add_Top_Shelf])

        right_top_shelf = common_parts.add_plant_on_top(self)
        right_top_shelf.set_name('Topshelf')
        right_top_shelf.loc_z('(Height+IF(Is_Hanging,0,Toe_Kick_Height))+PT', [Height, Toe_Kick_Height, Is_Hanging, PT])
        right_top_shelf.dim_x(
            'Width+Right_Side_Wall_Filler+Extend_Right',
            [Width, RRS, PT, Right_Side_Wall_Filler, Extend_Right])
        right_top_shelf.dim_y('-Right_Depth-Top_Shelf_Overhang', [Right_Depth, PT, RLS, Top_Shelf_Overhang])
        right_top_shelf.dim_z('-Shelf_Thickness', [Shelf_Thickness])
        right_top_shelf.get_prompt('Exposed Right').set_formula('Exposed_Right', [Exposed_Right])
        right_top_shelf.get_prompt('Hide').set_formula('IF(Add_Top_Shelf,False,True)', [Add_Top_Shelf])

        right_top_cleat = common_parts.add_cleat(self)
        right_top_cleat.set_name("Top Cleat")
        right_top_cleat.loc_x('Spine_Width', [Spine_Width])
        right_top_cleat.loc_z('(IF(Add_Top,Height-Shelf_Thickness,Height))+IF(Is_Hanging,0,Toe_Kick_Height)',
                              [Height, Shelf_Thickness, Add_Top, Is_Hanging, Toe_Kick_Height])
        right_top_cleat.rot_x(value=math.radians(-90))
        right_top_cleat.dim_x('Width-Spine_Width-IF(RRS,0,PT)', [RRS, Width, PT, Spine_Width])
        right_top_cleat.dim_y('Cleat_Height', [Cleat_Height])
        right_top_cleat.dim_z('-PT', [PT])
        right_top_cleat.get_prompt('Hide').set_formula('IF(Add_Backing,True,False) or Hide', [self.hide_var, Add_Backing])

        left_top_cleat = common_parts.add_cleat(self)
        left_top_cleat.set_name("Top Cleat")
        left_top_cleat.loc_y('IF(RLS,Depth,Depth+PT)', [Depth, RLS, PT])
        left_top_cleat.loc_z('(IF(Add_Top,Height-Shelf_Thickness,Height))+IF(Is_Hanging,0,Toe_Kick_Height)', [Height, Shelf_Thickness, Add_Top, Is_Hanging, Toe_Kick_Height])
        left_top_cleat.rot_x(value=math.radians(-90))
        left_top_cleat.rot_z(value=math.radians(90))
        left_top_cleat.dim_x('-Depth-Spine_Width-IF(RLS,0,PT)', [RLS, Depth, PT, Spine_Width])
        left_top_cleat.dim_y('Cleat_Height', [Cleat_Height])
        left_top_cleat.dim_z('-PT', [PT])
        left_top_cleat.get_prompt('Hide').set_formula('IF(Add_Backing,True,False) or Hide', [self.hide_var, Add_Backing])

        bottom = common_parts.add_l_shelf(self)
        bottom.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)', [Is_Hanging, Height, Panel_Height, Toe_Kick_Height])
        bottom.dim_x('Width-IF(RRS,0,PT)', [Width, RRS, PT])
        bottom.dim_y('Depth+IF(RLS,0,PT)', [Depth, PT, RLS])
        bottom.dim_z('Shelf_Thickness', [Shelf_Thickness])
        bottom.get_prompt('Left Depth').set_formula('Left_Depth', [Left_Depth])
        bottom.get_prompt('Right Depth').set_formula('Right_Depth', [Right_Depth])
        bottom.get_prompt('Is Locked Shelf').set_value(True)

        right_bot_cleat = common_parts.add_cleat(self)
        right_bot_cleat.set_name("Bottom Cleat")
        right_bot_cleat.loc_x('Spine_Width', [Spine_Width])
        right_bot_cleat.loc_z('IF(Is_Hanging,Height-Panel_Height+Shelf_Thickness,Shelf_Thickness+Toe_Kick_Height)', [Height, Panel_Height, Is_Hanging, Shelf_Thickness, Toe_Kick_Height])
        right_bot_cleat.rot_x(value=math.radians(-90))
        right_bot_cleat.dim_x('Width-Spine_Width-IF(RRS,0,PT)', [RRS, Width, PT, Spine_Width])
        right_bot_cleat.dim_y('-Cleat_Height', [Cleat_Height])
        right_bot_cleat.dim_z('-PT', [PT])
        right_bot_cleat.get_prompt('Hide').set_formula('IF(Add_Backing,True,False) or Hide', [self.hide_var, Add_Backing])

        left_bot_cleat = common_parts.add_cleat(self)
        left_bot_cleat.set_name("Bottom Cleat")
        left_bot_cleat.loc_y('IF(RLS,Depth,Depth+PT)', [Depth, RLS, PT])
        left_bot_cleat.loc_z('IF(Is_Hanging,Height-Panel_Height+Shelf_Thickness,Shelf_Thickness+Toe_Kick_Height)', [Height, Panel_Height, Is_Hanging, Shelf_Thickness, Toe_Kick_Height])
        left_bot_cleat.rot_x(value=math.radians(-90))
        left_bot_cleat.rot_z(value=math.radians(90))
        left_bot_cleat.dim_x('-Depth-Spine_Width-IF(RLS,0,PT)', [RLS, Depth, PT, Spine_Width])
        left_bot_cleat.dim_y('-Cleat_Height', [Cleat_Height])
        left_bot_cleat.dim_z('-PT', [PT])
        left_bot_cleat.get_prompt('Hide').set_formula('IF(Add_Backing,True,False) or Hide', [self.hide_var, Add_Backing])

        left_panel = common_parts.add_panel(self)
        left_panel.loc_y('Depth', [Depth, Add_Backing])
        left_panel.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height])
        left_panel.rot_y(value=math.radians(-90))
        left_panel.rot_z(value=math.radians(-90))
        left_panel.dim_x('Panel_Height', [Panel_Height])
        left_panel.dim_y('Left_Depth', [Left_Depth])
        left_panel.dim_z('PT', [PT])
        left_panel.get_prompt('Left Depth').set_formula('Left_Depth', [Left_Depth])  # Adding this in order to drill the panel on one side
        left_panel.get_prompt('Hide').set_formula('IF(RLS,True,False)', [RLS])

        right_panel = common_parts.add_panel(self)
        right_panel.loc_x('Width-PT', [Width, PT])
        right_panel.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height])
        right_panel.rot_y(value=math.radians(-90))
        right_panel.rot_z(value=math.radians(180))
        right_panel.dim_x('Panel_Height', [Panel_Height])
        right_panel.dim_y('Right_Depth', [Right_Depth])
        right_panel.dim_z('PT', [PT])
        right_panel.get_prompt('Right Depth').set_formula('Right_Depth', [Right_Depth])  # Adding this in order to drill the panel on one side
        right_panel.get_prompt('Hide').set_formula('IF(RRS,True,False)', [RRS])

        right_back = common_parts.add_corner_back(self)
        right_back.set_name("Backing")
        right_back.loc_x('Width-PT', [Width, PT])
        right_back.loc_y('-PT', [PT])
        right_back.loc_z('IF(Is_Hanging,Height-Panel_Height+PT,Toe_Kick_Height+PT)',
                         [Height, Panel_Height, Is_Hanging, Toe_Kick_Height, Cleat_Height, Back_Inset, PT])
        right_back.rot_y(value=math.radians(-90))
        right_back.rot_z(value=math.radians(-90))
        right_back.dim_x('Panel_Height-PT-IF(Add_Top,PT,0)', [Panel_Height, Cleat_Height, Back_Inset, PT, Add_Top])
        right_back.dim_y('-Width+(PT*2)', [Width, PT])
        right_back.dim_z('Backing_Thickness', [Backing_Thickness])
        right_back.get_prompt('Hide').set_formula('IF(Add_Backing,False,True)', [Add_Backing])

        left_back = common_parts.add_corner_back(self)
        left_back.loc_y('Depth+PT', [Depth, PT])
        left_back.loc_z('IF(Is_Hanging,Height-Panel_Height+PT,Toe_Kick_Height+PT)',
                        [Height, Panel_Height, Is_Hanging, Toe_Kick_Height, Cleat_Height, Back_Inset, PT])
        left_back.rot_y(value=math.radians(-90))
        left_back.rot_z(value=math.radians(-180))
        left_back.dim_x('Panel_Height-PT-IF(Add_Top,PT,0)', [Panel_Height, Cleat_Height, Back_Inset, PT, Add_Top])
        left_back.dim_y('Depth+(PT)', [Depth, PT])
        left_back.dim_z('Backing_Thickness', [Backing_Thickness])
        left_back.get_prompt('Is Left Back').set_value(True)
        left_back.get_prompt('Hide').set_formula('IF(Add_Backing,False,True)', [Add_Backing])

        # Fillers
        create_corner_fillers(self, Panel_Height, Left_Side_Wall_Filler,
                              Panel_Thickness, Left_Depth, Depth,
                              Left_Filler_Setback_Amount, Is_Hanging, Width,
                              Edge_Bottom_of_Left_Filler, self.hide_var,
                              Add_Capping_Left_Filler, Right_Side_Wall_Filler,
                              Right_Filler_Setback_Amount, Toe_Kick_Height,
                              Edge_Bottom_of_Right_Filler, Right_Depth,
                              Add_Capping_Right_Filler)

        spine = common_parts.add_panel(self)
        spine.set_name("Mitered Pard")
        spine.obj_bp["IS_BP_PANEL"] = False
        spine.obj_bp["IS_BP_MITERED_PARD"] = True
        spine.obj_bp.sn_closets.is_panel_bp = False  # TODO: remove
        spine.obj_bp.snap.comment_2 = "1510"
        spine.loc_y("-Spine_Y_Location", [Spine_Y_Location])
        spine.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height])
        spine.rot_y(value=math.radians(-90))
        spine.rot_z(value=math.radians(-45))
        spine.dim_x('Panel_Height', [Panel_Height])
        spine.dim_y(value=sn_unit.inch(2.92))
        spine.dim_z('PT', [PT])
        spine.get_prompt('Hide').set_formula('IF(Add_Backing,True,False)', [Add_Backing])

        # Toe_Kick
        create_corner_toe_kicks(
            self.obj_bp, Left_Depth, Toe_Kick_Setback, Depth,
            PT, Hide_Toe_Kick, Is_Hanging, Toe_Kick_Height,
            Width, Right_Depth)
        # Doors
        # L Reach Back Doors
        l_door_reach_back_left = common_parts.add_door(self)
        l_door_reach_back_left.set_name("Left Door")
        l_door_reach_back_left.loc_x('Left_Depth', [Depth, Left_Depth])
        l_door_reach_back_left.loc_y('Depth+(PT/2)', [Depth, PT])
        l_door_reach_back_left.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height, Shelf_Thickness])
        l_door_reach_back_left.rot_x(value=0)
        l_door_reach_back_left.rot_y(value=math.radians(-90))
        l_door_reach_back_left.rot_z("radians(180)-IF(DT==0,IF(Pull_Location==0,IF(Open<=Half,radians((Open*2)*Rotation),radians(Rotation)),IF(Open>Half,radians((Open-Half)*2*Rotation),0)),0)",
                                     [Pull_Location, Open, Rotation, DT, Half])
        l_door_reach_back_left.dim_x('Panel_Height-(Shelf_Thickness)', [Panel_Height, Shelf_Thickness])
        l_door_reach_back_left.dim_y('Depth+Right_Depth+(PT)+IF(Pull_Location==0,INCH(0.62),0)', [Depth, Right_Depth, PT, Pull_Location])
        l_door_reach_back_left.dim_z('PT', [PT])
        l_door_reach_back_left.get_prompt('Hide').set_formula('IF(Door,IF(DT==0,False,True),True)', [Door, DT])

        l_door_reach_back_right = common_parts.add_door(self)
        l_door_reach_back_right.set_name("Right Door")
        l_door_reach_back_right.loc_x('Width-(PT/2)', [Width, PT])
        l_door_reach_back_right.loc_y('-Right_Depth', [Right_Depth])
        l_door_reach_back_right.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height, Shelf_Thickness])
        l_door_reach_back_right.rot_x(value=0)
        l_door_reach_back_right.rot_y(value=math.radians(-90))
        l_door_reach_back_right.rot_z("radians(90)+IF(DT==0,IF(Pull_Location==1,IF(Open<=Half,radians((Open*2)*Rotation),radians(Rotation)),IF(Open>Half,radians((Open-Half)*2*Rotation),0)),0)",
                                      [Pull_Location, Open, Rotation, DT, Half])
        l_door_reach_back_right.dim_x('Panel_Height-(Shelf_Thickness)', [Panel_Height, Shelf_Thickness])
        l_door_reach_back_right.dim_y('Width-Left_Depth-(PT)-IF(Pull_Location==1,INCH(0.62),0)', [Width, Left_Depth, PT, Pull_Location])
        l_door_reach_back_right.dim_z('PT', [PT])
        l_door_reach_back_right.get_prompt('Hide').set_formula('IF(Door,IF(DT==0,False,True),True)', [Door, DT])

        # L Doors Lazy Susan
        l_door_lazy_susan_left = common_parts.add_door(self)
        l_door_lazy_susan_left.set_name("Left Door")
        l_door_lazy_susan_left.loc_x(
            'IF(Pull_Location==0,Left_Depth+IF(Open<Half,(Open*((Width-Left_Depth)*(1+(Open*2))-PT-INCH(0.25))),Open*((Width-Left_Depth)*(1+(Open*(3-(Open*2))))-PT-INCH(0.25))-PT*((Open-Half)*2))+PT,Left_Depth)',
            [Depth, Left_Depth, PT, Width, Open, Half, Pull_Location])
        l_door_lazy_susan_left.loc_y(
            'IF(Pull_Location==0,-Right_Depth-PT-(IF(Open<Half,Open*(Width-Left_Depth-(PT*2)-INCH(0.25))*2*(2-(2*Open)),Open*(Width-Left_Depth-(PT*2)-INCH(0.25))*2*(1-((Open-Half)*2))-PT*((Open-Half)*2))),Depth+(PT/2))',
            [Depth, PT, Open, Half, Width, Left_Depth, PT, Right_Depth, Pull_Location])
        l_door_lazy_susan_left.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height, Shelf_Thickness])
        l_door_lazy_susan_left.rot_x(value=0)
        l_door_lazy_susan_left.rot_y(value=math.radians(-90))
        l_door_lazy_susan_left.rot_z('IF(Pull_Location==0,(IF(Open>Half,((Open-Half)*2)*radians(45),0)),radians(180)-(Open*radians(180)))', [Open, Half, Pull_Location])
        l_door_lazy_susan_left.dim_x('Panel_Height-(Shelf_Thickness)', [Panel_Height, Shelf_Thickness])
        l_door_lazy_susan_left.dim_y('Depth+Right_Depth+(PT)+INCH(0.25)', [Depth, Right_Depth, PT])
        l_door_lazy_susan_left.dim_z('PT', [PT])
        l_door_lazy_susan_left.get_prompt('Hide').set_formula('IF(Door,IF(DT==1,False,True),True)', [Door, DT])

        l_door_lazy_susan_right = common_parts.add_door(self)
        l_door_lazy_susan_right.set_name("Right Door")
        l_door_lazy_susan_right.loc_x(
            'IF(Pull_Location==0,Width-(PT/2),Left_Depth+PT-(IF(Open<Half,Open*(Depth+Right_Depth+(PT*2))*2*(2-(2*Open)),Open*(Depth+Right_Depth+(PT*2))*2*(1-((Open-Half)*2))+PT*((Open-Half)*2))))',
            [Depth, PT, Open, Half, Width, Left_Depth, PT, Right_Depth, Pull_Location])
        l_door_lazy_susan_right.loc_y(
            'IF(Pull_Location==0,-Right_Depth,-Right_Depth-PT+IF(Open<Half,(Open*(Depth+Right_Depth+PT-INCH(0.25))*(1+(Open*2))),Open*((Depth+Right_Depth+PT-INCH(0.25))*(1+(Open*(3-(Open*2)))))))',
            [Depth, Left_Depth, PT, Width, Open, Half, Pull_Location, Right_Depth])
        l_door_lazy_susan_right.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height, Shelf_Thickness])
        l_door_lazy_susan_right.rot_x(value=0)
        l_door_lazy_susan_right.rot_y(value=math.radians(-90))
        l_door_lazy_susan_right.rot_z('IF(Pull_Location==0,radians(90)+(Open*radians(180)),radians(-90)-IF(Open>Half,((Open-Half)*2)*radians(45),0))', [Open, Pull_Location, Half])
        l_door_lazy_susan_right.dim_x('Panel_Height-(Shelf_Thickness)', [Panel_Height, Shelf_Thickness])
        l_door_lazy_susan_right.dim_y('Width-Left_Depth-(PT)-INCH(0.25)', [Width, Left_Depth, PT])
        l_door_lazy_susan_right.dim_z('PT', [PT])
        l_door_lazy_susan_right.get_prompt('Hide').set_formula('IF(Door,IF(DT==1,False,True),True)', [Door, DT])

        # Left L Reachback Pull
        l_door_reachback_left_pull = common_parts.add_drawer_pull(self)
        l_door_reachback_left_pull.set_name("Left Door Pull")
        l_door_reachback_left_pull.loc_x('Left_Depth', [Left_Depth, PT, DT])
        l_door_reachback_left_pull.loc_y('Depth-(PT/2)', [Depth, Right_Depth, DT, PT])
        l_door_reachback_left_pull.dim_y('Depth+Right_Depth+(PT)', [DT, Depth, Right_Depth, PT])
        l_door_reachback_left_pull.dim_z('PT', [DT, PT])
        l_door_reachback_left_pull.loc_z(
            'IF(Pull_Type==2,IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)+Upper_Pull_Location,IF(Pull_Type==1,Height-Tall_Pull_Location+World_Z,Height-Base_Pull_Location))',
            [Door_Pull_Height, Pull_Type, Base_Pull_Location, Tall_Pull_Location, Upper_Pull_Location, Height, World_Z, Toe_Kick_Height, Shelf_Thickness, Is_Hanging, Panel_Height])
        l_door_reachback_left_pull.rot_x(value=0)
        l_door_reachback_left_pull.rot_y(value=math.radians(-90))
        l_door_reachback_left_pull.rot_z("radians(180)-IF(DT==0,IF(Pull_Location==0,IF(Open<=Half,radians((Open*2)*Rotation),radians(Rotation)),IF(Open>Half,radians((Open-Half)*2*Rotation),0)),0)",
                                         [Pull_Location, Open, Rotation, DT, Half])
        l_door_reachback_left_pull.get_prompt('Hide').set_formula('IF(Pull_Location==1,True,IF(Door,IF(DT==0,False,True),True))', [Door, Pull_Location, DT])

        # Right L Reachback Pull
        l_door_reachback_right_pull = common_parts.add_drawer_pull(self)
        l_door_reachback_right_pull.set_name("Right Door Pull")
        l_door_reachback_right_pull.loc_x('Width', [Width, DT, Left_Depth, PT])
        l_door_reachback_right_pull.loc_y('-Right_Depth', [Right_Depth])
        l_door_reachback_right_pull.dim_y('Width-Left_Depth-(PT)-INCH(0.62)', [DT, Width, Left_Depth, PT])
        l_door_reachback_right_pull.dim_z('PT', [DT, PT])
        l_door_reachback_right_pull.loc_z(
            'IF(Pull_Type==2,IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)+Upper_Pull_Location,IF(Pull_Type==1,Height-Tall_Pull_Location+World_Z,Height-Base_Pull_Location))',
            [Door_Pull_Height, Pull_Type, Base_Pull_Location, Tall_Pull_Location, Upper_Pull_Location, Height, World_Z, Toe_Kick_Height, Shelf_Thickness, Is_Hanging, Panel_Height])
        l_door_reachback_right_pull.rot_x(value=0)
        l_door_reachback_right_pull.rot_y(value=math.radians(-90))
        l_door_reachback_right_pull.rot_z("radians(90)+IF(DT==0,IF(Pull_Location==1,IF(Open<=Half,radians((Open*2)*Rotation),radians(Rotation)),IF(Open>Half,radians((Open-Half)*2*Rotation),0)),0)",
                                          [Pull_Location, Open, Rotation, DT, Half])
        l_door_reachback_right_pull.get_prompt('Hide').set_formula('IF(Pull_Location==0,True,IF(Door,IF(DT==0,False,True),True))', [Door, Pull_Location, DT])

        # L Lazy Susan Left Pull
        l_door_lazy_susan_left_pull = common_parts.add_drawer_pull(self)
        l_door_lazy_susan_left_pull.set_name("Left Door Pull")
        l_door_lazy_susan_left_pull.loc_x(
            'Left_Depth+IF(Open<Half,(Open*((Width-Left_Depth)*(1+(Open*2))-PT-INCH(0.25))),Open*((Width-Left_Depth)*(1+(Open*(3-(Open*2))))-PT-INCH(0.25))-PT*((Open-Half)*2))+PT',
            [Depth, Left_Depth, PT, Width, Open, Half, Pull_Location])
        l_door_lazy_susan_left_pull.loc_y(
            '-Right_Depth+(PT/2)-(IF(Open<Half,Open*(Width-Left_Depth-(PT*2)-INCH(0.25))*2*(2-(2*Open)),Open*(Width-Left_Depth-(PT*2)-INCH(0.25))*2*(1-((Open-Half)*2))-PT*((Open-Half)*2)))',
            [Depth, PT, Open, Half, Width, Left_Depth, PT, Right_Depth, Pull_Location])
        l_door_lazy_susan_left_pull.dim_y('(Depth+Right_Depth+(PT)+INCH(0.25))*-1', [Depth, Right_Depth, PT])
        l_door_lazy_susan_left_pull.dim_z('IF(Open>Half,-PT*((Open-Half)*2),0)', [PT, Open, Half])
        l_door_lazy_susan_left_pull.loc_z(
            'IF(Pull_Type==2,IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)+Upper_Pull_Location,IF(Pull_Type==1,Height-Tall_Pull_Location+World_Z,Height-Base_Pull_Location))',
            [Door_Pull_Height, Pull_Type, Base_Pull_Location, Tall_Pull_Location, Upper_Pull_Location, Height, World_Z, Toe_Kick_Height, Shelf_Thickness, Is_Hanging, Panel_Height])
        l_door_lazy_susan_left_pull.rot_x(value=0)
        l_door_lazy_susan_left_pull.rot_y(value=math.radians(-90))
        l_door_lazy_susan_left_pull.rot_z('radians(180)+IF(Open>Half,((Open-Half)*2)*radians(45),0)', [Open, Half, Pull_Location])
        l_door_lazy_susan_left_pull.get_prompt('Hide').set_formula('IF(Pull_Location==1,True,IF(Door,IF(DT==1,False,True),True))', [Door, Pull_Location, DT])

        # L Lazy Suasan Right Pull
        l_door_lazy_susan_right_pull = common_parts.add_drawer_pull(self)
        l_door_lazy_susan_right_pull.set_name("Right Door Pull")
        l_door_lazy_susan_right_pull.loc_x(
            'Left_Depth-(IF(Open<Half,Open*(Depth+Right_Depth+(PT*2))*2*(2-(2*Open)),Open*(Depth+Right_Depth+(PT*2))*2*(1-((Open-Half)*2))+PT*((Open-Half)*2)))',
            [Depth, PT, Open, Half, Width, Left_Depth, PT, Right_Depth, Pull_Location])
        l_door_lazy_susan_right_pull.loc_y(
            '-Right_Depth-PT+IF(Open<Half,(Open*(Depth+Right_Depth+PT-INCH(0.25))*(1+(Open*2))),Open*((Depth+Right_Depth+PT-INCH(0.25))*(1+(Open*(3-(Open*2))))))',
            [Depth, Left_Depth, PT, Width, Open, Half, Pull_Location, Right_Depth])
        l_door_lazy_susan_right_pull.dim_y('(Width-Left_Depth-(PT)-INCH(0.25))*-1', [Width, Left_Depth, PT])
        l_door_lazy_susan_right_pull.dim_z('IF(Open>Half,-PT*((Open-Half)*1.5),0)', [PT, Open, Half])
        l_door_lazy_susan_right_pull.loc_z(
            'IF(Pull_Type==2,IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)+Upper_Pull_Location,IF(Pull_Type==1,Height-Tall_Pull_Location+World_Z,Height-Base_Pull_Location))',
            [Door_Pull_Height, Pull_Type, Base_Pull_Location, Tall_Pull_Location, Upper_Pull_Location, Height, World_Z, Toe_Kick_Height, Shelf_Thickness, Is_Hanging, Panel_Height])
        l_door_lazy_susan_right_pull.rot_x(value=0)
        l_door_lazy_susan_right_pull.rot_y(value=math.radians(-90))
        l_door_lazy_susan_right_pull.rot_z('radians(90)-IF(Open>Half,((Open-Half)*2)*radians(45),0)', [Open, Pull_Location, Half])
        l_door_lazy_susan_right_pull.get_prompt('Hide').set_formula('IF(Pull_Location==0,True,IF(Door,IF(DT==1,False,True),True))', [Door, Pull_Location, DT])

        # Shelves
        previous_l_shelf = None
        for i in range(1, 11):
            Shelf_Height = self.get_prompt("Shelf " + str(i) + " Height").get_var('Shelf_Height')

            l_shelf = common_parts.add_l_shelf(self)
            if previous_l_shelf:
                prev_shelf_z_loc = previous_l_shelf.obj_bp.snap.get_var('location.z', 'prev_shelf_z_loc')
                l_shelf.loc_z('prev_shelf_z_loc+Shelf_Height', [prev_shelf_z_loc, Shelf_Height])
            else:
                l_shelf.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+Shelf_Height',
                              [Shelf_Height, Is_Hanging, Toe_Kick_Height, Shelf_Thickness, Height, Panel_Height])

            l_shelf.loc_x('IF(Add_Backing,Backing_Thickness,0)', [Add_Backing, Backing_Thickness])
            l_shelf.loc_y('IF(Add_Backing,-Backing_Thickness,0)', [Add_Backing, Backing_Thickness])
            l_shelf.rot_x(value=0)
            l_shelf.rot_y(value=0)
            l_shelf.rot_z(value=0)
            l_shelf.dim_x('Width-PT-IF(Add_Backing,Backing_Thickness,0)', [Width, PT, Add_Backing, Backing_Thickness])
            l_shelf.dim_y('Depth+PT+IF(Add_Backing,Backing_Thickness,0)', [Depth, PT, Add_Backing, Backing_Thickness])
            l_shelf.dim_z('Shelf_Thickness', [Shelf_Thickness])
            l_shelf.get_prompt('Left Depth').set_formula('Left_Depth-IF(Add_Backing,Backing_Thickness,0)', [Left_Depth, Add_Backing, Backing_Thickness])
            l_shelf.get_prompt('Right Depth').set_formula('Right_Depth-IF(Add_Backing,Backing_Thickness,0)', [Right_Depth, Add_Backing, Backing_Thickness])
            l_shelf.get_prompt('Hide').set_formula('IF(Shelf_Quantity>' + str(i) + ',False,True)', [Shelf_Quantity])
            previous_l_shelf = l_shelf

    def draw(self):
        self.obj_bp["IS_BP_CLOSET"] = True
        self.obj_bp["IS_BP_L_SHELVES"] = True
        self.obj_bp["ID_PROMPT"] = self.id_prompt
        self.obj_y['IS_MIRROR'] = True
        self.obj_bp.snap.type_group = self.type_assembly
        self.update()
        set_tk_id_prompt(self.obj_bp)


def set_tk_id_prompt(obj_bp):
    children = obj_bp.children
    for child in children:
        if "Toe Kick" in child.name:
            set_obj_tk_id_prompt(child)
            child['IS_BP_ASSEMBLY'] = True
            child.snap.type_group = 'INSERT'


def set_obj_tk_id_prompt(obj):
    obj["ID_PROMPT"] = "sn_closets.toe_kick_prompts"
    children = obj.children
    for child in children:
        set_obj_tk_id_prompt(child)


def create_corner_toe_kicks(obj_bp, Left_Depth, Toe_Kick_Setback, Depth,
                            PT, Hide_Toe_Kick, Is_Hanging, Toe_Kick_Height,
                            Width, Right_Depth):
    tk_path = path.join(
        closet_paths.get_library_path(),
        "/Products - Basic/Toe Kick.png")
    wm_props = bpy.context.window_manager.snap

    left_tk = wm_props.get_asset(tk_path)
    left_tk.draw()
    left_tk.obj_bp.parent = obj_bp
    left_tk.obj_bp["ID_PROMPT"] = left_tk.id_prompt
    left_tk.obj_bp.snap.comment_2 = "1034"
    left_tk.loc_x(
        'Left_Depth - Toe_Kick_Setback',
        [Left_Depth, Toe_Kick_Setback])
    left_tk.loc_x('0', [])
    left_tk.loc_y('Depth', [Depth])
    left_tk.rot_x(value=math.radians(0))
    left_tk.rot_z(value=math.radians(90))
    left_tk.dim_x('-Depth + PT/2', [Depth, PT])
    left_tk.dim_y(
        '-Left_Depth + Toe_Kick_Setback',
        [Left_Depth, Toe_Kick_Setback])
    left_tk.get_prompt('Hide').set_formula(
        'IF(Hide_Toe_Kick,True,IF(Is_Hanging,True,False))',
        [Hide_Toe_Kick, Is_Hanging])
    left_tk.get_prompt('Toe Kick Height').set_formula(
        'Toe_Kick_Height', [Toe_Kick_Height])
    set_tk_hide(left_tk)
    left_depth_amount =\
        left_tk.get_prompt(
            "Extend Depth Amount").get_var(
                "left_depth_amount")

    right_tk = wm_props.get_asset(tk_path)
    right_tk.draw()
    right_tk.obj_bp.parent = obj_bp
    right_tk.obj_bp.snap.comment_2 = "1034"
    right_tk.rot_x(value=0)
    right_tk.rot_z(value=0)
    right_tk.loc_x(
        'Left_Depth - Toe_Kick_Setback - PT/2 + left_depth_amount',
        [Left_Depth, Toe_Kick_Setback, PT, left_depth_amount])
    right_tk.loc_y('0', [])
    right_tk.dim_x(
        'Width - Left_Depth + Toe_Kick_Setback + PT/2- left_depth_amount',
        [Width, Left_Depth, Toe_Kick_Setback, PT, left_depth_amount])
    right_tk.dim_y(
        '-Right_Depth + Toe_Kick_Setback',
        [Right_Depth, Toe_Kick_Setback])
    right_tk.get_prompt('Hide').set_formula(
        'IF(Hide_Toe_Kick,True,IF(Is_Hanging,True,False))',
        [Hide_Toe_Kick, Is_Hanging])
    right_tk.get_prompt('Toe Kick Height').set_formula(
        'Toe_Kick_Height', [Toe_Kick_Height])
    set_tk_hide(right_tk)


def set_tk_hide(toe_kick):
    Hide = toe_kick.get_prompt("Hide").get_var("Hide")
    children = toe_kick.obj_bp.children
    for child in children:
        is_obj = "obj" in child.name.lower()
        is_skin = "skin" in child.name.lower()
        if not is_obj and not is_skin:
            child_assembly =\
                sn_types.Assembly(obj_bp=child)
            child_hide = child_assembly.get_prompt("Hide")
            child_hide.set_formula("Hide", [Hide])


def create_corner_fillers(assemly, Panel_Height, Left_Side_Wall_Filler,
                          Panel_Thickness, Left_Depth, Depth,
                          Left_Filler_Setback_Amount, Is_Hanging, Width,
                          Edge_Bottom_of_Left_Filler, hide_var,
                          Add_Capping_Left_Filler, Right_Side_Wall_Filler,
                          Right_Filler_Setback_Amount, Toe_Kick_Height,
                          Edge_Bottom_of_Right_Filler, Right_Depth,
                          Add_Capping_Right_Filler):

    # Left Filler
    left_filler = common_parts.add_filler(assemly)
    left_filler.set_name("Left Filler")
    left_filler.dim_x(
        'Panel_Height',
        [Panel_Height])
    left_filler.dim_y('-Left_Side_Wall_Filler', [Left_Side_Wall_Filler])
    left_filler.dim_z('Panel_Thickness', [Panel_Thickness])
    left_filler.loc_x(
        'Left_Depth - Left_Filler_Setback_Amount - Panel_Thickness',
        [Left_Depth, Left_Filler_Setback_Amount, Panel_Thickness])
    left_filler.loc_y(
        "Depth-Left_Side_Wall_Filler",
        [Depth, Left_Side_Wall_Filler])
    left_filler.loc_z(
        'IF(Is_Hanging, 0, Toe_Kick_Height)',
        [Toe_Kick_Height, Is_Hanging])
    left_filler.rot_x(value=0)
    left_filler.rot_y(value=math.radians(-90))
    left_filler.rot_z(value=math.radians(180))
    hide = left_filler.get_prompt("Hide")
    hide.set_formula(
        'IF(Left_Side_Wall_Filler==0,True,False) or Hide',
        [Left_Side_Wall_Filler, hide_var])
    left_filler.get_prompt("Exposed Left").set_formula(
        'IF(Edge_Bottom_of_Left_Filler,True,False)',
        [Edge_Bottom_of_Left_Filler])
    left_filler.get_prompt("Exposed Left").set_value(True)
    left_filler.get_prompt("Exposed Right").set_value(True)
    left_filler.get_prompt("Exposed Back").set_value(True)

    # Left Capping Filler
    left_capping_filler = common_parts.add_filler(assemly)
    left_capping_filler.set_name("Left Capping Filler")
    left_capping_filler.dim_x(
        'Panel_Height-INCH(0.91)',
        [Panel_Height])
    left_capping_filler.dim_y(
        '-Left_Side_Wall_Filler', [Left_Side_Wall_Filler])
    left_capping_filler.dim_z('Panel_Thickness', [Panel_Thickness])
    left_capping_filler.loc_x(
        'Left_Depth-Left_Filler_Setback_Amount',
        [Left_Depth, Left_Filler_Setback_Amount])
    left_capping_filler.loc_y(
        "Depth-Left_Side_Wall_Filler",
        [Depth, Left_Side_Wall_Filler])
    left_capping_filler.loc_z(
        'IF(Is_Hanging, 0, Toe_Kick_Height)+INCH(0.455)',
        [Toe_Kick_Height, Is_Hanging])
    left_capping_filler.rot_y(value=math.radians(-90))
    left_capping_filler.rot_z(value=math.radians(180))
    left_capping_filler.get_prompt('Hide').set_formula(
        'IF(Add_Capping_Left_Filler,False,True) or Hide',
        [Left_Side_Wall_Filler, Add_Capping_Left_Filler, hide_var])
    left_capping_filler.get_prompt("Exposed Left").set_value(True)
    left_capping_filler.get_prompt("Exposed Right").set_value(True)
    left_capping_filler.get_prompt("Exposed Back").set_value(True)

    # Right Filler
    right_filler = common_parts.add_filler(assemly)
    right_filler.set_name("Right Filler")
    right_filler.dim_x(
        'Panel_Height',
        [Panel_Height])
    right_filler.dim_y('-Right_Side_Wall_Filler', [Right_Side_Wall_Filler])
    right_filler.dim_z('Panel_Thickness', [Panel_Thickness])
    right_filler.loc_x(
        "Width+Right_Side_Wall_Filler",
        [Width, Right_Side_Wall_Filler])
    right_filler.loc_y(
        '-Right_Depth+Right_Filler_Setback_Amount',
        [Right_Depth, Right_Filler_Setback_Amount])
    right_filler.loc_z(
        'IF(Is_Hanging, 0, Toe_Kick_Height)',
        [Toe_Kick_Height, Is_Hanging])
    right_filler.rot_x(value=0)
    right_filler.rot_y(value=math.radians(-90))
    right_filler.rot_z(value=math.radians(-90))
    hide = right_filler.get_prompt("Hide")
    hide.set_formula(
        'IF(Right_Side_Wall_Filler==0,True,False) or Hide',
        [Right_Side_Wall_Filler, hide_var])
    right_filler.get_prompt("Exposed Left").set_formula(
        'IF(Edge_Bottom_of_Right_Filler,True,False)',
        [Edge_Bottom_of_Right_Filler])
    right_filler.get_prompt("Exposed Left").set_value(True)
    right_filler.get_prompt("Exposed Right").set_value(True)
    right_filler.get_prompt("Exposed Back").set_value(True)

    # Right Capping Filler
    right_capping_filler = common_parts.add_filler(assemly)
    right_capping_filler.set_name("Right Capping Filler")
    right_capping_filler.dim_x(
        'Panel_Height-INCH(0.91)',
        [Panel_Height])
    right_capping_filler.dim_y(
        '-Right_Side_Wall_Filler', [Right_Side_Wall_Filler])
    right_capping_filler.dim_z('Panel_Thickness', [Panel_Thickness])
    right_capping_filler.loc_x(
        "Width+Right_Side_Wall_Filler",
        [Width, Right_Side_Wall_Filler])
    right_capping_filler.loc_y(
        '-Right_Depth+Right_Filler_Setback_Amount-Panel_Thickness',
        [Right_Depth, Right_Filler_Setback_Amount, Panel_Thickness])
    right_capping_filler.loc_z(
        'IF(Is_Hanging, 0, Toe_Kick_Height)+INCH(0.455)',
        [Toe_Kick_Height, Is_Hanging])
    right_capping_filler.rot_y(value=math.radians(-90))
    right_capping_filler.rot_z(value=math.radians(-90))
    right_capping_filler.get_prompt('Hide').set_formula(
        'IF(Add_Capping_Right_Filler,False,True) or Hide',
        [Right_Side_Wall_Filler, Add_Capping_Right_Filler, hide_var])
    right_capping_filler.get_prompt("Exposed Left").set_value(True)
    right_capping_filler.get_prompt("Exposed Right").set_value(True)
    right_capping_filler.get_prompt("Exposed Back").set_value(True)


class Corner_Shelves(sn_types.Assembly):

    """
    This Corner Shelf Includes a Back Spine for support and is hanging first
    """

    category_name = ""
    type_assembly = "PRODUCT"
    property_id = "sn_closets.corner_shelves"
    show_in_library = True
    placement_type = 'CORNER'

    def pre_draw(self):
        self.create_assembly()
        hide_prompt = self.add_prompt('Hide', 'CHECKBOX', False)
        self.hide_var = hide_prompt.get_var()
        self.obj_x.location.x = self.width
        self.obj_y.location.y = -self.depth
        self.obj_z.location.z = self.height

        props = bpy.context.scene.sn_closets

        self.add_prompt("Panel Height", 'DISTANCE', sn_unit.millimeter(2003))
        self.add_prompt("Back Inset", 'DISTANCE', sn_unit.inch(.25))
        self.add_prompt("Spine Width", 'DISTANCE', sn_unit.inch(1))
        self.add_prompt("Spine Y Location", 'DISTANCE', sn_unit.inch(2.1))
        self.add_prompt("Cleat Height", 'DISTANCE', sn_unit.inch(3.64))
        self.add_prompt("Left Depth", 'DISTANCE', sn_unit.inch(12))
        self.add_prompt("Right Depth", 'DISTANCE', sn_unit.inch(12))
        self.add_prompt("Shelf Quantity", 'QUANTITY', 3)
        self.add_prompt("Add Top KD", 'CHECKBOX', True)  # export=True
        self.add_prompt("Hide Toe Kick", 'CHECKBOX', False)  # export=True
        self.add_prompt("Add Backing", 'CHECKBOX', False)  # export=True
        self.add_prompt("Is Hanging", 'CHECKBOX', False)  # export=True
        self.add_prompt("Remove Left Side", 'CHECKBOX', False)  # export=True
        self.add_prompt("Remove Right Side", 'CHECKBOX', False)  # export=True
        self.add_prompt("Use Left Swing", 'CHECKBOX', False)  # export=True
        self.add_prompt("Force Double Doors", 'CHECKBOX', False)  # export=True
        self.add_prompt("Door", 'CHECKBOX', False)  # export=True
        self.add_prompt("Door Pull Height", 'DISTANCE', sn_unit.inch(36))
        self.add_prompt("Backing Thickness", 'DISTANCE', sn_unit.inch(0.75))

        self.add_prompt("Open Door", 'PERCENTAGE', 0)
        self.add_prompt("Door Rotation", 'QUANTITY', 120)
        self.add_prompt("Half Open", 'PERCENTAGE', 0.5)
        self.add_prompt("Pull Type", 'COMBOBOX', 1, ["Base", "Tall", "Upper"])

        self.add_prompt("Add Top Shelf", 'CHECKBOX', False)
        self.add_prompt("Exposed Left", 'CHECKBOX', False)
        self.add_prompt("Exposed Right", 'CHECKBOX', False)
        self.add_prompt("Top Shelf Overhang", 'DISTANCE', sn_unit.inch(0.5))

        self.add_prompt("Add Left Filler", 'CHECKBOX', False)
        self.add_prompt("Add Right Filler", 'CHECKBOX', False)
        self.add_prompt("Left Side Wall Filler", 'DISTANCE', 0.0)
        self.add_prompt("Right Side Wall Filler", 'DISTANCE', 0.0)
        self.add_prompt("Add Capping Left Filler", 'CHECKBOX', False)
        self.add_prompt("Add Capping Right Filler", 'CHECKBOX', False)
        self.add_prompt("Left Filler Setback Amount", 'DISTANCE', 0.0)
        self.add_prompt("Right Filler Setback Amount", 'DISTANCE', 0.0)
        self.add_prompt("Edge Bottom of Left Filler", 'CHECKBOX', False)
        self.add_prompt("Edge Bottom of Right Filler", 'CHECKBOX', False)

        for i in range(1, 11):
            self.add_prompt("Shelf " + str(i) + " Height", 'DISTANCE', sn_unit.millimeter(653.034))

        common_prompts.add_toe_kick_prompts(self)
        common_prompts.add_thickness_prompts(self)
        common_prompts.add_door_prompts(self)
        common_prompts.add_door_pull_prompts(self)

        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Panel_Height = self.get_prompt('Panel Height').get_var('Panel_Height')
        Left_Depth = self.get_prompt('Left Depth').get_var('Left_Depth')
        Right_Depth = self.get_prompt('Right Depth').get_var('Right_Depth')
        Shelf_Thickness = self.get_prompt('Shelf Thickness').get_var('Shelf_Thickness')
        PT = self.get_prompt('Panel Thickness').get_var("PT")
        Toe_Kick_Setback = self.get_prompt('Toe Kick Setback').get_var('Toe_Kick_Setback')
        Hide_Toe_Kick = self.get_prompt('Hide Toe Kick').get_var('Hide_Toe_Kick')
        Shelf_Quantity = self.get_prompt('Shelf Quantity').get_var('Shelf_Quantity')
        Add_Backing = self.get_prompt('Add Backing').get_var('Add_Backing')
        Back_Inset = self.get_prompt('Back Inset').get_var('Back_Inset')
        Add_Top = self.get_prompt('Add Top KD').get_var('Add_Top')
        Backing_Thickness = self.get_prompt('Backing Thickness').get_var('Backing_Thickness')
        Is_Hanging = self.get_prompt('Is Hanging').get_var('Is_Hanging')
        RLS = self.get_prompt('Remove Left Side').get_var("RLS")
        RRS = self.get_prompt('Remove Right Side').get_var("RRS")
        Spine_Width = self.get_prompt('Spine Width').get_var('Spine_Width')
        Spine_Y_Location = self.get_prompt('Spine Y Location').get_var('Spine_Y_Location')
        Cleat_Height = self.get_prompt('Cleat Height').get_var('Cleat_Height')
        Door = self.get_prompt('Door').get_var('Door')
        Door_Pull_Height = self.get_prompt('Door Pull Height').get_var('Door_Pull_Height')
        Use_Left_Swing = self.get_prompt("Use Left Swing").get_var('Use_Left_Swing')
        Force_Double_Doors = self.get_prompt("Force Double Doors").get_var('Force_Double_Doors')
        Open = self.get_prompt("Open Door").get_var('Open')
        Rotation = self.get_prompt("Door Rotation").get_var('Rotation')
        Pull_Type = self.get_prompt("Pull Type").get_var('Pull_Type')
        Base_Pull_Location = self.get_prompt("Base Pull Location").get_var('Base_Pull_Location')
        Tall_Pull_Location = self.get_prompt("Tall Pull Location").get_var('Tall_Pull_Location')
        Upper_Pull_Location = self.get_prompt("Upper Pull Location").get_var('Upper_Pull_Location')
        World_Z = self.obj_bp.snap.get_var('matrix_world[2][3]', 'World_Z')
        Toe_Kick_Height = self.get_prompt('Toe Kick Height').get_var('Toe_Kick_Height')
        Add_Top_Shelf = self.get_prompt('Add Top Shelf').get_var('Add_Top_Shelf')
        Top_Shelf_Overhang = self.get_prompt('Top Shelf Overhang').get_var('Top_Shelf_Overhang')
        Left_Side_Wall_Filler = self.get_prompt('Left Side Wall Filler').get_var('Left_Side_Wall_Filler')
        Panel_Thickness = self.get_prompt('Panel Thickness').get_var('Panel_Thickness')
        Left_Filler_Setback_Amount = self.get_prompt('Left Filler Setback Amount').get_var()
        Edge_Bottom_of_Left_Filler = self.get_prompt("Edge Bottom of Left Filler").get_var()
        Add_Capping_Left_Filler = self.get_prompt("Add Capping Left Filler").get_var()
        Right_Side_Wall_Filler = self.get_prompt('Right Side Wall Filler').get_var('Right_Side_Wall_Filler')
        Right_Filler_Setback_Amount = self.get_prompt('Right Filler Setback Amount').get_var()
        Edge_Bottom_of_Right_Filler = self.get_prompt("Edge Bottom of Right Filler").get_var()
        Add_Capping_Right_Filler = self.get_prompt("Add Capping Right Filler").get_var()


        top_angled = common_parts.add_angle_shelf(self)
        top_angled.loc_z('(Height+IF(Is_Hanging,0,Toe_Kick_Height))', [Height, Toe_Kick_Height, Is_Hanging])
        top_angled.dim_x('Width-IF(RRS,0,PT)', [Width, RRS, PT])
        top_angled.dim_y('Depth+IF(RLS,0,PT)', [Depth, PT, RLS])
        top_angled.dim_z('-Shelf_Thickness', [Shelf_Thickness])
        top_angled.get_prompt("Is Locked Shelf").set_value(True)
        top_angled.get_prompt('Left Depth').set_formula('Left_Depth', [Left_Depth])
        top_angled.get_prompt('Right Depth').set_formula('Right_Depth', [Right_Depth])
        top_angled.get_prompt('Hide').set_formula('IF(Add_Top,False,True)', [Add_Top])

        top_shelf_angled = common_parts.add_angle_shelf(self)
        top_shelf_angled.set_name("Corner Top Shelf")
        top_shelf_angled.loc_z('(Height+IF(Is_Hanging,0,Toe_Kick_Height))+Shelf_Thickness', [Height, Toe_Kick_Height, Is_Hanging, Shelf_Thickness])
        top_shelf_angled.dim_x(
            'Width-IF(RRS,0,PT)+PT+Right_Side_Wall_Filler',
            [Width, RRS, PT, Right_Side_Wall_Filler])
        top_shelf_angled.dim_y(
            'Depth+IF(RLS,0,PT)-PT-Left_Side_Wall_Filler',
            [Depth, PT, RLS, Left_Side_Wall_Filler])
        top_shelf_angled.dim_z('-Shelf_Thickness', [Shelf_Thickness])
        top_shelf_angled.get_prompt('Left Depth').set_formula('Left_Depth+Top_Shelf_Overhang', [Left_Depth, Top_Shelf_Overhang])
        top_shelf_angled.get_prompt('Right Depth').set_formula('Right_Depth+Top_Shelf_Overhang', [Right_Depth, Top_Shelf_Overhang])
        top_shelf_angled.get_prompt('Hide').set_formula('IF(Add_Top_Shelf,False,True)', [Add_Top_Shelf])

        right_top_cleat = common_parts.add_cleat(self)
        right_top_cleat.set_name("Top Cleat")
        right_top_cleat.loc_x('Spine_Width', [Spine_Width])
        right_top_cleat.loc_z('(IF(Add_Top,Height-Shelf_Thickness,Height))+IF(Is_Hanging,0,Toe_Kick_Height)', [Height, Shelf_Thickness, Add_Top, Is_Hanging, Toe_Kick_Height])
        right_top_cleat.rot_x(value=math.radians(-90))
        right_top_cleat.dim_x('Width-Spine_Width-IF(RRS,0,PT)', [RRS, Width, PT, Spine_Width])
        right_top_cleat.dim_y('Cleat_Height', [Cleat_Height])
        right_top_cleat.dim_z('-PT', [PT])
        right_top_cleat.get_prompt('Hide').set_formula('IF(Add_Backing,True,False) or Hide', [self.hide_var, Add_Backing])

        left_top_cleat = common_parts.add_cleat(self)
        left_top_cleat.set_name("Top Cleat")
        left_top_cleat.loc_y('IF(RLS,Depth,Depth+PT)', [Depth, RLS, PT])
        left_top_cleat.loc_z('(IF(Add_Top,Height-Shelf_Thickness,Height))+IF(Is_Hanging,0,Toe_Kick_Height)', [Height, Shelf_Thickness, Add_Top, Is_Hanging, Toe_Kick_Height])
        left_top_cleat.rot_x(value=math.radians(-90))
        left_top_cleat.rot_z(value=math.radians(90))
        left_top_cleat.dim_x('-Depth-Spine_Width-IF(RLS,0,PT)', [RLS, Depth, PT, Spine_Width])
        left_top_cleat.dim_y('Cleat_Height', [Cleat_Height])
        left_top_cleat.dim_z('-PT', [PT])
        left_top_cleat.get_prompt('Hide').set_formula('IF(Add_Backing,True,False) or Hide', [self.hide_var, Add_Backing])

        bottom_angled = common_parts.add_angle_shelf(self)
        bottom_angled.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)', [Is_Hanging, Height, Panel_Height, Toe_Kick_Height])
        bottom_angled.dim_x('Width-IF(RRS,0,PT)', [Width, RRS, PT])
        bottom_angled.dim_y('Depth+IF(RLS,0,PT)', [Depth, PT, RLS])
        bottom_angled.dim_z('Shelf_Thickness', [Shelf_Thickness])
        bottom_angled.get_prompt('Left Depth').set_formula('Left_Depth', [Left_Depth])
        bottom_angled.get_prompt('Right Depth').set_formula('Right_Depth', [Right_Depth])
        bottom_angled.get_prompt('Is Locked Shelf').set_value(True)

        right_bot_cleat = common_parts.add_cleat(self)
        right_bot_cleat.set_name("Bottom Cleat")
        right_bot_cleat.loc_x('Spine_Width', [Spine_Width])
        right_bot_cleat.loc_z('IF(Is_Hanging,Height-Panel_Height+Shelf_Thickness,Shelf_Thickness+Toe_Kick_Height)', [Height, Panel_Height, Is_Hanging, Shelf_Thickness, Toe_Kick_Height])
        right_bot_cleat.rot_x(value=math.radians(-90))
        right_bot_cleat.dim_x('Width-Spine_Width-IF(RRS,0,PT)', [RRS, Width, PT, Spine_Width])
        right_bot_cleat.dim_y('-Cleat_Height', [Cleat_Height])
        right_bot_cleat.dim_z('-PT', [PT])
        right_bot_cleat.get_prompt('Hide').set_formula('IF(Add_Backing,True,False) or Hide', [self.hide_var, Add_Backing])

        left_bot_cleat = common_parts.add_cleat(self)
        left_bot_cleat.set_name("Bottom Cleat")
        left_bot_cleat.loc_y('IF(RLS,Depth,Depth+PT)', [Depth, RLS, PT])
        left_bot_cleat.loc_z('IF(Is_Hanging,Height-Panel_Height+Shelf_Thickness,Shelf_Thickness+Toe_Kick_Height)', [Height, Panel_Height, Is_Hanging, Shelf_Thickness, Toe_Kick_Height])
        left_bot_cleat.rot_x(value=math.radians(-90))
        left_bot_cleat.rot_z(value=math.radians(90))
        left_bot_cleat.dim_x('-Depth-Spine_Width-IF(RLS,0,PT)', [RLS, Depth, PT, Spine_Width])
        left_bot_cleat.dim_y('-Cleat_Height', [Cleat_Height])
        left_bot_cleat.dim_z('-PT', [PT])
        left_bot_cleat.get_prompt('Hide').set_formula('IF(Add_Backing,True,False) or Hide', [self.hide_var, Add_Backing])

        left_panel = common_parts.add_panel(self)
        left_panel.loc_y('Depth', [Depth, Add_Backing])
        left_panel.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height])
        left_panel.rot_y(value=math.radians(-90))
        left_panel.rot_z(value=math.radians(-90))
        left_panel.dim_x('Panel_Height', [Panel_Height])
        left_panel.dim_y('Left_Depth', [Left_Depth])
        left_panel.dim_z('PT', [PT])
        left_panel.get_prompt('Left Depth').set_formula('Left_Depth', [Left_Depth])  # Adding this in order to drill the panel on one side
        left_panel.get_prompt('Hide').set_formula('IF(RLS,True,False)', [RLS])

        right_panel = common_parts.add_panel(self)
        right_panel.loc_x('Width-PT', [Width, PT])
        right_panel.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height])
        right_panel.rot_y(value=math.radians(-90))
        right_panel.rot_z(value=math.radians(180))
        right_panel.dim_x('Panel_Height', [Panel_Height])
        right_panel.dim_y('Right_Depth', [Right_Depth])
        right_panel.dim_z('PT', [PT])
        right_panel.get_prompt('Right Depth').set_formula('Right_Depth', [Right_Depth])  # Adding this in order to drill the panel on one side
        right_panel.get_prompt('Hide').set_formula('IF(RRS,True,False)', [RRS])

        right_back = common_parts.add_corner_back(self)
        right_back.set_name("Backing")
        right_back.loc_x('Width-PT', [Width, PT])
        right_back.loc_y('-PT', [PT])
        right_back.loc_z('IF(Is_Hanging,Height-Panel_Height+PT,Toe_Kick_Height+PT)',
                         [Height, Panel_Height, Is_Hanging, Toe_Kick_Height, Cleat_Height, Back_Inset, PT])
        right_back.rot_y(value=math.radians(-90))
        right_back.rot_z(value=math.radians(-90))
        right_back.dim_x('Panel_Height-PT-IF(Add_Top,PT,0)', [Panel_Height, Cleat_Height, Back_Inset, PT, Add_Top])
        right_back.dim_y('-Width+(PT*2)', [Width, PT])
        right_back.dim_z('Backing_Thickness', [Backing_Thickness])
        right_back.get_prompt('Hide').set_formula('IF(Add_Backing,False,True)', [Add_Backing])

        left_back = common_parts.add_corner_back(self)
        left_back.loc_y('Depth+PT', [Depth, PT])
        left_back.loc_z('IF(Is_Hanging,Height-Panel_Height+PT,Toe_Kick_Height+PT)',
                        [Height, Panel_Height, Is_Hanging, Toe_Kick_Height, Cleat_Height, Back_Inset, PT])
        left_back.rot_y(value=math.radians(-90))
        left_back.rot_z(value=math.radians(-180))
        left_back.dim_x('Panel_Height-PT-IF(Add_Top,PT,0)', [Panel_Height, Cleat_Height, Back_Inset, PT, Add_Top])
        left_back.dim_y('Depth+PT', [Depth, PT])
        left_back.dim_z('Backing_Thickness', [Backing_Thickness])
        left_back.get_prompt('Hide').set_formula('IF(Add_Backing,False,True)', [Add_Backing])

        spine = common_parts.add_panel(self)
        spine.set_name("Mitered Pard")
        spine.obj_bp["IS_BP_PANEL"] = False
        spine.obj_bp["IS_BP_MITERED_PARD"] = True
        spine.obj_bp.sn_closets.is_panel_bp = False  # TODO: remove
        spine.obj_bp.snap.comment_2 = "1510"
        spine.loc_y("-Spine_Y_Location", [Spine_Y_Location])
        spine.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height])
        spine.rot_y(value=math.radians(-90))
        spine.rot_z(value=math.radians(-45))
        spine.dim_x('Panel_Height', [Panel_Height])
        spine.dim_y(value=sn_unit.inch(2.92))
        spine.dim_z('PT', [PT])
        spine.get_prompt('Hide').set_formula('IF(Add_Backing,True,False)', [Add_Backing])

        # Toe_Kick
        create_corner_toe_kicks(
            self.obj_bp, Left_Depth, Toe_Kick_Setback, Depth,
            PT, Hide_Toe_Kick, Is_Hanging, Toe_Kick_Height,
            Width, Right_Depth)

        angle_kick = common_parts.add_toe_kick(self)
        angle_kick.set_name("Angle Kick")
        angle_kick.obj_bp.snap.comment_2 = "1034"
        angle_kick.loc_x(
            'Left_Depth-Toe_Kick_Setback-PT+.00635',
            [Left_Depth, Toe_Kick_Setback, PT])
        angle_kick.loc_y('Depth+3*PT/2-.00635', [Depth, PT])
        angle_kick.rot_x(value=math.radians(90))
        angle_kick.rot_z(
            '-atan((Depth+Right_Depth-Toe_Kick_Setback)'
            '/(Width-Left_Depth+Toe_Kick_Setback))',
            [Width, Depth, Right_Depth, Left_Depth, Toe_Kick_Setback])
        angle_kick.dim_x(
            'sqrt((Width-Left_Depth+Toe_Kick_Setback-Shelf_Thickness)**2'
            '+(Depth+Right_Depth-Toe_Kick_Setback)**2)',
            [Width, Depth, Left_Depth, Right_Depth,
             Toe_Kick_Setback, Shelf_Thickness])
        angle_kick.dim_y('Toe_Kick_Height', [Toe_Kick_Height])
        angle_kick.dim_z('PT', [PT])
        angle_kick.get_prompt(
            'Hide').set_formula(
                'IF(Hide_Toe_Kick,True,IF(Is_Hanging,True,False))',
                [Hide_Toe_Kick, Is_Hanging])

        # Fillers
        create_corner_fillers(self, Panel_Height, Left_Side_Wall_Filler,
                              Panel_Thickness, Left_Depth, Depth,
                              Left_Filler_Setback_Amount, Is_Hanging, Width,
                              Edge_Bottom_of_Left_Filler, self.hide_var,
                              Add_Capping_Left_Filler, Right_Side_Wall_Filler,
                              Right_Filler_Setback_Amount, Toe_Kick_Height,
                              Edge_Bottom_of_Right_Filler, Right_Depth,
                              Add_Capping_Right_Filler)
        # Doors
        # Left Angled Door
        angled_door_l = common_parts.add_door(self)
        angled_door_l.set_name("Angled Door Left")
        angled_door_l.loc_x('Left_Depth', [Left_Depth])
        angled_door_l.loc_y('Depth+PT', [Depth, PT])
        angled_door_l.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height, Shelf_Thickness])
        angled_door_l.rot_y(value=math.radians(-90))
        angled_door_l.rot_z('(atan((Width-Left_Depth)/(Depth+Right_Depth)))+3.14159-radians(Open*Rotation)', [Width, Depth, Right_Depth, Left_Depth, Open, Rotation])
        angled_door_l.dim_x('Panel_Height-(Shelf_Thickness)', [Panel_Height, Shelf_Thickness])
        angled_door_l.dim_y('IF(Force_Double_Doors,(sqrt((Width-Left_Depth-PT)**2+(Depth+Right_Depth+PT)**2)/2)-0.0015875,(sqrt((Width-Left_Depth-PT)**2+(Depth+Right_Depth+PT)**2)))*-1',
                            [Width, Left_Depth, Depth, Right_Depth, PT, Force_Double_Doors])
        angled_door_l.dim_z('PT', [PT])
        angled_door_l.get_prompt('Hide').set_formula(
            'IF((Door and Force_Double_Doors and Use_Left_Swing),False,IF((Door and Force_Double_Doors),False,IF((Door and Use_Left_Swing),False,IF(Door,True,True))))',
            [Door, Use_Left_Swing, Force_Double_Doors])

        # Right Angled Door
        angled_door_r = common_parts.add_door(self)
        angled_door_r.set_name("Angled Door Right")
        angled_door_r.loc_x('Width-PT', [Width, PT])
        angled_door_r.loc_y('-Right_Depth', [Right_Depth])
        angled_door_r.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)', [Height, Panel_Height, Is_Hanging, Toe_Kick_Height, Shelf_Thickness])
        angled_door_r.rot_y(value=math.radians(-90))
        angled_door_r.rot_z('(atan((Width-Left_Depth)/(Depth+Right_Depth)))+3.14159+radians(Open*Rotation)', [Width, Depth, Right_Depth, Left_Depth, Open, Rotation])
        angled_door_r.dim_x('Panel_Height-(Shelf_Thickness)', [Panel_Height, Shelf_Thickness])
        angled_door_r.dim_y('IF(Force_Double_Doors,(sqrt((Width-Left_Depth-PT)**2+(Depth+Right_Depth+PT)**2)/2)-0.0015875,(sqrt((Width-Left_Depth-PT)**2+(Depth+Right_Depth+PT)**2)))',
                            [Width, Left_Depth, Depth, Right_Depth, PT, Force_Double_Doors])
        angled_door_r.dim_z('PT', [PT])
        angled_door_r.get_prompt('Hide').set_formula(
            'IF((Door and Force_Double_Doors and Use_Left_Swing),False,IF((Door and Force_Double_Doors),False,IF((Door and Use_Left_Swing),True,IF(Door,False,True))))',
            [Door, Use_Left_Swing, Force_Double_Doors])

        # Left Angled Pull
        angled_door_l_pull = common_parts.add_drawer_pull(self)
        angled_door_l_pull.set_name("Left Door Pull")
        angled_door_l_pull.loc_x('Left_Depth', [Left_Depth])
        angled_door_l_pull.loc_y('Depth+PT', [Depth, PT])
        angled_door_l_pull.loc_z(
            'IF(Pull_Type==2,IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)+Upper_Pull_Location,IF(Pull_Type==1,Height-Tall_Pull_Location+World_Z,Height-Base_Pull_Location))',
            [Door_Pull_Height, Pull_Type, Base_Pull_Location, Tall_Pull_Location, Upper_Pull_Location, Height, World_Z, Toe_Kick_Height, Shelf_Thickness, Is_Hanging, Panel_Height])
        angled_door_l_pull.dim_z('PT', [PT])
        angled_door_l_pull.dim_y(
            'IF(Force_Double_Doors,(sqrt((Width-Left_Depth-PT)**2+(Depth+Right_Depth+PT)**2)/2)-0.0015875,(sqrt((Width-Left_Depth-PT)**2+(Depth+Right_Depth+PT)**2)))*-1+PT',
            [Width, Left_Depth, Depth, Right_Depth, PT, Force_Double_Doors])
        angled_door_l_pull.rot_y(value=math.radians(-90))
        angled_door_l_pull.rot_z('(atan((Width-Left_Depth)/(Depth+Right_Depth)))+3.14159-radians(Open*Rotation)', [Width, Depth, Right_Depth, Left_Depth, Open, Rotation])
        angled_door_l_pull.get_prompt('Hide').set_formula(
            'IF((Door and Force_Double_Doors and Use_Left_Swing),False,IF((Door and Force_Double_Doors),False,IF((Door and Use_Left_Swing),False,IF(Door,True,True))))',
            [Door, Use_Left_Swing, Force_Double_Doors])

        # Right Angled Pull
        angled_door_r_pull = common_parts.add_drawer_pull(self)
        angled_door_r_pull.set_name("Right Door Pull")
        angled_door_r_pull.loc_x('Width-PT', [Width, PT])
        angled_door_r_pull.loc_y('-Right_Depth', [Right_Depth])
        angled_door_r_pull.loc_z(
            'IF(Pull_Type==2,IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+(Shelf_Thickness/2)+Upper_Pull_Location,IF(Pull_Type==1,Height-Tall_Pull_Location+World_Z,Height-Base_Pull_Location))',
            [Door_Pull_Height, Pull_Type, Base_Pull_Location, Tall_Pull_Location, Upper_Pull_Location, Height, World_Z, Toe_Kick_Height, Shelf_Thickness, Is_Hanging, Panel_Height])
        angled_door_r_pull.dim_z('PT', [PT])
        angled_door_r_pull.dim_y(
            'IF(Force_Double_Doors,(sqrt((Width-Left_Depth-PT)**2+(Depth+Right_Depth+PT)**2)/2)-0.0015875,(sqrt((Width-Left_Depth-PT)**2+(Depth+Right_Depth+PT)**2)))-PT',
            [Width, Left_Depth, Depth, Right_Depth, PT, Force_Double_Doors])
        angled_door_r_pull.rot_y(value=math.radians(-90))
        angled_door_r_pull.rot_z('(atan((Width-Left_Depth)/(Depth+Right_Depth)))+3.14159+radians(Open*Rotation)', [Width, Depth, Right_Depth, Left_Depth, Open, Rotation])
        angled_door_r_pull.get_prompt('Hide').set_formula(
            'IF((Door and Force_Double_Doors and Use_Left_Swing),False,IF((Door and Force_Double_Doors),False,IF((Door and Use_Left_Swing),True,IF(Door,False,True))))',
            [Door, Use_Left_Swing, Force_Double_Doors])

        # Shelves
        # Angled Shelves
        previous_angled_shelf = None
        for i in range(1, 11):
            Shelf_Height = self.get_prompt("Shelf " + str(i) + " Height").get_var('Shelf_Height')

            shelf_angled = common_parts.add_angle_shelf(self)

            if previous_angled_shelf:
                prev_shelf_z_loc = previous_angled_shelf.obj_bp.snap.get_var('location.z', 'prev_shelf_z_loc')
                shelf_angled.loc_z('prev_shelf_z_loc+Shelf_Height', [prev_shelf_z_loc, Shelf_Height])
            else:
                shelf_angled.loc_z('IF(Is_Hanging,Height-Panel_Height,Toe_Kick_Height)+Shelf_Height+Shelf_Thickness',
                                   [Shelf_Height, Is_Hanging, Toe_Kick_Height, Shelf_Thickness, Panel_Height, Height])

            shelf_angled.loc_x('IF(Add_Backing,Backing_Thickness,0)', [Add_Backing, Backing_Thickness])
            shelf_angled.loc_y('IF(Add_Backing,-Backing_Thickness,0)', [Add_Backing, Backing_Thickness])
            shelf_angled.rot_x(value=0)
            shelf_angled.rot_y(value=0)
            shelf_angled.rot_z(value=0)
            shelf_angled.dim_x('Width-PT-IF(Add_Backing,Backing_Thickness,0)', [Width, PT, Add_Backing, Backing_Thickness])
            shelf_angled.dim_y('Depth+PT+IF(Add_Backing,Backing_Thickness,0)', [Depth, PT, Add_Backing, Backing_Thickness])
            shelf_angled.dim_z('Shelf_Thickness', [Shelf_Thickness])
            shelf_angled.get_prompt('Left Depth').set_formula('Left_Depth-IF(Add_Backing,Backing_Thickness,0)', [Left_Depth, Add_Backing, Backing_Thickness])
            shelf_angled.get_prompt('Right Depth').set_formula('Right_Depth-IF(Add_Backing,Backing_Thickness,0)', [Right_Depth, Add_Backing, Backing_Thickness])
            shelf_angled.get_prompt('Hide').set_formula('IF(Shelf_Quantity>' + str(i) + ',False,True)', [Shelf_Quantity])

            previous_angled_shelf = shelf_angled

    def draw(self):
        self.obj_bp["IS_BP_CLOSET"] = True
        self.obj_bp["IS_BP_CORNER_SHELVES"] = True
        self.obj_bp["ID_PROMPT"] = self.property_id
        self.obj_y['IS_MIRROR'] = True
        self.obj_bp.snap.type_group = self.type_assembly
        self.update()
        set_tk_id_prompt(self.obj_bp)


class PROMPTS_L_Shelves_214(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.l_shelves_214"
    bl_label = "L Shelves Prompts"
    bl_options = {'UNDO'}

    object_name: StringProperty(name="Object Name",
                                description="Stores the Base Point Object Name \
                                so the object can be retrieved from the database.")

    width: FloatProperty(name="Width", unit='LENGTH', precision=4)
    height: FloatProperty(name="Height", unit='LENGTH', precision=4)
    depth: FloatProperty(name="Depth", unit='LENGTH', precision=4)

    Product_Height: EnumProperty(name="Product Height",
                                 items=common_lists.PANEL_HEIGHTS,
                                 default='2003',
                                 update=update_product_height)

    Door_Type: EnumProperty(name="Door Type",
                            items=[("0", "Reach Back", "Reach Back"),
                                   ("1", "Lazy Susan", "Lazy Susan")],
                            default='0')

    Pull_Location: EnumProperty(name="Pull Location",
                                items=[("0", "Pull on Left Door", "Pull on Left Door"),
                                       ("1", "Pull on Right Door", "Pull on Right Door")],
                                default="0")

    Pull_Type: EnumProperty(name="Pull Type",
                            items=[("0", "Base", "Base"),
                                   ("1", "Tall", "Tall"),
                                   ("2", "Upper", "Upper")],
                            default="1")

    Shelf_1_Height: EnumProperty(name="Shelf 1 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_2_Height: EnumProperty(name="Shelf 2 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_3_Height: EnumProperty(name="Shelf 3 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_4_Height: EnumProperty(name="Shelf 4 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_5_Height: EnumProperty(name="Shelf 5 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_6_Height: EnumProperty(name="Shelf 6 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_7_Height: EnumProperty(name="Shelf 7 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_8_Height: EnumProperty(name="Shelf 8 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_9_Height: EnumProperty(name="Shelf 9 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_10_Height: EnumProperty(name="Shelf 10 Height",
                                  items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    shelf_quantity: EnumProperty(name="Shelf Quantity",
                                 items=[('1', "1", '1'),
                                        ('2', "2", '2'),
                                        ('3', "3", '3'),
                                        ('4', "4", '4'),
                                        ('5', "5", '5'),
                                        ('6', "6", '6'),
                                        ('7', "7", '7'),
                                        ('8', "8", '8'),
                                        ('9', "9", '9'),
                                        ('10', "10", '10')],
                                 default='3')

    product = None
    show_tk_mess = None

    prev_left_wall_filler = 0

    def check(self, context):
        """ This is called everytime a change is made in the UI """
        self.set_prompts_from_properties()
        self.check_fillers()
        self.set_obj_location()
        closet_props.update_render_materials(self, context)
        return True

    def execute(self, context):
        """ This is called when the OK button is clicked """
        return {'FINISHED'}

    def invoke(self, context, event):
        """ This is called before the interface is displayed """
        self.product = self.get_product()
        self.set_properties_from_prompts()
        self.set_filler_values()
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(400))

    def set_obj_location(self):
        right_wall_filler =\
            self.product.get_prompt("Right Side Wall Filler")
        left_wall_filler =\
            self.product.get_prompt("Left Side Wall Filler")
        self.product.obj_y.location.y =\
            -self.depth + left_wall_filler.get_value()
        self.product.obj_x.location.x =\
            self.width - right_wall_filler.get_value()

    def set_filler_values(self):
        left_wall_filler =\
            self.product.get_prompt("Left Side Wall Filler")
        right_wall_filler =\
            self.product.get_prompt("Right Side Wall Filler")
        self.prev_left_wall_filler = left_wall_filler.get_value()
        self.depth =\
            -self.product.obj_y.location.y + left_wall_filler.get_value()
        self.width =\
            self.product.obj_x.location.x + right_wall_filler.get_value()

    def check_fillers(self):
        add_left_filler =\
            self.product.get_prompt("Add Left Filler").get_value()
        add_right_filler =\
            self.product.get_prompt("Add Right Filler").get_value()
        if not add_left_filler:
            left_wall_filler =\
                self.product.get_prompt("Left Side Wall Filler")
            left_filler_setback_amount =\
                self.product.get_prompt("Left Filler Setback Amount")
            edge_bottom_of_left_filler =\
                self.product.get_prompt("Edge Bottom of Left Filler")
            add_capping_left_filler = \
                self.product.get_prompt("Add Capping Left Filler")
            left_wall_filler.set_value(0)
            left_filler_setback_amount.set_value(0)
            edge_bottom_of_left_filler.set_value(False)
            add_capping_left_filler.set_value(False)
            self.prev_left_wall_filler = 0
        if not add_right_filler:
            right_wall_filler =\
                self.product.get_prompt("Right Side Wall Filler")
            right_filler_setback_amount =\
                self.product.get_prompt("Right Filler Setback Amount")
            edge_bottom_of_righ_filler =\
                self.product.get_prompt("Edge Bottom of Right Filler")
            add_capping_righ_filler = \
                self.product.get_prompt("Add Capping Right Filler")
            right_wall_filler.set_value(0)
            right_filler_setback_amount.set_value(0)
            edge_bottom_of_righ_filler.set_value(False)
            add_capping_righ_filler.set_value(False)

    def set_prompts_from_properties(self):
        ''' This should be called in the check function to set the prompts
            to the same values as the class properties
        '''
        door_type = self.product.get_prompt('Door Type')
        pull_location = self.product.get_prompt('Pull Location')
        pull_type = self.product.get_prompt('Pull Type')
        is_hanging = self.product.get_prompt("Is Hanging")
        panel_height = self.product.get_prompt("Panel Height")
        shelf_quantity = self.product.get_prompt("Shelf Quantity")
        shelf_thickness = self.product.get_prompt("Shelf Thickness")
        toe_kick_height = self.product.get_prompt("Toe Kick Height")
        if toe_kick_height.distance_value <= inch(3):
            self.product.get_prompt("Toe Kick Height").set_value(inch(3))
            bpy.ops.snap.log_window('INVOKE_DEFAULT',
                                    message="Minimum Toe Kick Height is 3\"",
                                    icon="ERROR")

        prompts = [door_type, pull_location, pull_type, is_hanging, panel_height, shelf_quantity, shelf_thickness, toe_kick_height]
        if all(prompts):
            door_type.set_value(int(self.Door_Type))
            pull_location.set_value(int(self.Pull_Location))
            pull_type.set_value(int(self.Pull_Type))
            if is_hanging.get_value():
                panel_height.set_value(float(self.Product_Height) / 1000)
            else:
                panel_height.set_value(float(self.Product_Height) / 1000)
                self.product.obj_z.location.z = float(self.Product_Height) / 1000

            shelf_quantity.set_value(int(self.shelf_quantity))
            for i in range(1, int(self.shelf_quantity)):
                shelf = self.product.get_prompt("Shelf " + str(i) + " Height")

                hole_count = round(((panel_height.get_value()) * 1000) / 32)
                holes_per_shelf = round(hole_count / int(self.shelf_quantity))
                remainder = hole_count - (holes_per_shelf * (int(self.shelf_quantity)))

                if(i <= remainder):
                    holes_per_shelf = holes_per_shelf + 1
                if(holes_per_shelf >= 3):
                    shelf.set_value(float(common_lists.SHELF_IN_DOOR_HEIGHTS[holes_per_shelf - 3][0]) / 1000)
                    exec("self.Shelf_" + str(i) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[holes_per_shelf-3][0]")
                else:
                    shelf.set_value(float(common_lists.SHELF_IN_DOOR_HEIGHTS[0][0]) / 1000)
                    exec("self.Shelf_" + str(i) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[0][0]")

    def set_properties_from_prompts(self):
        ''' This should be called in the invoke function to set the class properties
            to the same values as the prompts
        '''
        panel_height = self.product.get_prompt("Panel Height")
        door_type = self.product.get_prompt('Door Type')
        pull_location = self.product.get_prompt('Pull Location')
        pull_type = self.product.get_prompt('Pull Type')
        shelf_quantity = self.product.get_prompt("Shelf Quantity")

        prompts = [door_type, pull_location, pull_type, panel_height, shelf_quantity]
        if all(prompts):
            self.Door_Type = str(door_type.get_value())
            self.Pull_Location = str(pull_location.get_value())
            self.Pull_Type = str(pull_type.get_value())
            for index, height in enumerate(common_lists.PANEL_HEIGHTS):
                if not round(panel_height.get_value() * 1000, 0) >= int(height[0]):
                    self.Product_Height = common_lists.PANEL_HEIGHTS[index - 1][0]
                    break

            self.shelf_quantity = str(shelf_quantity.get_value())
            for i in range(1, 11):
                shelf = self.product.get_prompt("Shelf " + str(i) + " Height")
                if shelf:
                    value = round(shelf.get_value() * 1000, 3)
                    for index, height in enumerate(common_lists.SHELF_IN_DOOR_HEIGHTS):
                        if not value >= float(height[0]):
                            exec("self.Shelf_" + str(i) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[index - 1][0]")
                            break

    def draw_product_size(self, layout):
        box = layout.box()
        row = box.row()

        col = row.column(align=True)
        row1 = col.row(align=True)
        row1.label(text='Width:')
        row1.prop(self, 'width', text="")

        row1 = col.row(align=True)
        if sn_utils.object_has_driver(self.product.obj_z):
            row1.label(text='Height: ' + str(sn_unit.meter_to_active_unit(math.fabs(self.product.obj_z.location.z))))
        else:
            row1.label(text='Height:')
            row1.prop(self, 'Product_Height', text="")

        row1 = col.row(align=True)
        row1.label(text='Depth:')
        row1.prop(self, 'depth', text="")

        col = row.column(align=True)
        col.label(text="Location X:")
        col.label(text="Location Y:")
        col.label(text="Location Z:")

        col = row.column(align=True)
        col.prop(self.product.obj_bp, 'location', text="")

        Toe_Kick_Height = self.product.get_prompt("Toe Kick Height")

        if Toe_Kick_Height:
            row = box.row()
            row.prop(Toe_Kick_Height, "distance_value", text=Toe_Kick_Height.name)

        is_hanging = self.product.get_prompt("Is Hanging")

        if is_hanging:
            row = box.row()
            row.prop(is_hanging, "checkbox_value", text=is_hanging.name)
            if is_hanging.get_value():
                row.prop(self.product.obj_z, 'location', index=2, text="Hanging Height")

        row = box.row()
        row.label(text='Rotation Z:')
        row.prop(self.product.obj_bp, 'rotation_euler', index=2, text="")

    def draw_filler_options(self, layout):
        add_left_filler = self.product.get_prompt("Add Left Filler")
        add_right_filler = self.product.get_prompt("Add Right Filler")
        left_wall_filler = self.product.get_prompt("Left Side Wall Filler")
        right_wall_filler =\
            self.product.get_prompt("Right Side Wall Filler")
        left_filler_setback_amount =\
            self.product.get_prompt("Left Filler Setback Amount")
        right_filler_setback_amount =\
            self.product.get_prompt("Right Filler Setback Amount")
        add_capping_left_filler =\
            self.product.get_prompt("Add Capping Left Filler")
        add_capping_right_filler =\
            self.product.get_prompt("Add Capping Right Filler")
        edge_bottom_of_left_filler =\
            self.product.get_prompt("Edge Bottom of Left Filler")
        edge_bottom_of_right_filler =\
            self.product.get_prompt("Edge Bottom of Right Filler")

        filler_box = layout.box()
        split = filler_box.split()
        col = split.column(align=True)
        col.label(text="Filler Options:")
        row = col.row()
        row.prop(add_left_filler, 'checkbox_value', text="Add Left Filler")
        row.prop(add_right_filler, 'checkbox_value', text="Add Right Filler")
        row = col.row()
        distance_row = col.row()
        setback_amount_row = col.row()
        capping_filler_row = col.row()
        edge_row = col.row()

        if add_left_filler.get_value():
            distance_row.prop(
                left_wall_filler,
                'distance_value', text="Left Filler Amount")
            setback_amount_row.prop(
                left_filler_setback_amount,
                'distance_value', text="Left Filler Setback Amount")
            capping_filler_row.prop(
                add_capping_left_filler,
                'checkbox_value', text="Add Capping Left Filler")
            edge_row.prop(
                edge_bottom_of_left_filler,
                'checkbox_value', text="Edge Bottom of Left Filler")
        elif add_right_filler.get_value():
            distance_row.label(text="")
            setback_amount_row.label(text="")
            capping_filler_row.label(text="")
            edge_row.label(text="")

        if add_right_filler.get_value():
            distance_row.prop(
                right_wall_filler,
                'distance_value', text="Right Filler Amount")
            setback_amount_row.prop(
                right_filler_setback_amount,
                'distance_value', text="Right Filler Setback Amount")
            capping_filler_row.prop(
                add_capping_right_filler,
                'checkbox_value', text="Add Capping Right Filler")
            edge_row.prop(
                edge_bottom_of_right_filler,
                'checkbox_value', text="Edge Bottom of Right Filler")
        elif add_left_filler.get_value():
            distance_row.label(text="")
            setback_amount_row.label(text="")
            capping_filler_row.label(text="")
            edge_row.label(text="")

    def draw(self, context):
        """ This is where you draw the interface """
        Left_Depth = self.product.get_prompt("Left Depth")
        Right_Depth = self.product.get_prompt("Right Depth")
        Shelf_Quantity = self.product.get_prompt("Shelf Quantity")
        Add_Backing = self.product.get_prompt("Add Backing")
        # Backing_Thickness = self.product.get_prompt("Backing Thickness")
        Add_Top = self.product.get_prompt("Add Top KD")
        Remove_Left_Side = self.product.get_prompt("Remove Left Side")
        Remove_Right_Side = self.product.get_prompt("Remove Right Side")
        Door = self.product.get_prompt("Door")
        Door_Type = self.product.get_prompt("Door Type")
        Open_Door = self.product.get_prompt("Open Door")
        Base_Pull_Location = self.product.get_prompt("Base Pull Location")
        Tall_Pull_Location = self.product.get_prompt("Tall Pull Location")
        Upper_Pull_Location = self.product.get_prompt("Upper Pull Location")
        Add_Top_Shelf = self.product.get_prompt("Add Top Shelf")
        Exposed_Left = self.product.get_prompt("Exposed Left")
        Exposed_Right = self.product.get_prompt("Exposed Right")
        Top_Shelf_Overhang = self.product.get_prompt("Top Shelf Overhang")
        Extend_Left = self.product.get_prompt("Extend Left")
        Extend_Right = self.product.get_prompt("Extend Right")

        layout = self.layout
        self.draw_product_size(layout)
        self.draw_filler_options(layout)

        if Left_Depth:
            box = layout.box()
            row = box.row()
            row.prop(Left_Depth, "distance_value", text=Left_Depth.name)

        if Right_Depth:
            row.prop(Right_Depth, "distance_value", text=Right_Depth.name)

        if Shelf_Quantity:
            col = box.column(align=True)
            row = col.row()
            row.label(text="Qty:")
            row.prop(self, "shelf_quantity", expand=True)
            col.separator()

        if Add_Backing:
            row = box.row()
            row.prop(Add_Backing, "checkbox_value", text=Add_Backing.name)

        # if Backing_Thickness:
        #    if Add_Backing.get_value():
        #        row = box.row()
        #        row.prop(Backing_Thickness, "distance_value", text=Backing_Thickness.name)

        if Add_Top:
            row = box.row()
            row.prop(Add_Top, "checkbox_value", text=Add_Top.name)

        if Add_Top_Shelf:
            row = box.row()
            row.prop(Add_Top_Shelf, "checkbox_value", text=Add_Top_Shelf.name)
            if Add_Top_Shelf.get_value():
                row = box.row()
                row.label(text="Exposed Edges: ")
                row.prop(Exposed_Left, "checkbox_value", text='Left')
                row.prop(Exposed_Right, "checkbox_value", text='Right')
                row = box.row()
                row.prop(Top_Shelf_Overhang, 'distance_value', text=Top_Shelf_Overhang.name)
                row = box.row()
                row.prop(Extend_Left, 'distance_value', text=Extend_Left.name)
                row.prop(Extend_Right, 'distance_value', text=Extend_Right.name)

        if Remove_Left_Side:
            row = box.row()
            row.prop(Remove_Left_Side, "checkbox_value", text=Remove_Left_Side.name)

        if Remove_Right_Side:
            row = box.row()
            row.prop(Remove_Right_Side, "checkbox_value", text=Remove_Right_Side.name)

        row = box.row()
        row.prop(Door, "checkbox_value", text=Door.name)

        if Door.get_value():
            if Door_Type:
                row = box.row()
                row.prop(self, 'Door_Type', text="Door Type")
                row = box.row()
                row.prop(self, 'Pull_Location', text="Pull Location", expand=True)
            row = box.row()
            row.prop(self, 'Pull_Type', text="Pull Type", expand=True)
            row = box.row()
            row.label(text="Pull Location: ")
            if self.Pull_Type == '0':
                row.prop(Base_Pull_Location, "distance_value", text="")
            elif self.Pull_Type == '1':
                row.prop(Tall_Pull_Location, "distance_value", text="")
            else:
                row.prop(Upper_Pull_Location, "distance_value", text="")
            if Open_Door:
                row = box.row()
                row.prop(Open_Door, "factor_value", text=Open_Door.name)


class PROMPTS_Corner_Shelves_214(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.corner_shelves_214"
    bl_label = "Corner Shelves Prompts"
    bl_options = {'UNDO'}

    object_name: StringProperty(name="Object Name",
                                description="Stores the Base Point Object Name \
                                so the object can be retrieved from the database.")

    width: FloatProperty(name="Width", unit='LENGTH', precision=4)
    height: FloatProperty(name="Height", unit='LENGTH', precision=4)
    depth: FloatProperty(name="Depth", unit='LENGTH', precision=4)

    Product_Height: EnumProperty(name="Product Height",
                                 items=common_lists.PANEL_HEIGHTS,
                                 default='2003',
                                 update=update_product_height)

    Pull_Type: EnumProperty(name="Pull Type",
                            items=[("0", "Base", "Base"),
                                   ("1", "Tall", "Tall"),
                                   ("2", "Upper", "Upper")],
                            default="1")

    Shelf_1_Height: EnumProperty(name="Shelf 1 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_2_Height: EnumProperty(name="Shelf 2 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_3_Height: EnumProperty(name="Shelf 3 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_4_Height: EnumProperty(name="Shelf 4 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_5_Height: EnumProperty(name="Shelf 5 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_6_Height: EnumProperty(name="Shelf 6 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_7_Height: EnumProperty(name="Shelf 7 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_8_Height: EnumProperty(name="Shelf 8 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_9_Height: EnumProperty(name="Shelf 9 Height",
                                 items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    Shelf_10_Height: EnumProperty(name="Shelf 10 Height",
                                  items=common_lists.SHELF_IN_DOOR_HEIGHTS)

    shelf_quantity: EnumProperty(name="Shelf Quantity",
                                 items=[('1', "1", '1'),
                                        ('2', "2", '2'),
                                        ('3', "3", '3'),
                                        ('4', "4", '4'),
                                        ('5', "5", '5'),
                                        ('6', "6", '6'),
                                        ('7', "7", '7'),
                                        ('8', "8", '8'),
                                        ('9', "9", '9'),
                                        ('10', "10", '10')],
                                 default='3')

    product = None

    def check_tk_height(self):
        toe_kick_height =\
            self.product.get_prompt("Toe Kick Height").distance_value
        if toe_kick_height < inch(3):
            self.product.get_prompt("Toe Kick Height").set_value(inch(3))
            bpy.ops.snap.log_window('INVOKE_DEFAULT',
                                    message="Minimum Toe Kick Height is 3\"",
                                    icon="ERROR")

    def check(self, context):
        """ This is called everytime a change is made in the UI """
        self.check_tk_height()
        self.set_prompts_from_properties()
        self.check_fillers()
        self.set_obj_location()
        closet_props.update_render_materials(self, context)
        return True

    def execute(self, context):
        """ This is called when the OK button is clicked """
        self.show_tk_mess = False
        return {'FINISHED'}

    def invoke(self, context, event):
        """ This is called before the interface is displayed """
        self.product = self.get_product()
        self.set_properties_from_prompts()
        self.set_filler_values()
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(400))

    def set_filler_values(self):
        left_wall_filler =\
            self.product.get_prompt("Left Side Wall Filler")
        right_wall_filler =\
            self.product.get_prompt("Right Side Wall Filler")
        self.prev_left_wall_filler = left_wall_filler.get_value()
        self.depth =\
            -self.product.obj_y.location.y + left_wall_filler.get_value()
        self.width =\
            self.product.obj_x.location.x + right_wall_filler.get_value()

    def set_prompts_from_properties(self):
        ''' This should be called in the check function to set the prompts
            to the same values as the class properties
        '''
        pull_type = self.product.get_prompt('Pull Type')
        is_hanging = self.product.get_prompt("Is Hanging")
        panel_height = self.product.get_prompt("Panel Height")
        shelf_quantity = self.product.get_prompt("Shelf Quantity")
        shelf_thickness = self.product.get_prompt("Shelf Thickness")
        toe_kick_height = self.product.get_prompt("Toe Kick Height")

        prompts = [pull_type, is_hanging, panel_height, shelf_quantity, shelf_thickness, toe_kick_height]
        if all(prompts):
            pull_type.set_value(int(self.Pull_Type))
            if is_hanging.get_value():
                panel_height.set_value(float(self.Product_Height) / 1000)
            else:
                panel_height.set_value(float(self.Product_Height) / 1000)
                self.product.obj_z.location.z = float(self.Product_Height) / 1000

            shelf_quantity.set_value(int(self.shelf_quantity))
            for i in range(1, int(self.shelf_quantity)):
                shelf = self.product.get_prompt("Shelf " + str(i) + " Height")

                hole_count = round(((panel_height.get_value()) * 1000) / 32)
                holes_per_shelf = round(hole_count / int(self.shelf_quantity))
                remainder = hole_count - (holes_per_shelf * (int(self.shelf_quantity)))

                if(i <= remainder):
                    holes_per_shelf = holes_per_shelf + 1
                if(holes_per_shelf >= 3):
                    shelf.set_value(float(common_lists.SHELF_IN_DOOR_HEIGHTS[holes_per_shelf - 3][0]) / 1000)
                    exec("self.Shelf_" + str(i) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[holes_per_shelf-3][0]")
                else:
                    shelf.set_value(float(common_lists.SHELF_IN_DOOR_HEIGHTS[0][0]) / 1000)
                    exec("self.Shelf_" + str(i) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[0][0]")

    def set_properties_from_prompts(self):
        ''' This should be called in the invoke function to set the class properties
            to the same values as the prompts
        '''
        panel_height = self.product.get_prompt("Panel Height")
        pull_type = self.product.get_prompt('Pull Type')
        shelf_quantity = self.product.get_prompt("Shelf Quantity")

        prompts = [pull_type, panel_height, shelf_quantity]
        if all(prompts):
            self.Pull_Type = str(pull_type.get_value())
            for index, height in enumerate(common_lists.PANEL_HEIGHTS):
                if not round(panel_height.get_value() * 1000, 0) >= int(height[0]):
                    self.Product_Height = common_lists.PANEL_HEIGHTS[index - 1][0]
                    break

            self.shelf_quantity = str(shelf_quantity.get_value())
            for i in range(1, 11):
                shelf = self.product.get_prompt("Shelf " + str(i) + " Height")
                if shelf:
                    value = round(shelf.get_value() * 1000, 3)
                    for index, height in enumerate(common_lists.SHELF_IN_DOOR_HEIGHTS):
                        if not value >= float(height[0]):
                            exec("self.Shelf_" + str(i) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[index - 1][0]")
                            break

    def draw_product_size(self, layout):
        box = layout.box()
        row = box.row()

        col = row.column(align=True)
        row1 = col.row(align=True)
        row1.label(text='Width:')
        row1.prop(self, 'width', text="")

        row1 = col.row(align=True)
        if sn_utils.object_has_driver(self.product.obj_z):
            row1.label(text='Height: ' + str(sn_unit.meter_to_active_unit(math.fabs(self.product.obj_z.location.z))))
        else:
            row1.label(text='Height:')
            row1.prop(self, 'Product_Height', text="")

        row1 = col.row(align=True)
        row1.label(text='Depth:')
        row1.prop(self, 'depth', text="")

        col = row.column(align=True)
        col.label(text="Location X:")
        col.label(text="Location Y:")
        col.label(text="Location Z:")

        col = row.column(align=True)
        col.prop(self.product.obj_bp, 'location', text="")

        Toe_Kick_Height = self.product.get_prompt("Toe Kick Height")

        if Toe_Kick_Height:
            row = box.row()
            row.prop(Toe_Kick_Height, "distance_value", text=Toe_Kick_Height.name)

        is_hanging = self.product.get_prompt("Is Hanging")

        if is_hanging:
            row = box.row()
            row.prop(is_hanging, "checkbox_value", text=is_hanging.name)
            if is_hanging.get_value():
                row.prop(self.product.obj_z, 'location', index=2, text="Hanging Height")

        row = box.row()
        row.label(text='Rotation Z:')
        row.prop(self.product.obj_bp, 'rotation_euler', index=2, text="")

    def set_obj_location(self):
        right_wall_filler =\
            self.product.get_prompt("Right Side Wall Filler")
        left_wall_filler =\
            self.product.get_prompt("Left Side Wall Filler")
        self.product.obj_y.location.y =\
            -self.depth + left_wall_filler.get_value()
        self.product.obj_x.location.x =\
            self.width - right_wall_filler.get_value()

    def check_fillers(self):
        add_left_filler =\
            self.product.get_prompt("Add Left Filler").get_value()
        add_right_filler =\
            self.product.get_prompt("Add Right Filler").get_value()
        if not add_left_filler:
            left_wall_filler =\
                self.product.get_prompt("Left Side Wall Filler")
            left_filler_setback_amount =\
                self.product.get_prompt("Left Filler Setback Amount")
            edge_bottom_of_left_filler =\
                self.product.get_prompt("Edge Bottom of Left Filler")
            add_capping_left_filler = \
                self.product.get_prompt("Add Capping Left Filler")
            left_wall_filler.set_value(0)
            left_filler_setback_amount.set_value(0)
            edge_bottom_of_left_filler.set_value(False)
            add_capping_left_filler.set_value(False)
            self.prev_left_wall_filler = 0
        if not add_right_filler:
            right_wall_filler =\
                self.product.get_prompt("Right Side Wall Filler")
            right_filler_setback_amount =\
                self.product.get_prompt("Right Filler Setback Amount")
            edge_bottom_of_righ_filler =\
                self.product.get_prompt("Edge Bottom of Right Filler")
            add_capping_righ_filler = \
                self.product.get_prompt("Add Capping Right Filler")
            right_wall_filler.set_value(0)
            right_filler_setback_amount.set_value(0)
            edge_bottom_of_righ_filler.set_value(False)
            add_capping_righ_filler.set_value(False)

    def draw_filler_options(self, layout):
        add_left_filler = self.product.get_prompt("Add Left Filler")
        add_right_filler = self.product.get_prompt("Add Right Filler")
        left_wall_filler = self.product.get_prompt("Left Side Wall Filler")
        right_wall_filler =\
            self.product.get_prompt("Right Side Wall Filler")
        left_filler_setback_amount =\
            self.product.get_prompt("Left Filler Setback Amount")
        right_filler_setback_amount =\
            self.product.get_prompt("Right Filler Setback Amount")
        add_capping_left_filler =\
            self.product.get_prompt("Add Capping Left Filler")
        add_capping_right_filler =\
            self.product.get_prompt("Add Capping Right Filler")
        edge_bottom_of_left_filler =\
            self.product.get_prompt("Edge Bottom of Left Filler")
        edge_bottom_of_right_filler =\
            self.product.get_prompt("Edge Bottom of Right Filler")

        filler_box = layout.box()
        split = filler_box.split()
        col = split.column(align=True)
        col.label(text="Filler Options:")
        row = col.row()
        row.prop(add_left_filler, 'checkbox_value', text="Add Left Filler")
        row.prop(add_right_filler, 'checkbox_value', text="Add Right Filler")
        row = col.row()
        distance_row = col.row()
        setback_amount_row = col.row()
        capping_filler_row = col.row()
        edge_row = col.row()

        if add_left_filler.get_value():
            distance_row.prop(
                left_wall_filler,
                'distance_value', text="Left Filler Amount")
            setback_amount_row.prop(
                left_filler_setback_amount,
                'distance_value', text="Left Filler Setback Amount")
            capping_filler_row.prop(
                add_capping_left_filler,
                'checkbox_value', text="Add Capping Left Filler")
            edge_row.prop(
                edge_bottom_of_left_filler,
                'checkbox_value', text="Edge Bottom of Left Filler")
        elif add_right_filler.get_value():
            distance_row.label(text="")
            setback_amount_row.label(text="")
            capping_filler_row.label(text="")
            edge_row.label(text="")

        if add_right_filler.get_value():
            distance_row.prop(
                right_wall_filler,
                'distance_value', text="Right Filler Amount")
            setback_amount_row.prop(
                right_filler_setback_amount,
                'distance_value', text="Right Filler Setback Amount")
            capping_filler_row.prop(
                add_capping_right_filler,
                'checkbox_value', text="Add Capping Right Filler")
            edge_row.prop(
                edge_bottom_of_right_filler,
                'checkbox_value', text="Edge Bottom of Right Filler")
        elif add_left_filler.get_value():
            distance_row.label(text="")
            setback_amount_row.label(text="")
            capping_filler_row.label(text="")
            edge_row.label(text="")

    def draw(self, context):
        """ This is where you draw the interface """
        Left_Depth = self.product.get_prompt("Left Depth")
        Right_Depth = self.product.get_prompt("Right Depth")
        Shelf_Quantity = self.product.get_prompt("Shelf Quantity")
        Add_Backing = self.product.get_prompt("Add Backing")
        # Backing_Thickness = self.product.get_prompt("Backing Thickness")
        Add_Top = self.product.get_prompt("Add Top KD")
        Remove_Left_Side = self.product.get_prompt("Remove Left Side")
        Remove_Right_Side = self.product.get_prompt("Remove Right Side")
        Door = self.product.get_prompt("Door")
        Use_Left_Swing = self.product.get_prompt("Use Left Swing")
        Force_Double_Doors = self.product.get_prompt("Force Double Doors")
        Open_Door = self.product.get_prompt("Open Door")
        Base_Pull_Location = self.product.get_prompt("Base Pull Location")
        Tall_Pull_Location = self.product.get_prompt("Tall Pull Location")
        Upper_Pull_Location = self.product.get_prompt("Upper Pull Location")
        Add_Top_Shelf = self.product.get_prompt("Add Top Shelf")
        Exposed_Left = self.product.get_prompt("Exposed Left")
        Exposed_Right = self.product.get_prompt("Exposed Right")
        Top_Shelf_Overhang = self.product.get_prompt("Top Shelf Overhang")

        layout = self.layout
        self.draw_product_size(layout)
        self.draw_filler_options(layout)

        if Left_Depth:
            box = layout.box()
            row = box.row()
            row.prop(Left_Depth, "distance_value", text=Left_Depth.name)

        if Right_Depth:
            row.prop(Right_Depth, "distance_value", text=Right_Depth.name)

        if Shelf_Quantity:
            col = box.column(align=True)
            row = col.row()
            row.label(text="Qty:")
            row.prop(self, "shelf_quantity", expand=True)
            col.separator()

        if Add_Backing:
            row = box.row()
            row.prop(Add_Backing, "checkbox_value", text=Add_Backing.name)

        # if Backing_Thickness:
        #    if Add_Backing.get_value():
        #        row = box.row()
        #        row.prop(Backing_Thickness, "distance_value", text=Backing_Thickness.name)

        if Add_Top:
            row = box.row()
            row.prop(Add_Top, "checkbox_value", text=Add_Top.name)

        if Add_Top_Shelf:
            row = box.row()
            row.prop(Add_Top_Shelf, "checkbox_value", text=Add_Top_Shelf.name)
            if Add_Top_Shelf.get_value():
                row = box.row()
                row.label(text="Exposed Edges: ")
                row.prop(Exposed_Left, "checkbox_value", text='Left')
                row.prop(Exposed_Right, "checkbox_value", text='Right')
                row = box.row()
                row.prop(Top_Shelf_Overhang, 'distance_value', text=Top_Shelf_Overhang.name)

        if Remove_Left_Side:
            row = box.row()
            row.prop(Remove_Left_Side, "checkbox_value", text=Remove_Left_Side.name)

        if Remove_Right_Side:
            row = box.row()
            row.prop(Remove_Right_Side, "checkbox_value", text=Remove_Right_Side.name)

        row = box.row()
        row.prop(Door, "checkbox_value", text=Door.name)

        if Door.get_value():
            row = box.row()
            row.prop(self, 'Pull_Type', text="Pull Type", expand=True)
            row = box.row()
            row.label(text="Pull Location: ")
            if self.Pull_Type == '0':
                row.prop(Base_Pull_Location, "distance_value", text="")
            elif self.Pull_Type == '1':
                row.prop(Tall_Pull_Location, "distance_value", text="")
            else:
                row.prop(Upper_Pull_Location, "distance_value", text="")
            if Open_Door:
                row = box.row()
                row.prop(Open_Door, "factor_value", text=Open_Door.name)

            row = box.row()
            row.prop(Use_Left_Swing, "checkbox_value", text=Use_Left_Swing.name)
            row = box.row()
            row.prop(Force_Double_Doors, "checkbox_value", text=Force_Double_Doors.name)


class Doors(sn_types.Assembly):

    type_assembly = "INSERT"
    id_prompt = "sn_closets.door_prompts"
    drop_id = "sn_closets.insert_doors_drop"
    placement_type = "EXTERIOR"
    show_in_library = True
    category_name = "Products - Basic"
    mirror_y = False

    door_type = ""  # {Base, Tall, Upper, Sink, Suspended}
    striker_depth = sn_unit.inch(3.4)
    striker_thickness = sn_unit.inch(0.75)
    shelf_thickness_ppt_obj = None

    shelves = []
    shelf_z_loc_empties = []

    def __init__(self, obj_bp=None):
        super().__init__(obj_bp=obj_bp)
        self.shelves = []
        self.shelf_z_loc_empties = []
        self.get_shelves()

    def get_shelves(self):
        for child in self.obj_bp.children:
            if child.get("IS_SHELF"):
                shelf = sn_types.Assembly(child)
                is_locked_shelf = shelf.get_prompt("Is Locked Shelf")
                if is_locked_shelf:
                    if not is_locked_shelf.get_value():
                        self.shelves.append(sn_types.Assembly(child))

    def add_common_doors_prompts(self):
        props = bpy.context.scene.sn_closets
        defaults = props.closet_defaults

        common_prompts.add_thickness_prompts(self)
        common_prompts.add_front_overlay_prompts(self)
        common_prompts.add_pull_prompts(self)
        common_prompts.add_door_prompts(self)
        common_prompts.add_door_pull_prompts(self)
        common_prompts.add_door_lock_prompts(self)

        if defaults.use_plant_on_top and self.door_type == 'Upper':
            door_height = sn_unit.millimeter(1184)
        else:
            door_height = sn_unit.millimeter(653.288)

        for i in range(1,16):
            self.add_prompt("Shelf " + str(i) + " Height", 'DISTANCE', sn_unit.millimeter(76.962))
            self.add_prompt("Shelf " + str(i) + " Setback", 'DISTANCE', 0)

        ppt_obj_shelves = self.add_prompt_obj("Shelves")
        self.add_prompt("Shelf Stack Height", 'DISTANCE', 0, prompt_obj=ppt_obj_shelves)
        self.add_prompt("Doors Backing Gap", 'DISTANCE', 0, prompt_obj=ppt_obj_shelves)
        glass_thickness = self.add_prompt("Glass Thickness", 'DISTANCE', sn_unit.inch(0.75), prompt_obj=ppt_obj_shelves)

        self.add_prompt("Fill Opening", 'CHECKBOX', False)
        self.add_prompt("Insert Height", 'DISTANCE', door_height)
        self.add_prompt("Offset For Plant On Top", 'CHECKBOX', defaults.use_plant_on_top)
        self.add_prompt("Add Striker", 'CHECKBOX', False)
        self.add_prompt("Striker Depth", 'DISTANCE', self.striker_depth)
        self.add_prompt("Striker Thickness", 'DISTANCE', self.striker_thickness)
        self.add_prompt("Use Mirror", 'CHECKBOX', False)
        self.add_prompt("Glass Shelves", 'CHECKBOX', False)
        self.add_prompt("Add Shelves", 'CHECKBOX', 0)
        self.add_prompt("Shelf Quantity", 'QUANTITY', 3)
        self.add_prompt("Shelf Backing Setback", 'DISTANCE', 0)

        self.add_prompt("Top KD", 'CHECKBOX', True)
        self.add_prompt("Bottom KD", 'CHECKBOX', True)
        self.add_prompt("Use Bottom KD Setback", 'CHECKBOX', False)
        self.add_prompt("Pard Has Top KD", 'CHECKBOX', False)
        self.add_prompt("Pard Has Bottom KD", 'CHECKBOX', False)
        self.add_prompt("Placed In Invalid Opening", 'CHECKBOX', False)
        self.add_prompt("Has Blind Left Corner", 'CHECKBOX', False)
        self.add_prompt("Has Blind Right Corner", 'CHECKBOX', False)
        self.add_prompt("Left Blind Corner Depth", 'DISTANCE', 0)
        self.add_prompt("Right Blind Corner Depth", 'DISTANCE', 0)

        self.add_prompt("Is Slab Door", 'CHECKBOX', True)
        self.add_prompt("Has Center Rail", 'CHECKBOX', False)
        self.add_prompt("Center Rail Distance From Center", 'DISTANCE', 0)

        self.add_prompt("Full Overlay", 'CHECKBOX', False)
        self.add_prompt("Evenly Space Shelves", 'CHECKBOX', True)
        self.add_prompt("Thick Adjustable Shelves", 'CHECKBOX', bpy.context.scene.sn_closets.closet_defaults.thick_adjustable_shelves)

        self.add_prompt("Glass Shelf Thickness", 'COMBOBOX', 0, ['1/4"', '3/8"', '1/2"'])  # columns=3
        ST = self.get_prompt("Glass Shelf Thickness").get_var("ST")
        glass_thickness.set_formula('IF(ST==0,INCH(0.25),IF(ST==1,INCH(0.375),INCH(0.5)))', [ST])

        front_thickness = self.get_prompt('Front Thickness')
        front_thickness.set_value(sn_unit.inch(0.75))

    def set_door_drivers(self, assembly):
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Door_Gap = self.get_prompt("Door to Cabinet Gap").get_var('Door_Gap')
        Top_Thickness = self.get_prompt("Top Thickness").get_var('Top_Thickness')
        Bottom_Thickness = self.get_prompt("Bottom Thickness").get_var('Bottom_Thickness')
        Top_Overlay = self.get_prompt("Top Overlay").get_var('Top_Overlay')
        Bottom_Overlay = self.get_prompt("Bottom Overlay").get_var('Bottom_Overlay')
        # TODO: create issue - prompts "Extend Top Amount", "Extend Bottom Amount" do not exist
        # eta = self.get_prompt("Extend Top Amount").get_var('eta')
        # eba = self.get_prompt("Extend Bottom Amount").get_var('eba')
        Front_Thickness = self.get_prompt("Front Thickness").get_var('Front_Thickness')
        Insert_Height = self.get_prompt("Insert Height").get_var('Insert_Height')
        Fill_Opening = self.get_prompt("Fill Opening").get_var('Fill_Opening')
        Door_Type = self.get_prompt("Door Type").get_var('Door_Type')

        assembly.loc_y('-Door_Gap', [Door_Gap, Front_Thickness])
        assembly.loc_z(
            'IF(Door_Type==2,IF(Fill_Opening,0,Height-Insert_Height)-Bottom_Overlay,-Bottom_Overlay)',
            [Fill_Opening, Door_Type, Height, Insert_Height, Bottom_Thickness, Bottom_Overlay])
        assembly.rot_y(value=math.radians(-90))
        assembly.dim_x('IF(Fill_Opening,Height,Insert_Height)+Top_Overlay+Bottom_Overlay',
                       [Fill_Opening, Insert_Height, Height, Top_Overlay, Bottom_Overlay, Top_Thickness])
        assembly.dim_z('Front_Thickness', [Front_Thickness])

    def set_pull_drivers(self, assembly):
        self.set_door_drivers(assembly)

        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Pull_Length = assembly.get_prompt("Pull Length").get_var('Pull_Length')
        Pull_From_Edge = self.get_prompt("Pull From Edge").get_var('Pull_From_Edge')
        Base_Pull_Location = self.get_prompt("Base Pull Location").get_var('Base_Pull_Location')
        Tall_Pull_Location = self.get_prompt("Tall Pull Location").get_var('Tall_Pull_Location')
        Upper_Pull_Location = self.get_prompt("Upper Pull Location").get_var('Upper_Pull_Location')

        World_Z = self.obj_bp.snap.get_var('matrix_world[2][3]', 'World_Z')

        Insert_Height = self.get_prompt("Insert Height").get_var('Insert_Height')
        Fill_Opening = self.get_prompt("Fill Opening").get_var('Fill_Opening')
        Door_Type = self.get_prompt("Door Type").get_var('Door_Type')

        pull_loc_x = assembly.get_prompt("Pull X Location")
        pull_loc_x.set_formula('Pull_From_Edge', [Pull_From_Edge])
        pull_loc_z = assembly.get_prompt("Pull Z Location")
        pull_loc_z.set_formula(
            'IF(Door_Type==0,Base_Pull_Location+(Pull_Length/2),'
            'IF(Door_Type==1,IF(Fill_Opening,Height,Insert_Height)-Tall_Pull_Location+(Pull_Length/2)+World_Z,'
            'IF(Fill_Opening,Height,Insert_Height)-Upper_Pull_Location-(Pull_Length/2)))',
            [Door_Type, Base_Pull_Location, Pull_Length, Fill_Opening, Insert_Height, Upper_Pull_Location,
             Tall_Pull_Location, World_Z, Height])

    def add_shelves(self, glass=False, shelf_amt=3):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Shelf_Quantity = self.get_prompt("Shelf Quantity").get_var('Shelf_Quantity')
        Shelf_Backing_Setback = self.get_prompt("Shelf Backing Setback").get_var('Shelf_Backing_Setback')
        ST = self.get_prompt("Shelf Thickness").get_var('ST')
        Insert_Height = self.get_prompt("Insert Height").get_var('Insert_Height')
        Fill_Opening = self.get_prompt("Fill Opening").get_var('Fill_Opening')
        Door_Type = self.get_prompt("Door Type").get_var('Door_Type')
        Door_Hide = self.get_prompt("Hide").get_var("Door_Hide")
        Fill_Opening = self.get_prompt("Fill Opening").get_var('Fill_Opening')
        Door_Type = self.get_prompt("Door Type").get_var('Door_Type')
        Add_Shelves = self.get_prompt("Add Shelves").get_var('Add_Shelves')
        Glass_Shelves = self.get_prompt("Glass Shelves").get_var('Glass_Shelves')
        Glass_Thickness = self.get_prompt("Glass Thickness").get_var('Glass_Thickness')
        TAS = self.get_prompt("Thick Adjustable Shelves").get_var('TAS')

        previous_shelf = None

        for i in range(1, shelf_amt):
            ppt_shelf_height = eval("self.get_prompt('Shelf {} Height')".format(str(i)))
            Shelf_Height = ppt_shelf_height.get_var('Shelf_Height')
            shelf_empty = self.add_empty("Shelf Z Loc Empty")
            self.shelf_z_loc_empties.append(shelf_empty)

            if previous_shelf:
                prev_shelf_z_loc = previous_shelf.obj_bp.snap.get_var('location.z', 'prev_shelf_z_loc')
                shelf_empty.snap.loc_z('prev_shelf_z_loc+Shelf_Height', [prev_shelf_z_loc, Shelf_Height])
            else:
                shelf_empty.snap.loc_z(
                    'IF(Fill_Opening,Shelf_Height,IF(Door_Type!=2,Shelf_Height,Height-Insert_Height+Shelf_Height))',
                    [Fill_Opening, Shelf_Height, Insert_Height, Height, Door_Type])

            sh_z_loc = shelf_empty.snap.get_var('location.z', 'sh_z_loc')

            if not glass:
                shelf = common_parts.add_shelf(self)
                IBEKD = shelf.get_prompt('Is Bottom Exposed KD').get_var('IBEKD')
                shelf.dim_z('IF(AND(TAS,IBEKD==False), INCH(1),ST)', [ST, TAS, IBEKD])
            else:
                shelf = common_parts.add_glass_shelf(self)
                shelf.dim_z('Glass_Thickness', [Glass_Thickness])
                shelf.get_prompt('Hide').set_formula(
                    'IF(Add_Shelves,IF(Glass_Shelves,IF(Shelf_Quantity+1>' + str(i) + ',False,True),True),True)',
                    [Add_Shelves, Shelf_Quantity, Glass_Shelves])

            self.shelves.append(shelf)

            Adj_Shelf_Setback = shelf.get_prompt('Adj Shelf Setback').get_var('Adj_Shelf_Setback')
            Locked_Shelf_Setback = shelf.get_prompt('Locked Shelf Setback').get_var('Locked_Shelf_Setback')
            Adj_Shelf_Clip_Gap = shelf.get_prompt('Adj Shelf Clip Gap').get_var('Adj_Shelf_Clip_Gap')
            Shelf_Setback = self.get_prompt("Shelf " + str(i) + " Setback").get_var('Shelf_Setback')

            if not glass:
                Is_Locked_Shelf = shelf.get_prompt('Is Locked Shelf').get_var('Is_Locked_Shelf')

            shelf.loc_x('IF(Is_Locked_Shelf,0,Adj_Shelf_Clip_Gap)', [Is_Locked_Shelf, Adj_Shelf_Clip_Gap])
            shelf.loc_y('Depth-Shelf_Backing_Setback', [Depth, Shelf_Backing_Setback])
            shelf.loc_z('sh_z_loc', [sh_z_loc])
            shelf.dim_x(
                'Width-IF(Is_Locked_Shelf,0,Adj_Shelf_Clip_Gap*2)',
                [Width, Is_Locked_Shelf, Adj_Shelf_Clip_Gap])
            shelf.dim_y(
                "-Depth"
                "+IF(Is_Locked_Shelf,Locked_Shelf_Setback,Adj_Shelf_Setback)"
                "+Shelf_Setback+Shelf_Backing_Setback",
                [Depth, Locked_Shelf_Setback, Is_Locked_Shelf, Adj_Shelf_Setback,
                    Shelf_Setback, Shelf_Backing_Setback])
            shelf.get_prompt('Hide').set_formula("Door_Hide", [Door_Hide])

            previous_shelf = shelf

    def add_glass_shelves(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Shelf_Qty = self.get_prompt("Shelf Qty").get_var('Shelf_Qty')
        Glass_Thickness = self.get_prompt("Glass Thickness").get_var('Glass_Thickness')
        Insert_Height = self.get_prompt("Insert Height").get_var('Insert_Height')
        Fill_Opening = self.get_prompt("Fill Opening").get_var('Fill_Opening')
        Door_Type = self.get_prompt("Door Type").get_var('Door_Type')
        Glass_Shelves = self.get_prompt("Glass Shelves").get_var('Glass_Shelves')

        glass_shelf = common_parts.add_glass_shelf(self)
        glass_shelf.draw_as_hidden_line()
        glass_shelf.loc_x(value=0)
        glass_shelf.loc_y('Depth',[Depth])
        glass_shelf.loc_z('IF(Fill_Opening,((Height-(Glass_Thickness*Shelf_Qty))/(Shelf_Qty+1)),IF(Door_Type==2,Height-Insert_Height,0)+((Insert_Height-(Glass_Thickness*Shelf_Qty))/(Shelf_Qty+1)))',
                        [Fill_Opening,Height,Glass_Thickness,Shelf_Qty,Insert_Height,Door_Type])
        glass_shelf.dim_x('Width',[Width])
        glass_shelf.dim_y('-Depth+.00635',[Depth])
        glass_shelf.dim_z('Glass_Thickness',[Glass_Thickness])

        hide = glass_shelf.get_prompt('Hide')
        hide.set_formula('IF(Glass_Shelves==False,True,IF(Shelf_Qty==0,True,False)) or Hide',[Shelf_Qty,Glass_Shelves,self.hide_var])
        z_qty = glass_shelf.get_prompt('Z Quantity')
        z_qty.set_formula('Shelf_Qty', [Shelf_Qty])

        z_offset = glass_shelf.get_prompt('Z Offset')
        z_offset.set_formula('IF(Fill_Opening,((Height-(Glass_Thickness*Shelf_Qty))/(Shelf_Qty+1))+Glass_Thickness,((Insert_Height-(Glass_Thickness*Shelf_Qty))/(Shelf_Qty+1))+Glass_Thickness)',
                         [Fill_Opening,Height,Glass_Thickness,Shelf_Qty,Insert_Height])

    def update(self):
        super().update()

        self.obj_bp["IS_BP_DOOR_INSERT"] = True
        self.obj_bp.snap.export_as_subassembly = True

        props = self.obj_bp.sn_closets
        props.is_door_insert_bp = True  # TODO: remove

        self.set_prompts()

        # self.obj_bp["ID_PROMPT"] = "sn_closets.openings"

    def draw(self):
        self.create_assembly()
        # we are adding a master hide for everything
        hide_prompt = self.add_prompt('Hide', 'CHECKBOX', False)
        self.hide_var = hide_prompt.get_var()
        self.add_common_doors_prompts()

        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        LO = self.get_prompt("Left Overlay").get_var('LO')
        RO = self.get_prompt("Right Overlay").get_var('RO')
        Vertical_Gap = self.get_prompt("Vertical Gap").get_var('Vertical_Gap')
        Rotation = self.get_prompt("Door Rotation").get_var('Rotation')
        Open = self.get_prompt("Open").get_var('Open')
        double_door = self.get_prompt("Force Double Doors").get_var('double_door')
        DD = self.get_prompt("Force Double Doors").get_var('DD')
        left_swing = self.get_prompt("Use Left Swing").get_var('left_swing')
        ST = self.get_prompt("Shelf Thickness").get_var( 'ST')
        Insert_Height = self.get_prompt("Insert Height").get_var('Insert_Height')
        Fill_Opening = self.get_prompt("Fill Opening").get_var('Fill_Opening')
        DDAS = self.get_prompt("Double Door Auto Switch").get_var( 'DDAS')
        No_Pulls = self.get_prompt("No Pulls").get_var('No_Pulls')
        Lock_Door = self.get_prompt("Lock Door").get_var('Lock_Door')
        Lock_to_Panel = self.get_prompt("Lock to Panel").get_var('Lock_to_Panel')
        dt = self.get_prompt("Division Thickness").get_var('dt')
        ddl_offset = self.get_prompt("Double Door Lock Offset").get_var('ddl_offset')
        Front_Thickness = self.get_prompt("Front Thickness").get_var('Front_Thickness')
        Door_Gap = self.get_prompt("Door to Cabinet Gap").get_var('Door_Gap')
        Door_Type = self.get_prompt("Door Type").get_var('Door_Type')
        Offset_For_Plant_On_Top = self.get_prompt("Offset For Plant On Top").get_var('Offset_For_Plant_On_Top')
        Add_Striker = self.get_prompt("Add Striker").get_var('Add_Striker')
        Striker_Depth = self.get_prompt("Striker Depth").get_var('Striker_Depth')
        Striker_Thickness = self.get_prompt("Striker Thickness").get_var('Striker_Thickness')
        Glass_Shelves = self.get_prompt("Glass Shelves").get_var('Glass_Shelves')
        Shelf_Backing_Setback = self.get_prompt("Shelf Backing Setback").get_var('Shelf_Backing_Setback')
        Use_Bottom_KD_Setback = self.get_prompt("Use Bottom KD Setback").get_var()

        FO = self.get_prompt("Full Overlay").get_var('FO')
        DDHOD = self.get_prompt("Double Door Half Overlay Difference").get_var('DDHOD')
        DDFOD = self.get_prompt("Double Door Full Overlay Difference").get_var('DDFOD')
        SDFOD = self.get_prompt("Single Door Full Overlay Difference").get_var('SDFOD')

        Top_KD = self.get_prompt("Top KD").get_var('Top_KD')
        Bottom_KD = self.get_prompt("Bottom KD").get_var('Bottom_KD')
        Pard_Has_Top_KD = self.get_prompt("Pard Has Top KD").get_var('Pard_Has_Top_KD')
        Pard_Has_Bottom_KD = self.get_prompt("Pard Has Bottom KD").get_var('Pard_Has_Bottom_KD')
        Placed_In_Invalid_Opening = self.get_prompt("Placed In Invalid Opening").get_var('Placed_In_Invalid_Opening')
        Full_Overlay = self.get_prompt("Full Overlay").get_var('Full_Overlay')
        DDHOD = self.get_prompt("Double Door Half Overlay Difference").get_var('DDHOD')
        DDFOD = self.get_prompt("Double Door Full Overlay Difference").get_var('DDFOD')
        SDFOD = self.get_prompt("Single Door Full Overlay Difference").get_var('SDFOD')

        HBLC = self.get_prompt("Has Blind Left Corner").get_var('HBLC')
        HBRC = self.get_prompt("Has Blind Right Corner").get_var('HBRC')
        LBCD = self.get_prompt("Left Blind Corner Depth").get_var('LBCD')
        RBCD = self.get_prompt("Right Blind Corner Depth").get_var('RBCD')

        TAS = self.get_prompt("Thick Adjustable Shelves").get_var('TAS')

        door_backing_gap = self.get_prompt('Doors Backing Gap')
        door_backing_gap.set_formula('Insert_Height+ST*2', [Insert_Height, ST])  

        sq = self.get_prompt("Shelf Quantity").get_var('sq')
        sf1 = self.get_prompt("Shelf 1 Height").get_var('sf1')
        sf2 = self.get_prompt("Shelf 2 Height").get_var('sf2')
        sf3 = self.get_prompt("Shelf 3 Height").get_var('sf3')
        sf4 = self.get_prompt("Shelf 4 Height").get_var('sf4')
        sf5 = self.get_prompt("Shelf 5 Height").get_var('sf5')
        sf6 = self.get_prompt("Shelf 6 Height").get_var('sf6')
        sf7 = self.get_prompt("Shelf 7 Height").get_var('sf7')
        sf8 = self.get_prompt("Shelf 8 Height").get_var('sf8')
        sf9 = self.get_prompt("Shelf 9 Height").get_var('sf9')
        sf10 = self.get_prompt("Shelf 10 Height").get_var('sf10')
        sf11 = self.get_prompt("Shelf 11 Height").get_var('sf11')
        sf12 = self.get_prompt("Shelf 12 Height").get_var('sf12')
        sf13 = self.get_prompt("Shelf 13 Height").get_var('sf13')
        sf14 = self.get_prompt("Shelf 14 Height").get_var('sf14')
        sf15 = self.get_prompt("Shelf 15 Height").get_var('sf15')

        shelf_stack_height = self.get_prompt('Shelf Stack Height')
        shelf_stack_height.set_formula(
            'sf1+IF(sq>1,sf2,0)+IF(sq>2,sf3,0)+IF(sq>3,sf4,0)+IF(sq>4,sf5,0)+IF(sq>5,sf6,0)+IF(sq>6,sf7,0)+IF(sq>7,sf8,0)+IF(sq>8,sf9,0)+IF(sq>9,sf10,0)+IF(sq>10,sf11,0)+IF(sq>11,sf12,0)+IF(sq>12,sf13,0)+IF(sq>13,sf14,0)+IF(sq>14,sf15,0)', # ? Change height to allow correct door heights
            [sf1, sf2, sf3, sf4, sf5, sf6, sf7, sf8, sf9, sf10, sf11, sf12, sf13, sf14, sf15, sq])

        # STRIKER
        striker = common_parts.add_door_striker(self)
        striker.loc_y('Striker_Depth', [Striker_Depth])
        striker.loc_z('Height+Striker_Thickness', [Height, Striker_Thickness])
        striker.rot_x(value=math.radians(180))
        striker.dim_x('Width', [Width])
        striker.dim_y('Striker_Depth', [Striker_Depth])
        striker.dim_z('ST', [ST])
        hide = striker.get_prompt('Hide')
        hide.set_formula('IF(Add_Striker,False,True) or Hide',[Add_Striker,self.hide_var])

        # TODO: glass shelves
        # self.add_glass_shelves()
        # self.add_shelves()

        left_door = common_parts.add_door(self)
        left_door.set_name("Left Door")
        self.set_door_drivers(left_door)
        left_door.loc_x('IF(HBLC,LBCD-ST/4-INCH(0.375),IF(FO,-LO*2,-LO))', [LO, FO, HBLC, HBRC, ST, LBCD, Width])
        left_door.rot_z('radians(90)-Open*Rotation', [Open, Rotation])
        left_door.dim_y(
            'IF(OR(HBLC,HBRC),IF(OR(DD,Width-IF(HBLC,LBCD,RBCD)+ST>DDAS),(Width-IF(HBLC,LBCD,RBCD)+ST)/2,(Width-IF(HBLC,LBCD,RBCD)+ST)+ST/6),IF(OR(DD,Width>DDAS), IF(FO,(Width+(ST*2)-DDFOD)/2,(Width+LO+RO)/2-DDHOD) ,IF(FO,Width+(ST*2)-SDFOD,Width+LO+RO))) *-1',
            [DDHOD, DDFOD, SDFOD, DD, DDAS, Width, LO, RO, Vertical_Gap, FO, ST, HBLC, HBRC, LBCD, RBCD])
        hide = left_door.get_prompt('Hide')
        hide.set_formula(
            'IF(OR(HBLC,HBRC),IF(OR(double_door,Width-IF(HBLC,LBCD,RBCD)+ST>DDAS,left_swing),False,True),IF(OR(double_door,Width>DDAS,left_swing),False,True)) or Hide', 
            [self.hide_var, double_door, DDAS, left_swing, Width, HBLC, HBRC, LBCD, RBCD, ST])
        door_type = left_door.get_prompt('Door Type')
        door_type.set_formula('Door_Type', [Door_Type])
        door_swing = left_door.get_prompt('Door Swing')
        door_swing.set_value(0)
        no_pulls = left_door.get_prompt('No Pulls')
        no_pulls.set_formula('No_Pulls', [No_Pulls])
        cat_num = left_door.get_prompt('CatNum')
        cat_num.set_formula('IF(OR(double_door,Width>DDAS),51,52)', [double_door, Width, DDAS])

        left_pull = common_parts.add_door_pull(self)
        self.set_pull_drivers(left_pull)
        left_pull.loc_x('IF(HBLC,LBCD-ST/4-INCH(0.375),-LO)',[LO,HBLC,Width,LBCD,ST,HBRC,RBCD,double_door,DDAS])
        left_pull.rot_z('IF(HBLC,radians(90)-Open*Rotation,radians(90)-Open*Rotation)', [Open, Rotation, HBLC])
        left_pull.dim_y(
            'IF(OR(HBLC,HBRC),IF(OR(double_door,Width-IF(HBLC,LBCD,RBCD)+ST>DDAS),((Width-IF(HBLC,LBCD,RBCD))/2),(Width-(IF(HBLC,LBCD,RBCD)))),IF(OR(double_door,Width>DDAS),(Width+LO+RO-Vertical_Gap)/2,(Width+LO+RO)))*-1',
            [double_door, DDAS, Width, LO, RO, Vertical_Gap, ST, HBLC, HBRC, LBCD, RBCD])
        hide = left_pull.get_prompt('Hide')
        hide.set_formula(
            'IF(No_Pulls,True,IF(OR(HBLC,HBRC),IF(OR(double_door,Width-IF(HBLC,LBCD,RBCD)+ST>DDAS,left_swing),False,True),IF(OR(double_door,Width>DDAS,left_swing),False,True))) or Hide', 
            [self.hide_var, No_Pulls, double_door, DDAS, left_swing, Width, HBLC, HBRC, LBCD, RBCD, ST])

        right_door = common_parts.add_door(self)
        right_door.set_name("Right Door")
        self.set_door_drivers(right_door)
        right_door.loc_x('IF(HBRC,Width-RBCD+ST/4+INCH(0.375),IF(FO, Width+(RO*2), Width+RO))',[Width,RO,FO,HBLC,HBRC,RBCD,ST])
        right_door.rot_z('radians(90)+Open*Rotation', [Open, Rotation])
        right_door.dim_y('IF(OR(HBLC,HBRC),IF(OR(DD,Width-IF(HBLC,LBCD,RBCD)+ST>DDAS),(Width-IF(HBLC,LBCD,RBCD)+ST)/2,(Width-IF(HBLC,LBCD,RBCD)+ST)+ST/6),IF(OR(DD,Width>DDAS), IF(FO,(Width+(ST*2)-DDFOD)/2,(Width+LO+RO)/2-DDHOD) ,IF(FO,Width+(ST*2)-SDFOD,Width+LO+RO)))',[DDHOD,DDFOD,SDFOD,DD,DDAS,Width,LO,RO,Vertical_Gap,FO,ST,HBLC,HBRC,LBCD,RBCD])
        hide = right_door.get_prompt('Hide')
        hide.set_formula(
            'IF(OR(HBLC,HBRC),IF(OR(double_door,Width-IF(HBLC,LBCD,RBCD)+ST>DDAS),False,IF(left_swing,True,False)),IF(OR(double_door,Width>DDAS),False,IF(left_swing,True,False))) or Hide', 
            [self.hide_var, double_door,DDAS,Width,HBLC,HBRC,LBCD,RBCD,ST,left_swing])
        door_type = right_door.get_prompt('Door Type')
        door_type.set_formula('Door_Type',[Door_Type])
        door_swing = right_door.get_prompt('Door Swing')
        door_swing.set_value(1)
        no_pulls = right_door.get_prompt('No Pulls')
        no_pulls.set_formula('No_Pulls', [No_Pulls])
        cat_num = right_door.get_prompt('CatNum')
        cat_num.set_formula('IF(OR(double_door,Width>DDAS),51,52)', [double_door, Width, DDAS])

        right_pull = common_parts.add_door_pull(self)
        self.set_pull_drivers(right_pull)
        right_pull.loc_x('IF(HBRC,Width-RBCD+ST/4+INCH(0.375),Width+RO)',[RO,HBRC,Width,RBCD,ST,HBRC,double_door,DDAS])
        right_pull.rot_z('radians(90)+Open*Rotation', [Open, Rotation])
        right_pull.dim_y(
            'IF(OR(HBLC,HBRC),IF(OR(double_door,Width-IF(HBLC,LBCD,RBCD)+ST>DDAS),((Width-IF(HBLC,LBCD,RBCD))/2),(Width-IF(HBLC,LBCD,RBCD))),IF(OR(double_door,Width>DDAS),(Width+LO+RO-Vertical_Gap)/2,(Width+LO+RO)))',
            [double_door, DDAS, Width, LO, RO, Vertical_Gap, ST, HBLC, HBRC, LBCD, RBCD])
        hide = right_pull.get_prompt('Hide')
        hide.set_formula('IF(No_Pulls,True,IF(OR(HBLC,HBRC),IF(OR(double_door,Width-IF(HBLC,LBCD,RBCD)+ST>DDAS,left_swing==False),False,True),IF(OR(double_door,Width>DDAS,left_swing==False),False,True))) or Hide', 
                          [self.hide_var, No_Pulls, double_door, DDAS, left_swing, Width, HBLC, HBRC, LBCD, RBCD, ST])
        
        #BOTTOM KD SHELF
        bottom_shelf = common_parts.add_shelf(self)
        IBEKD = bottom_shelf.get_prompt('Is Bottom Exposed KD').get_var('IBEKD')
        bottom_shelf.loc_x('Width',[Width])
        bottom_shelf.loc_y(
            'Depth-IF(Use_Bottom_KD_Setback,Shelf_Backing_Setback,0)',
            [Depth, Shelf_Backing_Setback, Use_Bottom_KD_Setback])
        bottom_shelf.loc_z('IF(Fill_Opening, 0, IF(Door_Type==2,Height-Insert_Height,0))', 
                    [Door_Type,Insert_Height,Height,ST,Fill_Opening])
        bottom_shelf.rot_z(value=math.radians(180))
        bottom_shelf.dim_x('Width',[Width])
        bottom_shelf.dim_y(
            'Depth-IF(Use_Bottom_KD_Setback,Shelf_Backing_Setback,0)',
            [Depth, Shelf_Backing_Setback, Use_Bottom_KD_Setback])
        # bottom_shelf.dim_z('IF(AND(TAS,IBEKD==False), INCH(1),ST) *-1', [ST, TAS, IBEKD])
        bottom_shelf.dim_z('-ST', [ST, TAS, IBEKD])
        hide = bottom_shelf.get_prompt('Hide')
        hide.set_formula(
            "IF(Placed_In_Invalid_Opening,IF(Door_Type!=2,True,IF(Bottom_KD, False, True)),IF(OR(AND(Pard_Has_Bottom_KD,Door_Type!=2),AND(Pard_Has_Bottom_KD,Fill_Opening)), True, IF(Bottom_KD, False, True))) or Hide", 
            [self.hide_var, Bottom_KD,Pard_Has_Bottom_KD,Door_Type,Fill_Opening,Placed_In_Invalid_Opening])
        is_locked_shelf = bottom_shelf.get_prompt('Is Locked Shelf')
        is_locked_shelf.set_value(True)
        bottom_shelf.get_prompt("Is Forced Locked Shelf").set_value(value=True)

        #TOP KD SHELF
        top_shelf = common_parts.add_shelf(self)
        IBEKD = top_shelf.get_prompt('Is Bottom Exposed KD').get_var('IBEKD')
        top_shelf.loc_x('Width',[Width])
        top_shelf.loc_y('Depth',[Depth])
        top_shelf.loc_z('IF(Fill_Opening, Height + ST,IF(Door_Type==2,Height + ST,Insert_Height + ST))',
                    [Door_Type,Insert_Height,Height,ST, Fill_Opening])
        top_shelf.rot_z(value=math.radians(180))
        top_shelf.dim_x('Width',[Width])
        top_shelf.dim_y('Depth-Shelf_Backing_Setback',[Depth,Shelf_Backing_Setback])
        # top_shelf.dim_z('IF(AND(TAS,IBEKD==False), INCH(1),ST) *-1', [ST, TAS, IBEKD])
        top_shelf.dim_z('-ST', [ST, TAS, IBEKD])
        hide = top_shelf.get_prompt('Hide')
        hide.set_formula("IF(Placed_In_Invalid_Opening,IF(Door_Type==2,True,IF(Top_KD, False, True)),IF(OR(AND(Pard_Has_Top_KD,Door_Type==2),AND(Pard_Has_Top_KD,Fill_Opening)), True, IF(Top_KD, False, True))) or Hide", [Top_KD, Pard_Has_Top_KD,Door_Type,Fill_Opening,Placed_In_Invalid_Opening,self.hide_var])
        is_locked_shelf = top_shelf.get_prompt('Is Locked Shelf')
        is_locked_shelf.set_value(True)
        top_shelf.get_prompt("Is Forced Locked Shelf").set_value(value=True)
        
        opening = common_parts.add_opening(self)
        opening.loc_z('IF(Fill_Opening,0,IF(Door_Type==2,0,Insert_Height+ST))', [Door_Type, Insert_Height, ST, Fill_Opening])
        opening.dim_x('Width', [Width])
        opening.dim_y('Depth', [Depth])
        opening.dim_z('IF(Fill_Opening,Insert_Height,Height-Insert_Height-ST)', [Fill_Opening, Height, Insert_Height, ST])

        # LOCK
        door_lock = common_parts.add_lock(self)
        door_lock.loc_x('IF(OR(double_door,Width>DDAS),Width/2+ddl_offset,IF(left_swing,Width+IF(Lock_to_Panel,dt,-dt),IF(Lock_to_Panel,-dt,dt)))',
                        [Lock_to_Panel,left_swing,Width,double_door,dt,DDAS,ddl_offset])
        door_lock.loc_y('IF(OR(double_door,Width>DDAS),-Front_Thickness-Door_Gap,IF(Lock_to_Panel,Front_Thickness,-Front_Thickness-Door_Gap))',
                        [Lock_to_Panel,Door_Gap,Front_Thickness,dt,DDAS,double_door,Width])
        door_lock.rot_y('IF(OR(double_door,Width>DDAS),radians(90),IF(AND(left_swing,Lock_to_Panel==False),radians(180),0))',
                        [left_swing,double_door,Width,Lock_to_Panel,DDAS])
        door_lock.rot_z('IF(OR(double_door,Width>DDAS),0,IF(Lock_to_Panel==False,0,IF(left_swing,radians(90),radians(-90))))',
                        [Lock_to_Panel,left_swing,double_door,DDAS,Width])
        base_lock_z_location_formula = "IF(Fill_Opening,Height,Insert_Height)-INCH(1.5)"
        tall_lock_z_location_formula = "IF(Fill_Opening,Height/2,Insert_Height/2)-INCH(1.5)"
        upper_lock_z_location_formula = "IF(Fill_Opening,0,Height-Insert_Height)+INCH(1.5)"
        door_lock.loc_z('IF(Door_Type==0,' + base_lock_z_location_formula + ',IF(Door_Type==1,' + tall_lock_z_location_formula + ',' + upper_lock_z_location_formula + '))',
                        [Door_Type,Fill_Opening,Insert_Height,Height])
        hide = door_lock.get_prompt('Hide')
        hide.set_formula('IF(Lock_Door==True,IF(Open>0,IF(Lock_to_Panel,False,True),False),True) or Hide',  [self.hide_var, Lock_Door, Open, Lock_to_Panel])
        door_lock.material('Chrome')        
        
        self.update()


class PROMPTS_Door_Prompts_214(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.door_prompts_214"
    bl_label = "Door Prompt" 
    bl_description = "This shows all of the available door options"
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")


    tabs: EnumProperty(name="Tabs",
                        items=[('DOOR','Door Options','Options for the door'),
                               ('SHELVES','Shelf Options','Options for the shelves')],
                        default = 'DOOR')

    door_type: EnumProperty(
        name="Door Type",
        items=[
            ('0', 'Base', 'Base'),
            ('1', 'Tall', 'Tall'),
            ('2', 'Upper', 'Upper')],
        default='2')

    glass_thickness: EnumProperty(
        name="Glass Thickness",
        items=[
            ('0', '1/4"', '1/4"'),
            ('1', '3/8"', '3/8"'),
            ('2', '1/2"', '1/2"')],
        default='0')

    glass_thickness_prompt = None
    shelf_thickness_prompt = None        
    
    assembly = None
    part = None

    shelf_quantity: EnumProperty(name="Shelf Quantity",
                                   items=[('1',"1",'1'),
                                          ('2',"2",'2'),
                                          ('3',"3",'3'),
                                          ('4',"4",'4'),
                                          ('5',"5",'5'),
                                          ('6',"6",'6'),
                                          ('7',"7",'7'),
                                          ('8',"8",'8'),
                                          ('9',"9",'9'),
                                          ('10',"10",'10'),
                                          ('11',"11",'11'),
                                          ('12',"12",'12'),
                                          ('13',"13",'13'),
                                          ('14',"14",'14'),
                                          ('15',"15",'15')],
                                   default = '3')

    Shelf_1_Height: EnumProperty(name="Shelf 1 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
    
    Shelf_2_Height: EnumProperty(name="Shelf 2 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
    
    Shelf_3_Height: EnumProperty(name="Shelf 3 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
    
    Shelf_4_Height: EnumProperty(name="Shelf 4 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
    
    Shelf_5_Height: EnumProperty(name="Shelf 5 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
    
    Shelf_6_Height: EnumProperty(name="Shelf 6 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
    
    Shelf_7_Height: EnumProperty(name="Shelf 7 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
    
    Shelf_8_Height: EnumProperty(name="Shelf 8 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
    
    Shelf_9_Height: EnumProperty(name="Shelf 9 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
                                    
    Shelf_10_Height: EnumProperty(name="Shelf 10 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
                                    
    Shelf_11_Height: EnumProperty(name="Shelf 11 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
                                    
    Shelf_12_Height: EnumProperty(name="Shelf 12 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
                                    
    Shelf_13_Height: EnumProperty(name="Shelf 13 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
                                    
    Shelf_14_Height: EnumProperty(name="Shelf 14 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
                                    
    Shelf_15_Height: EnumProperty(name="Shelf 15 Height",
                                    items=common_lists.SHELF_IN_DOOR_HEIGHTS)
    
    plant_on_top_opening_height: EnumProperty(name="Height",
                                                 items=common_lists.PLANT_ON_TOP_OPENING_HEIGHTS)    
    
    door_opening_height: EnumProperty(name="Height",
                                                 items=common_lists.OPENING_HEIGHTS)  

    use_shelves: BoolProperty(name="Use Shelves", default=False)

    shelf_quantity_prompt = None
    door_type_prompt = None
    cur_shelf_height = None   

    @classmethod
    def poll(cls, context):
        return True

    def delete_shelves(self):
        for assembly in self.assembly.shelves:
            sn_utils.delete_object_and_children(assembly.obj_bp)
        sn_utils.delete_obj_list(self.assembly.shelf_z_loc_empties)    
        self.assembly.shelves.clear()
        self.assembly.shelf_z_loc_empties.clear()
    
    def add_shelves(self):
        glass_shelves = self.assembly.get_prompt("Glass Shelves")

        if glass_shelves.get_value():
            self.assembly.add_shelves(glass=True, shelf_amt=int(self.shelf_quantity))
        else:
            self.assembly.add_shelves(shelf_amt=int(self.shelf_quantity))

        self.assembly.update()
        bpy.ops.object.select_all(action='DESELECT')
    
    def update_shelves(self, context):
        add_shelves = self.assembly.get_prompt("Add Shelves")
        add_shelves.set_value(self.use_shelves)
        glass_shelves = self.assembly.get_prompt("Glass Shelves")
        shelf_amt_changed = len(self.assembly.shelves) != int(self.shelf_quantity)
        shelf_type_changed = False

        if self.assembly.shelves:
            shelf_bp = self.assembly.shelves[0].obj_bp
            shelf_type_changed = shelf_bp.get("IS_GLASS_SHELF") != glass_shelves.get_value()

        if add_shelves.get_value() and not self.assembly.shelves:
            self.add_shelves()
        if add_shelves.get_value() and shelf_amt_changed or shelf_type_changed:
            self.delete_shelves()
            self.add_shelves()
        if not add_shelves.get_value() and self.assembly.shelves:
            self.delete_shelves()

        context.view_layer.objects.active = self.assembly.obj_bp

    def check(self, context):
        start_time = time.perf_counter()
        props = bpy.context.scene.sn_closets
        self.update_shelves(context)

        if self.door_type_prompt:
            self.door_type_prompt.set_value(int(self.door_type))
            door_type_name = self.door_type_prompt.combobox_items[self.door_type_prompt.get_value()].name            

        if self.glass_thickness_prompt:
            self.glass_thickness_prompt.set_value(int(self.glass_thickness))

        if self.shelf_quantity_prompt:
            self.shelf_quantity_prompt.quantity_value = int(self.shelf_quantity)

        insert_height = self.assembly.get_prompt("Insert Height")
        carcass_height = self.assembly.obj_z.location.z
        fill_opening = self.assembly.get_prompt("Fill Opening")
        evenly_space_shelves = self.assembly.get_prompt("Evenly Space Shelves")
        prompts = [insert_height,fill_opening,evenly_space_shelves]
        
        for i in range(1,int(self.shelf_quantity)+1):
            shelf = self.assembly.get_prompt("Shelf " + str(i) + " Height")
            if shelf:
                # if not shelf.equal:
                exec("self.cur_shelf_height = float(self.Shelf_" + str(i) + "_Height)/1000")
                #If Shelf was Just Moved
                if(sn_unit.meter_to_inch(shelf.get_value()) != sn_unit.meter_to_inch(self.cur_shelf_height)):
                    
                    #Get the height of the previous shelves
                    total_shelf_height = 0
                    for ii in range (1,i+1):
                        exec("self.cur_shelf_height = float(self.Shelf_" + str(ii) + "_Height)/1000")
                        total_shelf_height = total_shelf_height + self.cur_shelf_height
                        #print(sn_unit.meter_to_inch(total_shelf_height))

                    #Adjust All Shelves above shelf that was just moved to evenly space themselves in the remaining space
                    for iii in range(i+1,int(self.shelf_quantity)+1):
                        next_shelf = self.assembly.get_prompt("Shelf " + str(iii) + " Height")
                        if all(prompts):
                            if(not evenly_space_shelves.get_value()):
                                if(fill_opening.get_value()):
                                    hole_count = math.ceil(((carcass_height-total_shelf_height)*1000)/32)
                                else:
                                    hole_count = math.ceil(((insert_height.get_value()-total_shelf_height)*1000)/32)
                                holes_per_shelf = round(hole_count/(int(self.shelf_quantity)+1-i))
                                if(holes_per_shelf >=3):
                                    next_shelf.set_value(float(common_lists.SHELF_IN_DOOR_HEIGHTS[holes_per_shelf-3][0])/1000)
                                    exec("self.Shelf_" + str(iii) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[holes_per_shelf-3][0]")
                                else:
                                    next_shelf.set_value(float(common_lists.SHELF_IN_DOOR_HEIGHTS[0][0])/1000)
                                    exec("self.Shelf_" + str(iii) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[0][0]")

                exec("shelf.distance_value = sn_unit.inch(float(self.Shelf_" + str(i) + "_Height) / 25.4)")  
                
                if all(prompts):
                    if(evenly_space_shelves.get_value()):
                        if(fill_opening.get_value()):
                            hole_count = math.ceil((carcass_height*1000)/32)
                        else:
                            hole_count = math.ceil((insert_height.get_value()*1000)/32)
                        holes_per_shelf = round(hole_count/(int(self.shelf_quantity)+1))
                        remainder = hole_count - (holes_per_shelf * (int(self.shelf_quantity)))

                        if(i <= remainder):
                                holes_per_shelf = holes_per_shelf + 1
                        if(holes_per_shelf >=3):
                            shelf.set_value(float(common_lists.SHELF_IN_DOOR_HEIGHTS[holes_per_shelf-3][0])/1000)
                            exec("self.Shelf_" + str(i) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[holes_per_shelf-3][0]")
                        else:
                            shelf.set_value(float(common_lists.SHELF_IN_DOOR_HEIGHTS[0][0])/1000)
                            exec("self.Shelf_" + str(i) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[0][0]")

        if props.closet_defaults.use_32mm_system:
            insert_height = self.assembly.get_prompt("Insert Height")
            offset_for_plant_on_top = self.assembly.get_prompt("Offset For Plant On Top")
            if insert_height:
                if door_type_name == 'Upper' and offset_for_plant_on_top.get_value():
                    insert_height.distance_value = sn_unit.inch(float(self.plant_on_top_opening_height) / 25.4)
                else:
                    if fill_opening:
                        if fill_opening.get_value():
                            insert_height.distance_value = self.assembly.obj_z.location.z
                        else:
                            insert_height.distance_value = sn_unit.inch(float(self.door_opening_height) / 25.4)
                    else:
                        insert_height.distance_value = sn_unit.inch(float(self.door_opening_height) / 25.4)
        
        lucite_doors = self.assembly.get_prompt('Lucite Doors')
        draw_type = 'TEXTURED'

        fill_opening = self.assembly.get_prompt("Fill Opening").get_value()
        top_pard_KD = self.assembly.get_prompt("Pard Has Top KD")
        top_KD = self.assembly.get_prompt("Top KD")
        bottom_pard_KD = self.assembly.get_prompt("Pard Has Bottom KD")
        bottom_KD = self.assembly.get_prompt("Bottom KD")

        kd_prompts = [
            top_pard_KD,
            bottom_pard_KD,
            top_KD,
            bottom_KD
        ]
        closet_obj = None
        closet_assembly = None

        closet_obj = sn_utils.get_closet_bp(self.assembly.obj_bp)
        if "IS_BP_CLOSET" in closet_obj:
            closet_assembly = sn_types.Assembly(closet_obj)

        if all(kd_prompts):
            if(closet_assembly):
                if(closet_assembly.get_prompt("Remove Top Shelf " + self.assembly.obj_bp.sn_closets.opening_name)):
                    does_opening_have_top_KD = closet_assembly.get_prompt("Remove Top Shelf " + self.assembly.obj_bp.sn_closets.opening_name)
                    does_opening_have_bottom_KD = closet_assembly.get_prompt("Remove Bottom Hanging Shelf " + self.assembly.obj_bp.sn_closets.opening_name)
                    if(fill_opening):
                        if(top_KD.get_value()):
                            does_opening_have_top_KD.set_value(True)
                            top_pard_KD.set_value(True)
                        else:
                            does_opening_have_top_KD.set_value(False)
                            top_pard_KD.set_value(False)

                        if(bottom_KD.get_value()):
                            does_opening_have_bottom_KD.set_value(True)
                            bottom_pard_KD.set_value(True)
                        else:
                            does_opening_have_bottom_KD.set_value(False)
                            bottom_pard_KD.set_value(False)
                    else:
                        if door_type_name=='Upper':
                            if(top_KD.get_value()):
                                does_opening_have_top_KD.set_value(True)
                                top_pard_KD.set_value(True)
                            else:
                                does_opening_have_top_KD.set_value(False)
                                top_pard_KD.set_value(False)
                        else:
                            if(bottom_KD.get_value()):
                                does_opening_have_bottom_KD.set_value(True)
                                bottom_pard_KD.set_value(True)
                            else:
                                does_opening_have_bottom_KD.set_value(False)
                                bottom_pard_KD.set_value(False)
            else:
                placed_in_invalid_opening = self.assembly.get_prompt("Placed In Invalid Opening")
                placed_in_invalid_opening.set_value(True)
                if(fill_opening):
                    top_KD.set_value(False)
                    bottom_KD.set_value(False)
                elif door_type_name == 'Upper':
                    top_KD.set_value(False)
                else:
                    bottom_KD.set_value(False)
        
        self.assign_mirror_material(self.assembly.obj_bp)
        
        for child in self.assembly.obj_bp.children:
            if 'IS_DOOR' in child:
                if not child.visible_get:
                    door_assembly = sn_types.Assembly(child)
                    door_style = door_assembly.get_prompt("Door Style")
                    is_slab_door = self.assembly.get_prompt("Is Slab Door")
                    has_center_rail = self.assembly.get_prompt("Has Center Rail")
                    prompts = [door_style,is_slab_door,has_center_rail]
                    if all(prompts):
                        if(door_style.get_value() == "Slab Door"):
                            is_slab_door.set_value(True)
                            has_center_rail.set_value(False)
                        else:
                            is_slab_door.set_value(False)

        self.assembly.obj_bp.location = self.assembly.obj_bp.location # Redraw Viewport
        bpy.ops.snap.update_scene_from_pointers()
        return True
    
    def assign_mirror_material(self,obj):
        use_mirror = self.assembly.get_prompt("Use Mirror")
        if use_mirror.get_value():
            if obj.snap.type_mesh == 'BUYOUT':
                for mat_slot in obj.snap.material_slots:
                    if "Glass" in mat_slot.name:
                        mat_slot.pointer_name = 'Mirror'  
        else:
            if obj.snap.type_mesh == 'BUYOUT':
                for mat_slot in obj.snap.material_slots:
                    if "Glass" in mat_slot.name:
                        mat_slot.pointer_name = 'Glass'  
                    
        
        for child in obj.children:
            self.assign_mirror_material(child)

    def execute(self, context):
        self.tabs = 'DOOR'      
        return {'FINISHED'}

    def set_properties_from_prompts(self):
        insert_height = self.assembly.get_prompt("Insert Height")
        door_type = self.assembly.get_prompt("Door Type")
        offset_for_plant_on_top = self.assembly.get_prompt("Offset For Plant On Top")
        self.glass_thickness_prompt = self.assembly.get_prompt("Glass Shelf Thickness")
        add_shelves = self.assembly.get_prompt("Add Shelves")

        if add_shelves:
            self.use_shelves = add_shelves.get_value()

        if door_type:
            self.door_type_prompt = door_type
            self.door_type = str(self.door_type_prompt.combobox_index)
            door_type_name = self.door_type_prompt.combobox_items[self.door_type_prompt.get_value()].name

        if self.glass_thickness_prompt:
            self.glass_thickness = str(self.glass_thickness_prompt.combobox_index)        

        self.shelf_quantity_prompt = self.assembly.get_prompt("Shelf Quantity")
        if self.shelf_quantity_prompt:
            self.shelf_quantity = str(self.shelf_quantity_prompt.quantity_value)

        for i in range(1, 16):
            shelf = self.assembly.get_prompt("Shelf " + str(i) + " Height")
            if shelf:
                value = round(shelf.get_value() * 1000, 3)
                for index, height in enumerate(common_lists.SHELF_IN_DOOR_HEIGHTS):
                    if not value >= float(height[0]):
                        exec("self.Shelf_" + str(i) + "_Height = common_lists.SHELF_IN_DOOR_HEIGHTS[index - 1][0]")
                        break

        if insert_height:
            if door_type_name == 'Upper' and offset_for_plant_on_top.get_value():
                value = round(insert_height.distance_value * 1000, 3)
                for index, height in enumerate(common_lists.PLANT_ON_TOP_OPENING_HEIGHTS):
                    if not value >= float(height[0]):
                        self.plant_on_top_opening_height = common_lists.PLANT_ON_TOP_OPENING_HEIGHTS[index - 1][0]
                        break
            else:
                fill_opening = self.assembly.get_prompt("Fill Opening")
                if fill_opening:
                    if not fill_opening.get_value():
                        value = round(insert_height.distance_value * 1000, 3)
                        for index, height in enumerate(common_lists.OPENING_HEIGHTS):
                            if not value >= float(height[0]):
                                self.door_opening_height = common_lists.OPENING_HEIGHTS[index - 1][0]
                                break
                else:
                    value = round(insert_height.distance_value * 1000, 3)
                    for index, height in enumerate(common_lists.OPENING_HEIGHTS):
                        if not value >= float(height[0]):
                            self.door_opening_height = common_lists.OPENING_HEIGHTS[index - 1][0]
                            break

    def invoke(self,context,event):
        obj = bpy.data.objects[context.object.name]
        self.assembly = Doors(self.get_insert().obj_bp)
        obj_assembly_bp = sn_utils.get_assembly_bp(obj)
        self.part = sn_types.Assembly(obj_assembly_bp)
        self.set_properties_from_prompts()
        
        door_type_name = self.door_type_prompt.combobox_items[self.door_type_prompt.get_value()].name        
        fill_opening = self.assembly.get_prompt("Fill Opening").get_value()

        top_pard_KD = self.assembly.get_prompt("Pard Has Top KD")
        top_KD = self.assembly.get_prompt("Top KD")
        bottom_pard_KD = self.assembly.get_prompt("Pard Has Bottom KD")
        bottom_KD = self.assembly.get_prompt("Bottom KD")

        closet_obj = None
        closet_assembly = None

        closet_obj = sn_utils.get_closet_bp(self.assembly.obj_bp)
        if "IS_BP_CLOSET" in closet_obj:
            closet_assembly = sn_types.Assembly(closet_obj)

        placed_in_invalid_opening = self.assembly.get_prompt("Placed In Invalid Opening")            

        if(closet_assembly):
            Blind_Corner_Left = closet_assembly.get_prompt("Blind Corner Left")
            Blind_Corner_Right = closet_assembly.get_prompt("Blind Corner Right")
            Blind_Left_Depth = closet_assembly.get_prompt("Blind Left Depth")
            Blind_Right_Depth = closet_assembly.get_prompt("Blind Right Depth")
            Has_Blind_Left_Corner = self.assembly.get_prompt("Has Blind Left Corner")                
            Has_Blind_Right_Corner = self.assembly.get_prompt("Has Blind Right Corner")
            Left_Blind_Corner_Depth = self.assembly.get_prompt("Left Blind Corner Depth")                
            Right_Blind_Corner_Depth = self.assembly.get_prompt("Right Blind Corner Depth")


            kd_prompts = [
                top_pard_KD,
                bottom_pard_KD,
                top_KD,
                bottom_KD
            ]       


            bcp_prompts = [
                Blind_Corner_Left,
                Blind_Corner_Right,
                Blind_Left_Depth,
                Blind_Right_Depth,
                Has_Blind_Left_Corner,
                Has_Blind_Right_Corner,
                Left_Blind_Corner_Depth,
                Right_Blind_Corner_Depth
            ]

            if all(kd_prompts):
                if(closet_assembly.get_prompt("Remove Top Shelf " + self.assembly.obj_bp.sn_closets.opening_name)):
                    does_opening_have_top_KD = closet_assembly.get_prompt("Remove Top Shelf " + self.assembly.obj_bp.sn_closets.opening_name).get_value()
                    does_opening_have_bottom_KD = closet_assembly.get_prompt("Remove Bottom Hanging Shelf " + self.assembly.obj_bp.sn_closets.opening_name).get_value()
                    if(fill_opening):
                        if(does_opening_have_top_KD):
                            top_pard_KD.set_value(True)
                            top_KD.set_value(True)
                        else:
                            top_pard_KD.set_value(False)
                            top_KD.set_value(False)

                        if(does_opening_have_bottom_KD):
                            bottom_pard_KD.set_value(True)
                            bottom_KD.set_value(True)
                        else:
                            bottom_pard_KD.set_value(False)
                            bottom_KD.set_value(False)
                    else:
                        if door_type_name == 'Upper':
                            if(does_opening_have_top_KD):
                                top_pard_KD.set_value(True)
                                top_KD.set_value(True)
                            else:
                                top_pard_KD.set_value(False)
                                top_KD.set_value(False)
                        else:
                            if(does_opening_have_bottom_KD):
                                bottom_pard_KD.set_value(True)
                                bottom_KD.set_value(True)
                            else:
                                bottom_pard_KD.set_value(False)
                                bottom_KD.set_value(False)


            if(closet_assembly.get_prompt("Opening 1 Height")):
                opening_quantity = 0
                for i in range(1,10):
                    if(sn_types.Assembly(self.assembly.obj_bp.parent).get_prompt("Opening " + str(i) + " Height") == None):
                                    opening_quantity = i - 1
                                    break

                if all(bcp_prompts):
                    if(opening_quantity == 1):
                        if Blind_Corner_Left:
                            Has_Blind_Right_Corner.set_value(False)

                        elif Blind_Corner_Right:
                            Has_Blind_Right_Corner.set_value(True)
                            Has_Blind_Left_Corner.set_value(False)

                        else:
                            Has_Blind_Right_Corner.set_value(False)
                            Has_Blind_Left_Corner.set_value(False)

                    elif(self.assembly.obj_bp.sn_closets.opening_name == '1'):
                        if Blind_Corner_Left:
                            Has_Blind_Left_Corner.set_value(True)
                        else:
                            Has_Blind_Left_Corner.set_value(False)

                    elif(self.assembly.obj_bp.sn_closets.opening_name == str(opening_quantity)):

                        if Blind_Corner_Right:
                            Has_Blind_Right_Corner.set_value(True)
                        else:
                            Has_Blind_Right_Corner.set_value(False)

                    else:
                        Has_Blind_Left_Corner.set_value(False)
                        Has_Blind_Right_Corner.set_value(False)
                    Left_Blind_Corner_Depth.set_value(Blind_Left_Depth.get_value())
                    Right_Blind_Corner_Depth.set_value(Blind_Right_Depth.get_value())

        else:
            placed_in_invalid_opening.set_value(True)
            Has_Blind_Left_Corner = self.assembly.get_prompt("Has Blind Left Corner")                
            Has_Blind_Right_Corner = self.assembly.get_prompt("Has Blind Right Corner")
            Left_Blind_Corner_Depth = self.assembly.get_prompt("Left Blind Corner Depth")                
            Right_Blind_Corner_Depth = self.assembly.get_prompt("Right Blind Corner Depth")
            if(fill_opening):
                top_KD.set_value(False)
                bottom_KD.set_value(False)
            elif door_type_name == 'Upper':
                top_KD.set_value(False)
            else:
                bottom_KD.set_value(False)
            Has_Blind_Left_Corner.set_value(False)
            Has_Blind_Right_Corner.set_value(False)


        for child in self.assembly.obj_bp.children:
            if 'IS_DOOR' in child:
                if not child.visible_get():
                    door_assembly = sn_types.Assembly(child)
                    door_style = door_assembly.get_prompt("Door Style")
                    is_slab_door = self.assembly.get_prompt("Is Slab Door")
                    has_center_rail = self.assembly.get_prompt("Has Center Rail")
                    prompts = [door_style,is_slab_door,has_center_rail]
                    if all(prompts):
                        if(door_style.get_value() == "Slab Door"):
                            is_slab_door.set_value(True)
                            has_center_rail.set_value(False)
                        else:
                            is_slab_door.set_value(False)
                
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=375)
        
    def is_glass_door(self):
        if "Glass" in self.part.obj_bp.snap.comment:
            return True
        else:
            return False
        
    def draw(self, context):
        layout = self.layout

        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                props = bpy.context.scene.sn_closets
                
                door_type = self.assembly.get_prompt("Door Type")
                open_prompt = self.assembly.get_prompt("Open")
                pull_type = self.assembly.get_prompt('Pull Location')
                use_left_swing = self.assembly.get_prompt('Use Left Swing')
                force_double_door = self.assembly.get_prompt('Force Double Doors')
                lucite_doors = self.assembly.get_prompt('Lucite Doors')
                force_double_door = self.assembly.get_prompt('Force Double Doors')
                lucite_doors = self.assembly.get_prompt('Lucite Doors')    
                fill_opening = self.assembly.get_prompt('Fill Opening')       
                lock_door = self.assembly.get_prompt('Lock Door')   
                lock_to_panel = self.assembly.get_prompt('Lock to Panel')   
                insert_height = self.assembly.get_prompt("Insert Height")
                no_pulls = self.assembly.get_prompt("No Pulls")
                shelf_qty = self.assembly.get_prompt("Shelf Qty")
                offset_for_plant_on_top = self.assembly.get_prompt("Offset For Plant On Top") 
                add_striker = self.assembly.get_prompt("Add Striker")
                use_mirror = self.assembly.get_prompt("Use Mirror")
                glass_shelves = self.assembly.get_prompt("Glass Shelves")
                glass_shelf_thickness = self.assembly.get_prompt("Glass Shelf Thickness")
                full_overlay = self.assembly.get_prompt("Full Overlay")
                top_KD = self.assembly.get_prompt("Top KD")
                bottom_KD = self.assembly.get_prompt("Bottom KD")
                placed_in_invalid_opening = self.assembly.get_prompt("Placed In Invalid Opening")       
                is_slab_door = self.assembly.get_prompt("Is Slab Door")
                has_center_rail = self.assembly.get_prompt("Has Center Rail")        
                center_rail_distance_from_center = self.assembly.get_prompt("Center Rail Distance From Center")
                shelf_quantity = self.assembly.get_prompt("Shelf Quantity")   
                evenly_space_shelves = self.assembly.get_prompt("Evenly Space Shelves") 
                add_shelves = self.assembly.get_prompt("Add Shelves")
                door_type_name = door_type.combobox_items[door_type.get_value()].name
                      
                box = layout.box()
                row = box.row()
                if add_shelves:
                    row.prop(self,'tabs',expand=True)

                if self.tabs == 'DOOR':
                    box.label(text="Opening Options:")
                    box.prop(add_striker, "checkbox_value", text=add_striker.name)
                    row = box.row()
                    row.label(text="Fill Opening")
                    row.prop(fill_opening,'checkbox_value',text="") 
                    if fill_opening.get_value() != True:
                        row = box.row()
                        if props.closet_defaults.use_32mm_system:
                            row.label(text="Opening Height:")
                            row = box.row()                            
                            if door_type_name == 'Upper' and offset_for_plant_on_top.get_value():
                                row.prop(self,'plant_on_top_opening_height',text="") 
                            else:
                                row.prop(self,'door_opening_height',text="") 
                        else:
                            insert_height.draw_prompt(row)
                            row.prop(insert_height, "distance_value", text=insert_height.name)
                    
                    row = box.row()
                    if shelf_qty:
                        row.prop(shelf_qty, "quantity_value", text=shelf_qty.name)               
                    
                    box = layout.box()
                    box.label(text="Door Options:")
                    if door_type:
                        row = box.row()
                        row.prop(self, "door_type", expand=True)
                        row = box.row()

                        if door_type_name == 'Base':
                            pull_location = self.assembly.get_prompt('Base Pull Location')
                            row.label(text=pull_location.name)
                            row.prop(pull_location, "distance_value", text="")
                        if door_type_name == 'Tall':
                            pull_location = self.assembly.get_prompt('Tall Pull Location')
                            row.label(text=pull_location.name)
                            row.prop(pull_location, "distance_value", text="")
                        if door_type_name == 'Upper':
                            pull_location = self.assembly.get_prompt('Upper Pull Location')
                            row.label(text=pull_location.name)
                            row.prop(pull_location, "distance_value", text="")              

                    row = box.row()
                    row.label(text="Open Door")
                    row.prop(open_prompt, 'factor_value', slider=True, text="")

                    if has_center_rail and is_slab_door and center_rail_distance_from_center:
                        if not is_slab_door.get_value():
                            row = box.row()
                            row.label(text="Center Rail")
                            row.prop(has_center_rail, 'checkbox_value', text="")
                            if has_center_rail.get_value():
                                row = box.row()
                                row.label(text="Distance From Center")
                                row.prop(center_rail_distance_from_center, 'distance_value', text="")

                    if top_KD and bottom_KD:
                        if(placed_in_invalid_opening and placed_in_invalid_opening.get_value()==False):
                            row = box.row()              
                            row.label(text="Top KD")
                            row.prop(top_KD,'checkbox_value',text="")
                            row = box.row()               
                            row.label(text="Bottom KD")
                            row.prop(bottom_KD,'checkbox_value',text="")
                        else:
                            if(fill_opening.get_value()==False):
                                if door_type_name == 'Upper':
                                    row = box.row()              
                                    row.label(text="Top KD")
                                    row.prop(top_KD,'checkbox_value',text="")
                                    row = box.row()               
                                    row.label(text="Bottom KD")
                                    row.prop(bottom_KD,'checkbox_value',text="")
                                else:
                                    row = box.row()              
                                    row.label(text="Top KD")
                                    row.prop(top_KD,'checkbox_value',text="")

                        row = box.row()
                        row.label(text="Force Double Door")
                        row.prop(force_double_door,'checkbox_value',text="")
                        row = box.row()
                        row.label(text="Left Swing")
                        row.prop(use_left_swing,'checkbox_value',text="")
                        row = box.row()
                        row.label(text="No Pulls")
                        row.prop(no_pulls,'checkbox_value',text="")        
                        row = box.row()
                        row.label(text="Lock Door")
                        row.prop(lock_door,'checkbox_value',text="")   
                        if lock_door.get_value() and force_double_door.get_value() == False and self.assembly.obj_x.location.x < sn_unit.inch(24):             
                            row = box.row()
                            row.label(text="Lock to Panel")
                            row.prop(lock_to_panel,'checkbox_value',text="")
                        
                        if full_overlay:
                            row = box.row()
                            row.label(text="Full Overlay")
                            row.prop(full_overlay,'checkbox_value',text="")

                        if self.is_glass_door():
                            row = box.row()
                            use_mirror.draw_prompt(row)

                elif self.tabs == 'SHELVES':
                    row=box.row()
                    row.label(text="Add Shelves")
                    row.prop(self, 'use_shelves', text="")
                    if(add_shelves):
                        if(add_shelves.get_value()):
                            if shelf_quantity:
                                col = box.column(align=True)
                                row = col.row()
                                row.label(text="Qty:")
                                row.prop(self, "shelf_quantity", expand=True)
                                col.separator()

                                if glass_shelves:
                                    row = box.row()
                                    row.label(text="Glass Shelves: ")
                                    row.prop(glass_shelves, "checkbox_value", text="")
                                    if glass_shelves.get_value() and self.glass_thickness_prompt:
                                        row = box.row()
                                        row.label(text="Glass Shelf Thickness: ")
                                        row.prop(self, "glass_thickness", expand=True)

                                row = box.row()
                                row.label(text="Evenly Space Shelves: ")
                                row.prop(evenly_space_shelves, 'checkbox_value', text="")
                                for i in range(1, shelf_quantity.get_value() + 1):
                                    shelf = self.assembly.get_prompt("Shelf " + str(i) + " Height")
                                    setback = self.assembly.get_prompt("Shelf " + str(i) + " Setback")
                                    if shelf:
                                        row = box.row()
                                        if(evenly_space_shelves.get_value()):
                                            row.label(text="Shelf " + str(i) + " Height:")
                                            row.label(text=str(math.ceil((shelf.get_value()*1000)/32)) +"H-" + str(round(sn_unit.meter_to_active_unit(shelf.distance_value),3)) + '"')
                                        else:
                                            row.label(text="Shelf " + str(i) + " Height:")
                                            row.prop(self,'Shelf_' + str(i) + '_Height',text="")
                                    
                                    if setback:
                                        row = box.row()
                                        row.label(text="Shelf " + str(i) + " Setback")
                                        row.prop(setback,'distance_value',text="")


bpy.utils.register_class(PROMPTS_Vertical_Splitter_Prompts_214)
bpy.utils.register_class(PROMPTS_L_Shelves_214)
bpy.utils.register_class(PROMPTS_Corner_Shelves_214)
bpy.utils.register_class(PROMPTS_Door_Prompts_214)
