import math

import os

import bpy

from bpy.props import StringProperty, IntProperty, CollectionProperty, FloatProperty, EnumProperty
from bpy.types import Operator
from snap import sn_types, sn_unit, sn_utils, bl_info
from .data_closet_carcass_corner import Corner_Shelves, L_Shelves
from ..common import common_parts
from ..common import common_lists
from ..ops.drop_closet import PlaceClosetInsert
from .. import closet_props


SHELF_OPENING_MIN_HEIGHT = 124  # milllimeters 4H opening space


opening_height_ppt = None
shelf_stack_assembly = None



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

        calc_distance_obj = self.add_empty(self.calculator_obj_name)
        calc_distance_obj.empty_display_size = .001
        self.calculator = self.obj_prompts.snap.add_calculator(self.calculator_name, calc_distance_obj)
        self.calculator.set_total_distance("Height-Thickness*{}".format(str(amt - 1)), [Height, Thickness])

    def add_calculator_prompts(self, amt):
        self.calculator.prompts.clear()
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
        Shelf_Backing_Setback = self.get_prompt('Shelf Backing Setback').get_var("Shelf_Backing_Setback")
        Parent_Has_Bottom_KD = self.get_prompt('Parent Has Bottom KD').get_var("Parent_Has_Bottom_KD")
        Individual_Shelf_Setbacks = self.get_prompt("Individual Shelf Setbacks").get_var()
        parent_hide = self.get_prompt('Hide').get_var()
        previous_splitter = None
        TAS = self.get_prompt("Thick Adjustable Shelves").get_var('TAS')

        if not self.calculator:
            self.add_calculator(amt)

        self.add_calculator_prompts(amt)

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

        self.update_collections()

    def update(self):
        super().update()
        if hasattr(self, "width"):
            self.obj_x.location.x = self.width
        if hasattr(self, "height"):
            self.obj_z.location.z = self.height
        if hasattr(self, "depth"):
            self.obj_y.location.y = self.depth
        self.obj_bp.snap.export_as_subassembly = True

    def draw(self):
        self.create_assembly()
        self.add_prompts()
        self.add_splitters()
        self.update()
        self.obj_bp['IS_BP_SPLITTER'] = True
        props = self.obj_bp.sn_closets
        props.is_splitter_bp = True  # TODO: remove

    def add_to_wall_collection(self, obj_bp):
        wall_bp = sn_utils.get_wall_bp(self.obj_bp)
        if wall_bp:
            wall_coll = bpy.data.collections[wall_bp.snap.name_object]
            scene_coll = bpy.context.scene.collection
            sn_utils.add_assembly_to_collection(obj_bp, wall_coll)
            sn_utils.remove_assembly_from_collection(obj_bp, scene_coll)

    def update_collections(self):
        for i, shelf in enumerate(self.splitters):
            self.add_to_wall_collection(shelf.obj_bp)


class Shoe_Shelf_Stack(Shelf_Stack):

    shoe_shelves = []
    shelf_lips = []

    def __init__(self, obj_bp=None):
        super().__init__(obj_bp=obj_bp)
        self.shoe_shelves = []
        self.shelf_lips = []
        self.get_shelves()
        self.get_shelf_lips(self.obj_bp)
        self.calculator = self.get_calculator(self.calculator_name)

    def add_to_wall_collection(self, obj_bp):
        wall_bp = sn_utils.get_wall_bp(self.obj_bp)
        if wall_bp:
            wall_coll = bpy.data.collections[wall_bp.snap.name_object]
            scene_coll = bpy.context.scene.collection
            sn_utils.add_assembly_to_collection(obj_bp, wall_coll)
            sn_utils.remove_assembly_from_collection(obj_bp, scene_coll)

    def update_collections(self):
        for i, shelf in enumerate(self.shoe_shelves):
            self.add_to_wall_collection(shelf.obj_bp)
        for i, shelf_lip in enumerate(self.shelf_lips):
            self.add_to_wall_collection(shelf_lip.obj_bp)

    def get_shelves(self):
        for child in self.obj_bp.children:
            if child.get("IS_STACK_SHELF"):
                shelf = sn_types.Assembly(child)
                self.shoe_shelves.append(shelf)

    def get_shelf_lips(self, obj_bp):
        for child in obj_bp.children:
            if child.get("IS_SHOE_SHELF_LIP"):
                lip = sn_types.Assembly(child)
                self.shelf_lips.append(lip)
            if 'IS_BP_ASSEMBLY' in child:
                self.get_shelf_lips(child)

    def add_shoe_shelf_prompts(self):
        defaults = bpy.context.scene.sn_closets.closet_defaults
        super().add_prompts()

        shelf_lip_type = self.add_prompt(
            "Shelf Lip Type", 'COMBOBOX', 0, ["Melamine Lip", "Applied Flat Molding", "Ogee Molding", "Steel Fence"])
        shelf_lip_type.combobox_columns = 3

        self.add_prompt("Shelf Clip Gap", 'DISTANCE', defaults.adj_shelf_clip_gap)
        self.add_prompt("Shelf Angle", 'ANGLE', 17.25)
        self.add_prompt("Space From Bottom", 'DISTANCE', sn_unit.inch(3.5))
        self.add_prompt("Space From Top", 'DISTANCE', sn_unit.inch(8))
        self.add_prompt("Shelf Lip Width", 'DISTANCE', defaults.shelf_lip_width)
        self.add_prompt("Distance Between Shelves", 'DISTANCE', sn_unit.inch(8))
        ppt_obj_shelf_setback = self.add_prompt_obj("Shelf_Setback")
        self.add_prompt("Adj Shelf Setback", 'DISTANCE', sn_unit.inch(1), prompt_obj=ppt_obj_shelf_setback)
        self.add_prompt("Thickness", 'DISTANCE', sn_unit.inch(.75))

    def add_mel_lip(self, shelf, ppt_vars):
        shelf.dim_y('-Depth+Adj_Shelf_Setback+Shelf_Backing_Setback', ppt_vars)
        shelf_lip = common_parts.add_shelf_lip(self)
        self.shelf_lips.append(shelf_lip)
        shelf_lip.obj_bp.parent = shelf.obj_bp
        shelf_lip.obj_bp["IS_SHOE_SHELF_LIP"] = True
        shelf_lip.obj_bp["IS_BP_MEL_SHELF_LIP"] = True
        shelf_lip.loc_x('Shelf_Clip_Gap', ppt_vars)
        shelf_lip.loc_y('-Depth+Adj_Shelf_Setback+Shelf_Backing_Setback', ppt_vars)
        shelf_lip.loc_z('Thickness', ppt_vars)
        shelf_lip.rot_x(value=math.radians(-90))
        shelf_lip.dim_x('Width-(Shelf_Clip_Gap*2)', ppt_vars)
        shelf_lip.dim_y('-Shelf_Lip_Width', ppt_vars)
        shelf_lip.dim_z('Thickness', ppt_vars)
        shelf_lip.get_prompt("Adj Shelf Setback").set_formula(
            'IF(Individual_Shelf_Setbacks,Shelf_Setback,Shelf_Setback_All)',
            ppt_vars)

    def add_applied_molding(self, shelf, ppt_vars):
        shelf.dim_y('-Depth+INCH(1)+Shelf_Backing_Setback', ppt_vars)
        shelf_lip = common_parts.add_shelf_lip(self)
        self.shelf_lips.append(shelf_lip)
        shelf_lip.obj_bp.parent = shelf.obj_bp
        shelf_lip.obj_bp["IS_SHOE_SHELF_LIP"] = True
        shelf_lip.loc_x('Shelf_Clip_Gap', ppt_vars)
        shelf_lip.loc_y('-Depth+INCH(1)+Shelf_Backing_Setback', ppt_vars)
        shelf_lip.rot_x(value=math.radians(90))
        shelf_lip.dim_x('Width-(Shelf_Clip_Gap*2)', ppt_vars)
        shelf_lip.dim_y(value=sn_unit.inch(1.5))
        shelf_lip.dim_z('Thickness', ppt_vars)

    def add_ogee_molding(self, shelf, ppt_vars):
        shelf.dim_y('-Depth+INCH(1)+Shelf_Backing_Setback', ppt_vars)
        ogee_lip = common_parts.add_deco_shelf_lip_1(self)
        self.shelf_lips.append(ogee_lip)
        ogee_lip.obj_bp.parent = shelf.obj_bp
        ogee_lip.obj_bp["IS_SHOE_SHELF_LIP"] = True
        ogee_lip.loc_x('Shelf_Clip_Gap', ppt_vars)
        ogee_lip.loc_y('-Depth+INCH(1)+Shelf_Backing_Setback', ppt_vars)
        ogee_lip.rot_x(value=math.radians(-90))
        ogee_lip.dim_x('Width-(Shelf_Clip_Gap*2)', ppt_vars)
        ogee_lip.dim_y(value=sn_unit.inch(1.5))
        ogee_lip.dim_z('Thickness', ppt_vars)

    def add_fence(self, shelf, ppt_vars):
        shelf.dim_y('-Depth+Adj_Shelf_Setback+Shelf_Backing_Setback', ppt_vars)
        steel_fence = common_parts.add_shelf_fence(self)
        self.shelf_lips.append(steel_fence)
        steel_fence.obj_bp.parent = shelf.obj_bp
        steel_fence.obj_bp["IS_SHOE_SHELF_LIP"] = True
        steel_fence.loc_x('Shelf_Clip_Gap+INCH(1)', ppt_vars)
        steel_fence.loc_y('-Depth+Adj_Shelf_Setback+Shelf_Backing_Setback+INCH(1)', ppt_vars)
        steel_fence.rot_x(value=math.radians(90))
        steel_fence.dim_x('Width-(Shelf_Clip_Gap*2)-INCH(2)', ppt_vars)

    def add_shelf_lips(self):
        self.shelf_lips = []
        lip_type_ppt = self.get_prompt("Shelf Lip Type")
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Thickness = self.get_prompt("Thickness").get_var()
        Shelf_Backing_Setback = self.get_prompt('Shelf Backing Setback').get_var("Shelf_Backing_Setback")
        Individual_Shelf_Setbacks = self.get_prompt("Individual Shelf Setbacks").get_var()
        Shelf_Setback_All = self.get_prompt("Adj Shelf Setback").get_var('Shelf_Setback_All')
        Shelf_Lip_Width = self.get_prompt("Shelf Lip Width").get_var()

        for i, shelf in enumerate(self.shoe_shelves):
            Adj_Shelf_Setback = shelf.get_prompt('Adj Shelf Setback').get_var('Adj_Shelf_Setback')
            Shelf_Clip_Gap = shelf.get_prompt('Adj Shelf Clip Gap').get_var('Shelf_Clip_Gap')
            Shelf_Setback = self.get_prompt("Shelf " + str(i + 1) + " Setback").get_var("Shelf_Setback")
            lip_ppt_vars = [
                Width, Shelf_Clip_Gap, Depth, Adj_Shelf_Setback,
                Shelf_Backing_Setback, Thickness, Shelf_Lip_Width,
                Shelf_Setback, Shelf_Setback_All, Individual_Shelf_Setbacks]

            if lip_type_ppt.get_value() == 0:
                self.add_mel_lip(shelf, lip_ppt_vars)

            elif lip_type_ppt.get_value() == 1:
                self.add_applied_molding(shelf, lip_ppt_vars)

            elif lip_type_ppt.get_value() == 2:
                self.add_ogee_molding(shelf, lip_ppt_vars)

            elif lip_type_ppt.get_value() == 3:
                self.add_fence(shelf, lip_ppt_vars)

        self.update_collections()

    def add_shoe_shelves(self, amt=4):
        self.shoe_shelves = []
        previous_shelf = None

        if not self.calculator:
            super().add_calculator(amt + 1)

        super().add_calculator_prompts(amt + 1)

        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Height = self.obj_z.snap.get_var('location.z', 'Height')

        Thickness = self.get_prompt("Thickness").get_var()
        Shelf_Backing_Setback = self.get_prompt('Shelf Backing Setback').get_var("Shelf_Backing_Setback")
        Individual_Shelf_Setbacks = self.get_prompt("Individual Shelf Setbacks").get_var()

        Shelf_Angle = self.get_prompt("Shelf Angle").get_var()

        for i in range(1, amt + 1):
            self.add_prompt("Shelf " + str(i) + " Setback", 'DISTANCE', sn_unit.inch(0.25))
            Shelf_Setback = self.get_prompt("Shelf " + str(i) + " Setback").get_var("Shelf_Setback")
            height_prompt = eval("self.calculator.get_calculator_prompt('Opening {} Height')".format(str(i)))
            opening_height = eval("height_prompt.get_var(self.calculator.name, 'opening_{}_height')".format(str(i)))

            adj_shelf = common_parts.add_slanted_shoe_shelf(self)
            adj_shelf.obj_bp["IS_STACK_SHELF"] = True
            adj_shelf.obj_bp["IS_SHOE_SHELF"] = True
            self.shoe_shelves.append(adj_shelf)
            Adj_Shelf_Setback = adj_shelf.get_prompt('Adj Shelf Setback').get_var('Adj_Shelf_Setback')
            Shelf_Clip_Gap = adj_shelf.get_prompt('Adj Shelf Clip Gap').get_var('Shelf_Clip_Gap')
            Shelf_Setback_All = self.get_prompt("Adj Shelf Setback").get_var('Shelf_Setback_All')

            adj_shelf.loc_x('Shelf_Clip_Gap', [Shelf_Clip_Gap])
            adj_shelf.loc_y('Depth-Shelf_Backing_Setback', [Depth, Shelf_Backing_Setback])

            if previous_shelf:
                Previous_Z_Loc = previous_shelf.obj_bp.snap.get_var("location.z", "Previous_Z_Loc")
                adj_shelf.loc_z('Previous_Z_Loc-opening_{}_height-Thickness'.format(str(i)), [Previous_Z_Loc, opening_height, Thickness])
            else:
                adj_shelf.loc_z(
                    'Height-opening_{}_height+INCH(2.75)'.format(str(i)),
                    [Height, opening_height])

            adj_shelf.rot_x('Shelf_Angle', [Shelf_Angle])

            adj_shelf.dim_x('Width-(Shelf_Clip_Gap*2)', [Width, Shelf_Clip_Gap])
            adj_shelf.dim_y('-Depth+Adj_Shelf_Setback+Shelf_Backing_Setback', [Depth, Adj_Shelf_Setback, Shelf_Backing_Setback])
            adj_shelf.dim_z('Thickness', [Thickness])

            adj_shelf.get_prompt("Adj Shelf Setback").set_formula(
                'IF(Individual_Shelf_Setbacks,Shelf_Setback,Shelf_Setback_All)',
                [Shelf_Setback, Shelf_Setback_All, Individual_Shelf_Setbacks])

            previous_shelf = adj_shelf

        for shelf in self.shoe_shelves:
            sn_utils.update_obj_driver_expressions(shelf.obj_bp)

        self.add_shelf_lips()
        self.update_collections()

    def add_kd_shelf(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Shelf_Backing_Setback = self.get_prompt('Shelf Backing Setback').get_var("Shelf_Backing_Setback")
        Remove_Bottom_Shelf = self.get_prompt('Remove Bottom Shelf').get_var("Remove_Bottom_Shelf")
        Shelf_Backing_Setback = self.get_prompt('Shelf Backing Setback').get_var("Shelf_Backing_Setback")
        Parent_Has_Bottom_KD = self.get_prompt('Parent Has Bottom KD').get_var("Parent_Has_Bottom_KD")
        Thickness = self.get_prompt('Thickness').get_var("Thickness")
        TAS = self.get_prompt("Thick Adjustable Shelves").get_var('TAS')
        parent_hide = self.get_prompt('Hide').get_var()

        shelf = common_parts.add_shelf(self)
        Is_Locked_Shelf = shelf.get_prompt('Is Locked Shelf').get_var('Is_Locked_Shelf')
        Adj_Shelf_Clip_Gap = shelf.get_prompt('Adj Shelf Clip Gap').get_var('Adj_Shelf_Clip_Gap')
        Locked_Shelf_Setback = shelf.get_prompt('Locked Shelf Setback').get_var('Locked_Shelf_Setback')
        Adj_Shelf_Setback = shelf.get_prompt('Adj Shelf Setback').get_var('Adj_Shelf_Setback')
        IBEKD = shelf.get_prompt('Is Bottom Exposed KD').get_var('IBEKD')

        shelf.loc_x('IF(Is_Locked_Shelf,0,Adj_Shelf_Clip_Gap)', [Is_Locked_Shelf, Adj_Shelf_Clip_Gap])
        shelf.loc_y('Depth-Shelf_Backing_Setback', [Depth, Shelf_Backing_Setback])

        is_locked_shelf = shelf.get_prompt("Is Locked Shelf")
        is_locked_shelf.set_value(True)
        hide = shelf.get_prompt("Hide")
        hide.set_formula(
            'IF(Remove_Bottom_Shelf,True,IF(Parent_Has_Bottom_KD,True,False)) or Hide',
            [Remove_Bottom_Shelf, Parent_Has_Bottom_KD, parent_hide])
        shelf.get_prompt("Is Forced Locked Shelf").set_value(value=True)

        shelf.dim_x(
            'Width-IF(Is_Locked_Shelf,0,Adj_Shelf_Clip_Gap*2)',
            [Width, Is_Locked_Shelf, Adj_Shelf_Clip_Gap])
        shelf.dim_y(
            '-Depth+IF(Is_Locked_Shelf,Locked_Shelf_Setback,Adj_Shelf_Setback)+Shelf_Backing_Setback',
            [Depth, Locked_Shelf_Setback, Is_Locked_Shelf, Adj_Shelf_Setback, Shelf_Backing_Setback])
        shelf.dim_z('IF(AND(TAS,IBEKD==False), INCH(1),Thickness) *-1', [Thickness, TAS, IBEKD])

    def draw(self):
        self.create_assembly()
        self.add_shoe_shelf_prompts()
        self.add_shoe_shelves()
        self.add_kd_shelf()
        super().update()
        self.obj_bp['IS_BP_SHOE_SHELVES'] = True
        props = self.obj_bp.sn_closets
        props.is_slanted_shelf_bp = True  # TODO: remove


class Horizontal_Splitters(sn_types.Assembly):

    type_assembly = "INSERT"
    id_prompt = "sn_closets.horizontal_splitters"
    drop_id = "sn_closets.drop_insert"
    placement_type = "SPLITTER"
    show_in_library = True
    category_name = "Products - Shelves"
    mirror_y = False
    calculator = None

    ''' Number of openings to create for this splitter
    '''
    horizontal_openings = 2  # 1-10

    ''' Override the default width for the openings
        0 will make the opening calculate equally
    '''
    opening_1_width = 0
    opening_2_width = 0
    opening_3_width = 0
    opening_4_width = 0
    opening_5_width = 0
    opening_6_width = 0
    opening_7_width = 0
    opening_8_width = 0
    opening_9_width = 0
    opening_10_width = 0

    ''' sn_types.Assembly to put into the interior
        or exterior of the opening
    '''
    interior_1 = None
    exterior_1 = None
    interior_2 = None
    exterior_2 = None
    interior_3 = None
    exterior_3 = None
    interior_4 = None
    exterior_4 = None
    interior_5 = None
    exterior_5 = None
    interior_6 = None
    exterior_6 = None
    interior_7 = None
    exterior_7 = None
    interior_8 = None
    exterior_8 = None
    interior_9 = None
    exterior_9 = None
    interior_10 = None
    exterior_10 = None
    interior_11 = None
    exterior_11 = None

    def add_prompts(self):
        calc_distance_obj = self.add_empty('Calc Distance Obj')
        calc_distance_obj.empty_display_size = .001
        self.add_prompt("Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.calculator = self.obj_prompts.snap.add_calculator(
            "Opening Widths",
            calc_distance_obj)

        for i in range(1, self.horizontal_openings + 1):
            size = eval("self.opening_" + str(i) + "_width")
            calc_prompt = self.calculator.add_calculator_prompt("Opening " + str(i) + " Width")
            calc_prompt.equal = True if size == 0 else False

        Thickness = self.get_prompt('Thickness').get_var()
        width = self.obj_x.snap.get_var('location.x', 'width')
        self.calculator.set_total_distance(
            "width-Thickness*(" + str(self.horizontal_openings) + "-1)",
            [width, Thickness])

    def add_insert(self, insert, index, x_loc_vars=[], x_loc_expression=""):
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        open_prompt = eval("self.calculator.get_calculator_prompt('Opening {} Width')".format(str(index)))
        open_var = eval("open_prompt.get_var(self.calculator.name, 'Opening_{}_Width')".format(str(index)))
        x_dim_expression = "Opening_" + str(index) + "_Width"

        if insert:
            if not insert.obj_bp:
                insert.draw()

            insert.obj_bp.parent = self.obj_bp
            if index == 1:
                insert.loc_x(value=0)
            else:
                insert.loc_x(x_loc_expression, x_loc_vars)

            insert.dim_x(x_dim_expression, [open_var])
            insert.dim_y('Depth',[Depth])
            insert.dim_z('Height',[Height])

    def get_opening(self, index):
        opening = common_parts.add_opening(self)
        exterior = eval('self.exterior_' + str(index))
        interior = eval('self.interior_' + str(index))

        if interior:
            opening.obj_bp.snap.interior_open = False

        if exterior:
            opening.obj_bp.snap.exterior_open = False

        return opening

    def add_splitters(self):
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Thickness = self.get_prompt('Thickness').get_var()
        previous_splitter = None

        for i in range(1, self.horizontal_openings):
            x_loc_vars = []
            open_prompt = eval("self.calculator.get_calculator_prompt('Opening {} Width')".format(str(i)))
            open_var = eval("open_prompt.get_var(self.calculator.name, 'Opening_{}_Width')".format(str(i)))
            x_loc_vars.append(open_var)

            if previous_splitter:
                x_loc = previous_splitter.obj_bp.snap.get_var("location.x", "Splitter_X_Loc")
                x_loc_vars.append(x_loc)
                x_loc_vars.append(Thickness)

            splitter = common_parts.add_division(self)
            if previous_splitter:
                splitter.loc_x("Splitter_X_Loc+Thickness+Opening_" + str(i) + "_Width",x_loc_vars)
            else:
                splitter.loc_x("Opening_" + str(i) + "_Width",[open_var])

            splitter.loc_y('Depth', [Depth])
            splitter.rot_y(value=math.radians(-90))
            splitter.dim_x('Height', [Height])
            splitter.dim_y('-Depth', [Depth])
            splitter.dim_z('-Thickness', [Thickness])

            previous_splitter = splitter

            exterior = eval('self.exterior_' + str(i))
            self.add_insert(exterior, i, x_loc_vars, "Splitter_X_Loc+Thickness")

            interior = eval('self.interior_' + str(i))
            self.add_insert(interior, i, x_loc_vars, "Splitter_X_Loc+Thickness")

            opening = self.get_opening(i)
            self.add_insert(opening, i, x_loc_vars, "Splitter_X_Loc+Thickness")

        insert_x_loc_vars = []
        insert_x_loc = previous_splitter.obj_bp.snap.get_var("location.x", "Splitter_X_Loc")
        insert_x_loc_vars.append(insert_x_loc)
        insert_x_loc_vars.append(Thickness)

        # ADD LAST INSERT
        last_exterior = eval('self.exterior_' + str(self.horizontal_openings))
        self.add_insert(last_exterior, self.horizontal_openings, insert_x_loc_vars, "Splitter_X_Loc+Thickness")

        last_interior = eval('self.interior_' + str(self.horizontal_openings))
        self.add_insert(last_interior, self.horizontal_openings, insert_x_loc_vars, "Splitter_X_Loc+Thickness")

        last_opening = self.get_opening(self.horizontal_openings)
        self.add_insert(last_opening, self.horizontal_openings, insert_x_loc_vars, "Splitter_X_Loc+Thickness")

    def update(self):
        super().update()
        self.obj_bp.snap.export_as_subassembly = True
        self.obj_bp['IS_BP_SPLITTER'] = True
        props = self.obj_bp.sn_closets
        props.is_splitter_bp = True  # TODO: remove

    def pre_draw(self):
        self.create_assembly()
        self.add_prompts()
        self.add_splitters()
        self.update()


class OpeningHeights:
    def __init__(self, start, start_hole_amt, end_hole_amt):
        self.start = start
        self.end_hole_amt = end_hole_amt
        self.hole_amt = start_hole_amt

    def __iter__(self):
        self.num = self.start
        return self

    def __next__(self):
        mm = self.num
        inch = round(self.num / 25.4, 2)
        name = '{}H-{}"'.format(str(self.hole_amt), str(inch))
        self.num += 32
        self.hole_amt += 1

        if(self.hole_amt > self.end_hole_amt):
            raise StopIteration

        return ((str(mm), name, ""))


class SNAP_OT_set_opening_height(Operator):
    bl_idname = "sn_closets.set_opening_height"
    bl_label = "Set Vertical Opening Height"
    bl_description = "This sets the vertical opening height"
    bl_options = {'UNDO'}

    height: FloatProperty(name="Opening Height")

    def execute(self, context):
        global opening_height_ppt
        opening_height_ppt.set_value(sn_unit.millimeter(self.height))

        return {'FINISHED'}


def get_opening_heights(end_hole_amt=76):
    start = SHELF_OPENING_MIN_HEIGHT
    start_hole_amt = 4
    opening_heights = OpeningHeights(start, start_hole_amt, end_hole_amt)
    heights_iter = iter(opening_heights)
    opening_heights = list(heights_iter)

    return opening_heights


class SNAP_MT_Opening_Heights(bpy.types.Menu):
    bl_label = ""

    opening_num = "0"

    def draw(self, context):
        col = self.layout.column()
        obj = bpy.data.objects[bpy.context.object.name]
        insert_bp = sn_utils.get_bp(obj, 'INSERT')
        product_bp = sn_utils.get_bp(obj, 'PRODUCT')
        assembly = None

        if insert_bp:
            insert = Shelf_Stack(insert_bp)
            assembly = insert
            shelf_qty_ppt = insert.get_prompt("Shelf Quantity")
            calculator = insert.calculator
        elif product_bp:
            if product_bp.get("IS_BP_CORNER_SHELVES"):
                product = Corner_Shelves(product_bp)
            if product_bp.get("IS_BP_L_SHELVES"):
                product = L_Shelves(product_bp)

            assembly = product
            shelf_qty_ppt = product.get_prompt("Shelf Quantity")
            calculator = product.calculator

        if assembly:
            opening_height = calculator.get_calculator_prompt("Opening {} Height".format(self.opening_num))
            total_distance = calculator.distance_obj.snap.calculator_distance
            min_height = sn_unit.millimeter(float(SHELF_OPENING_MIN_HEIGHT))

            taken_space = 0
            equal_ppts = []

            for i in range(1, shelf_qty_ppt.get_value() + 1):
                height_ppt = eval("calculator.get_calculator_prompt('Opening {} Height')".format(str(i)))
                if height_ppt.equal:
                    equal_ppts.append(height_ppt)
                elif height_ppt != opening_height:
                    taken_space += height_ppt.get_value()

            equal_min_height = min_height * len(equal_ppts)
            available_space = total_distance - equal_min_height
            available_space -= taken_space
            max_height = available_space // sn_unit.millimeter(32)

            for height in get_opening_heights(int(max_height)):

                selected_height = float(height[0]) == round(sn_unit.meter_to_millimeter(opening_height.get_value()), 2)
                op = col.operator(
                    "sn_closets.set_opening_height",
                    text=height[1],
                    icon='RADIOBUT_ON' if selected_height else 'RADIOBUT_OFF')

                op.height = float(height[0])
                global opening_height_ppt
                global shelf_stack_assembly
                opening_height_ppt = opening_height
                shelf_stack_assembly = assembly


class SNAP_MT_Opening_1_Heights(SNAP_MT_Opening_Heights):
    bl_label = ""

    def draw(self, context):
        self.opening_num = "1"
        super().draw(context)


class SNAP_MT_Opening_2_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 2 Heights"

    def draw(self, context):
        self.opening_num = "2"
        super().draw(context)


class SNAP_MT_Opening_3_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 3 Heights"

    def draw(self, context):
        self.opening_num = "3"
        super().draw(context)


class SNAP_MT_Opening_4_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 4 Heights"

    def draw(self, context):
        self.opening_num = "4"
        super().draw(context)


class SNAP_MT_Opening_5_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 5 Heights"

    def draw(self, context):
        self.opening_num = "5"
        super().draw(context)


class SNAP_MT_Opening_6_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 6 Heights"

    def draw(self, context):
        self.opening_num = "6"
        super().draw(context)


class SNAP_MT_Opening_7_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 7 Heights"

    def draw(self, context):
        self.opening_num = "7"
        super().draw(context)


class SNAP_MT_Opening_8_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 8 Heights"

    def draw(self, context):
        self.opening_num = "8"
        super().draw(context)


class SNAP_MT_Opening_9_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 9 Heights"

    def draw(self, context):
        self.opening_num = "9"
        super().draw(context)


class SNAP_MT_Opening_10_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 10 Heights"

    def draw(self, context):
        self.opening_num = "10"
        super().draw(context)


class SNAP_MT_Opening_11_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 11 Heights"

    def draw(self, context):
        self.opening_num = "11"
        super().draw(context)


class SNAP_MT_Opening_12_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 12 Heights"

    def draw(self, context):
        self.opening_num = "12"
        super().draw(context)


class SNAP_MT_Opening_13_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 13 Heights"

    def draw(self, context):
        self.opening_num = "13"
        super().draw(context)


class SNAP_MT_Opening_14_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 14 Heights"

    def draw(self, context):
        self.opening_num = "14"
        super().draw(context)


class SNAP_MT_Opening_15_Heights(SNAP_MT_Opening_Heights):
    bl_label = "Opening 15 Heights"

    def draw(self, context):
        self.opening_num = "15"
        super().draw(context)


class PROMPTS_Vertical_Splitter_Prompts(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.vertical_splitters"
    bl_label = "Shelf Prompts"
    bl_description = "This shows all of the available vertical splitter options"
    bl_options = {'UNDO'}

    object_name: StringProperty(name="Object Name")

    shelf_quantity: EnumProperty(
        name="Shelf Quantity",
        items=[
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

    shelf_type: EnumProperty(
        name="Shelf Type",
        items=[
            ('0', 'Splitter', 'Splitter'),
            ('1', 'Shoe Shelf', 'Shoe Shelf')],
        default='0')

    shelf_lip_type: EnumProperty(
        name="Shelf Lip Type",
        items=[
            ('0', 'Melamine Lip', 'Melamine Lip'),
            ('1', 'Applied Flat Molding', 'Applied Flat Molding'),
            ('2', 'Ogee Molding', 'Ogee Molding'),
            ('3', 'Steel Fence', 'Steel Fence')],
        default='0')

    assembly = None
    cur_shelf_height = None
    shelf_lip_type_prompt = None
    prev_lip_type = 0

    lip_type_changed = False
    lip_type_changed: bpy.props.BoolProperty(name="lip_type_changed", default=False)

    def update_shelves(self):
        shelves = []
        shoe_shelves = self.shelf_type == '1'
        glass_shelves = self.shelf_type == '2'
        lip_type_changed = False

        if shoe_shelves:
            shelves = self.assembly.shoe_shelves
            num_shelves = len(shelves) + 1
            if self.shelf_lip_type_prompt:
                lip_type_changed = self.shelf_lip_type_prompt.get_value() != self.prev_lip_type
                self.prev_lip_type = self.shelf_lip_type_prompt.get_value()
        else:
            shelves = self.assembly.splitters
            num_shelves = len(shelves)

        shelf_amt_changed = num_shelves != int(self.shelf_quantity)

        if shelf_amt_changed:
            for i, assembly in enumerate(shelves):
                sn_utils.delete_object_and_children(assembly.obj_bp)
                setback_ppt = self.assembly.get_prompt("Shelf " + str(i + 1) + " Setback")

                if setback_ppt:
                    bpy.ops.sn_prompt.delete_prompt(
                        obj_name=self.assembly.obj_prompts.name,
                        prompt_name=setback_ppt.name)

            shelves.clear()

            for assembly in self.assembly.openings:
                sn_utils.delete_object_and_children(assembly.obj_bp)
            self.assembly.openings.clear()

            if shoe_shelves:
                self.assembly.add_shoe_shelves(amt=int(self.shelf_quantity) - 1)
            else:
                self.assembly.add_splitters(amt=int(self.shelf_quantity))

        elif lip_type_changed:
            self.lip_type_changed = False

            for assembly in self.assembly.shelf_lips:
                sn_utils.delete_object_and_children(assembly.obj_bp)
            self.assembly.shelf_lips.clear()
            self.assembly.add_shelf_lips()

        self.assembly.update()
        bpy.ops.object.select_all(action='DESELECT')

        if shelves:
            shelf = shelves[0]
            for child in shelf.obj_bp.children:
                if child.type == 'MESH':
                    bpy.context.view_layer.objects.active = child
                    break

    def closest_hole_amt(self, opening_heights, height):
        return opening_heights[min(range(len(opening_heights)), key=lambda i: abs(opening_heights[i] - height))]

    def update_opening_heights(self):
        opening_num = 2 if self.shelf_type == '1' else 1

        for i in range(1, int(self.shelf_quantity) + opening_num):
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
        self.run_calculators(self.assembly.obj_bp)

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

        if self.shelf_lip_type_prompt:
            self.shelf_lip_type_prompt.set_value(int(self.shelf_lip_type))

    def set_properties_from_prompts(self):
        ''' This should be called in the invoke function to set the class properties
            to the same values as the prompts
        '''
        shelf_quantity = self.assembly.get_prompt("Shelf Quantity")

        if self.shelf_lip_type_prompt:
            self.shelf_lip_type = str(self.shelf_lip_type_prompt.get_value())

        if shelf_quantity:
            self.shelf_quantity = str(shelf_quantity.get_value())

    def invoke(self, context, event):
        obj_bp = self.get_insert().obj_bp

        if not obj_bp.get("SNAP_VERSION"):
            print("Found old lib data!")
            return bpy.ops.sn_closets.vertical_splitters_214('INVOKE_DEFAULT')

        if obj_bp.get("IS_BP_SPLITTER"):
            self.shelf_type = '0'
            self.assembly = Shelf_Stack(obj_bp)
        if obj_bp.get("IS_BP_SHOE_SHELVES"):
            self.shelf_type = '1'
            self.assembly = Shoe_Shelf_Stack(obj_bp)
            self.shelf_lip_type_prompt = self.assembly.get_prompt("Shelf Lip Type")
            self.prev_lip_type = self.shelf_lip_type_prompt.get_value()

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
        return wm.invoke_props_dialog(self, width=350)

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

    def draw_opening_row(self, i, box, height, opening_heights):
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
            row.label(text=str(round(sn_unit.meter_to_active_unit(height.distance_value), 2)) + '"')
        else:
            label = ""
            for opening_height in opening_heights:
                if float(opening_height[0]) == round(sn_unit.meter_to_millimeter(height.distance_value), 1):
                    label = opening_height[1]
            row.menu("SNAP_MT_Opening_{}_Heights".format(str(i + 1)), text=label)

    def draw_splitter_heights(self, layout):
        if self.assembly.obj_bp.get("IS_BP_SPLITTER"):
            shelves = self.assembly.splitters
        if self.assembly.obj_bp.get("IS_BP_SHOE_SHELVES"):
            shelves = self.assembly.shoe_shelves

        idv_shelf_setbacks = self.assembly.get_prompt("Individual Shelf Setbacks")
        opening_heights = get_opening_heights()

        col = layout.column(align=True)
        box = col.box()
        box.label(text="Opening Heights:")

        for i, shelf in enumerate(shelves):
            calculator = self.assembly.get_calculator('Opening Heights Calculator')
            height = eval("calculator.get_calculator_prompt('Opening {} Height')".format(str(i + 1)))
            setback = self.assembly.get_prompt("Shelf " + str(i + 1) + " Setback")
            is_locked_shelf = shelf.get_prompt("Is Locked Shelf")

            if height:
                self.draw_opening_row(i, box, height, opening_heights)

            if setback and idv_shelf_setbacks and is_locked_shelf:
                if idv_shelf_setbacks.get_value() and not is_locked_shelf.get_value():
                    row = box.row()
                    row.label(text="Shelf " + str(i + 1) + " Setback")
                    row.prop(setback, 'distance_value', text="")

        last_height = calculator.get_calculator_prompt("Opening {} Height".format(len(shelves) + 1))
        if last_height:
            self.draw_opening_row(i + 1, box, last_height, opening_heights)

    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                box = layout.box()
                row = box.row()
                adj_shelf_setback = self.assembly.get_prompt("Adj Shelf Setback")
                shelf_quantity = self.assembly.get_prompt("Shelf Quantity")
                idv_shelf_setbacks = self.assembly.get_prompt("Individual Shelf Setbacks")
                shelf_lip_type = self.assembly.get_prompt("Shelf Lip Type")

                if shelf_quantity:
                    col = box.column(align=True)
                    row = col.row()
                    row.label(text="Qty (Includes KD):")
                    row = col.row()
                    row.prop(self, "shelf_quantity", expand=True)

                if adj_shelf_setback:
                    col = box.column(align=True)
                    row = col.row()
                    adj_shelf_setback.draw(row, allow_edit=False)

                if self.shelf_type == '0' and idv_shelf_setbacks:
                    col = box.column(align=True)
                    row = col.row()
                    idv_shelf_setbacks.draw(row, allow_edit=False)

                if shelf_lip_type:
                    col = box.column(align=True)
                    col.label(text="Shoe Shelf Lip Type")
                    row = col.row(align=True)
                    row.prop_enum(self, "shelf_lip_type", '0')
                    row.prop_enum(self, "shelf_lip_type", '1')
                    row = col.row(align=True)
                    row.prop_enum(self, "shelf_lip_type", '2')
                    row.prop_enum(self, "shelf_lip_type", '3')

                self.draw_splitter_heights(box)

                remove_bottom_shelf = self.assembly.get_prompt('Remove Bottom Shelf')
                if remove_bottom_shelf:
                    box.prop(remove_bottom_shelf, "checkbox_value", text=remove_bottom_shelf.name)


class PROMPTS_Horizontal_Splitter_Prompts(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.horizontal_splitters"
    bl_label = "Horizontal Splitter Prompts"
    bl_description = "This shows all of the available horizontal splitter options"
    bl_options = {'UNDO'}

    object_name: bpy.props.StringProperty(name="Object Name")

    assembly = None

    def check(self, context):
        sn_utils.run_calculators(self.assembly.obj_bp)
        return True

    def get_splitter(self, obj_bp):
        ''' Gets the splitter based on selection
        '''
        props = self.obj_bp.sn_closets
        if props.is_splitter_bp:
            return sn_types.Assembly(obj_bp)
        if obj_bp.parent:
            return self.get_splitter(obj_bp.parent)        

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        self.assembly = self.get_insert()
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)

    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                box = layout.box()
                for i in range(1,10):
                    opening = self.assembly.get_prompt("Opening " + str(i) + " Width")
                    if opening:
                        row = box.row()
                        row.label(text="Opening " + str(i) + " Width:")
                        if opening.equal:
                            row.label(text=str(sn_unit.meter_to_active_unit(opening.distance_value)) + '"')
                            row.prop(opening,'equal',text="")
                        else:
                            row.prop(opening,'distance_value',text="")
                            row.prop(opening,'equal',text="")  


class OPERATOR_Vertical_Splitters_Drop(Operator, PlaceClosetInsert):
    bl_idname = "sn_closets.insert_vertical_splitters_drop"
    bl_label = "Custom drag and drop for vertical_splitters insert"
    bl_description = "This places a shelf stack."
    bl_options = {'UNDO'}

    insert = None

    def execute(self, context):
        self.insert = self.asset
        return super().execute(context)

    def set_carcass_bottom_kd_formula(self, context):
        parent_obj = self.insert.obj_bp.parent
        parent_assembly = sn_types.Assembly(parent_obj)
        floor = parent_assembly.get_prompt("Opening " + str(self.insert.obj_bp.sn_closets.opening_name) + " Floor Mounted")
        parent_remove_bottom_shelf = parent_assembly.get_prompt('Remove Bottom Hanging Shelf ' + str(self.insert.obj_bp.sn_closets.opening_name))
        remove_bottom_shelf = self.insert.get_prompt("Remove Bottom Shelf")
        parent_has_bottom_kd = self.insert.get_prompt("Parent Has Bottom KD")
        door_type = parent_assembly.get_prompt("Door Type")
        prompts = [floor, parent_remove_bottom_shelf, remove_bottom_shelf, parent_has_bottom_kd]

        if all(prompts):
            if parent_remove_bottom_shelf.get_value() or floor.get_value():
                parent_has_bottom_kd.set_value(True)
            else:
                parent_remove_bottom_shelf.set_value(False)
                parent_has_bottom_kd.set_value(False)
        elif door_type:
            if door_type.get_value() == 0:
                remove_bottom_shelf.set_value(True)

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

        self.selected_point, self.selected_obj, ignore = sn_utils.get_selection_point(
            context,
            event,
            objects=self.include_objects,
            exclude_objects=self.exclude_objects)

        self.position_asset(context)

        if self.event_is_place_first_point(event) and self.selected_opening:
            self.confirm_placement(context)
            self.set_carcass_bottom_kd_formula(context)
            return self.finish(context)

        if self.event_is_cancel_command(event):
            return self.cancel_drop(context)

        if self.event_is_pass_through(event):
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}


bpy.utils.register_class(SNAP_MT_Opening_1_Heights)
bpy.utils.register_class(SNAP_MT_Opening_2_Heights)
bpy.utils.register_class(SNAP_MT_Opening_3_Heights)
bpy.utils.register_class(SNAP_MT_Opening_4_Heights)
bpy.utils.register_class(SNAP_MT_Opening_5_Heights)
bpy.utils.register_class(SNAP_MT_Opening_6_Heights)
bpy.utils.register_class(SNAP_MT_Opening_7_Heights)
bpy.utils.register_class(SNAP_MT_Opening_8_Heights)
bpy.utils.register_class(SNAP_MT_Opening_9_Heights)
bpy.utils.register_class(SNAP_MT_Opening_10_Heights)
bpy.utils.register_class(SNAP_MT_Opening_11_Heights)
bpy.utils.register_class(SNAP_MT_Opening_12_Heights)
bpy.utils.register_class(SNAP_MT_Opening_13_Heights)
bpy.utils.register_class(SNAP_MT_Opening_14_Heights)
bpy.utils.register_class(SNAP_MT_Opening_15_Heights)
bpy.utils.register_class(PROMPTS_Vertical_Splitter_Prompts)
bpy.utils.register_class(PROMPTS_Horizontal_Splitter_Prompts)
bpy.utils.register_class(OPERATOR_Vertical_Splitters_Drop)
bpy.utils.register_class(SNAP_OT_set_opening_height)
