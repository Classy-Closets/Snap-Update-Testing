import math

from snap import sn_types, sn_unit, sn_utils
from os import path
from snap.libraries.closets import closet_paths
from . import cabinet_properties

LIBRARY_NAME_SPACE = "sn_kitchen_bath"

ROOT_DIR = path.dirname(__file__)
COUNTERTOP_PARTS_DIR = path.join(ROOT_DIR,"assets","Kitchen Bath Assemblies")
CTOP = path.join(COUNTERTOP_PARTS_DIR, "Countertop Part.blend")
BACKSPLASH_PART = path.join(COUNTERTOP_PARTS_DIR, "Countertop Part.blend")
NOTCHED_CTOP = path.join(COUNTERTOP_PARTS_DIR, "Corner Notch Part.blend")
DIAGONAL_CTOP = path.join(COUNTERTOP_PARTS_DIR, "Chamfered Part.blend")


def add_part(assembly, path):
    part_bp = assembly.add_assembly_from_file(path)
    part = sn_types.Assembly(part_bp)
    part.obj_bp["IS_BP_CABINET_COUNTERTOP"] = True
    return part


#---------PRODUCT: COUNTERTOPS

class PRODUCT_Straight_Countertop(sn_types.Assembly):
    
    def __init__(self):
        self.library_name = "Countertops"
        self.category_name = "Countertops"
        self.assembly_name = "Straight Countertop"

        self.type_assembly = 'INSERT'
        self.placement_type = "EXTERIOR"
        self.id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"

        self.width = sn_unit.inch(30)
        self.height = sn_unit.inch(5.5)
        self.depth = sn_unit.inch(24)
        self.height_above_floor = sn_unit.inch(34.1)
        
    def draw(self):
        self.create_assembly()
        self.obj_bp["IS_BP_CABINET_COUNTERTOP"] = True
        
        self.add_prompt("Add Backsplash",'CHECKBOX',True)
        self.add_prompt("Add Left Backsplash",'CHECKBOX',False)
        self.add_prompt("Add Right Backsplash",'CHECKBOX',False)
        self.add_prompt("Side Splash Setback",'DISTANCE',sn_unit.inch(2.75))
        self.add_prompt("Deck Thickness",'DISTANCE',sn_unit.inch(1.5))
        self.add_prompt("Splash Thickness",'DISTANCE',sn_unit.inch(.75))
        
        Product_Width = self.obj_x.snap.get_var('location.x','Product_Width')
        Product_Height = self.obj_z.snap.get_var('location.z','Product_Height')
        Product_Depth =  self.obj_y.snap.get_var('location.y','Product_Depth')
        Add_Backsplash = self.get_prompt('Add Backsplash').get_var()
        Add_Left_Backsplash = self.get_prompt('Add Left Backsplash').get_var()
        Add_Right_Backsplash = self.get_prompt('Add Right Backsplash').get_var()
        Side_Splash_Setback = self.get_prompt('Side Splash Setback').get_var()
        Deck_Thickness = self.get_prompt('Deck Thickness').get_var()
        Splash_Thickness = self.get_prompt('Splash Thickness').get_var()
        
        deck = add_part(self, CTOP)
        deck.set_name("Countertop Deck")
        deck.dim_x("Product_Width",[Product_Width])
        deck.dim_y("Product_Depth",[Product_Depth])
        deck.dim_z("Deck_Thickness",[Deck_Thickness])
        # deck.material("Countertop_Surface")

        splash = add_part(self, BACKSPLASH_PART)
        splash.set_name("Backsplash")
        splash.loc_z('Deck_Thickness',[Deck_Thickness])
        splash.rot_x(value=math.radians(90))
        splash.dim_x("Product_Width",[Product_Width]) 
        splash.dim_y("Product_Height-Deck_Thickness",[Product_Height,Deck_Thickness]) 
        splash.dim_z("Splash_Thickness",[Splash_Thickness]) 
        splash.get_prompt("Hide").set_formula("IF(Add_Backsplash,False,True)",[Add_Backsplash])
        # splash.material("Countertop_Surface")

        left_splash = add_part(self, BACKSPLASH_PART)
        left_splash.set_name("Left Backsplash")
        left_splash.loc_y("IF(Add_Backsplash,-Splash_Thickness,0)",[Splash_Thickness,Add_Backsplash])
        left_splash.loc_z('Deck_Thickness',[Deck_Thickness])
        left_splash.rot_x(value=math.radians(90))
        left_splash.rot_z(value=math.radians(-90))
        left_splash.dim_x("fabs(Product_Depth)-Side_Splash_Setback-Splash_Thickness",[Product_Depth,Side_Splash_Setback,Splash_Thickness])
        left_splash.dim_y("Product_Height-Deck_Thickness",[Product_Height,Deck_Thickness]) 
        left_splash.dim_z("-Splash_Thickness",[Splash_Thickness])
        left_splash.get_prompt("Hide").set_formula("IF(Add_Left_Backsplash,False,True)",[Add_Left_Backsplash])
        # left_splash.material("Countertop_Surface")

        right_splash = add_part(self, BACKSPLASH_PART)
        right_splash.set_name("Rear Backsplash")
        right_splash.loc_x("Product_Width",[Product_Width])
        right_splash.loc_y("IF(Add_Backsplash,-Splash_Thickness,0)",[Splash_Thickness,Add_Backsplash])
        right_splash.loc_z('Deck_Thickness',[Deck_Thickness])
        right_splash.rot_x(value=math.radians(90))
        right_splash.rot_z(value=math.radians(-90))
        right_splash.dim_x("fabs(Product_Depth)-Side_Splash_Setback-Splash_Thickness",[Product_Depth,Side_Splash_Setback,Splash_Thickness])
        right_splash.dim_y("Product_Height-Deck_Thickness",[Product_Height,Deck_Thickness]) 
        right_splash.dim_z("Splash_Thickness",[Splash_Thickness])
        right_splash.get_prompt("Hide").set_formula("IF(Add_Right_Backsplash,False,True)",[Add_Right_Backsplash])
        # right_splash.material("Countertop_Surface")
        
        self.update()
        
class Corner_Countertop(sn_types.Assembly):

    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    corner_type = "Notched"

    def update(self):
        super().update()
        self.obj_bp["IS_BP_CABINET_COUNTERTOP"] = True

        self.obj_bp.location.z = self.height_above_floor
        self.obj_x.location.x = self.width
        self.obj_y.location.y = self.depth
        self.obj_z.location.z = self.height
    
    def draw(self):
        self.create_assembly()

        self.add_prompt("Left Side Depth", 'DISTANCE', sn_unit.inch(24.0))
        self.add_prompt("Right Side Depth", 'DISTANCE', sn_unit.inch(24.0))
        self.add_prompt("Add Left Rear Backsplash", 'CHECKBOX', True)
        self.add_prompt("Add Right Rear Backsplash", 'CHECKBOX', True)
        self.add_prompt("Add Left Backsplash", 'CHECKBOX', False)
        self.add_prompt("Add Right Backsplash", 'CHECKBOX', False)
        self.add_prompt("Side Splash Setback", 'DISTANCE', sn_unit.inch(2.75))
        self.add_prompt("Deck Thickness", 'DISTANCE', sn_unit.inch(1.5))
        self.add_prompt("Splash Thickness", 'DISTANCE', sn_unit.inch(.75))
        
        #VARS
        Product_Width = self.obj_x.snap.get_var('location.x', 'Product_Width')
        Product_Height = self.obj_z.snap.get_var('location.z', 'Product_Height')
        Product_Depth = self.obj_y.snap.get_var('location.y', 'Product_Depth')
        Left_Side_Depth = self.get_prompt('Left Side Depth').get_var()
        Right_Side_Depth = self.get_prompt('Right Side Depth').get_var()
        Add_Left_Backsplash = self.get_prompt('Add Left Backsplash').get_var()
        Add_Right_Backsplash = self.get_prompt('Add Right Backsplash').get_var()
        Add_Left_Rear_Backsplash = self.get_prompt('Add Left Rear Backsplash').get_var()
        Add_Right_Rear_Backsplash = self.get_prompt('Add Right Rear Backsplash').get_var()
        Side_Splash_Setback = self.get_prompt('Side Splash Setback').get_var()
        Deck_Thickness = self.get_prompt('Deck Thickness').get_var()
        Splash_Thickness = self.get_prompt('Splash Thickness').get_var()
        
        if self.corner_type == 'Notched':
            deck = add_part(self, NOTCHED_CTOP)
        else:
            deck = add_part(self, DIAGONAL_CTOP)
        deck.set_name("Countertop Deck")
        deck.dim_x("Product_Width",[Product_Width])
        deck.dim_y("Product_Depth",[Product_Depth])
        deck.dim_z("Deck_Thickness",[Deck_Thickness])
        deck.get_prompt("Left Depth").set_formula("Left_Side_Depth",[Left_Side_Depth])
        deck.get_prompt("Right Depth").set_formula("Right_Side_Depth",[Right_Side_Depth])
        # deck.material("Countertop_Surface")
        
        rear_left_splash = add_part(self, BACKSPLASH_PART)
        rear_left_splash.set_name("Left Rear Backsplash")
        rear_left_splash.loc_z('Deck_Thickness',[Deck_Thickness])
        rear_left_splash.rot_x(value=math.radians(90)) 
        rear_left_splash.rot_z(value=math.radians(-90))
        rear_left_splash.dim_x("fabs(Product_Depth)",[Product_Depth])
        rear_left_splash.dim_y("Product_Height-Deck_Thickness",[Product_Height,Deck_Thickness]) 
        rear_left_splash.dim_z("-Splash_Thickness",[Splash_Thickness])
        rear_left_splash.get_prompt("Hide").set_formula("IF(Add_Left_Rear_Backsplash,False,True)",[Add_Left_Rear_Backsplash])
        # rear_left_splash.material("Countertop_Surface")
        
        rear_rear_splash = add_part(self, BACKSPLASH_PART)
        rear_rear_splash.set_name("Right Rear Backsplash")
        rear_rear_splash.loc_x('IF(Add_Left_Rear_Backsplash,Splash_Thickness,0)',[Splash_Thickness,Add_Left_Rear_Backsplash])
        rear_rear_splash.loc_z('Deck_Thickness',[Deck_Thickness])
        rear_rear_splash.rot_x(value=math.radians(90)) 
        rear_rear_splash.dim_x("Product_Width-IF(Add_Left_Rear_Backsplash,Splash_Thickness,0)",[Product_Width,Add_Left_Rear_Backsplash,Splash_Thickness])
        rear_rear_splash.dim_y("Product_Height-Deck_Thickness",[Product_Height,Deck_Thickness]) 
        rear_rear_splash.dim_z("Splash_Thickness",[Splash_Thickness])
        rear_rear_splash.get_prompt("Hide").set_formula("IF(Add_Right_Rear_Backsplash,False,True)",[Add_Right_Rear_Backsplash])
        # rear_rear_splash.material("Countertop_Surface")
        
        left_splash = add_part(self, BACKSPLASH_PART)
        left_splash.set_name("Left Backsplash")
        left_splash.loc_x('IF(Add_Left_Rear_Backsplash,Splash_Thickness,0)',[Add_Left_Rear_Backsplash,Splash_Thickness])
        left_splash.loc_y("Product_Depth",[Product_Depth])
        left_splash.loc_z('Deck_Thickness',[Deck_Thickness])
        left_splash.rot_x(value=math.radians(90))
        left_splash.dim_x("Left_Side_Depth-Side_Splash_Setback-Splash_Thickness",[Left_Side_Depth,Side_Splash_Setback,Splash_Thickness])
        left_splash.dim_y("Product_Height-Deck_Thickness",[Product_Height,Deck_Thickness])
        left_splash.dim_z("-Splash_Thickness",[Splash_Thickness])
        left_splash.get_prompt("Hide").set_formula("IF(Add_Left_Backsplash,False,True)",[Add_Left_Backsplash])
        # left_splash.material("Countertop_Surface")
        
        right_splash = add_part(self, BACKSPLASH_PART) 
        right_splash.set_name("Rear Backsplash")
        right_splash.loc_x("Product_Width",[Product_Width])
        right_splash.loc_y("IF(Add_Right_Rear_Backsplash,-Splash_Thickness,0)",[Splash_Thickness,Add_Right_Rear_Backsplash])
        right_splash.loc_z('Deck_Thickness',[Deck_Thickness])
        right_splash.rot_x(value=math.radians(90))
        right_splash.rot_z(value=math.radians(-90))
        right_splash.dim_x("Right_Side_Depth-Side_Splash_Setback-Splash_Thickness",[Right_Side_Depth,Side_Splash_Setback,Splash_Thickness])
        right_splash.dim_y("Product_Height-Deck_Thickness",[Product_Height,Deck_Thickness]) 
        right_splash.dim_z("Splash_Thickness",[Splash_Thickness])
        right_splash.get_prompt("Hide").set_formula("IF(Add_Right_Backsplash,False,True)",[Add_Right_Backsplash])
        # right_splash.material("Countertop_Surface")
        
        self.update()
        
class PRODUCT_Notched_Corner_Countertop(Corner_Countertop):
    
    def __init__(self):
        self.library_name = "Countertops"
        self.category_name = "Countertops"
        self.assembly_name = "Notched Corner Countertop"
        self.placement_type = "Corner"
        self.corner_type = "Notched"
        self.id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(5.5)
        self.depth = sn_unit.inch(36)
        self.height_above_floor = sn_unit.inch(34.1)        
        
class PRODUCT_Diagonal_Corner_Countertop(Corner_Countertop):
    
    def __init__(self):
        self.library_name = "Countertops"
        self.category_name = "Countertops"
        self.assembly_name = "Diagonal Corner Countertop"
        self.placement_type = "Corner"
        self.corner_type = "Diagonal"
        self.id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(5.5)
        self.depth = sn_unit.inch(36)
        self.height_above_floor = sn_unit.inch(34.1)           

        
