import math

import bpy
from bpy.types import Operator

import os
from snap import sn_types, sn_unit, sn_utils
from os import path

from snap.libraries.kitchen_bath import cabinet_interiors

from . import drawer_boxes
from . import cabinet_properties
from . import cabinet_pulls
from . import frameless_splitters
from snap.libraries.closets import closet_paths
from snap.libraries.closets.common import common_lists
from snap.views import opengl_dim
from snap.libraries.closets.ops.drop_closet import PlaceClosetInsert


LIBRARY_NAME_SPACE = "sn_kitchen_bath"
LIBRARY_NAME = "Cabinets"
INSERT_DOOR_CATEGORY_NAME = "Starter Inserts"
INSERT_DRAWER_CATEGORY_NAME = "Starter Inserts"


PART_WITH_FRONT_EDGEBANDING = path.join(closet_paths.get_closet_assemblies_path(), "Part with Front Edgebanding.blend")
DOOR = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")
DRAWER_FRONT = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")
BUYOUT_DRAWER_BOX = os.path.join(os.path.dirname(__file__),"assets","Kitchen Bath Assemblies","Buyout Drawer Box.blend")
DIVISION = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")


def get_hole_size(obj_height_meters):
    label = ""
    # print("get_hole_size.obj_height_meters = " + str(obj_height_meters))

    obj_height = str(round(math.fabs(sn_unit.meter_to_millimeter(obj_height_meters + sn_unit.inch(0.25)))))
    # print("get_hole_size.obj_height = " + obj_height)

    if obj_height in common_lists.HOLE_HEIGHTS.keys():
        label = common_lists.HOLE_HEIGHTS[obj_height]
    else: 
        tolerance = 20   # millimeter allowance for variable door overlay values
        for key, value in common_lists.HOLE_HEIGHTS.items():
            if abs(float(key) - float(obj_height)) <= tolerance:
                label = value
    # print("get_hole_size.label = " + label)
    return label

def add_door_height_dimension(door):
    Length = door.obj_x.snap.get_var('location.x','Length')
    Width = door.obj_y.snap.get_var('location.y','Width')
    
    dim = sn_types.Dimension()
    dim.anchor["DOOR_HOLE_LABEL"] = True
    dim.parent(door.obj_bp)
    dim.start_x("Length*0.6", [Length])
    dim.start_y("Width*0.5", [Width])
    dim.set_label("")

def add_drawer_height_dimension(drawer):
    Length = drawer.obj_x.snap.get_var('location.x','Length')
    Width = drawer.obj_y.snap.get_var('location.y','Width')

    dim = sn_types.Dimension()
    dim.anchor["DRAWER_HOLE_LABEL"] = True
    dim.parent(drawer.obj_bp)
    dim.start_x("Length*0.5+INCH(1.5)", [Length])
    dim.start_y("Width*0.5", [Width])
    dim.set_label("")

def update_dimensions(part):
    dimensions = []
    
    for child in part.obj_bp.children:
        if 'IS_DOOR' in child:
            for nchild in child.children:
                if 'DOOR_HOLE_LABEL' in nchild:
                    dimensions.append(nchild)
        elif 'IS_BP_DRAWER_FRONT' in child:
            for nchild in child.children:
                if 'DRAWER_HOLE_LABEL' in nchild:
                    dimensions.append(nchild)

    for anchor in dimensions:
        assembly = sn_types.Assembly(anchor.parent)
        height = assembly.obj_x.location.x
        anchor.snap.opengl_dim.gl_label = str(get_hole_size(height))


def add_common_door_prompts(assembly):
    props = cabinet_properties.get_scene_props().exterior_defaults
    door_location = 0

    if assembly.door_type == 'Base':
        door_location = 0
    elif assembly.door_type == 'Tall':
        door_location = 1
    else:
        door_location = 2

    assembly.add_prompt("Door Rotation", 'ANGLE', 0)
    assembly.add_prompt("Open Door", 'PERCENTAGE', 0)

    if assembly.door_swing in {"Left Swing", "Right Swing"}:
        assembly.add_prompt("Door Swing", 'COMBOBOX', 0, ['Left', 'Right'])
        ppt_obj_door_swing = assembly.add_prompt_obj("Backing_Config")
        use_left_swing = True if assembly.door_swing == 'Left Swing' else False
        assembly.add_prompt("Left Swing", 'CHECKBOX', use_left_swing, prompt_obj=ppt_obj_door_swing)
        assembly.add_prompt("Right Swing", 'CHECKBOX', False, prompt_obj=ppt_obj_door_swing)

        Door_Swing = assembly.get_prompt("Door Swing").get_var()
        assembly.get_prompt('Left Swing').set_formula('IF(Door_Swing==0,True,False)', [Door_Swing])
        assembly.get_prompt('Right Swing').set_formula('IF(Door_Swing==1,True,False)', [Door_Swing])

    assembly.add_prompt("Inset Front", 'CHECKBOX', props.inset_door)
    assembly.add_prompt("Inset Reveal", 'DISTANCE', props.inset_reveal)
    assembly.add_prompt("Door to Cabinet Gap", 'DISTANCE', props.door_to_cabinet_gap)
    assembly.add_prompt("No Pulls", 'CHECKBOX', props.no_pulls)
    assembly.add_prompt("Pull Rotation", 'ANGLE', props.pull_rotation)
    assembly.add_prompt("Pull From Edge", 'DISTANCE', props.pull_from_edge)
    assembly.add_prompt("Pull Location", 'COMBOBOX', door_location, ['Base', 'Tall', 'Upper'])
    assembly.add_prompt("Base Pull Location", 'DISTANCE', props.base_pull_location)
    assembly.add_prompt("Tall Pull Location", 'DISTANCE', props.tall_pull_location)
    assembly.add_prompt("Upper Pull Location", 'DISTANCE', props.upper_pull_location)
    assembly.add_prompt("Lock Door", 'CHECKBOX', False)
    assembly.add_prompt("Pull Length", 'DISTANCE', 0)
    assembly.add_prompt("Door Thickness", 'DISTANCE', sn_unit.inch(.75))
    assembly.add_prompt("Edgebanding Thickness", 'DISTANCE', sn_unit.inch(.02))
    assembly.get_prompt('Door Thickness').set_value(sn_unit.inch(0.75))

def add_common_drawer_prompts(assembly):
    props = cabinet_properties.get_scene_props().exterior_defaults
    
    assembly.add_prompt("No Pulls", 'CHECKBOX', props.no_pulls)
    assembly.add_prompt("Center Pulls on Drawers", 'CHECKBOX', props.center_pulls_on_drawers)
    assembly.add_prompt("Drawer Pull From Top", 'DISTANCE', props.drawer_pull_from_top)
    assembly.add_prompt("Pull Double Max Span", 'DISTANCE', sn_unit.inch(30))
    assembly.add_prompt("Lock From Top", 'DISTANCE', sn_unit.inch(1.0))
    assembly.add_prompt("Lock Drawer", 'CHECKBOX', False)
    assembly.add_prompt("Inset Front", 'CHECKBOX', props.inset_door)
    assembly.add_prompt("Horizontal Grain", 'CHECKBOX', props.horizontal_grain_on_drawer_fronts)
    assembly.add_prompt("Open", 'PERCENTAGE', 0)
    
    assembly.add_prompt("Open Drawers", 'PERCENTAGE', 0)
    
    assembly.add_prompt("Inset Reveal", 'DISTANCE', sn_unit.inch(0.125)) 
    assembly.add_prompt("Door to Cabinet Gap", 'DISTANCE', sn_unit.inch(0.125))   
    assembly.add_prompt("Drawer Box Top Gap", 'DISTANCE', sn_unit.inch(1.5))
    assembly.add_prompt("Drawer Box Bottom Gap", 'DISTANCE', sn_unit.inch(1))
    assembly.add_prompt("Drawer Box Slide Gap", 'DISTANCE', sn_unit.inch(0.5))
    assembly.add_prompt("Drawer Box Rear Gap", 'DISTANCE', sn_unit.inch(0.5))
    
    assembly.add_prompt("Front Thickness", 'DISTANCE', sn_unit.inch(.75))
    assembly.add_prompt("Edgebanding Thickness", 'DISTANCE', sn_unit.inch(.02))

def add_frameless_overlay_prompts(assembly):
    props = cabinet_properties.get_scene_props().exterior_defaults
    assembly.add_prompt("Half Overlay Top", 'CHECKBOX', True)
    assembly.add_prompt("Half Overlay Bottom", 'CHECKBOX', True)
    assembly.add_prompt("Half Overlay Left", 'CHECKBOX', False)
    assembly.add_prompt("Half Overlay Right", 'CHECKBOX', False)

    ppt_obj_reveals = assembly.add_prompt_obj("Reveals")
    assembly.add_prompt("Horizontal Gap", 'DISTANCE', props.vertical_gap, prompt_obj=ppt_obj_reveals)
    assembly.add_prompt("Vertical Gap", 'DISTANCE', props.vertical_gap, prompt_obj=ppt_obj_reveals)
    assembly.add_prompt("Top Reveal", 'DISTANCE', sn_unit.inch(.25), prompt_obj=ppt_obj_reveals)
    assembly.add_prompt("Bottom Reveal", 'DISTANCE', 0, prompt_obj=ppt_obj_reveals)
    assembly.add_prompt("Left Reveal", 'DISTANCE', props.left_reveal, prompt_obj=ppt_obj_reveals)
    assembly.add_prompt("Right Reveal", 'DISTANCE', props.right_reveal, prompt_obj=ppt_obj_reveals)

    # CALCULATED
    ppt_obj_overlays = assembly.add_prompt_obj("Overlays")
    assembly.add_prompt("Top Overlay", 'DISTANCE', sn_unit.inch(.6875), prompt_obj=ppt_obj_overlays)
    assembly.add_prompt("Bottom Overlay", 'DISTANCE', sn_unit.inch(.6875), prompt_obj=ppt_obj_overlays)
    assembly.add_prompt("Left Overlay", 'DISTANCE', sn_unit.inch(.6875), prompt_obj=ppt_obj_overlays)
    assembly.add_prompt("Right Overlay", 'DISTANCE', sn_unit.inch(.6875), prompt_obj=ppt_obj_overlays)
    assembly.add_prompt("Division Overlay", 'DISTANCE', sn_unit.inch(.6875), prompt_obj=ppt_obj_overlays)

    # INHERITED
    assembly.add_prompt("Extend Top Amount", 'DISTANCE', 0)
    assembly.add_prompt("Extend Bottom Amount", 'DISTANCE', 0)
    assembly.add_prompt("Top Thickness", 'DISTANCE', sn_unit.inch(.75))
    assembly.add_prompt("Bottom Thickness", 'DISTANCE', sn_unit.inch(.75))
    assembly.add_prompt("Left Side Thickness", 'DISTANCE', sn_unit.inch(.75))
    assembly.add_prompt("Right Side Thickness", 'DISTANCE', sn_unit.inch(.75))
    assembly.add_prompt("Division Thickness", 'DISTANCE', sn_unit.inch(.75))

    inset = assembly.get_prompt("Inset Front").get_var('inset')
    ir = assembly.get_prompt("Inset Reveal").get_var('ir')
    tr = assembly.get_prompt("Top Reveal").get_var('tr')
    br = assembly.get_prompt("Bottom Reveal").get_var('br')
    lr = assembly.get_prompt("Left Reveal").get_var('lr')
    rr = assembly.get_prompt("Right Reveal").get_var('rr')
    vg = assembly.get_prompt("Vertical Gap").get_var('vg')
    hot = assembly.get_prompt("Half Overlay Top").get_var('hot')
    hob = assembly.get_prompt("Half Overlay Bottom").get_var('hob')
    hol = assembly.get_prompt("Half Overlay Left").get_var('hol')
    hor = assembly.get_prompt("Half Overlay Right").get_var('hor')
    tt = assembly.get_prompt("Top Thickness").get_var('tt')
    lst = assembly.get_prompt("Left Side Thickness").get_var('lst')
    rst = assembly.get_prompt("Right Side Thickness").get_var('rst')
    bt = assembly.get_prompt("Bottom Thickness").get_var('bt')
    dt = assembly.get_prompt("Division Thickness").get_var('dt')

    assembly.get_prompt('Top Overlay').set_formula('IF(inset,-ir,IF(hot,(tt/2)-(vg/2),tt-tr))', [inset, ir, hot, tt, tr, vg])
    assembly.get_prompt('Bottom Overlay').set_formula('IF(inset,-ir,IF(hob,(bt/2)-(vg/2),bt-br))', [inset, ir, hob, bt, br, vg])
    assembly.get_prompt('Left Overlay').set_formula('IF(inset,-ir,IF(hol,(lst/2)-(vg/2),lst-lr))', [inset, ir, hol, lst, lr, vg])
    assembly.get_prompt('Right Overlay').set_formula('IF(inset,-ir,IF(hor,(rst/2)-(vg/2),rst-rr))', [inset, ir, hor, rst, rr, vg])
    assembly.get_prompt('Division Overlay').set_formula('IF(inset,-ir,(dt/2)-(vg/2))', [inset, ir, dt, vg])

def add_part(self, path):
    part_bp = self.add_assembly_from_file(path)
    part = sn_types.Assembly(part_bp)
    part.obj_bp.sn_closets.is_panel_bp = True
    return part

class Doors(sn_types.Assembly):

    library_name = LIBRARY_NAME
    category_name = INSERT_DOOR_CATEGORY_NAME
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    show_in_library = True
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    # drop_id = "sn_closets.drop_insert"
    drop_id = "lm_cabinets.insert_doors_drop"

    door_type = ""  # {Base, Tall, Upper}
    door_swing = ""  # {Left Swing, Right Swing, Double Door, Flip up}
    false_front_qty = 0 # 0, 1, 2

    def update_dimensions(self):
        update_dimensions(self)  # Call module level function to find and update door dim labels

    def add_doors_prompts(self):
        add_common_door_prompts(self)
        add_frameless_overlay_prompts(self)
        if self.false_front_qty > 0:
            self.add_prompt("False Front Height", 'DISTANCE', sn_unit.inch(6))

    def set_standard_drivers(self,assembly):
        Height = self.obj_z.snap.get_var('location.z','Height')

        Inset_Front = self.get_prompt("Inset Front").get_var()
        Door_Gap = self.get_prompt("Door to Cabinet Gap").get_var('Door_Gap')
        tt = self.get_prompt("Top Thickness").get_var('tt')
        bt = self.get_prompt("Bottom Thickness").get_var('bt')
        Top_Overlay = self.get_prompt("Top Overlay").get_var()
        Bottom_Overlay = self.get_prompt("Bottom Overlay").get_var()
        eta = self.get_prompt("Extend Top Amount").get_var('eta')
        eba = self.get_prompt("Extend Bottom Amount").get_var('eba')
        Door_Thickness = self.get_prompt("Door Thickness").get_var()
        Vertical_Gap = self.get_prompt("Vertical Gap").get_var()

        false_front_ppt = self.get_prompt("False Front Height")
        if false_front_ppt:
            False_Front_Height = self.get_prompt("False Front Height").get_var()

        assembly.loc_y('IF(Inset_Front,Door_Thickness,-Door_Gap)',[Inset_Front,Door_Gap,Door_Thickness])
        assembly.loc_z('IF(OR(eba==0,Inset_Front==True),-Bottom_Overlay,-eba)',
                       [Inset_Front,eba,bt,Bottom_Overlay])
        assembly.rot_y(value=math.radians(-90))
        if self.false_front_qty > 0:
            assembly.dim_x('Height+IF(OR(eta==0,Inset_Front==True),Top_Overlay,eta)+IF(OR(eba==0,Inset_Front==True),Bottom_Overlay,eba)-False_Front_Height-Vertical_Gap',
                           [Inset_Front,Height,Top_Overlay,Bottom_Overlay,eta,eba,tt,bt,False_Front_Height,Vertical_Gap])
        else:
            assembly.dim_x('Height+IF(OR(eta==0,Inset_Front==True),Top_Overlay,eta)+IF(OR(eba==0,Inset_Front==True),Bottom_Overlay,eba)',
                           [Inset_Front,Height,Top_Overlay,Bottom_Overlay,eta,eba,tt,bt])
        assembly.dim_z('Door_Thickness',[Door_Thickness])
        
    def set_pull_drivers(self,assembly):
        self.set_standard_drivers(assembly)
        
        Height = self.obj_z.snap.get_var('location.z','Height')

        Pull_Length = assembly.get_prompt("Pull Length").get_var()
        Pull_From_Edge = self.get_prompt("Pull From Edge").get_var()
        Base_Pull_Location = self.get_prompt("Base Pull Location").get_var()
        Tall_Pull_Location = self.get_prompt("Tall Pull Location").get_var()
        Upper_Pull_Location = self.get_prompt("Upper Pull Location").get_var()

        eta = self.get_prompt("Extend Top Amount").get_var('eta')
        eba = self.get_prompt("Extend Bottom Amount").get_var('eba')

        # TODO tall cabinet pull
        #World_Z = self.get_var('world_loc_z','World_Z',transform_type='LOC_Z')
        World_Z = self.obj_bp.snap.get_var('matrix_world[2][3]', 'World_Z')
        
        assembly.get_prompt("Pull X Location").set_formula('Pull_From_Edge',[Pull_From_Edge])
        if self.door_type == "Base":
            assembly.get_prompt("Pull Z Location").set_formula('Base_Pull_Location+(Pull_Length/2)',[Base_Pull_Location,Pull_Length])
        if self.door_type == "Tall":
            assembly.get_prompt("Pull Z Location").set_formula('Height-Tall_Pull_Location+(Pull_Length/2)+World_Z',[Height,World_Z,Tall_Pull_Location,Pull_Length])
        # if self.door_type == "Tall":
        #     assembly.get_prompt("Pull Z Location").set_formula('Height-Tall_Pull_Location+(Pull_Length/2)+0',[Height,Tall_Pull_Location,Pull_Length])
        if self.door_type == "Upper":
            assembly.get_prompt("Pull Z Location").set_formula('Height+(eta+eba)-Upper_Pull_Location-(Pull_Length/2)',[Height,eta,eba,Upper_Pull_Location,Pull_Length])

    def draw(self):
        self.create_assembly()
        self.obj_bp["IS_BP_DOOR_INSERT"] = True
   
        self.add_doors_prompts()

        Height = self.obj_z.snap.get_var('location.z','Height')
        Width = self.obj_x.snap.get_var('location.x','Width')
        Left_Overlay = self.get_prompt("Left Overlay").get_var()
        Right_Overlay = self.get_prompt("Right Overlay").get_var()
        Vertical_Gap = self.get_prompt("Vertical Gap").get_var()
        Door_Rotation = self.get_prompt("Door Rotation").get_var()
        No_Pulls = self.get_prompt("No Pulls").get_var()
        Door_Thickness = self.get_prompt("Door Thickness").get_var()
        eta = self.get_prompt("Extend Top Amount").get_var('eta')
        Open_Door = self.get_prompt("Open Door").get_var()

        left_swing_ppt =  self.get_prompt("Left Swing")
        if left_swing_ppt:
            Left_Swing = left_swing_ppt.get_var()

        false_front_ppt = self.get_prompt("False Front Height")
        if false_front_ppt:
            False_Front_Height = self.get_prompt("False Front Height").get_var()

        if self.false_front_qty > 0:
            false_front = add_part(self, PART_WITH_FRONT_EDGEBANDING)
            false_front.set_name("False Front")
            false_front.obj_bp['IS_BP_DRAWER_FRONT'] = True
            false_front.obj_bp['IS_BP_FALSE_FRONT'] = True
            false_front.loc_x('-Left_Overlay',[Left_Overlay])
            false_front.loc_z('Height+eta',[Height,eta])
            false_front.rot_x(value=math.radians(90))

            if self.false_front_qty > 1:
                false_front.dim_x('(Width+Left_Overlay+Right_Overlay-Vertical_Gap)/2',[Width,Left_Overlay,Right_Overlay,Vertical_Gap])
            else:
                false_front.dim_x('Width+Left_Overlay+Right_Overlay',[Width,Left_Overlay,Right_Overlay])
            false_front.dim_y('-False_Front_Height',[False_Front_Height])
            false_front.dim_z('Door_Thickness',[Door_Thickness])

            if self.false_front_qty > 1:
                false_front_2 = add_part(self, PART_WITH_FRONT_EDGEBANDING)
                false_front_2.set_name("False Front")
                false_front_2.obj_bp['IS_BP_DRAWER_FRONT'] = True
                false_front_2.loc_x('Width*0.5+Vertical_Gap*0.5', [Width, Vertical_Gap])
                false_front_2.loc_z('Height+eta',[Height,eta])
                false_front_2.rot_x(value=math.radians(90))
                false_front_2.dim_x("(Width+Left_Overlay+Right_Overlay-Vertical_Gap)/2", [Width, Left_Overlay, Right_Overlay, Vertical_Gap])
                false_front_2.dim_y('-False_Front_Height',[False_Front_Height])
                false_front_2.dim_z('Door_Thickness',[Door_Thickness])

        #LEFT DOOR
        left_door = add_part(self, DOOR)
        left_door.set_name("Cabinet Left Door")
        left_door.obj_bp.parent = self.obj_bp
        left_door.obj_bp['IS_DOOR'] = True
        self.set_standard_drivers(left_door)
        left_door.loc_x('-Left_Overlay',[Left_Overlay])
        left_door.rot_z('radians(90)-(radians(120)*Open_Door)',[Open_Door])
        if self.door_swing == 'Double Door':
            left_door.dim_y('((Width+Left_Overlay+Right_Overlay-Vertical_Gap)/2)*-1',[Width,Left_Overlay,Right_Overlay,Vertical_Gap])
        else:
            left_door.dim_y('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])
            left_door.get_prompt('Hide').set_formula('IF(Left_Swing,False,True)',[Left_Swing])
        add_door_height_dimension(left_door)

        #LEFT PULL
        left_pull = cabinet_pulls.Standard_Pull()
        left_pull.door_type = self.door_type
        left_pull.door_swing = "Left Swing"
        left_pull.draw()
        left_pull.set_name(left_pull.pull_name)
        left_pull.obj_bp.parent = self.obj_bp
        self.set_pull_drivers(left_pull)
        left_pull.loc_x('-Left_Overlay',[Left_Overlay])
        left_pull.rot_z('radians(90)-(radians(120)*Open_Door)',[Open_Door])
        if self.door_swing == 'Double Door':
            left_pull.dim_y('((Width+Left_Overlay+Right_Overlay-Vertical_Gap)/2)*-1',[Width,Left_Overlay,Right_Overlay,Vertical_Gap])
            left_pull.get_prompt('Hide').set_formula('IF(No_Pulls,True,False)',[No_Pulls])
        else:
            left_pull.dim_y('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])
            left_pull.get_prompt('Hide').set_formula('IF(Left_Swing,IF(No_Pulls,True,False),True)',[Left_Swing,No_Pulls])

        #RIGHT DOOR
        right_door = add_part(self, DOOR)
        right_door.obj_bp['IS_DOOR'] = True
        right_door.set_name("Cabinet Right Door")
        self.set_standard_drivers(right_door)
        right_door.loc_x('Width+Right_Overlay',[Width,Right_Overlay])
        right_door.rot_z('radians(90)+(radians(120)*Open_Door)',[Open_Door])
        if self.door_swing == 'Double Door':
            right_door.dim_y('(Width+Left_Overlay+Right_Overlay-Vertical_Gap)/2',[Width,Left_Overlay,Right_Overlay,Vertical_Gap])
        else:
            right_door.dim_y('Width+Left_Overlay+Right_Overlay',[Width,Left_Overlay,Right_Overlay])
            right_door.get_prompt('Hide').set_formula('IF(Left_Swing,True,False)',[Left_Swing])
        add_door_height_dimension(right_door)
      
        #RIGHT PULL
        right_pull = cabinet_pulls.Standard_Pull()
        right_pull.door_type = self.door_type
        right_pull.door_swing = "Right Swing"
        right_pull.draw()
        right_pull.set_name(right_pull.pull_name)
        right_pull.obj_bp.parent = self.obj_bp
        self.set_pull_drivers(right_pull)
        right_pull.loc_x('Width+Right_Overlay',[Width,Right_Overlay])
        right_pull.rot_z('radians(90)+(radians(120)*Open_Door)',[Open_Door])
        if self.door_swing == "Double Door":
            right_pull.dim_y('(Width+Left_Overlay+Right_Overlay-Vertical_Gap)/2',[Width,Left_Overlay,Right_Overlay,Vertical_Gap])
            right_pull.get_prompt('Hide').set_formula('IF(No_Pulls,True,False)',[No_Pulls])
        else:
            right_pull.dim_y('(Width+Left_Overlay+Right_Overlay)',[Width,Left_Overlay,Right_Overlay])
            right_pull.get_prompt('Hide').set_formula('IF(Left_Swing,True,IF(No_Pulls,True,False))',[Left_Swing,No_Pulls])

        self.update()

class Pie_Cut_Doors(sn_types.Assembly):

    library_name = LIBRARY_NAME
    category_name = INSERT_DOOR_CATEGORY_NAME
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    show_in_library = True
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    drop_id = "sn_closets.drop_insert"

    door_type = ""  # {Base, Tall, Upper}
    door_swing = ""  # {Left Swing, Right Swing, Double Door, Flip up}

    def update_dimensions(self):
        update_dimensions(self)  # Call module level function to find and update door dim labels

    def add_doors_prompts(self):
       
        add_common_door_prompts(self)
        add_frameless_overlay_prompts(self)
        
    def set_standard_drivers(self,assembly):

        Height = self.obj_z.snap.get_var('location.z','Height')

        Inset_Front = self.get_prompt("Inset Front").get_var()
        tt = self.get_prompt("Top Thickness").get_var('tt')
        bt = self.get_prompt("Bottom Thickness").get_var('bt')
        Top_Overlay = self.get_prompt("Top Overlay").get_var()
        Bottom_Overlay = self.get_prompt("Bottom Overlay").get_var()
        eta = self.get_prompt("Extend Top Amount").get_var('eta')
        eba = self.get_prompt("Extend Bottom Amount").get_var('eba')
        Door_Thickness = self.get_prompt("Door Thickness").get_var()
        
        assembly.loc_z('IF(OR(eba==0,Inset_Front==True),-Bottom_Overlay,-eba)',
                       [Inset_Front,eba,bt,Bottom_Overlay])
        assembly.rot_y(value=math.radians(-90))
        assembly.rot_z(value=math.radians(90))
        assembly.dim_x('Height+IF(OR(eta==0,Inset_Front==True),Top_Overlay,eta)+IF(OR(eba==0,Inset_Front==True),Bottom_Overlay,eba)',
                       [Inset_Front,Height,Top_Overlay,Bottom_Overlay,eta,eba,tt,bt])
        assembly.dim_z('Door_Thickness',[Door_Thickness])
        
    def set_pull_drivers(self,assembly):
        self.set_standard_drivers(assembly)
        
        Height = self.obj_z.snap.get_var('location.z','Height')

        Pull_Length = assembly.get_prompt("Pull Length").get_var()
        Pull_From_Edge = self.get_prompt("Pull From Edge").get_var()
        Base_Pull_Location = self.get_prompt("Base Pull Location").get_var()
        Tall_Pull_Location = self.get_prompt("Tall Pull Location").get_var()
        Upper_Pull_Location = self.get_prompt("Upper Pull Location").get_var()
        eta = self.get_prompt("Extend Top Amount").get_var('eta')
        eba = self.get_prompt("Extend Bottom Amount").get_var('eba')
        
        assembly.get_prompt("Pull X Location").set_formula('Pull_From_Edge',[Pull_From_Edge])
        if self.door_type == "Base":
            assembly.get_prompt("Pull Z Location").set_formula('Base_Pull_Location+(Pull_Length/2)',[Base_Pull_Location,Pull_Length])
        if self.door_type == "Tall":
            assembly.get_prompt("Pull Z Location").set_formula('Tall_Pull_Location+(Pull_Length/2)',[Tall_Pull_Location,Pull_Length])
        if self.door_type == "Upper":
            assembly.get_prompt("Pull Z Location").set_formula('Height+(eta+eba)-Upper_Pull_Location-(Pull_Length/2)',[Height,eta,eba,Upper_Pull_Location,Pull_Length])
    
    def draw(self):
        self.create_assembly()
        self.obj_bp["IS_BP_DOOR_INSERT"] = True
           
        self.add_doors_prompts()
        
        Width = self.obj_x.snap.get_var('location.x','Width')
        Depth = self.obj_y.snap.get_var('location.y','Depth')

        Left_Overlay = self.get_prompt("Left Overlay").get_var()
        Right_Overlay = self.get_prompt("Right Overlay").get_var()
        Left_Swing = self.get_prompt("Left Swing").get_var()
        No_Pulls = self.get_prompt("No Pulls").get_var()
        Door_to_Cabinet_Gap = self.get_prompt("Door to Cabinet Gap").get_var()
        Door_Thickness = self.get_prompt("Door Thickness").get_var()
        Inset_Front = self.get_prompt("Inset Front").get_var()
        
        #LEFT DOOR
        left_door = add_part(self, DOOR)  
        left_door.obj_bp['IS_DOOR'] = True
        left_door.set_name("Left Cabinet Door")
        self.set_standard_drivers(left_door)
        left_door.loc_x('IF(Inset_Front,-Door_Thickness,Door_to_Cabinet_Gap)',[Door_to_Cabinet_Gap,Door_Thickness,Inset_Front])
        left_door.loc_y('Depth-Left_Overlay',[Depth,Left_Overlay])
        left_door.rot_x(value=math.radians( 90))
        left_door.dim_y('(fabs(Depth)+Left_Overlay-IF(Inset_Front,0,Door_Thickness+Door_to_Cabinet_Gap))*-1',[Depth,Left_Overlay,Inset_Front,Right_Overlay,Door_Thickness,Door_to_Cabinet_Gap])
        add_door_height_dimension(left_door)
        left_door.obj_bp.snap.is_cabinet_door = True
        
        #LEFT PULL
        left_pull = cabinet_pulls.Standard_Pull()
        left_pull.door_type = self.door_type
        left_pull.draw()
        left_pull.set_name(left_pull.pull_name)
        left_pull.obj_bp.parent = self.obj_bp
        self.set_pull_drivers(left_pull)
        left_pull.loc_x('IF(Inset_Front,-Door_Thickness,Door_to_Cabinet_Gap)',[Door_to_Cabinet_Gap,Door_Thickness,Inset_Front])
        left_pull.loc_y('-Door_to_Cabinet_Gap',[Door_to_Cabinet_Gap])
        left_pull.rot_x(value=math.radians(90))
        left_pull.dim_y('fabs(Depth)+Left_Overlay-Door_Thickness-Door_to_Cabinet_Gap',[Depth,Left_Overlay,Right_Overlay,Door_Thickness,Door_to_Cabinet_Gap])
        left_pull.get_prompt('Hide').set_formula('IF(Left_Swing,True,IF(No_Pulls,True,False))',[Left_Swing,No_Pulls])
        
        #RIGHT DOOR
        right_door = add_part(self, DOOR)  
        right_door.obj_bp['IS_DOOR'] = True
        right_door.set_name("Right Cabinet Door")
        self.set_standard_drivers(right_door)
        right_door.loc_x('IF(Inset_Front,0,Door_to_Cabinet_Gap+Door_Thickness)',[Inset_Front,Door_to_Cabinet_Gap,Door_Thickness])
        right_door.loc_y('IF(Inset_Front,Door_Thickness,-Door_to_Cabinet_Gap)',[Inset_Front,Door_to_Cabinet_Gap,Door_Thickness])
        right_door.dim_y('(Width+Right_Overlay-IF(Inset_Front,0,Door_Thickness+Door_to_Cabinet_Gap))*-1',[Width,Inset_Front,Right_Overlay,Door_Thickness,Door_to_Cabinet_Gap])
        add_door_height_dimension(right_door)
        right_door.obj_bp.snap.is_cabinet_door = True
        
        #RIGHT PULL
        right_pull = cabinet_pulls.Standard_Pull()
        right_pull.door_type = self.door_type
        right_pull.draw()
        right_pull.set_name(right_pull.pull_name)
        right_pull.obj_bp.parent = self.obj_bp
        self.set_pull_drivers(right_pull)
        right_pull.loc_x('IF(Inset_Front,0,Door_to_Cabinet_Gap+Door_Thickness)',[Inset_Front,Door_to_Cabinet_Gap,Door_Thickness])
        right_pull.loc_y('IF(Inset_Front,Door_Thickness,-Door_to_Cabinet_Gap)',[Inset_Front,Door_to_Cabinet_Gap,Door_Thickness])
        right_pull.dim_y('(Width+Right_Overlay-IF(Inset_Front,0,Door_Thickness+Door_to_Cabinet_Gap))*-1',[Width,Inset_Front,Right_Overlay,Door_Thickness,Door_to_Cabinet_Gap])
        right_pull.get_prompt('Hide').set_formula('IF(Left_Swing,IF(No_Pulls,True,False),True)',[Left_Swing,No_Pulls])

        self.update()

class Vertical_Drawers(sn_types.Assembly):

    library_name = LIBRARY_NAME
    category_name = INSERT_DRAWER_CATEGORY_NAME
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    show_in_library = True
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    # drop_id = "sn_closets.drop_insert"
    drop_id = "lm_cabinets.insert_drawers_drop"
    drawer_qty = 1
    
    front_heights = []
    
    add_pull = True
    add_drawer = True
    use_buyout_box = True

    calculator = None
    calculator_name = "Vertical Drawers Calculator"
    calculator_obj_name = "Vertical Drawers Distance Obj"     
    
    def update_dimensions(self):
        update_dimensions(self)  # Call module level function to find and update door dim labels

    def add_common_prompts(self):
        
        add_common_drawer_prompts(self)
        add_frameless_overlay_prompts(self)
    
    def add_drawer_front(self, i, prev_drawer_empty):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Left_Overlay = self.get_prompt("Left Overlay").get_var()
        Right_Overlay = self.get_prompt("Right Overlay").get_var()
        Top_Overlay = self.get_prompt("Top Overlay").get_var()
        Vertical_Gap = self.get_prompt("Vertical Gap").get_var()
        Center_Pulls_on_Drawers = self.get_prompt("Center Pulls on Drawers").get_var()
        Drawer_Pull_From_Top = self.get_prompt("Drawer Pull From Top").get_var()
        Door_to_Cabinet_Gap = self.get_prompt("Door to Cabinet Gap").get_var()
        Front_Thickness = self.get_prompt("Front Thickness").get_var()
        No_Pulls = self.get_prompt("No Pulls").get_var()
        Inset_Front = self.get_prompt("Inset Front").get_var()
        Horizontal_Grain = self.get_prompt("Horizontal Grain").get_var()
        Drawer_Box_Slide_Gap = self.get_prompt("Drawer Box Slide Gap").get_var()
        Drawer_Box_Bottom_Gap = self.get_prompt("Drawer Box Bottom Gap").get_var()
        Drawer_Box_Rear_Gap = self.get_prompt("Drawer Box Rear Gap").get_var()
        Drawer_Box_Top_Gap = self.get_prompt("Drawer Box Top Gap").get_var()
        Open_Drawers = self.get_prompt("Open Drawers").get_var()

        height_prompt = eval("self.calculator.get_calculator_prompt('Drawer Front {} Height')".format(str(i)))
        Drawer_Front_Height = eval("height_prompt.get_var(self.calculator.name, 'Drawer_Front_Height')".format(str(i)))        
        
        front_empty = self.add_empty("front_empty")
        if prev_drawer_empty:
            prev_drawer_z_loc = prev_drawer_empty.snap.get_var('location.z','prev_drawer_z_loc')
            front_empty.snap.loc_z('prev_drawer_z_loc-Drawer_Front_Height-Vertical_Gap',[prev_drawer_z_loc,Drawer_Front_Height,Vertical_Gap])
        else:
            front_empty.snap.loc_z('Height-Drawer_Front_Height+Top_Overlay',[Height,Drawer_Front_Height,Top_Overlay])        
        drawer_z_loc = front_empty.snap.get_var('location.z','drawer_z_loc')
        
        drawer_front = add_part(self, DRAWER_FRONT)
        drawer_front.obj_bp["IS_BP_DRAWER_FRONT"] = True
        drawer_front.set_name("Drawer Front")
        drawer_front.loc_x('-Left_Overlay',[Left_Overlay])
        drawer_front.loc_y('IF(Inset_Front,Front_Thickness,-Door_to_Cabinet_Gap)-(Depth*Open_Drawers)',
                           [Inset_Front,Door_to_Cabinet_Gap,Front_Thickness,Depth,Open_Drawers])
        drawer_front.loc_z('drawer_z_loc',[drawer_z_loc])

        drawer_front.rot_x('IF(Horizontal_Grain,radians(90),0)',[Horizontal_Grain])
        drawer_front.rot_y('IF(Horizontal_Grain,0,radians(-90))',[Horizontal_Grain])
        drawer_front.rot_z('IF(Horizontal_Grain,0,radians(90))',[Horizontal_Grain])

        drawer_front.dim_x('IF(Horizontal_Grain,(Width+Left_Overlay+Right_Overlay),Drawer_Front_Height)',
                           [Horizontal_Grain,Drawer_Front_Height,Width,Left_Overlay,Right_Overlay])
        drawer_front.dim_y('IF(Horizontal_Grain,Drawer_Front_Height,(Width+Left_Overlay+Right_Overlay)*-1)',
                           [Horizontal_Grain,Drawer_Front_Height,Width,Left_Overlay,Right_Overlay])        
        drawer_front.dim_z('Front_Thickness',[Front_Thickness])
        add_drawer_height_dimension(drawer_front)
         
        if self.add_pull:
            pull = cabinet_pulls.Standard_Pull()
            pull.door_type = self.door_type
            pull.draw()
            pull.set_name(pull.pull_name)
            pull.obj_bp.parent = self.obj_bp

            pull.loc_x('-Left_Overlay',[Left_Overlay])
            pull.loc_y('IF(Inset_Front,Front_Thickness,-Door_to_Cabinet_Gap)-(Depth*Open_Drawers)',[Inset_Front,Door_to_Cabinet_Gap,Front_Thickness,Depth,Open_Drawers])
            pull.loc_z('drawer_z_loc',[drawer_z_loc])

            pull.rot_x(value=math.radians(90))

            pull.dim_x('Width+Left_Overlay+Right_Overlay',[Width,Left_Overlay,Right_Overlay])
            pull.dim_y('Drawer_Front_Height',[Drawer_Front_Height])
            pull.dim_z('Front_Thickness',[Front_Thickness])

            pull.get_prompt("Pull X Location").set_formula('IF(Center_Pulls_on_Drawers,Drawer_Front_Height/2,Drawer_Pull_From_Top)',[Center_Pulls_on_Drawers,Drawer_Front_Height,Drawer_Pull_From_Top])
            pull.get_prompt("Pull Z Location").set_formula('(Width/2)+Right_Overlay',[Width,Right_Overlay])
            pull.get_prompt("Hide").set_formula('IF(No_Pulls,True,False)',[No_Pulls])        
        
        if self.add_drawer:
            if self.use_buyout_box:
                drawer_bp = self.add_assembly_from_file(BUYOUT_DRAWER_BOX)
                drawer = sn_types.Assembly(drawer_bp)
                drawer.obj_bp["CABINET_DRAWER_BOX"] = True
                # drawer.material('Drawer_Box_Surface')
            # else:
            #     drawer = drawer_boxes.Wood_Drawer_Box()
            #     drawer.draw()
            #     drawer.obj_bp.parent = self.obj_bp
            drawer.set_name("Drawer Box " + str(i))
            drawer.loc_x('Drawer_Box_Slide_Gap',[Drawer_Box_Slide_Gap])
            drawer.loc_y('IF(Inset_Front,Front_Thickness,-Door_to_Cabinet_Gap)-(Depth*Open_Drawers)',[Inset_Front,Door_to_Cabinet_Gap,Front_Thickness,Depth,Open_Drawers])
            drawer.loc_z('drawer_z_loc+Drawer_Box_Bottom_Gap',[Drawer_Box_Bottom_Gap,drawer_z_loc])
            drawer.dim_x('Width-(Drawer_Box_Slide_Gap*2)',[Width,Drawer_Box_Slide_Gap])
            drawer.dim_y('Depth-Drawer_Box_Rear_Gap-IF(Inset_Front,Front_Thickness,0)',[Depth,Drawer_Box_Rear_Gap,Inset_Front,Front_Thickness])
            drawer.dim_z('Drawer_Front_Height-Drawer_Box_Top_Gap-Drawer_Box_Bottom_Gap',[Drawer_Front_Height,Drawer_Box_Top_Gap,Drawer_Box_Bottom_Gap])        
        
        return front_empty, pull.obj_y, drawer.obj_z
        
    def draw(self):
        self.create_assembly()
        self.obj_bp['IS_DRAWERS_BP'] = True
        self.obj_bp['VERTICAL_DRAWERS'] = True

        self.add_common_prompts()

        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Vertical_Gap = self.get_prompt("Vertical Gap").get_var()
        Top_Overlay = self.get_prompt("Top Overlay").get_var()
        Bottom_Overlay = self.get_prompt("Bottom Overlay").get_var()

        calc_distance_obj = self.add_empty(self.calculator_obj_name)
        calc_distance_obj.empty_display_size = .001
        self.calculator = self.obj_prompts.snap.add_calculator(self.calculator_name, calc_distance_obj)
        self.calculator.set_total_distance(
            "Height+Vertical_Gap*(" + str(self.drawer_qty) +"-1)+Top_Overlay+Bottom_Overlay",
            [Height, Vertical_Gap, Top_Overlay, Bottom_Overlay])

        empties = []            

        drawer = None
        for i in range(self.drawer_qty):
            equal = True
            height = 0
            if len(self.front_heights) >= i + 1:
                equal = True if self.front_heights[i] == 0 else False
                height = self.front_heights[i]
            self.calculator.add_calculator_prompt("Drawer Front " + str(i+1) + " Height")
            drawer, pull_y, box_dim_z = self.add_drawer_front(i+1,drawer)
            empties.append(drawer)
            empties.append(pull_y)
            empties.append(box_dim_z)

        self.update()

        for df_empty in empties:
            z_loc_driver = df_empty.animation_data.drivers[0].driver
            data_path = z_loc_driver.variables["Drawer_Front_Height"].targets[0].data_path
            z_loc_driver.variables["Drawer_Front_Height"].targets[0].data_path = data_path
            
class Horizontal_Drawers(sn_types.Assembly):
    
    library_name = LIBRARY_NAME
    category_name = INSERT_DRAWER_CATEGORY_NAME
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    show_in_library = True
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    drop_id = "sn_closets.drop_insert"

    drawer_qty = 1
    front_heights = []
    
    add_pull = True
    add_drawer = True
    use_buyout_box = True
    
    def update_dimensions(self):
        update_dimensions(self)  # Call module level function to find and update door dim labels

    def add_common_prompts(self):
        add_common_drawer_prompts(self)
        add_frameless_overlay_prompts(self)
    
    def add_drawer_front(self, i, prev_drawer_empty):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Left_Overlay = self.get_prompt("Left Overlay").get_var()
        Right_Overlay = self.get_prompt("Right Overlay").get_var()
        Top_Overlay = self.get_prompt("Top Overlay").get_var()
        Bottom_Overlay = self.get_prompt("Bottom Overlay").get_var()
        Division_Overlay = self.get_prompt("Division Overlay").get_var()
        Vertical_Gap = self.get_prompt("Vertical Gap").get_var()
        Center_Pulls_on_Drawers = self.get_prompt("Center Pulls on Drawers").get_var()
        Drawer_Pull_From_Top = self.get_prompt("Drawer Pull From Top").get_var()
        Door_to_Cabinet_Gap = self.get_prompt("Door to Cabinet Gap").get_var()
        Front_Thickness = self.get_prompt("Front Thickness").get_var()
        No_Pulls = self.get_prompt("No Pulls").get_var()
        Inset_Front = self.get_prompt("Inset Front").get_var()
        Horizontal_Grain = self.get_prompt("Horizontal Grain").get_var()
        Drawer_Box_Slide_Gap = self.get_prompt("Drawer Box Slide Gap").get_var()
        Drawer_Box_Bottom_Gap = self.get_prompt("Drawer Box Bottom Gap").get_var()
        Drawer_Box_Rear_Gap = self.get_prompt("Drawer Box Rear Gap").get_var()
        Drawer_Box_Top_Gap = self.get_prompt("Drawer Box Top Gap").get_var()
        Open_Drawers = self.get_prompt("Open Drawers").get_var()
        
        front_empty = self.add_empty("Front Empty")
        drawer_front_width = '((Left_Overlay+Right_Overlay+Width-(Vertical_Gap*' + str(self.drawer_qty - 1) + '))/' + str(self.drawer_qty) + ')'

        if prev_drawer_empty:
            prev_drawer_x_loc = prev_drawer_empty.snap.get_var('location.x','prev_drawer_x_loc')
            front_empty.snap.loc_x('prev_drawer_x_loc+Vertical_Gap+' + drawer_front_width,
                              [prev_drawer_x_loc,Width,Vertical_Gap,Left_Overlay,Right_Overlay])
        else:
            front_empty.snap.loc_x('-Left_Overlay',[Left_Overlay])

        drawer_x_loc = front_empty.snap.get_var('location.x','drawer_x_loc')
        
        drawer_front = add_part(self, DRAWER_FRONT)
        drawer_front.obj_bp["IS_BP_DRAWER_FRONT"] = True
        drawer_front.set_name("Drawer Front")

        drawer_front.loc_x('drawer_x_loc',[drawer_x_loc])
        drawer_front.loc_y('IF(Inset_Front,Front_Thickness,-Door_to_Cabinet_Gap)-(Depth*Open_Drawers)',
                           [Inset_Front,Door_to_Cabinet_Gap,Front_Thickness,Depth,Open_Drawers])
        drawer_front.loc_z('-Bottom_Overlay',[Bottom_Overlay])

        drawer_front.rot_x('IF(Horizontal_Grain,radians(90),0)',[Horizontal_Grain])
        drawer_front.rot_y('IF(Horizontal_Grain,0,radians(-90))',[Horizontal_Grain])
        drawer_front.rot_z('IF(Horizontal_Grain,0,radians(90))',[Horizontal_Grain])

        drawer_front.dim_x('IF(Horizontal_Grain,' + drawer_front_width + ',Height+Top_Overlay+Bottom_Overlay)',
                           [Horizontal_Grain,Height,Width,Top_Overlay,Bottom_Overlay,Width,Vertical_Gap,Left_Overlay,Right_Overlay])
        drawer_front.dim_y('IF(Horizontal_Grain,Height+Top_Overlay+Bottom_Overlay,(' + drawer_front_width + ')*-1)',
                           [Horizontal_Grain,Height,Width,Top_Overlay,Bottom_Overlay,Width,Vertical_Gap,Left_Overlay,Right_Overlay])       
        drawer_front.dim_z('Front_Thickness',[Front_Thickness])
        add_drawer_height_dimension(drawer_front)
        
        if self.add_pull:
            pull = cabinet_pulls.Standard_Pull()
#             pull.door_type = self.door_type
            pull.draw()
            pull.set_name(pull.pull_name)
            pull.obj_bp.parent = self.obj_bp

            pull.loc_x('drawer_x_loc',[drawer_x_loc])
            pull.loc_y('IF(Inset_Front,Front_Thickness,-Door_to_Cabinet_Gap)-(Depth*Open_Drawers)',[Inset_Front,Door_to_Cabinet_Gap,Front_Thickness,Depth,Open_Drawers])
            pull.loc_z('-Bottom_Overlay',[Bottom_Overlay])

            pull.rot_x(value=math.radians(90))
 
            pull.dim_x(drawer_front_width,[Left_Overlay,Right_Overlay,Width,Vertical_Gap])
            pull.dim_y('Height+Top_Overlay+Bottom_Overlay',[Height,Top_Overlay,Bottom_Overlay])
            pull.dim_z('Front_Thickness',[Front_Thickness])

            pull.get_prompt("Pull X Location").set_formula('IF(Center_Pulls_on_Drawers,(Height+Top_Overlay+Bottom_Overlay)/2,Drawer_Pull_From_Top)',
                                                            [Center_Pulls_on_Drawers,Height,Top_Overlay, Bottom_Overlay, Drawer_Pull_From_Top])
            pull.get_prompt("Pull Z Location").set_formula(drawer_front_width + "/2",[Left_Overlay,Right_Overlay,Width,Vertical_Gap])
            pull.get_prompt("Hide").set_formula('IF(No_Pulls,True,False)',[No_Pulls])        
         
        if self.add_drawer:
            if self.use_buyout_box:
                drawer_bp = self.add_assembly_from_file(BUYOUT_DRAWER_BOX)
                drawer = sn_types.Assembly(drawer_bp)
                # drawer.material('Drawer_Box_Surface')
            # else:
            #     drawer = drawer_boxes.Wood_Drawer_Box()
            #     drawer.draw()
            #     drawer.obj_bp.parent = self.obj_bp
            drawer.set_name("Drawer Box " + str(i))
            if i == 1: #FIRST
                drawer.loc_x('drawer_x_loc+Left_Overlay+Drawer_Box_Slide_Gap',[drawer_x_loc,Left_Overlay,Drawer_Box_Slide_Gap])
                drawer.dim_x(drawer_front_width + "-Left_Overlay-Division_Overlay-(Drawer_Box_Slide_Gap*2)",[Left_Overlay,Division_Overlay,Right_Overlay,Width,Vertical_Gap,Drawer_Box_Slide_Gap])
            elif i == self.drawer_qty: #LAST
                drawer.loc_x('drawer_x_loc+Division_Overlay+Drawer_Box_Slide_Gap',[drawer_x_loc,Division_Overlay,Drawer_Box_Slide_Gap])
                drawer.dim_x(drawer_front_width + "-Right_Overlay-Division_Overlay-(Drawer_Box_Slide_Gap*2)",[Left_Overlay,Right_Overlay,Division_Overlay,Width,Vertical_Gap,Drawer_Box_Slide_Gap])
            else: #MIDDLE
                drawer.loc_x('drawer_x_loc+Division_Overlay+Drawer_Box_Slide_Gap',[drawer_x_loc,Division_Overlay,Drawer_Box_Slide_Gap])
                drawer.dim_x(drawer_front_width + '-(Division_Overlay*2)-(Drawer_Box_Slide_Gap*2)',[Left_Overlay,Right_Overlay,Division_Overlay,Width,Vertical_Gap,Drawer_Box_Slide_Gap])
            drawer.loc_y('IF(Inset_Front,Front_Thickness,-Door_to_Cabinet_Gap)-(Depth*Open_Drawers)',[Inset_Front,Door_to_Cabinet_Gap,Front_Thickness,Depth,Open_Drawers])
            drawer.loc_z('Drawer_Box_Bottom_Gap',[Drawer_Box_Bottom_Gap])
            drawer.dim_y('Depth-Drawer_Box_Rear_Gap-IF(Inset_Front,Front_Thickness,0)',[Depth,Drawer_Box_Rear_Gap,Inset_Front,Front_Thickness])
            drawer.dim_z('Height-Drawer_Box_Top_Gap-Drawer_Box_Bottom_Gap',[Height,Drawer_Box_Top_Gap,Drawer_Box_Bottom_Gap])        
        
        return front_empty
        
    def draw(self):
        self.create_assembly()
        self.obj_bp['IS_DRAWERS_BP'] = True
        self.obj_bp['HORIZONTAL_DRAWERS'] = True
        self.add_common_prompts()
        
        drawer = None
        for i in range(self.drawer_qty):
            drawer = self.add_drawer_front(i+1,drawer)

            if i != 0:
                drawer_x_loc = drawer.snap.get_var('loc_x','drawer_x_loc')
                Height = self.obj_z.snap.get_var('location.z', 'Height')
                Depth = self.obj_y.snap.get_var('location.y', 'Depth')
                Division_Thickness = self.get_prompt("Division Thickness").get_var()
                Inset_Front = self.get_prompt("Inset Front").get_var()
                Front_Thickness = self.get_prompt("Front Thickness").get_var()
                Vertical_Gap = self.get_prompt("Vertical Gap").get_var()
                
                division = add_part(self, DIVISION)
                division.set_name("Drawer Division")

                division.loc_x('drawer_x_loc-(Division_Thickness/2)-(Vertical_Gap/2)',[drawer_x_loc,Division_Thickness,Vertical_Gap])
                division.loc_y('IF(Inset_Front,Front_Thickness,0)',[Inset_Front,Front_Thickness])
                
                division.rot_x(value=math.radians(90))
                division.rot_z(value=math.radians(90))

                division.dim_x('Depth-IF(Inset_Front,Front_Thickness,0)',[Depth,Inset_Front,Front_Thickness])
                division.dim_y('Height',[Height])
                division.dim_z('Division_Thickness',[Division_Thickness])

        self.update()


# Drop operators
class OPS_KB_Doors_Drop(Operator, PlaceClosetInsert):
    bl_idname = "lm_cabinets.insert_doors_drop"
    bl_label = "Custom drag and drop for doors insert"

    def execute(self, context):
        return super().execute(context)    

    def confirm_placement(self, context):
        super().confirm_placement(context)

        insert = sn_types.Assembly(self.insert.obj_bp)
        product = sn_types.Assembly(self.insert.obj_bp.parent)

        carcass = None
        inserts = sn_utils.get_insert_bp_list(product.obj_bp, [])
        for obj_bp in inserts:
            if "IS_BP_CARCASS" in obj_bp:
                carcass = sn_types.Assembly(obj_bp)
            
        if not carcass:
            product = sn_types.Assembly(product.obj_bp.parent)
            inserts = sn_utils.get_insert_bp_list(product.obj_bp, [])
            for obj_bp in inserts:
                if "IS_BP_CARCASS" in obj_bp:
                    carcass = sn_types.Assembly(obj_bp)

         # ALLOW DOOR TO EXTEND WHEN SUB FRONT IS FOUND
        sub_front_height = carcass.get_prompt("Sub Front Height")
        top_reveal = insert.get_prompt("Top Reveal")

        if sub_front_height and top_reveal:
            Sub_Front_Height = carcass.get_prompt("Sub Front Height").get_var()
            Top_Reveal = top_reveal.get_var()

            insert.get_prompt('Extend Top Amount').set_formula('Sub_Front_Height-Top_Reveal',[Sub_Front_Height,Top_Reveal])


        # if door being dropped in opening with empty interior, add default shelves and mark interior filled
        opening = self.selected_opening

        if opening:
            if opening.obj_bp.snap.interior_open == True:
                shelf_insert = cabinet_interiors.INSERT_Shelves()
                shelf_insert = product.add_assembly(shelf_insert)
                shelf_insert.obj_bp.parent = opening.obj_bp
                opening.obj_bp.snap.interior_open = False

                Width = opening.obj_x.snap.get_var('location.x', 'Width')
                Height = opening.obj_z.snap.get_var('location.z', 'Height')
                Depth = opening.obj_y.snap.get_var('location.y', 'Depth')
                Shelf_Qty = shelf_insert.get_prompt("Shelf Qty").get_var()
                Shelf_Setback = shelf_insert.get_prompt("Shelf Setback").get_var()
                Shelf_Thickness = shelf_insert.get_prompt("Shelf Thickness").get_var()

                for child in shelf_insert.obj_bp.children:
                    if "IS_CABINET_SHELF" in child:
                        adj_shelf = sn_types.Assembly(child)
                                 
                if adj_shelf:
                    adj_shelf.loc_y('Depth',[Depth])
                    adj_shelf.loc_z('((Height-(Shelf_Thickness*Shelf_Qty))/(Shelf_Qty+1))',[Height,Shelf_Thickness,Shelf_Qty])
                    adj_shelf.dim_x('Width',[Width])
                    adj_shelf.dim_y('-Depth+Shelf_Setback',[Depth,Shelf_Setback])
                    adj_shelf.dim_z('Shelf_Thickness',[Shelf_Thickness])
                    adj_shelf.get_prompt('Hide').set_formula('IF(Shelf_Qty==0,True,False)',[Shelf_Qty])
                    adj_shelf.get_prompt('Z Quantity').set_formula('Shelf_Qty',[Shelf_Qty])
                    adj_shelf.get_prompt('Z Offset').set_formula('((Height-(Shelf_Thickness*Shelf_Qty))/(Shelf_Qty+1))',[Height,Shelf_Thickness,Shelf_Qty])

                opening.run_all_calculators()

bpy.utils.register_class(OPS_KB_Doors_Drop)


class OPS_KB_Drawers_Drop(Operator, PlaceClosetInsert):
    bl_idname = "lm_cabinets.insert_drawers_drop"
    bl_label = "Custom drag and drop for drawers insert"

    def execute(self, context):
        return super().execute(context)    

    def confirm_placement(self, context):
        super().confirm_placement(context)

        has_splitter = False
        drawer_qty = 0
        splitter = None
        
        insert = sn_types.Assembly(self.insert.obj_bp)
        product = sn_types.Assembly(self.insert.obj_bp.parent)
        carcass = None
        opening = None

        if "IS_BP_SPLITTER" in product.obj_bp:
            has_splitter = True

        for obj_bp in insert.obj_bp.children:
            if "IS_BP_DRAWER_FRONT" in obj_bp:
                drawer_qty += 1
        
        # if insert is single drawer and there is no splitter, create splitte and set size to default for top drawer...
        if not has_splitter and drawer_qty == 1:
            self.insert.obj_bp["DEFAULT_OVERRIDE"] = True

            for obj_bp in product.obj_bp.children:
                if "IS_BP_CARCASS" in obj_bp:
                    carcass = sn_types.Assembly(obj_bp)
                if "IS_BP_OPENING" in obj_bp:
                    opening = sn_types.Assembly(obj_bp)

            props = cabinet_properties.get_scene_props().size_defaults

            splitter = frameless_splitters.INSERT_2_Vertical_Openings()
            drawer = INSERT_1_Drawer()

            splitter.opening_1_height = sn_unit.millimeter(float(props.top_drawer_front_height)) - sn_unit.inch(0.8)
            splitter.exterior_1 = drawer
            splitter.exterior_1.prompts = {'Half Overlay Bottom':True}

            splitter = product.add_assembly(splitter)
            opening.obj_bp.snap.interior_open = False
            opening.obj_bp.snap.exterior_open = False
            splitter.run_all_calculators()
            
            Width = product.obj_x.snap.get_var('location.x', 'Width')
            Height = product.obj_z.snap.get_var('location.z', 'Height')
            Depth = product.obj_y.snap.get_var('location.y', 'Depth')
            Left_Side_Thickness = carcass.get_prompt("Left Side Thickness").get_var()
            Right_Side_Thickness = carcass.get_prompt("Right Side Thickness").get_var()
            Top_Thickness = carcass.get_prompt("Top Thickness").get_var()
            Bottom_Thickness = carcass.get_prompt("Bottom Thickness").get_var()
            Top_Inset = carcass.get_prompt("Top Inset").get_var()
            Bottom_Inset = carcass.get_prompt("Bottom Inset").get_var()
            Back_Inset = carcass.get_prompt("Back Inset").get_var()

            splitter.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
            splitter.loc_y('Depth',[Depth])
            splitter.loc_z('Bottom_Inset',[Bottom_Inset])
            
            splitter.dim_x('Width-(Left_Side_Thickness+Right_Side_Thickness)',[Width,Left_Side_Thickness,Right_Side_Thickness])
            splitter.dim_y('fabs(Depth)-Back_Inset',[Depth,Back_Inset])
            splitter.dim_z('fabs(Height)-Bottom_Inset-Top_Inset',[Height,Bottom_Inset,Top_Inset])

            splitter.run_all_calculators()
           
    def finish(self, context):
            super().finish(context)

            if "DEFAULT_OVERRIDE" in self.insert.obj_bp:
                sn_utils.delete_object_and_children(self.insert.obj_bp)

            return {'FINISHED'}
          
bpy.utils.register_class(OPS_KB_Drawers_Drop)

#---------DOOR INSERTS

class INSERT_Base_Single_Door(Doors):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Base Single Door"
        self.door_type = "Base"
        self.door_swing = "Left Swing"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.prompts = {'Half Overlay Top':True}

class INSERT_Base_Single_Door_with_False_Front(Doors):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Base Single Door with False Front"
        self.door_type = "Base"
        self.door_swing = "Left Swing"
        self.false_front_qty = 1
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.prompts = {'Half Overlay Top':True}

class INSERT_Base_Double_Door(Doors):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Base Double Door"
        self.door_type = "Base"
        self.door_swing = "Double Door"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.prompts = {'Half Overlay Top':True}

class INSERT_Base_Double_Door_with_False_Front(Doors):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Base Double Door with False Front"
        self.door_type = "Base"
        self.door_swing = "Double Door"
        self.false_front_qty = 1
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.prompts = {'Half Overlay Top':True}

class INSERT_Base_Double_Door_with_2_False_Front(Doors):

     def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Base Double Door with 2 False Front"
        self.door_type = "Base"
        self.door_swing = "Double Door"
        self.false_front_qty = 2
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.prompts = {'Half Overlay Top':True}

class INSERT_Tall_Single_Door(Doors):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Tall Single Door"
        self.door_type = "Tall"
        self.door_swing = "Left Swing"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(84)
        self.depth = sn_unit.inch(23)
        self.prompts = {'Half Overlay Top':True}

class INSERT_Tall_Double_Door(Doors):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Tall Double Door"
        self.door_type = "Tall"
        self.door_swing = "Double Door"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(84)
        self.depth = sn_unit.inch(23)
        self.prompts = {'Half Overlay Top':True}

class INSERT_Upper_Single_Door(Doors):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Upper Single Door"
        self.door_type = "Upper"
        self.door_swing = "Left Swing"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(42)
        self.depth = sn_unit.inch(23)
        self.prompts = {'Half Overlay Top':True}

class INSERT_Upper_Double_Door(Doors):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Upper Double Door"
        self.door_type = "Upper"
        self.door_swing = "Double Door"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(42)
        self.prompts = {'Half Overlay Top':True}

class INSERT_Base_Pie_Cut_Door(Pie_Cut_Doors):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Base Pie Cut Door"
        self.door_type = "Base"
        self.door_swing = "Left Swing"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        
class INSERT_Upper_Pie_Cut_Door(Pie_Cut_Doors):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DOOR_CATEGORY_NAME
        self.assembly_name = "Upper Pie Cut Door"
        self.door_type = "Upper"
        self.door_swing = "Left Swing"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)

#---------DRAWER INSERTS
class INSERT_1_Drawer(Vertical_Drawers):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().exterior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DRAWER_CATEGORY_NAME
        self.assembly_name = "1 Drawer"
        self.door_type = "Drawer"
        self.direction = 'Vertical'
        self.drawer_qty = 1
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(6*2)
        self.depth = sn_unit.inch(19)
        self.mirror_y = False
        self.use_buyout_box = props.use_buyout_drawer_boxes

        
class INSERT_2_Drawer_Stack(Vertical_Drawers):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().exterior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DRAWER_CATEGORY_NAME
        self.assembly_name = "2 Drawer Stack"
        self.door_type = "Drawer"
        self.direction = 'Vertical'
        self.drawer_qty = 2
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(6*2)
        self.depth = sn_unit.inch(19)
        self.mirror_y = False
        self.use_buyout_box = props.use_buyout_drawer_boxes
        
class INSERT_3_Drawer_Stack(Vertical_Drawers):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().exterior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DRAWER_CATEGORY_NAME
        self.assembly_name = "3 Drawer Stack"
        self.door_type = "Drawer"
        self.direction = 'Vertical'
        self.drawer_qty = 3
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(6*3)
        self.depth = sn_unit.inch(19)
        self.mirror_y = False
        self.use_buyout_box = props.use_buyout_drawer_boxes
        
class INSERT_4_Drawer_Stack(Vertical_Drawers):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().exterior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DRAWER_CATEGORY_NAME
        self.assembly_name = "4 Drawer Stack"
        self.door_type = "Drawer"
        self.direction = 'Vertical'
        self.drawer_qty = 4
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(6*4)
        self.depth = sn_unit.inch(19)
        self.mirror_y = False
        self.use_buyout_box = props.use_buyout_drawer_boxes
        
class INSERT_Horizontal_Drawers(Horizontal_Drawers):
     
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_DRAWER_CATEGORY_NAME
        self.assembly_name = "Horizontal Drawers"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(6)
        self.depth = sn_unit.inch(20)
        self.mirror_y = False
        self.drawer_qty = 2
        