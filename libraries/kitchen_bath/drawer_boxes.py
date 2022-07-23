

import bpy
import math
from snap import sn_unit, sn_utils, sn_types
from os import path
from snap.libraries.closets import closet_paths
from . import cabinet_properties

PART = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")



def add_slide_token(part):

    # Depth = part.snap.get_prompt('dim_x','Depth')
    
    tokens = []
    tokens.append(part.add_machine_token('Slide Drilling' ,'SLIDE','1'))
    
    for token in tokens:
        token[1].dim_from_drawer_bottom = sn_unit.inch(.5)
        token[1].dim_to_first_hole = sn_unit.inch(1.5817)
        token[1].dim_to_second_hole = sn_unit.inch(6.6211)
        token[1].dim_to_third_hole = sn_unit.inch(10.4006)
        token[1].dim_to_fourth_hole = sn_unit.inch(15.44)
        token[1].dim_to_fifth_hole = sn_unit.inch(17.9596)
        token[1].face_bore_depth = sn_unit.inch(.5511)
        token[1].face_bore_dia = 5
        token[1].drawer_slide_clearance = sn_unit.inch(.5)
        
#---------SPEC GROUP POINTERS

class Wood_Drawer_Box(sn_types.Assembly):
    
    type_assembly = "NONE"
    placement_type = "INTERIOR"
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    mirror_y = False
    
    def draw(self):
        self.create_assembly()
        # self.obj_bp.mv.is_cabinet_drawer_box = True
        # self.obj_bp.is_cabinet_drawer_box = True
        # self.obj_bp.mv.comment = 'Wood Box'
        
        self.add_prompt("Hide", 'CHECKBOX', False)
        self.add_prompt("Drawer Side Thickness", 'DISTANCE', sn_unit.inch(.5))
        self.add_prompt("Front Back Thickness", 'DISTANCE', sn_unit.inch(.5))
        self.add_prompt("Drawer Bottom Thickness", 'DISTANCE', sn_unit.inch(.25))
        self.add_prompt("Bottom Dado Depth", 'DISTANCE', sn_unit.inch(.25))
        self.add_prompt("Bottom Z Location", 'DISTANCE', sn_unit.inch(.5))
        self.add_prompt("Drawer Slide Quantity", 'QUANTITY', 1)
        
        Drawer_Width = self.obj_x.snap.get_var('location.x', 'Drawer_Width')
        Drawer_Height = self.obj_z.snap.get_var('location.z', 'Drawer_Height')
        Drawer_Depth = self.obj_y.snap.get_var('location.y', 'Drawer_Depth')
        Drawer_Side_Thickness = self.get_prompt('Drawer Side Thickness').get_var()
        Front_Back_Thickness = self.get_prompt('Front Back Thickness').get_var()
        Drawer_Bottom_Thickness = self.get_prompt('Drawer Bottom Thickness').get_var()
        Bottom_Dado_Depth = self.get_prompt('Bottom Dado Depth').get_var()
        Bottom_Z_Location = self.get_prompt('Bottom Z Location').get_var()
        Hide = self.get_prompt('Hide').get_var()
        
        left_side_bp = self.add_assembly_from_file(PART)
        left_side = sn_types.Assembly(left_side_bp)
        left_side.set_name("Left Drawer Side")
        left_side.rot_x(value=math.radians(90))
        left_side.rot_z(value=math.radians(90))
        left_side.dim_x('Drawer_Depth',[Drawer_Depth])
        left_side.dim_y('Drawer_Height',[Drawer_Height])
        left_side.dim_z('Drawer_Side_Thickness',[Drawer_Side_Thickness])
        left_side.get_prompt('Hide').set_formula('Hide',[Hide])
        # left_side.cutpart("Drawer_Box_Parts")
        # left_side.edgebanding('Drawer_Box_Edges',l1 = True)
        # add_slide_token(left_side)
        
        right_side_bp = self.add_assembly_from_file(PART)
        right_side = sn_types.Assembly(right_side_bp)
        right_side.set_name("Right Drawer Side")
        right_side.loc_x('Drawer_Width',[Drawer_Width])
        left_side.rot_x(value=math.radians(90))
        left_side.rot_z(value=math.radians(90))
        right_side.dim_x('Drawer_Depth',[Drawer_Depth])
        right_side.dim_y('Drawer_Height',[Drawer_Height])
        right_side.dim_z('-Drawer_Side_Thickness',[Drawer_Side_Thickness])
        right_side.get_prompt('Hide').set_formula('Hide',[Hide])
        # right_side.cutpart("Drawer_Box_Parts")
        # right_side.edgebanding('Drawer_Box_Edges',l1 = True)
        # add_slide_token(right_side)
        
        front_bp = self.add_assembly_from_file(PART)
        front = sn_types.Assembly(front_bp)
        front.set_name("Sub Front")
        front.loc_x('Drawer_Side_Thickness',[Drawer_Side_Thickness])
        front.rot_x(value=math.radians(90))
        front.dim_x('Drawer_Width-(Drawer_Side_Thickness*2)',[Drawer_Width,Drawer_Side_Thickness])
        front.dim_y('Drawer_Height',[Drawer_Height])
        front.dim_z('-Front_Back_Thickness',[Front_Back_Thickness])
        front.get_prompt('Hide').set_formula('Hide',[Hide])
        # front.cutpart("Drawer_Box_Parts")
        # front.edgebanding('Drawer_Box_Edges',l1 = True)
                
        back_bp = self.add_assembly_from_file(PART)
        back = sn_types.Assembly(back_bp)
        back.set_name("Drawer Back")
        back.loc_x('Drawer_Side_Thickness',[Drawer_Side_Thickness])
        back.loc_y('Drawer_Depth',[Drawer_Depth])
        back.rot_x(value=math.radians(90))
        back.dim_x('Drawer_Width-(Drawer_Side_Thickness*2)',[Drawer_Width,Drawer_Side_Thickness])
        back.dim_y('Drawer_Height',[Drawer_Height])
        back.dim_z('Front_Back_Thickness',[Front_Back_Thickness])
        back.get_prompt('Hide').set_formula('Hide',[Hide])
        # back.cutpart("Drawer_Box_Parts")
        # back.edgebanding('Drawer_Box_Edges',l1 = True)
                
        bottom_bp = self.add_assembly_from_file(PART)
        bottom = sn_types.Assembly(bottom_bp)
        bottom.set_name("Drawer Bottom")
        bottom.loc_x('Drawer_Width-Drawer_Side_Thickness+Bottom_Dado_Depth',[Drawer_Width,Drawer_Side_Thickness,Bottom_Dado_Depth])
        bottom.loc_y('Front_Back_Thickness-Bottom_Dado_Depth',[Front_Back_Thickness,Bottom_Dado_Depth])
        bottom.loc_z('Bottom_Z_Location',[Bottom_Z_Location])
        bottom.rot_z(value=math.radians(90))
        bottom.dim_x('Drawer_Depth-(Drawer_Side_Thickness*2)+(Bottom_Dado_Depth*2)',[Drawer_Depth,Drawer_Side_Thickness,Bottom_Dado_Depth])
        bottom.dim_y('Drawer_Width-(Front_Back_Thickness*2)+(Bottom_Dado_Depth*2)',[Drawer_Width,Front_Back_Thickness,Bottom_Dado_Depth])
        bottom.dim_z('Drawer_Bottom_Thickness',[Drawer_Bottom_Thickness])
        bottom.get_prompt('Hide').set_formula('Hide',[Hide])
        # bottom.cutpart("Drawer_Box_Bottom")
                
        self.update()
    