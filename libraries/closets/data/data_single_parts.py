import math

import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty

from snap import sn_types, sn_unit, sn_utils
from ..ops.drop_closet import PlaceClosetInsert
from .. import closet_props
from ..common import common_parts, common_lists, common_prompts


class Pants_Rack(sn_types.Assembly):

    id_prompt = ""
    drop_id = "sn_closets.place_single_part"
    show_in_library = True
    insert_type = "Interior"
    placement_type = "INTERIOR"
    type_assembly = "INSERT"
    mirror_y = False
    library_name = ""
    category_name = ""

    def draw(self):
        self.create_assembly()
        self.obj_bp.sn_closets.is_accessory_bp = True
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        pants_rack = common_parts.add_sliding_pants_rack(self)
        pants_rack.obj_bp.snap.type_mesh = 'HARDWARE'
        pants_rack.loc_y('Depth', [Depth])
        pants_rack.dim_x('Width', [Width])
        pants_rack.dim_y('-Depth', [Depth])
        self.update()


class Single_Pull_Out_Hamper(sn_types.Assembly):

    id_prompt = ""
    drop_id = "sn_closets.place_single_part"
    show_in_library = True
    insert_type = "Interior"
    placement_type = "INTERIOR"
    type_assembly = "INSERT"
    mirror_y = False
    library_name = ""
    category_name = ""

    def draw(self):
        self.create_assembly()
        self.obj_bp.sn_closets.is_accessory_bp = True
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        hamper = common_parts.add_single_pull_out_canvas_hamper(self)
        hamper.obj_bp.snap.type_mesh = 'HARDWARE'
        hamper.loc_y('Depth', [Depth])
        hamper.dim_x('Width', [Width])
        hamper.dim_y('-Depth', [Depth])

        self.update()


class Double_Pull_Out_Hamper(sn_types.Assembly):

    id_prompt = ""
    drop_id = "sn_closets.place_single_part"
    show_in_library = True
    insert_type = "Interior"
    placement_type = "INTERIOR"
    type_assembly = "INSERT"
    mirror_y = False
    library_name = ""
    category_name = ""

    def draw(self):
        self.create_assembly()
        self.obj_bp.sn_closets.is_accessory_bp = True
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        hamper = common_parts.add_double_pull_out_canvas_hamper(self)
        hamper.obj_bp.snap.type_mesh = 'HARDWARE'
        hamper.loc_y('Depth', [Depth])
        hamper.dim_x('Width', [Width])
        hamper.dim_y('-Depth', [Depth])
        self.update()


class Wire_Basket(sn_types.Assembly):

    id_prompt = "sn_closets.wire_baskets"
    drop_id = "sn_closets.place_single_part"
    show_in_library = True
    placement_type = "INTERIOR"
    type_assembly = "INSERT"
    mirror_y = False
    max_qty = 6
    library_name = ""
    category_name = ""

    def draw(self):
        self.create_assembly()
        self.obj_bp.sn_closets.is_accessory_bp = True

        for i in range(1, self.max_qty):
            self.add_prompt("Basket Height " + str(i), 'DISTANCE', sn_unit.inch(6))

        self.add_prompt("Distance Between Baskets", 'DISTANCE', sn_unit.inch(3))
        self.add_prompt("Baskets Qty", 'QUANTITY', 1)

        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Distance_Between_Baskets = self.get_prompt('Distance Between Baskets').get_var()
        Baskets_Qty = self.get_prompt('Baskets Qty').get_var()
        prev_basket = None

        for i in range(1, self.max_qty):
            Basket_Height = self.get_prompt('Basket Height ' + str(i)).get_var('Basket_Height')
            wire_basket = common_parts.add_wire_basket(self)

            if prev_basket:
                basket_loc = prev_basket.obj_bp.snap.get_var('location.z', 'basket_loc')
                basket_height = prev_basket.obj_z.snap.get_var('location.z','basket_height')
                wire_basket.loc_z('basket_loc+basket_height+Distance_Between_Baskets',[basket_loc,basket_height,Distance_Between_Baskets])

            wire_basket.dim_x('Width',[Width])
            wire_basket.dim_y('Depth',[Depth])
            wire_basket.dim_z('Basket_Height',[Basket_Height])
            wire_basket.get_prompt('Hide').set_formula('IF(Baskets_Qty>=' + str(i) + ',False,True)',[Baskets_Qty])
            prev_basket = wire_basket

        self.update()


class Hanging_Rod(sn_types.Assembly):

    id_prompt = "sn_closets.single_hanging_rod_prompts"
    drop_id = "sn_closets.insert_rods_and_shelves_drop"
    show_in_library = True
    placement_type = "INTERIOR"
    type_assembly = "INSERT"
    mirror_y = False
    hanging_rod_qty = 1
    library_name = ""
    category_name = ""

    def add_rod(self, assembly, is_hanger=False):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        # Setback_from_Rear = self.get_var("Setback from Rear")
        Z_Loc = self.get_prompt("Top Rod Location From Top").get_var('Z_Loc')
        Top_Rod_Location = self.get_prompt("Top Rod Location").get_var('Top_Rod_Location')
        Turn_Off_Hangers = self.get_prompt("Turn Off Hangers").get_var('Turn_Off_Hangers')
        Hanging_Rod_Width_Deduction = self.get_prompt(
            "Hanging Rod Width Deduction").get_var('Hanging_Rod_Width_Deduction')
        Hanging_Rod_Setback = self.get_prompt("Hanging Rod Setback").get_var('Hanging_Rod_Setback')
        Add_Rod_Setback = self.get_prompt("Add Rod Setback").get_var('Add_Rod_Setback')
        Add_Deep_Rod_Setback = self.get_prompt("Add Deep Rod Setback").get_var('Add_Deep_Rod_Setback')
        Default_Deep_Setback = self.get_prompt("Default Deep Setback").get_var('Default_Deep_Setback')
        Extra_Deep_Pard = self.get_prompt("Extra Deep Pard").get_var('Extra_Deep_Pard')
        Top_Rod = self.get_prompt('Add Top Rod').get_var('Add_Top_Rod')

        assembly.loc_x('Hanging_Rod_Width_Deduction/2', [Hanging_Rod_Width_Deduction])
        assembly.dim_x('Width-Hanging_Rod_Width_Deduction', [Width, Hanging_Rod_Width_Deduction])
        assembly.dim_y(value=sn_unit.inch(.5))
        assembly.dim_z(value=sn_unit.inch(-1))

    
        Add_Middle_Rod = self.get_prompt("Add Middle Rod").get_var('Add_Middle_Rod')
        assembly.loc_z('Height-Z_Loc+IF(Add_Top_Rod,0,-Top_Rod_Location+0.032004)',
                        [Height, Top_Rod_Location, Z_Loc, Top_Rod])
        assembly.loc_y('IF(Depth>=Extra_Deep_Pard,Hanging_Rod_Setback+Add_Deep_Rod_Setback,Hanging_Rod_Setback+Add_Rod_Setback)',
                       [Hanging_Rod_Setback, Add_Rod_Setback, Extra_Deep_Pard, Depth, Default_Deep_Setback, Add_Deep_Rod_Setback])
        if is_hanger:
            hide = assembly.get_prompt("Hide")
            hide.set_formula(
                'IF(Turn_Off_Hangers,True,IF(Add_Middle_Rod,False,True))',
                [Add_Middle_Rod, Turn_Off_Hangers])
        else:
            hide = assembly.get_prompt("Hide")
            hide.set_formula('IF(Add_Middle_Rod,False,True)', [Add_Middle_Rod])

        return assembly

    def draw(self):
        self.create_assembly()
        props = bpy.context.scene.sn_closets.closet_defaults
        self.obj_bp.sn_closets.is_accessory_bp = True

        self.add_prompt("Add Top Rod", 'CHECKBOX', False)
        self.add_prompt("Add Middle Rod", 'CHECKBOX', True)

        self.add_prompt("Top Rod Location", 'DISTANCE', sn_unit.millimeter(428.95))
        self.add_prompt("Hanging Rod Width Deduction", 'DISTANCE', sn_unit.inch(0))

        self.add_prompt("Top Rod Location From Top", 'DISTANCE', sn_unit.inch(1.26))
        self.add_prompt("Turn Off Hangers", 'CHECKBOX', props.hide_hangers)

        self.add_prompt("Hanging Rod Setback", 'DISTANCE', sn_unit.inch(1.69291))
        self.add_prompt("Add Rod Setback", 'DISTANCE', sn_unit.inch(0))

        self.add_prompt("Default Deep Setback", 'DISTANCE', sn_unit.inch(12))
        self.add_prompt("Extra Deep Pard", 'DISTANCE', sn_unit.inch(16))
        self.add_prompt("Add Deep Rod Setback", 'DISTANCE', sn_unit.inch(0))

        opts = bpy.context.scene.sn_closets.closet_options

        if "Oval" in opts.rods_name:
            self.add_rod(common_parts.add_oval_hanging_rod(self))

        else:
            self.add_rod(common_parts.add_round_hanging_rod(self))

        self.add_rod(common_parts.add_hangers(self), is_hanger=True)

        self.update()


class Shelf(sn_types.Assembly):

    type_assembly = 'INSERT'
    mirror_y = False
    property_id = "sn_closets.shelf"
    drop_id = "sn_closets.place_single_part"

    hanging_rod_qty = 1

    def draw(self):
        self.create_assembly()
        self.add_prompt("Shelf Quantity", 'QUANTITY', 1)
        self.add_prompt("Shelf Type", 'COMBOBOX', ['Adjustable','Fixed','Sliding'])
        self.add_prompt("Drawer Slide Gap", 'DISTANCE', sn_unit.inch(.25))
        self.add_prompt("Shelf Spacing", 'DISTANCE', sn_unit.inch(6))
        self.add_prompt("Thick Adjustable Shelves", 'CHECKBOX', bpy.context.scene.sn_closets.closet_defaults.thick_adjustable_shelves)

        common_prompts.add_thickness_prompts(self)

        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Shelf_Thickness = self.get_var('Shelf Thickness')
        Shelf_Type = self.get_var('Shelf Type')
        Drawer_Slide_Gap = self.get_var('Drawer Slide Gap')
        Shelf_Quantity = self.get_var('Shelf Quantity')
        Shelf_Spacing = self.get_var('Shelf Spacing')
        TAS = self.get_prompt("Thick Adjustable Shelves").get_var('TAS')

        shelf = common_parts.add_shelf(self)

        Is_Locked_Shelf = shelf.get_var('Is Locked Shelf')
        IBEKD = shelf.get_prompt('Is Bottom Exposed KD').get_var('IBEKD')
        Adj_Shelf_Setback = shelf.get_var('Adj Shelf Setback')
        Locked_Shelf_Setback = shelf.get_var('Locked Shelf Setback')
        Adj_Shelf_Clip_Gap = shelf.get_var('Adj Shelf Clip Gap')

        shelf.loc_x('IF(Shelf_Type==2,Drawer_Slide_Gap,IF(Is_Locked_Shelf,0,Adj_Shelf_Clip_Gap))',[Shelf_Type,Drawer_Slide_Gap,Is_Locked_Shelf,Adj_Shelf_Clip_Gap])
        shelf.loc_y('Depth',[Depth])
        shelf.dim_x('Width-IF(Shelf_Type==2,Drawer_Slide_Gap*2,IF(Is_Locked_Shelf,0,Adj_Shelf_Clip_Gap*2))',[Width,Shelf_Type,Drawer_Slide_Gap,Is_Locked_Shelf,Adj_Shelf_Clip_Gap])
        shelf.dim_y('-Depth+IF(Is_Locked_Shelf,Locked_Shelf_Setback,Adj_Shelf_Setback)',[Depth,Is_Locked_Shelf,Locked_Shelf_Setback,Adj_Shelf_Setback])
        shelf.dim_z('IF(AND(TAS,IBEKD==False), INCH(1),Shelf_Thickness)', [Shelf_Thickness, TAS, IBEKD])
        shelf.get_prompt('Is Locked Shelf').set_formula('IF(Shelf_Type==1,True,False)',[Shelf_Type])
        shelf.get_prompt('Z Quantity').set_formula('Shelf_Quantity',[Shelf_Quantity])
        shelf.get_prompt('Z Offset').set_formula('Shelf_Spacing',[Shelf_Spacing])
        shelf.get_prompt('Hide').set_formula('IF(Shelf_Type==2,True,False)',[Shelf_Type])

        sliding_shelf = common_parts.add_sliding_shelf(self)
        sliding_shelf.loc_x('IF(Shelf_Type==2,Drawer_Slide_Gap,IF(Is_Locked_Shelf,0,Adj_Shelf_Clip_Gap))',[Shelf_Type,Drawer_Slide_Gap,Is_Locked_Shelf,Adj_Shelf_Clip_Gap])
        sliding_shelf.loc_y('Depth',[Depth])
        sliding_shelf.dim_x('Width-IF(Shelf_Type==2,Drawer_Slide_Gap*2,IF(Is_Locked_Shelf,0,Adj_Shelf_Clip_Gap*2))',[Width,Shelf_Type,Drawer_Slide_Gap,Is_Locked_Shelf,Adj_Shelf_Clip_Gap])
        sliding_shelf.dim_y('-Depth+IF(Is_Locked_Shelf,Locked_Shelf_Setback,Adj_Shelf_Setback)',[Depth,Is_Locked_Shelf,Locked_Shelf_Setback,Adj_Shelf_Setback])
        sliding_shelf.dim_z('Shelf_Thickness',[Shelf_Thickness])
        sliding_shelf.get_prompt('Is Locked Shelf').set_formula('IF(Shelf_Type==1,True,False)',[Shelf_Type])
        sliding_shelf.get_prompt('Z Quantity').set_formula('Shelf_Quantity',[Shelf_Quantity])
        sliding_shelf.get_prompt('Z Offset').set_formula('Shelf_Spacing',[Shelf_Spacing])        
        sliding_shelf.get_prompt('Hide').set_formula('IF(Shelf_Type==2,False,True)',[Shelf_Type])
        
        self.update()


# class Tray(sn_types.Assembly):
    
    # type_assembly = 'INSERT'
    # mirror_y = False
    # property_id = "sn_closets.tray"
    # drop_id = "sn_closets.place_single_part"
    
    # hanging_rod_qty = 1
    
    # def draw(self):
    #     self.create_assembly()

    #     self.add_prompt("Tray Height", 'DISTANCE', sn_unit.inch(3))
    #     self.add_prompt("Drawer Slide Gap", 'DISTANCE', sn_unit.inch(.25))
        
    #     common_prompts.add_thickness_prompts(self)
        
    #     Width = self.obj_x.snap.get_var('location.x', 'Width')
    #     Depth = self.obj_y.snap.get_var('location.y', 'Depth')
    #     Tray_Height = self.get_var('Tray Height')
    #     Drawer_Slide_Gap = self.get_var('Drawer Slide Gap')

    #     tray = common_parts.add_drawer(self)
    #     tray.loc_x('Drawer_Slide_Gap',[Drawer_Slide_Gap])
    #     tray.loc_y(value = 0)
    #     tray.loc_z(value = 0)
    #     tray.rot_x(value = 0)
    #     tray.rot_y(value = 0)
    #     tray.rot_z(value = 0)
    #     tray.dim_x('Width-Drawer_Slide_Gap*2',[Width,Drawer_Slide_Gap])
    #     tray.dim_y('Depth',[Depth])
    #     tray.dim_z('Tray_Height',[Tray_Height])
        
    #     self.update()


class Accessory(sn_types.Assembly):

    id_prompt = "sn_closets.accessory"
    drop_id = "sn_closets.place_closet_accessory"
    show_in_library = True
    placement_type = "INTERIOR"
    type_assembly = "INSERT"
    mirror_y = False

    library_name = ""
    category_name = ""
    accessory_name = ""
    object_path = ""

    def update(self):
        super().update()
        self.obj_bp.sn_closets.is_accessory_bp = True

    def draw(self):
        self.create_assembly()
        accessory = self.add_object_from_file(self.object_path)
        accessory.snap.name_object = self.accessory_name
        accessory.snap.loc_x(value=sn_unit.inch(12))
        # accessory.material("Chrome")

        self.update()


class Valet_Rod(sn_types.Assembly):

    id_prompt = "sn_closets.valet_rod"
    drop_id = "sn_closets.place_valet_rod"
    show_in_library = True
    placement_type = "INTERIOR"
    type_assembly = "INSERT"
    mirror_y = False

    library_name = ""
    category_name = ""
    accessory_name = ""
    object_path = ""

    def update(self):
        super().update()
        self.obj_bp.sn_closets.is_accessory_bp = True
        self.obj_bp['IS_BP_VALET_ROD'] = True

    def draw(self):
        self.create_assembly()

        self.add_prompt('Valet Category', 'COMBOBOX', 0, ['Synergy', 'Elite'])
        self.add_prompt('Metal Color', 'COMBOBOX', 0, ['Chrome', 'Matte Aluminum', 'Matte Nickel', 'Matte Gold', 'ORB', 'Slate'])
        self.add_prompt('Valet Length', 'COMBOBOX', 0, ['12"', '14"'])

        Valet_Length = self.get_prompt("Valet Length").get_var("Valet_Length")


        # valet_rod = self.add_assembly_from_file(self.object_path)
        valet_rod = sn_types.Part(self.add_assembly_from_file(self.object_path))
        self.add_assembly(valet_rod)
        # valet_rod.create_assembly()
        valet_rod.set_name(self.accessory_name)
        valet_rod.loc_x('IF(Valet_Length==0, INCH(12), INCH(14))', [Valet_Length])
        valet_rod.dim_x('IF(Valet_Length==0, INCH(12), INCH(14))* -1', [Valet_Length])

        self.update()


class Slanted_Shoe_Shelves(sn_types.Assembly):

    id_prompt = "sn_closets.shoe_shelf_prompt"
    drop_id = "sn_closets.place_single_part"
    show_in_library = True
    placement_type = "INTERIOR"
    type_assembly = "INSERT"
    mirror_y = False

    library_name = ""
    category_name = ""

    def add_shoe_shelf_prompts(self):
        defaults = bpy.context.scene.sn_closets.closet_defaults

        shelf_lip_type = self.add_prompt("Shelf Lip Type", 'COMBOBOX',  0, ["Wood Toe", "Deco 1", "Deco 2", "Deco 3", "Steel Fence"])
        shelf_lip_type.combobox_columns = 3
        self.add_prompt("Adj Shelf Qty",'QUANTITY', 1)
        self.add_prompt("Shelf Clip Gap", 'DISTANCE', defaults.adj_shelf_clip_gap)
        self.add_prompt("Shelf Angle", 'ANGLE', 17.25)
        self.add_prompt("Space From Bottom", 'DISTANCE', sn_unit.inch(3.5))
        self.add_prompt("Space From Top", 'DISTANCE', sn_unit.inch(8))
        self.add_prompt("Shelf Lip Width", 'DISTANCE', defaults.shelf_lip_width)
        self.add_prompt("Distance Between Shelves", 'DISTANCE', sn_unit.inch(8))
        ppt_obj_shelf_setback = self.add_prompt_obj("Shelf_Setback")
        self.add_prompt("Adj Shelf Setback", 'DISTANCE', sn_unit.inch(1), prompt_obj=ppt_obj_shelf_setback)
        self.add_prompt("Adjustable Shelf Thickness", 'DISTANCE', sn_unit.inch(.75))

        Shelf_Lip_Type = self.get_prompt("Shelf Lip Type").get_var()

        self.get_prompt('Adj Shelf Setback').set_formula('IF(Shelf_Lip_Type==4,0,INCH(.75))', [Shelf_Lip_Type])

    def draw_shoe_shelves(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Adj_Shelf_Qty = self.get_prompt("Adj Shelf Qty").get_var()
        Adj_Shelf_Setback = self.get_prompt("Adj Shelf Setback").get_var()
        Adjustable_Shelf_Thickness = self.get_prompt("Adjustable Shelf Thickness").get_var()
        Shelf_Clip_Gap = self.get_prompt("Shelf Clip Gap").get_var()
        Shelf_Angle = self.get_prompt("Shelf Angle").get_var()
        Shelf_Lip_Type = self.get_prompt("Shelf Lip Type").get_var()
        Space_From_Bottom = self.get_prompt("Space From Bottom").get_var()
        Distance_Between_Shelves = self.get_prompt("Distance Between Shelves").get_var()
        Shelf_Lip_Width = self.get_prompt("Shelf Lip Width").get_var()

        for i in range(1, 11):
            adj_shelf = common_parts.add_slanted_shoe_shelf(self)
            adj_shelf.loc_x('Shelf_Clip_Gap', [Shelf_Clip_Gap])
            adj_shelf.loc_y('Depth', [Depth])
            if i == 1:
                adj_shelf.loc_z('Space_From_Bottom', [Space_From_Bottom])
            else:
                adj_shelf.loc_z(
                    'Space_From_Bottom+(Distance_Between_Shelves*' + str(i - 1) + ')',
                    [Space_From_Bottom, Adjustable_Shelf_Thickness, Distance_Between_Shelves])
            adj_shelf.rot_x('Shelf_Angle', [Shelf_Angle])
            adj_shelf.dim_x('Width-(Shelf_Clip_Gap*2)', [Width, Shelf_Clip_Gap])
            adj_shelf.dim_y('-Depth+Adj_Shelf_Setback', [Depth, Adj_Shelf_Setback])
            adj_shelf.dim_z('Adjustable_Shelf_Thickness', [Adjustable_Shelf_Thickness])
            adj_shelf.get_prompt('Hide').set_formula('IF(' + str(i) + '>Adj_Shelf_Qty,True,False)',  [Adj_Shelf_Qty])
            
            Z_Loc = adj_shelf.obj_bp.snap.get_var('location.z', 'Z_Loc')
            Shelf_Depth = adj_shelf.obj_y.snap.get_var('location.y', 'Shelf_Depth')

            shelf_lip = common_parts.add_shelf_lip(self)
            shelf_lip.loc_x('Shelf_Clip_Gap', [Shelf_Clip_Gap])
            shelf_lip.loc_y('fabs(Depth)-(fabs(Shelf_Depth)*cos(Shelf_Angle))', [Depth, Shelf_Depth, Shelf_Angle])
            shelf_lip.loc_z('Z_Loc-(fabs(Shelf_Depth)*sin(Shelf_Angle))', [Z_Loc, Shelf_Depth, Shelf_Angle])
            shelf_lip.rot_x('Shelf_Angle-radians(90)', [Shelf_Angle])
            shelf_lip.dim_x('Width-(Shelf_Clip_Gap*2)', [Width, Shelf_Clip_Gap])
            shelf_lip.dim_y('-Shelf_Lip_Width', [Shelf_Lip_Width])
            shelf_lip.dim_z('-Adjustable_Shelf_Thickness', [Adjustable_Shelf_Thickness])
            shelf_lip.get_prompt('Hide').set_formula(
                'IF(' + str(i) + '>Adj_Shelf_Qty,True,IF(Shelf_Lip_Type==0,False,True))', 
                [Shelf_Lip_Type, Adj_Shelf_Qty])
            
            deco_1_shelf_lip = common_parts.add_deco_shelf_lip_1(self)
            deco_1_shelf_lip.loc_x('Shelf_Clip_Gap', [Shelf_Clip_Gap])
            deco_1_shelf_lip.loc_y(
                'fabs(Depth)-(fabs(Shelf_Depth)*cos(Shelf_Angle))', [Depth, Shelf_Depth, Shelf_Angle])
            deco_1_shelf_lip.loc_z('Z_Loc-(fabs(Shelf_Depth)*sin(Shelf_Angle))', [Z_Loc, Shelf_Depth, Shelf_Angle])
            deco_1_shelf_lip.rot_x('Shelf_Angle-radians(90)', [Shelf_Angle])
            deco_1_shelf_lip.dim_x('Width-(Shelf_Clip_Gap*2)', [Width, Shelf_Clip_Gap])
            deco_1_shelf_lip.dim_y('-Shelf_Lip_Width',[Shelf_Lip_Width])
            deco_1_shelf_lip.dim_z('-Adjustable_Shelf_Thickness', [Adjustable_Shelf_Thickness])
            deco_1_shelf_lip.get_prompt('Hide').set_formula(
                'IF(' + str(i) + '>Adj_Shelf_Qty,True,IF(Shelf_Lip_Type==1,False,True))', 
                [Shelf_Lip_Type, Adj_Shelf_Qty])

            deco_2_shelf_lip = common_parts.add_deco_shelf_lip_2(self)
            deco_2_shelf_lip.loc_x('Shelf_Clip_Gap', [Shelf_Clip_Gap])
            deco_2_shelf_lip.loc_y(
                'fabs(Depth)-(fabs(Shelf_Depth)*cos(Shelf_Angle))', [Depth, Shelf_Depth, Shelf_Angle])
            deco_2_shelf_lip.loc_z('Z_Loc-(fabs(Shelf_Depth)*sin(Shelf_Angle))', [Z_Loc, Shelf_Depth, Shelf_Angle])
            deco_2_shelf_lip.rot_x('Shelf_Angle-radians(90)', [Shelf_Angle])
            deco_2_shelf_lip.dim_x('Width-(Shelf_Clip_Gap*2)', [Width, Shelf_Clip_Gap])
            deco_2_shelf_lip.dim_y('-Shelf_Lip_Width', [Shelf_Lip_Width])
            deco_2_shelf_lip.dim_z('-Adjustable_Shelf_Thickness', [Adjustable_Shelf_Thickness])
            deco_2_shelf_lip.get_prompt('Hide').set_formula(
                'IF(' + str(i) + '>Adj_Shelf_Qty,True,IF(Shelf_Lip_Type==2,False,True))', 
                [Shelf_Lip_Type, Adj_Shelf_Qty])
            
            deco_3_shelf_lip = common_parts.add_deco_shelf_lip_3(self)
            deco_3_shelf_lip.loc_x('Shelf_Clip_Gap',[Shelf_Clip_Gap])
            deco_3_shelf_lip.loc_y(
                'fabs(Depth)-(fabs(Shelf_Depth)*cos(Shelf_Angle))', [Depth, Shelf_Depth, Shelf_Angle])
            deco_3_shelf_lip.loc_z('Z_Loc-(fabs(Shelf_Depth)*sin(Shelf_Angle))', [Z_Loc, Shelf_Depth, Shelf_Angle])
            deco_3_shelf_lip.rot_x('Shelf_Angle-radians(90)', [Shelf_Angle])
            deco_3_shelf_lip.dim_x('Width-(Shelf_Clip_Gap*2)', [Width, Shelf_Clip_Gap])
            deco_3_shelf_lip.dim_y('-Shelf_Lip_Width', [Shelf_Lip_Width])
            deco_3_shelf_lip.dim_z('-Adjustable_Shelf_Thickness', [Adjustable_Shelf_Thickness])
            deco_3_shelf_lip.get_prompt('Hide').set_formula(
                'IF(' + str(i) + '>Adj_Shelf_Qty,True,IF(Shelf_Lip_Type==3,False,True))', 
                [Shelf_Lip_Type, Adj_Shelf_Qty])
            
            steel_fence = common_parts.add_shelf_fence(self)
            steel_fence.loc_x('Shelf_Clip_Gap+INCH(1)', [Shelf_Clip_Gap])
            steel_fence.loc_y(
                'fabs(Depth)-(fabs(Shelf_Depth+INCH(1))*cos(Shelf_Angle))', [Depth, Shelf_Depth, Shelf_Angle])
            steel_fence.loc_z(
                'Z_Loc-(fabs(Shelf_Depth+INCH(1))*sin(Shelf_Angle))', [Z_Loc, Shelf_Depth, Shelf_Angle])
            steel_fence.rot_x('Shelf_Angle+radians(90)', [Shelf_Angle])
            steel_fence.dim_x('Width-(Shelf_Clip_Gap*2)-INCH(2)', [Width, Shelf_Clip_Gap])
            steel_fence.dim_y('-Shelf_Lip_Width', [Shelf_Lip_Width])
            steel_fence.dim_z('-Adjustable_Shelf_Thickness', [Adjustable_Shelf_Thickness])
            steel_fence.get_prompt('Hide').set_formula(
                'IF(' + str(i) + '>Adj_Shelf_Qty,True,IF(Shelf_Lip_Type==4,False,True))', 
                [Shelf_Lip_Type, Adj_Shelf_Qty])

    def update(self):
        super().update()

        self.obj_bp["ID_PROMPT"] = self.id_prompt
        self.obj_bp["ID_DROP"] = self.drop_id                

    def draw(self):
        self.create_assembly()
        self.add_shoe_shelf_prompts()
        self.draw_shoe_shelves()
        self.update()
        
#----------PROMPTS PAGES
class PROMPTS_Single_Hanging_Rod_Prompts(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.single_hanging_rod_prompts"
    bl_label = "Single Hanging Rod Prompts" 
    bl_description = "This shows all of the available door options"
    bl_options = {'UNDO'}
    
    object_name: bpy.props.StringProperty(name="Object Name")

    top_rod_location: bpy.props.EnumProperty(name="Top Rod Location",
                                              items=common_lists.ROD_HEIGHTS)

    assembly = None

    def check(self, context):
        self.set_prompts_from_properties()
        self.insert.obj_bp.location = self.insert.obj_bp.location  # Redraw Viewport
        return True

    def set_prompts_from_properties(self):
        ''' This should be called in the check function to set the prompts
            to the same values as the class properties
        '''
        top_rod_location = self.insert.get_prompt("Top Rod Location")
        if top_rod_location:
            top_rod_location.set_value(sn_unit.inch(
                float(self.top_rod_location) / 25.4))

    def set_properties_from_prompts(self):
        ''' This should be called in the invoke function to set the class properties
            to the same values as the prompts
        '''
        top_rod_location = self.insert.get_prompt("Top Rod Location")
        if top_rod_location:
            value = round(top_rod_location.get_value() * 1000, 2)
            for index, height in enumerate(common_lists.ROD_HEIGHTS):
                if not value >= float(height[0]):
                    self.top_rod_location = common_lists.ROD_HEIGHTS[index - 1][0]
                    break

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        self.insert = Hanging_Rod(self.get_insert().obj_bp)
        self.set_properties_from_prompts()
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)

    def draw(self, context):
        layout = self.layout
        if self.insert.obj_bp:
            if self.insert.obj_bp.name in context.scene.objects:
                add_top_rod = self.insert.get_prompt("Add Top Rod")
                add_middle_rod = self.insert.get_prompt("Add Middle Rod")
                rod_setback = self.insert.get_prompt("Hanging Rod Setback")
                Add_Rod_Setback = self.insert.get_prompt("Add Rod Setback")
                extra_deep_pard = self.insert.get_prompt("Extra Deep Pard")
                Add_Deep_Rod_Setback = self.insert.get_prompt(
                    "Add Deep Rod Setback")

                if add_top_rod and add_middle_rod:
                    column = layout.column(align=True)

                    # Top
                    box = column.box()
                    row = box.row()
                    row.label(text="", icon='BLANK1')
                    row.prop(add_top_rod, "checkbox_value", text="Rod at Top")


                    row = box.row()
                    row.label(text="", icon='BLANK1')
                    row.prop(self, 'top_rod_location', text="")
                    row.label(text="", icon='TRIA_DOWN')

                    row = box.row()
                    if(extra_deep_pard and self.insert.obj_y.location.y >= extra_deep_pard.get_value()):
                            row = box.row()
                            row.label(text="", icon='BLANK1')
                            row.prop(Add_Deep_Rod_Setback, "distance_value", text="Rod Setback: ")
                    else:
                        row = box.row()
                        row.label(text="", icon='BLANK1')
                        row.prop(Add_Rod_Setback, "distance_value", text="Rod Setback: ")



class PROMPTS_Pants_Rack_Prompts(bpy.types.Operator):
    bl_idname = "sn_closets.single_pants_racks"
    bl_label = "Pants Rack Prompts" 
    bl_description = "This shows all of the available pants rack options"
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")
    
    assembly = None
    
    @classmethod
    def poll(cls, context):
        return True
        
    def check(self, context):
        return True
        
    def execute(self, context):
        return {'FINISHED'}
        
    def invoke(self,context,event):
        obj = bpy.data.objects[self.object_name]
        obj_insert_bp = sn_utils.get_bp(obj,'INSERT')
        self.assembly = sn_types.Assembly(obj_insert_bp)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)
        
    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                row = layout.row()
                row.label(text="Pants Rack Location")
                row.prop(self.assembly.obj_bp,'location',index=2,text="")


class PROMPTS_Accessory_Prompts(bpy.types.Operator):
    bl_idname = "sn_closets.accessory"
    bl_label = "Accessory Prompts" 
    bl_description = "This shows all of the available accessory options"
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")
    
    assembly = None
    
    @classmethod
    def poll(cls, context):
        return True
        
    def check(self, context):
        return True
        
    def execute(self, context):
        return {'FINISHED'}
        
    def invoke(self,context,event):
        obj = bpy.data.objects[self.object_name]
        obj_insert_bp = sn_utils.get_bp(obj,'INSERT')
        self.assembly = sn_types.Assembly(obj_insert_bp)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)
        
    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                row = layout.row()
                row.label(text="Accessory Location")
                row.prop(self.assembly.obj_bp,'location',index=2,text="")


class PROMPTS_Valet_Rod_Prompts(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.valet_rod"
    bl_label = "Valet Rod Prompts"
    bl_description = "This shows all of the available valet rod options"
    bl_options = {'UNDO'}

    object_name: StringProperty(name="Object Name")

    valet_category: EnumProperty(
        name="Valet Category",
        items=[
            ('0', 'Synergy', 'Synergy'),
            ('1', 'Elite', 'Elite')],
        default='0')

    valet_length: EnumProperty(
        name="Valet Length",
        items=[
            ('0', '12"', '12"'),
            ('1', '14"', '14"')],
        default='0')
    
    metal_color: EnumProperty(
        name="Metal Color",
        items=[
            ('0', 'Chrome', 'Chrome'),
            ('1', 'Matte Aluminum', 'Matte Aluminum'),
            ('2', 'Matte Nickel', 'Matte Nickel'),
            ('3', 'Matte Gold', 'Matte Gold'),
            ('4', 'Orb', 'Orb'),
            ('5', 'Slate', 'Slate')],
        default='0')

    assembly = None

    @classmethod
    def poll(cls, context):
        return True

    def check(self, context):
        self.set_prompts_from_properties()
        closet_props.update_render_materials(self, context)
        return True

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        self.assembly = self.get_insert()
        self.set_properties_from_prompts()
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)

    def set_properties_from_prompts(self):
        valet_category = self.assembly.get_prompt("Valet Category")
        valet_length = self.assembly.get_prompt("Valet Length")
        metal_color = self.assembly.get_prompt("Metal Color")

        if valet_category:
            self.valet_category = str(valet_category.get_value())
        if valet_length:
            self.valet_length = str(valet_length.get_value())
        if metal_color:
            if valet_category.get_value() == 0:
                metal_color.set_value(0)
                self.metal_color = '0'
            else:
                self.metal_color = str(metal_color.get_value())

    def set_prompts_from_properties(self):
        valet_category = self.assembly.get_prompt("Valet Category")
        valet_length = self.assembly.get_prompt("Valet Length")
        metal_color = self.assembly.get_prompt("Metal Color")

        if valet_category:
            valet_category.set_value(int(self.valet_category))
        if valet_length:
            valet_length.set_value(int(self.valet_length))
        if metal_color:
            if valet_category.get_value() == 0:
                metal_color.set_value(0)
                self.metal_color = '0'
            else:
                metal_color.set_value(int(self.metal_color))

    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                valet_category = self.assembly.get_prompt("Valet Category")
                valet_length = self.assembly.get_prompt("Valet Length")
                metal_color = self.assembly.get_prompt("Metal Color")

                row = layout.row()
                row.label(text="Location")
                row.prop(self.assembly.obj_bp, 'location', index=0, text="")

                if valet_category:
                    row = layout.row()
                    row.label(text="Category")
                    row.prop(self, 'valet_category', expand=True)

                if valet_length:
                    row = layout.row()
                    row.label(text="Length")
                    row.prop(self, 'valet_length', expand=True)

                if valet_category:
                    if valet_category.get_value() == 1:
                        if metal_color:
                            row = layout.row()
                            row.label(text="Metal Color")
                            row.prop(self, 'metal_color', text='')


class PROMPTS_Single_Hamper_Prompts(bpy.types.Operator):
    bl_idname = "sn_closets.single_hamper"
    bl_label = "Single Hamper Prompts" 
    bl_description = "This shows all of the available hamper options"
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")
    
    assembly = None
    
    @classmethod
    def poll(cls, context):
        return True
        
    def check(self, context):
        return True
        
    def execute(self, context):
        return {'FINISHED'}
        
    def invoke(self,context,event):
        obj = bpy.data.objects[self.object_name]
        obj_insert_bp = sn_utils.get_bp(obj,'INSERT')
        self.assembly = sn_types.Assembly(obj_insert_bp)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)
        
    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                row = layout.row()
                row.label(text="Hamper Location")
                row.prop(self.assembly.obj_bp,'location',index=2,text="")


class PROMPTS_Shelf_Prompts(bpy.types.Operator):
    bl_idname = "sn_closets.shelf"
    bl_label = "Shelf Prompts" 
    bl_description = "This shows all of the available shelf options"
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")
    
    assembly = None
    
    shelf = None
    
    @classmethod
    def poll(cls, context):
        return True
        
    def check(self, context):
        return True
        
    def execute(self, context):
        return {'FINISHED'}
        
    def invoke(self,context,event):
        obj = bpy.data.objects[self.object_name]
        obj_insert_bp = sn_utils.get_bp(obj,'INSERT')
        obj_bp = sn_utils.get_assembly_bp(obj)
        self.assembly = sn_types.Assembly(obj_insert_bp)
        self.shelf = sn_types.Assembly(obj_bp)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)
        
    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                row = layout.row()
                row.label(text="Shelf Location")
                row.prop(self.assembly.obj_bp,'location',index=2,text="")
                shelf_type = self.assembly.get_prompt("Shelf Type")
                shelf_quantity = self.assembly.get_prompt("Shelf Quantity")
                shelf_spacing = self.assembly.get_prompt("Shelf Spacing")
                
                row = layout.row()
                shelf_type.draw(row)

                row = layout.row()
                shelf_quantity.draw(row)
                
                row = layout.row()
                shelf_spacing.draw(row)     


class PROMPTS_Tray_Prompts(bpy.types.Operator):
    bl_idname = "sn_closets.tray"
    bl_label = "Tray Prompts" 
    bl_description = "This shows all of the available tray options"
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")
    
    assembly = None
    
    tray = None
    
    @classmethod
    def poll(cls, context):
        return True
        
    def check(self, context):
        return True
        
    def execute(self, context):
        return {'FINISHED'}
        
    def invoke(self,context,event):
        obj = bpy.data.objects[self.object_name]
        obj_insert_bp = sn_utils.get_bp(obj,'INSERT')
        obj_bp = sn_utils.get_assembly_bp(obj)
        self.assembly = sn_types.Assembly(obj_insert_bp)
        self.tray = sn_types.Assembly(obj_bp)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)
        
    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                row = layout.row()
                row.label(text="Tray Location")
                row.prop(self.assembly.obj_bp,'location',index=2,text="")
                tray_height = self.assembly.get_prompt("Tray Height")
                row = layout.row()
                tray_height.draw(row)


class PROMPTS_Wire_Baskets_Prompts(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.wire_baskets"
    bl_label = "Wire Baskets Prompts" 
    bl_description = "This shows all of the available wire_basket options"
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")
    
    assembly = None
    
    @classmethod
    def poll(cls, context):
        return True
        
    def check(self, context):
        return True
        
    def execute(self, context):
        return {'FINISHED'}
        
    def invoke(self,context,event):
        self.assembly = self.get_insert()
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)
        
    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                basket_qty = self.assembly.get_prompt("Baskets Qty")
                box = layout.box()
                basket_qty.draw(box, allow_edit=False)
                
                for i in reversed(range(1,6)):
                    if basket_qty.get_value() >= i:
                        basket_height = self.assembly.get_prompt("Basket Height " + str(i))
                        basket_height.draw(box, allow_edit=False)
                    
                dist_between_baskets = self.assembly.get_prompt("Distance Between Baskets")
                dist_between_baskets.draw(box, allow_edit=False)
                
                row = box.row()
                row.label(text="Basket Location")
                row.prop(self.assembly.obj_bp, 'location', index=2, text="")


class PROMPTS_Shoe_Shelf_Prompts(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.shoe_shelf_prompt"
    bl_label = "Shoe Shelf Prompt" 
    bl_description = "This shows all of the available shoe shelf options"
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")
    shelf_qty: IntProperty(name="Shelf Quantity",min=1,max=10)
    shelf_lip_type: EnumProperty(
        name="Shelf Lip Type",
        items=[
                ('0', 'Wood Toe', 'Wood Toe'),
                ('1', 'Deco 1', 'Deco 1'),
                ('2', 'Deco 2', 'Deco 2'),
                ('3', 'Deco 3', 'Deco 3'),
                ('4', 'Steel Fence', 'Steel Fence')],
            default='0')
    adj_shelf_qty_prompt = None
    assembly = None
    shelf_lip_type_prompt = None
        
    def check(self, context):
        # sn_utils.run_calculators(self.assembly.obj_bp)
        
        if self.adj_shelf_qty_prompt:
            self.adj_shelf_qty_prompt.set_value(self.shelf_qty)

        if self.shelf_lip_type_prompt:
            self.shelf_lip_type_prompt.set_value(int(self.shelf_lip_type))
            
        self.assembly.obj_bp.location = self.assembly.obj_bp.location # Redraw Viewport
        
        return True
        
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self,context,event):
        self.assembly = self.get_insert()
        
        self.adj_shelf_qty_prompt = self.assembly.get_prompt("Adj Shelf Qty")
        self.shelf_lip_type_prompt = self.assembly.get_prompt("Shelf Lip Type")

        if self.adj_shelf_qty_prompt:
            self.shelf_qty = self.adj_shelf_qty_prompt.get_value()

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=330)
        
    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                
                if self.adj_shelf_qty_prompt:
                    shelf_lip_type = self.assembly.get_prompt("Shelf Lip Type")
                    dist_between_shelves = self.assembly.get_prompt("Distance Between Shelves")

                    box = layout.box()
                    row = box.row()
                    row.label(text="Adjustable Shelf Options:")
                    
                    row = box.row()
                    row.prop(self, "shelf_lip_type", expand=True)

                    row = box.row()
                    row.label(text="Shelf Quantity")
                    row.prop(self,'shelf_qty',text="")
                    
                    row = box.row()
                    row.label(text="Shoe Shelf Location")
                    row.prop(self.assembly.obj_bp,'location',index=2)

                    row = box.row()
                    dist_between_shelves.draw(row, allow_edit=False)                        

#----------DROP OPERATORS
class OPERATOR_Drop_Single_Part(bpy.types.Operator, PlaceClosetInsert):
    """ This will be called when you drop a hanging rod into the scene
    """
    bl_idname = "sn_closets.place_single_part"
    bl_label = "Place Single Part"
    bl_description = "This will allow the user to place a hanging rod into the scene"

    object_name: StringProperty(name="Object Name")

    product_name: StringProperty(name="Product Name")
    category_name: StringProperty(name="Category Name")
    library_name: StringProperty(name="Library Name")
    filepath: StringProperty(name="Filepath") #MAYBE DONT NEED THIS?

    insert = None
    default_z_loc = 0.0
    default_height = 0.0
    default_depth = 0.0
    
    openings = []
    objects = []
    
    def execute(self, context):
        return super().execute(context)

    def get_32mm_position(self,selected_point):
        number_of_holes =  math.floor((selected_point / sn_unit.millimeter(32)))
        return number_of_holes * sn_unit.millimeter(32)
            
    def set_opening_name(self,obj,name):
        obj.sn_closets.opening_name = name
        for child in obj.children:
            self.set_opening_name(child, name)
        
    def confirm_placement(self, context):
        super().confirm_placement(context)

        if self.selected_opening:
            loc_pos = self.selected_opening.obj_bp.matrix_world.inverted() @ self.selected_point
            loc_z = self.get_32mm_position(loc_pos[2]) + self.selected_opening.obj_bp.location.z
            
            height = self.insert.obj_z.location.z
            sn_utils.copy_assembly_drivers(self.selected_opening, self.insert)
            self.insert.obj_bp.driver_remove('location', 2)
            self.insert.obj_z.driver_remove('location', 2)
            self.insert.obj_bp.location.z = loc_z
            self.insert.obj_z.location.z = height
            self.selected_opening.obj_bp.snap.interior_open = True
            self.selected_opening.obj_bp.snap.exterior_open = True            

    def position_asset(self, context):
        super().position_asset(context)

        if self.selected_obj and self.selected_opening:
            if self.selected_opening.obj_bp.parent:
                if self.insert.obj_bp.parent is not self.selected_opening.obj_bp.parent:
                    self.insert.obj_bp.matrix_world = self.selected_opening.obj_bp.matrix_world
                    loc_pos = self.selected_opening.obj_bp.matrix_world.inverted() @ self.selected_point
                    loc_z = self.get_32mm_position(loc_pos[2])     
                    self.insert.obj_bp.location.z += loc_z

            edp = self.insert.get_prompt("Extra Deep Pard")
            adrs = self.insert.get_prompt("Add Deep Rod Setback")
            
            if edp and adrs:
                if self.insert.obj_y.location.y >= edp.get_value():
                    adrs.set_value(self.insert.obj_y.location.y - sn_unit.inch(12))

class OPERATOR_Place_Panel_Accessory_Y(bpy.types.Operator):
    bl_idname = "sn_closets.place_panel_accessory_y"
    bl_label = "Place Panel Accessory Y"
    bl_description = "This allows you to place an accessory object into the scene."
    bl_options = {'UNDO'}
    
    #READONLY
    object_name: StringProperty(name="Object Name")
    
    product = None
    
    def invoke(self, context, event):
        bp = bpy.data.objects[self.object_name]
        self.product = sn_types.Assembly(bp)
        context.window.cursor_set('PAINT_BRUSH')
        context.scene.update() # THE SCENE MUST BE UPDATED FOR RAY CAST TO WORK
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def get_rotation(self,obj,prev_rotation):
        rotation = obj.rotation_euler.z + prev_rotation
        if obj.parent:
            return self.get_rotation(obj.parent, rotation)
        else:
            return rotation

    def cancel_drop(self,context,event):
        if self.product:
            sn_utils.delete_object_and_children(self.product.obj_bp)
        bpy.context.window.cursor_set('DEFAULT')
        return {'FINISHED'}

    def accessory_drop(self,context,event):
        selected_point, selected_obj, _ = sn_utils.get_selection_point(context,event)
        bpy.ops.object.select_all(action='DESELECT')
        selected_assembly = None
        
        self.product.obj_bp.location = selected_point
        self.product.obj_bp.parent = None
        
        if selected_obj:
            wall_bp = sn_utils.get_wall_bp(selected_obj)
            selected_assembly_bp = sn_utils.get_assembly_bp(selected_obj)
            selected_assembly = sn_types.Assembly(selected_assembly_bp)
            
            assembly_props = selected_assembly.obj_bp.sn_closets
            
            if wall_bp:
                self.product.obj_bp.rotation_euler.z = wall_bp.rotation_euler.z
                self.product.obj_bp.rotation_euler.y = 0
                self.product.obj_bp.rotation_euler.x = 0
                
            if selected_assembly and selected_assembly.obj_bp and assembly_props.is_panel_bp:
                
                ass_world_loc = (selected_assembly.obj_bp.matrix_world[0][3],
                                 selected_assembly.obj_bp.matrix_world[1][3],
                                 selected_assembly.obj_bp.matrix_world[2][3])
                
                ass_z_world_loc = (selected_assembly.obj_z.matrix_world[0][3],
                                   selected_assembly.obj_z.matrix_world[1][3],
                                   selected_assembly.obj_z.matrix_world[2][3])                
                
                dist_to_bp = math.fabs(sn_utils.calc_distance(selected_point,ass_world_loc))
                dist_to_z = math.fabs(sn_utils.calc_distance(selected_point,ass_z_world_loc))

                loc_pos = selected_assembly.obj_bp.matrix_world.inverted() * selected_point

                self.product.obj_bp.parent = selected_assembly.obj_bp
                
                self.product.obj_bp.location.x = loc_pos[0]
                
                self.product.obj_bp.location.z = 0
                
                self.product.obj_x.location.x = math.fabs(selected_assembly.obj_y.location.y) #SET DEPTH
                
                if selected_assembly.obj_z.location.z < 0: #LEFT PANEL
                    if dist_to_bp > dist_to_z:#PLACE ON RIGHT SIDE
                        self.product.obj_bp.location.y = selected_assembly.obj_y.location.y
                        self.product.obj_bp.rotation_euler.x = math.radians(90)
                        self.product.obj_bp.rotation_euler.y = math.radians(0)
                        self.product.obj_bp.rotation_euler.z = math.radians(90)   
                        self.product.obj_bp.location.z = selected_assembly.obj_z.location.z                     
                    else:#PLACE ON LEFT SIDE
                        self.product.obj_bp.location.y = 0
                        self.product.obj_bp.rotation_euler.x = math.radians(90)
                        self.product.obj_bp.rotation_euler.y = math.radians(180)
                        self.product.obj_bp.rotation_euler.z = math.radians(90)   
                        self.product.obj_bp.location.z = 0
                else: # CENTER AND RIGHT PANEL
                    if dist_to_bp > dist_to_z:#PLACE ON LEFT SIDE
                        self.product.obj_bp.location.y = 0
                        self.product.obj_bp.rotation_euler.x = math.radians(90)
                        self.product.obj_bp.rotation_euler.y = math.radians(180)
                        self.product.obj_bp.rotation_euler.z = math.radians(90) 
                        self.product.obj_bp.location.z = selected_assembly.obj_z.location.z                       
                    else:#PLACE ON RIGHT SIDE
                        self.product.obj_bp.location.y = selected_assembly.obj_y.location.y
                        self.product.obj_bp.rotation_euler.x = math.radians(90)
                        self.product.obj_bp.rotation_euler.y = math.radians(0)
                        self.product.obj_bp.rotation_euler.z = math.radians(90)
                        self.product.obj_bp.location.z = 0

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            bpy.context.window.cursor_set('DEFAULT')
            bpy.ops.object.select_all(action='DESELECT')
            sn_utils.set_wireframe(self.product.obj_bp,False)
            context.scene.objects.active = self.product.obj_bp
            self.product.obj_bp.select = True
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
        
        if event.type in {'ESC'}:
            self.cancel_drop(context,event)
            return {'FINISHED'}    
        
        return self.accessory_drop(context,event)


class OPERATOR_Place_Panel_Accessory_X(bpy.types.Operator, PlaceClosetInsert):
    bl_idname = "sn_closets.place_panel_accessory_x"
    bl_label = "Place Panel Accessory X"
    bl_description = "This allows you to place an accessory on a panel."
    bl_options = {'UNDO'}
    
    #READONLY
    object_name: StringProperty(name="Object Name")
    
    product = None

    def execute(self, context):
        self.product = self.asset
        return super().execute(context)        

    def get_rotation(self,obj,prev_rotation):
        rotation = obj.rotation_euler.z + prev_rotation
        if obj.parent:
            return self.get_rotation(obj.parent, rotation)
        else:
            return rotation

    def cancel_drop(self,context,event):
        if self.product:
            sn_utils.delete_object_and_children(self.product.obj_bp)
        bpy.context.window.cursor_set('DEFAULT')
        return {'FINISHED'}

    def accessory_drop(self,context,event):
        selected_point, selected_obj, _ = sn_utils.get_selection_point(context,event)
        bpy.ops.object.select_all(action='DESELECT')
        selected_assembly = None
        
        self.product.obj_bp.location = selected_point
        self.product.obj_bp.parent = None
        
        if selected_obj:
            wall_bp = sn_utils.get_wall_bp(selected_obj)
            selected_assembly_bp = sn_utils.get_assembly_bp(selected_obj)
            selected_assembly = sn_types.Assembly(selected_assembly_bp)
            
            if selected_assembly.obj_bp:
                assembly_props = selected_assembly.obj_bp.sn_closets
                
                if wall_bp:
                    self.product.obj_bp.rotation_euler.z = wall_bp.rotation_euler.z
                    self.product.obj_bp.rotation_euler.y = 0
                    self.product.obj_bp.rotation_euler.x = 0
                    
                if selected_assembly and selected_assembly.obj_bp and assembly_props.is_panel_bp:
                    
                    ass_world_loc = (selected_assembly.obj_bp.matrix_world[0][3],
                                     selected_assembly.obj_bp.matrix_world[1][3],
                                     selected_assembly.obj_bp.matrix_world[2][3])
                    
                    ass_z_world_loc = (selected_assembly.obj_z.matrix_world[0][3],
                                       selected_assembly.obj_z.matrix_world[1][3],
                                       selected_assembly.obj_z.matrix_world[2][3])                
                    
                    dist_to_bp = math.fabs(sn_utils.calc_distance(selected_point,ass_world_loc))
                    dist_to_z = math.fabs(sn_utils.calc_distance(selected_point,ass_z_world_loc))
                    loc_pos = selected_assembly.obj_bp.matrix_world.inverted() * selected_point
                    self.product.obj_bp.parent = selected_assembly.obj_bp
                    self.product.obj_bp.location.x = loc_pos[0]
                    self.product.obj_bp.location.z = 0
                    self.product.obj_x.location.x = math.fabs(selected_assembly.obj_y.location.y) #SET DEPTH
                    
                    if selected_assembly.obj_z.location.z < 0: #LEFT PANEL
                        if dist_to_bp > dist_to_z: #PLACE ON RIGHT SIDE
                            self.product.obj_bp.location.y = selected_assembly.obj_y.location.y + sn_unit.inch(12)
                            self.product.obj_bp.rotation_euler.x = math.radians(-90)
                            self.product.obj_bp.rotation_euler.y = math.radians(180)
                            self.product.obj_bp.rotation_euler.z = math.radians(90)   
                            self.product.obj_bp.location.z = selected_assembly.obj_z.location.z                     
                        else: #PLACE ON LEFT SIDE
                            self.product.obj_bp.location.y = selected_assembly.obj_y.location.y + sn_unit.inch(12)
                            self.product.obj_bp.rotation_euler.x = math.radians(90)
                            self.product.obj_bp.rotation_euler.y = math.radians(180)
                            self.product.obj_bp.rotation_euler.z = math.radians(90)   
                            self.product.obj_bp.location.z = 0
                    else: # CENTER AND RIGHT PANEL
                        if dist_to_bp > dist_to_z: #PLACE ON LEFT SIDE
                            self.product.obj_bp.location.y = selected_assembly.obj_y.location.y + sn_unit.inch(12)
                            self.product.obj_bp.rotation_euler.x = math.radians(90)
                            self.product.obj_bp.rotation_euler.y = math.radians(180)
                            self.product.obj_bp.rotation_euler.z = math.radians(90) 
                            self.product.obj_bp.location.z = selected_assembly.obj_z.location.z                       
                        else :#PLACE ON RIGHT SIDE
                            self.product.obj_bp.location.y = selected_assembly.obj_y.location.y + sn_unit.inch(12)
                            self.product.obj_bp.rotation_euler.x = math.radians(-90)
                            self.product.obj_bp.rotation_euler.y = math.radians(180)
                            self.product.obj_bp.rotation_euler.z = math.radians(90)
                            self.product.obj_bp.location.z = 0

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            bpy.context.window.cursor_set('DEFAULT')
            bpy.ops.object.select_all(action='DESELECT')
            sn_utils.set_wireframe(self.product.obj_bp,False)
            context.scene.objects.active = self.product.obj_bp
            self.product.obj_bp.select = True
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
        
        if event.type in {'ESC'}:
            self.cancel_drop(context,event)
            return {'FINISHED'}    
        
        return self.accessory_drop(context,event)

class OPERATOR_Place_Valet_Rod(bpy.types.Operator, PlaceClosetInsert):
    bl_idname = "sn_closets.place_valet_rod"
    bl_label = "Place Accessory"
    bl_description = "This allows you to place a Valet Rod onto a panel"

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

    def accessory_drop(self, context, event):
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
                            self.asset.obj_bp.location.y = 0
                            self.asset.obj_bp.rotation_euler.x = math.radians(90)
                            self.asset.obj_bp.rotation_euler.y = math.radians(0)
                            self.asset.obj_bp.rotation_euler.z = math.radians(270)
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
                            self.asset.obj_bp.location.y = 0
                            self.asset.obj_bp.rotation_euler.x = math.radians(90)
                            self.asset.obj_bp.rotation_euler.y = math.radians(0)
                            self.asset.obj_bp.rotation_euler.z = math.radians(270)
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

        return self.accessory_drop(context, event)


bpy.utils.register_class(PROMPTS_Pants_Rack_Prompts)
bpy.utils.register_class(PROMPTS_Single_Hanging_Rod_Prompts)
bpy.utils.register_class(PROMPTS_Single_Hamper_Prompts)
bpy.utils.register_class(PROMPTS_Shelf_Prompts)
bpy.utils.register_class(PROMPTS_Tray_Prompts)
bpy.utils.register_class(PROMPTS_Wire_Baskets_Prompts)
bpy.utils.register_class(PROMPTS_Accessory_Prompts)
bpy.utils.register_class(PROMPTS_Valet_Rod_Prompts)
bpy.utils.register_class(PROMPTS_Shoe_Shelf_Prompts)
bpy.utils.register_class(OPERATOR_Drop_Single_Part)
bpy.utils.register_class(OPERATOR_Place_Panel_Accessory_Y)
bpy.utils.register_class(OPERATOR_Place_Panel_Accessory_X)
bpy.utils.register_class(OPERATOR_Place_Valet_Rod)
