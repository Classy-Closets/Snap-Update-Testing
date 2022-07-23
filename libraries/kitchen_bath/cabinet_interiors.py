import bpy
from snap import sn_unit, sn_types
from . import drawer_boxes
# from . import cabinet_machining
from . import cabinet_properties
from snap.libraries.closets import closet_paths
from os import path
import math

LIBRARY_NAME_SPACE = "sn_kitchen_bath"
ROOT_PATH = path.join(path.dirname(__file__),"Cabinet Assemblies")

SHELVES = path.join(ROOT_PATH,"Shelves","Shelves.blend")
SHELF = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")
DIVIDER = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")
DIVISION = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")
# ADJ_MACHINING = path.join(ROOT_PATH,"Machining","Adjustable Shelf Holes.blend")

# def add_adj_shelf_machining(part,insert):
    
#     Height = insert.obj_z.snap.get_var('location.z','Height')
#     Width = insert.obj_x.snap.get_var('location.x','Width')
#     Depth = insert.obj_y.snap.get_var('location.y','Depth')

#     Part_Width = part.get_prompt('dim_y').get_var('Part_Width')
#     Part_Z_Loc = part.get_prompt('loc_z').get_var('Part_Z_Loc')
#     Adj_Shelf_Setback = insert.get_prompt("Adj Shelf Setback").get_var()
#     Space_From_Front = insert.get_prompt("Space From Front").get_var()
#     Space_From_Rear = insert.get_prompt("Space From Rear").get_var()
#     Space_From_Top = insert.get_prompt("Space From Top").get_var()
#     Space_From_Bottom = insert.get_prompt("Space From Bottom").get_var()
#     Shelf_Hole_Spacing = insert.get_prompt("Shelf Hole Spacing").get_var()
#     Shelf_Clip_Gap = insert.get_prompt("Shelf Clip Gap").get_var()
#     Adj_Shelf_Qty = insert.get_prompt("Adj Shelf Qty").get_var()
    
#     tokens = []
#     tokens.append(part.add_machine_token('Left Shelf Drilling' ,'SHELF','3'))
#     tokens.append(part.add_machine_token('Right Shelf Drilling' ,'SHELF','4'))

#     for token in tokens:
#         token[1].add_driver(token[0],'space_from_bottom','Part_Z_Loc-Space_From_Bottom',[Part_Z_Loc,Space_From_Bottom])
#         token[1].add_driver(token[0],'dim_to_first_row','Space_From_Front',[Space_From_Front])
#         token[1].face_bore_depth = sn_unit.inch(.5)
#         token[1].add_driver(token[0],'space_from_top','Height-Part_Z_Loc-Space_From_Top',[Height,Part_Z_Loc,Space_From_Top])
#         token[1].add_driver(token[0],'dim_to_second_row','fabs(Part_Width)-Space_From_Rear',[Part_Width,Space_From_Rear])
#         token[1].face_bore_dia = 5
#         token[1].shelf_hole_spacing = sn_unit.millimeter(32)
#         token[1].add_driver(token[0],'shelf_clip_gap','Shelf_Clip_Gap',[Shelf_Clip_Gap])
#         token[1].reverse_direction = False

#---------ASSEMBLY INSTRUCTIONS
def add_part(assembly, path):
    part_bp = assembly.add_assembly_from_file(path)
    part = sn_types.Assembly(part_bp)
    part.obj_bp.sn_closets.is_panel_bp = True
    return part

class Simple_Shelves(sn_types.Assembly):
    
    library_name = "Cabinet Interiors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    mirror_y = False
    
    carcass_type = "" # {Base, Tall, Upper, Sink, Suspended}
    open_name = ""
    shelf_qty = 1
    
    def add_common_prompts(self): 

        self.add_prompt("Shelf Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Edgebanding Thickness", 'DISTANCE', sn_unit.inch(.1))

    def add_adj_prompts(self):
        props = cabinet_properties.get_scene_props().interior_defaults
        
        self.add_prompt("Shelf Qty", 'QUANTITY', self.shelf_qty)
        self.add_prompt("Shelf Setback", 'DISTANCE', props.adj_shelf_setback)

    def add_shelves(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Height = self.obj_z.snap.get_var('location.z','Height')
        Depth =  self.obj_y.snap.get_var('location.y','Depth')
        Shelf_Qty = self.get_prompt("Shelf Qty").get_var()
        Shelf_Setback = self.get_prompt("Shelf Setback").get_var()
        Shelf_Thickness = self.get_prompt("Shelf Thickness").get_var()

        adj_shelf = add_part(self, SHELF)
        adj_shelf.obj_bp["IS_CABINET_SHELF"] = True
        adj_shelf.set_name("Adjustable Shelf")
        adj_shelf.loc_y('Depth',[Depth])
        adj_shelf.loc_z('((Height-(Shelf_Thickness*Shelf_Qty))/(Shelf_Qty+1))',[Height,Shelf_Thickness,Shelf_Qty])
        adj_shelf.dim_x('Width',[Width])
        adj_shelf.dim_y('-Depth+Shelf_Setback',[Depth,Shelf_Setback])
        adj_shelf.dim_z('Shelf_Thickness',[Shelf_Thickness])
        adj_shelf.get_prompt('Hide').set_formula('IF(Shelf_Qty==0,True,False)',[Shelf_Qty])
        adj_shelf.get_prompt('Z Quantity').set_formula('Shelf_Qty',[Shelf_Qty])
        adj_shelf.get_prompt('Z Offset').set_formula('((Height-(Shelf_Thickness*Shelf_Qty))/(Shelf_Qty+1))',[Height,Shelf_Thickness,Shelf_Qty])
        # adj_shelf.cutpart("Cabinet_Shelf")
        # adj_shelf.edgebanding('Cabinet_Interior_Edges',l1 = True, w1 = True, l2 = True, w2 = True)

    def draw(self):
        self.create_assembly()
        self.obj_bp["IS_BP_SHELVES"] = True
        props = self.obj_bp.sn_closets
        props.is_shelf_bp = True
        
        self.add_common_prompts()
        self.add_adj_prompts()
        self.add_shelves()

        self.update()    
    
class Shelves(sn_types.Assembly):
    
    library_name = "Cabinet Interiors"
    type_assembly = "INSERT"
    placement_type = "INTERIOR"
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    mirror_y = False
    
    carcass_type = "" # {Base, Tall, Upper, Sink, Suspended}
    open_name = ""
    shelf_qty = 1
    add_adjustable_shelves = True
    add_fixed_shelves = False
    
    def add_common_prompts(self):
        sgi = self.get_prompt('cabinetlib.spec_group_index').get_var('sgi')
        self.add_prompt("Edgebanding Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.get_prompt('Edgebanding Thickness').set_formula('EDGE_THICKNESS(sgi,"Cabinet_Interior_Edges' + self.open_name + '")',[sgi])
    
    def add_adj_prompts(self):
        props = cabinet_properties.get_scene_props().interior_defaults
        
        self.add_prompt("Adj Shelf Qty", 'QUANTITY', self.shelf_qty)
        self.add_prompt("Adj Shelf Setback", 'DISTANCE', props.adj_shelf_setback)
        self.add_prompt("Space From Front", 'DISTANCE', sn_unit.inch(1.5))
        self.add_prompt("Space From Rear", 'DISTANCE', sn_unit.inch(1.5))
        self.add_prompt("Space From Top", 'DISTANCE', sn_unit.inch(1.5))
        self.add_prompt("Space From Bottom", 'DISTANCE', sn_unit.inch(1.5))
        self.add_prompt("Shelf Hole Spacing", 'DISTANCE', sn_unit.inch(32/25.4))
        self.add_prompt("Shelf Clip Gap", 'DISTANCE', sn_unit.inch(.125))
        self.add_prompt("Adjustable Shelf Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Shelf Pin Quantity", 'QUANTITY', 0)

        sgi = self.get_prompt('cabinetlib.spec_group_index').get_var('sgi')
        self.get_prompt('Adjustable Shelf Thickness').set_formula('THICKNESS(sgi,"Cabinet_Shelf' + self.open_name + '")',[sgi])

    def add_fixed_prompts(self):
        props = cabinet_properties.get_scene_props().interior_defaults

        self.add_prompt("Fixed Shelf Qty", 'QUANTITY', 0)
        self.add_prompt("Fixed Shelf Setback", 'DISTANCE', props.fixed_shelf_setback)
        self.add_prompt("Fixed Shelf Thickness", 'DISTANCE', sn_unit.inch(.75))
        
        sgi = self.get_prompt('cabinetlib.spec_group_index').get_var('sgi')
        self.get_prompt('Fixed Shelf Thickness').set_formula('THICKNESS(sgi,"Cabinet_Shelf' + self.open_name + '")',[sgi])
        
    def add_advanced_frameless_prompts(self):
        self.add_prompt("Shelf Row Quantity", 'QUANTITY', 0)
        
        adj_qty = self.get_prompt('Adj Shelf Qty').get_var()
        fixed_qty = self.get_prompt('Fixed Shelf Qty').get_var()
        
        self.get_prompt('Shelf Row Quantity').set_formula('IF(adj_qty>fixed_qty,adj_qty,fixed_qty)',[adj_qty,fixed_qty])
        
    def add_adjustable_shelves(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Height =self.obj_z.snap.get_var('location.z','Height')
        Depth = self.obj_y.snap.get_var('location.y','Depth')
        Adj_Shelf_Qty = self.get_prompt("Adj Shelf Qty").get_var()
        Adj_Shelf_Setback = self.get_prompt("Adj Shelf Setback").get_var()
        Adjustable_Shelf_Thickness = self.prompt("Adjustable Shelf Thickness").get_var()
        Shelf_Clip_Gap = self.get_prompt("Shelf Clip Gap").get_var()

        for i in range(1,6):
            spacing = '((Height-(Adjustable_Shelf_Thickness*Adj_Shelf_Qty))/(Adj_Shelf_Qty+1))'
            adj_shelf = add_part(self, SHELF)
            adj_shelf.set_name("Adjustable Shelf")

            adj_shelf.loc_x('Shelf_Clip_Gap',[Shelf_Clip_Gap])
            adj_shelf.loc_y('Depth',[Depth])
            adj_shelf.loc_z('(' + spacing + ')*IF(' + str(i) + '>Adj_Shelf_Qty,0,' + str(i) + ')+IF(' + str(i) + '>Adj_Shelf_Qty,0,Adjustable_Shelf_Thickness*' + str(i - 1) + ')',
                            [Height,Adjustable_Shelf_Thickness,Adj_Shelf_Qty])

            adj_shelf.dim_x('Width-(Shelf_Clip_Gap*2)',[Width,Shelf_Clip_Gap])
            adj_shelf.dim_y('-Depth+Adj_Shelf_Setback',[Depth,Adj_Shelf_Setback])
            adj_shelf.dim_z('Adjustable_Shelf_Thickness',[Adjustable_Shelf_Thickness])
            adj_shelf.get_prompt('Hide').set_formula('IF(' + str(i) + '>Adj_Shelf_Qty,True,False)',[Adj_Shelf_Qty])
            # adj_shelf.cutpart("Cabinet_Shelf")
            # adj_shelf.edgebanding('Cabinet_Interior_Edges',l1 = True, w1 = True, l2 = True, w2 = True)
            # if i == 1:
            #     add_adj_shelf_machining(adj_shelf,self)
            
    # def add_adjustable_shelf_holes(self):
    #     Width = self.obj_x.snap.get_var('location.x','Width')
    #     Height =self.obj_z.snap.get_var('location.z','Height')
    #     Depth = self.obj_y.snap.get_var('location.y','Depth')
    #     Adj_Shelf_Setback = self.get_prompt("Adj Shelf Setback").get_var()
    #     Space_From_Front = self.get_prompt("Space From Front").get_var()
    #     Space_From_Rear = self.get_prompt("Space From Rear").get_var()
    #     Space_From_Top = self.get_prompt("Space From Top").get_var()
    #     Space_From_Bottom = self.get_prompt("Space From Bottom").get_var()
    #     Shelf_Hole_Spacing = self.get_prompt("Shelf Hole Spacing").get_var()
    #     Adj_Shelf_Qty = self.get_prompt("Adj Shelf Qty").get_var()
        
    #     shelf_holes_bp = self.add_assembly_from_file(ADJ_MACHINING)
    #     shelf_holes = sn_types.Assembly(shelf_holes_bp)
    #     shelf_holes.set_name("Adjustable Shelf Holes")

    #     shelf_holes.loc_y('Adj_Shelf_Setback',[Adj_Shelf_Setback])
    #     # shelf_holes.loc_z('',[])

    #     shelf_holes.dim_x('Width',[Width])
    #     shelf_holes.dim_y('Depth-Adj_Shelf_Setback',[Depth,Adj_Shelf_Setback])
    #     shelf_holes.dim_z('Height',[Height])

    #     shelf_holes.get_prompt('Hide').set_formula('IF(Adj_Shelf_Qty>0,False,True)',[Adj_Shelf_Qty])
    #     shelf_holes.get_prompt('Space From Bottom').set_formula('Space_From_Bottom',[Space_From_Bottom])
    #     shelf_holes.get_prompt('Space From Top').set_formula('Space_From_Top',[Space_From_Top])
    #     shelf_holes.get_prompt('Space From Front').set_formula('Space_From_Front',[Space_From_Front])
    #     shelf_holes.get_prompt('Space From Rear').set_formula('Space_From_Rear',[Space_From_Rear])
    #     shelf_holes.get_prompt('Shelf Hole Spacing').set_formula('Shelf_Hole_Spacing',[Shelf_Hole_Spacing])
        
    def add_fixed_shelves(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Height =self.obj_z.snap.get_var('location.z','Height')
        Depth = self.obj_y.snap.get_var('location.y','Depth')
        Fixed_Shelf_Qty = self.get_prompt("Fixed Shelf Qty").get_var()
        Fixed_Shelf_Setback = self.get_prompt("Fixed Shelf Setback").get_var()
        Fixed_Shelf_Thickness = self.get_prompt("Fixed Shelf Thickness").get_var()

        for i in range(1,6):
            spacing = '((Height-(Fixed_Shelf_Thickness*Fixed_Shelf_Qty))/(Fixed_Shelf_Qty+1))'
            fix_shelf = add_part(self, SHELF)
            fix_shelf.set_name("Fixed Shelf")
   
            fix_shelf.loc_y('Depth',[Depth])
            fix_shelf.loc_z('(' + spacing + ')*IF(' + str(i) + '>Fixed_Shelf_Qty,0,' + str(i) + ')+IF(' + str(i) + '>Fixed_Shelf_Qty,0,Fixed_Shelf_Thickness*' + str(i - 1) + ')',
                            [Height,Fixed_Shelf_Thickness,Fixed_Shelf_Qty])

            fix_shelf.dim_x('Width',[Width])
            fix_shelf.dim_y('-Depth+Fixed_Shelf_Setback',[Depth,Fixed_Shelf_Setback])
            fix_shelf.dim_z('Fixed_Shelf_Thickness',[Fixed_Shelf_Thickness])
            fix_shelf.get_prompt('Hide').set_formula('IF(' + str(i) + '>Fixed_Shelf_Qty,True,False)',[Fixed_Shelf_Qty])

            # fix_shelf.cutpart("Cabinet_Shelf")
            # fix_shelf.edgebanding('Cabinet_Interior_Edges',l1 = True)
            # cabinet_machining.add_drilling(fix_shelf)
            
    def draw(self):
        self.create_assembly()
        
        self.add_common_prompts()
        
        if self.add_adjustable_shelves:
            self.add_adj_prompts()
            self.add_adjustable_shelves()
            # self.add_adjustable_shelf_holes()
            
        if self.add_fixed_shelves:
            self.add_fixed_prompts()
            self.add_fixed_shelves()
            
        if self.add_adjustable_shelves and self.add_fixed_shelves:
            self.add_advanced_frameless_prompts()
            
        self.obj_bp["IS_BP_SHELVES"]
        props = self.obj_bp.sn_closets
        props.is_shelf_bp = True
        
        self.update()
        
class Dividers(sn_types.Assembly):
    
    library_name = "Cabinet Interiors"
    type_assembly = "INSERT"
    placement_type = "INTERIOR"
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    mirror_y = False
    
    carcass_type = "" # {Base, Tall, Upper, Sink, Suspended}
    open_name = ""
    shelf_qty = 1
    add_adjustable_shelves = True
    add_fixed_shelves = False
    
    def add_common_prompts(self):
        self.add_prompt("Fixed Shelf Qty",'QUANTITY',self.shelf_qty)
        self.add_prompt("Divider Qty Per Row",'QUANTITY',2)
        self.add_prompt("Divider Setback",'DISTANCE',sn_unit.inch(0.25))
        
        self.add_prompt("Shelf Setback",'DISTANCE',0)
        self.add_prompt("Shelf Thickness",'DISTANCE',sn_unit.inch(0.75))
        self.add_prompt("Divider Thickness",'DISTANCE',sn_unit.inch(0.25))

        self.add_prompt("Edgebanding Thickness", 'DISTANCE', sn_unit.inch(.75))
    
        sgi = self.get_prompt('cabinetlib.spec_group_index').get_var('sgi')
        self.get_prompt('Divider Thickness').set_formula('THICKNESS(sgi,"Cabinet_Divider' + self.open_name +'")',[sgi])
        self.get_prompt('Shelf Thickness').set_formula('THICKNESS(sgi,"Cabinet_Shelf' + self.open_name +'")',[sgi])
        self.get_prompt('Edgebanding Thickness').set_formula('EDGE_THICKNESS(sgi,"Cabinet_Interior_Edges' + self.open_name + '")',[sgi])
    
    def add_dividers(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Height =self.obj_z.snap.get_var('location.z','Height')
        Depth = self.obj_y.snap.get_var('location.y','Depth')
        Shelf_Thickness = self.get_prompt('Shelf Thickness').get_var()
        Shelf_Setback = self.get_prompt('Shelf Setback').get_var()
        Divider_Setback = self.get_prompt('Divider Setback').get_var()
        Divider_Thickness = self.get_prompt('Divider Thickness').get_var()
        Fixed_Shelf_Qty = self.get_prompt('Fixed Shelf Qty').get_var()
        Divider_Qty_Per_Row = self.get_prompt('Divider Qty Per Row').get_var()

        divider = add_part(self, DIVIDER)
        divider.set_name("Divider")

        divider.loc_x("Width-(Width/(Divider_Qty_Per_Row+1))+(Divider_Thickness/2)",[Width,Divider_Thickness,Divider_Qty_Per_Row])
        divider.loc_y("Depth",[Depth])
  
        divider.rot_y(value=math.radians(-90))
 
        divider.dim_x("(Height-(Shelf_Thickness*Fixed_Shelf_Qty))/(Fixed_Shelf_Qty+1)",[Height,Shelf_Thickness,Fixed_Shelf_Qty])
        divider.dim_y("(Depth*-1)+Divider_Setback+Shelf_Setback",[Depth,Divider_Setback,Shelf_Setback])
        divider.dim_z("Divider_Thickness",[Divider_Thickness])

        divider.get_prompt('Z Quantity').set_formula('Divider_Qty_Per_Row',[Divider_Qty_Per_Row])
        divider.get_prompt('Z Offset').set_formula('Width/(Divider_Qty_Per_Row+1)',[Width,Divider_Qty_Per_Row])
        divider.get_prompt('X Quantity').set_formula('Fixed_Shelf_Qty+1',[Fixed_Shelf_Qty])
        divider.get_prompt('X Offset').set_formula('Height/(Fixed_Shelf_Qty+1)+(Shelf_Thickness/(Fixed_Shelf_Qty+1))',[Height,Fixed_Shelf_Qty,Shelf_Thickness])

        # divider.cutpart("Cabinet_Divider")
        # divider.edgebanding('Cabinet_Interior_Edges',l1 = True)
        
    def add_fixed_shelves(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Height =self.obj_z.snap.get_var('location.z','Height')
        Depth = self.obj_y.snap.get_var('location.y','Depth')
        Fixed_Shelf_Qty = self.get_prompt("Fixed Shelf Qty").get_var()
        Shelf_Setback = self.get_prompt("Shelf Setback").get_var()
        Shelf_Thickness = self.get_prompt("Shelf Thickness").get_var()

        fix_shelf = add_part(self, SHELF)
        fix_shelf.set_name("Fixed Shelf")

        fix_shelf.loc_y("Depth",[Depth])
        fix_shelf.loc_z("(Height-(Shelf_Thickness*Fixed_Shelf_Qty))/(Fixed_Shelf_Qty+1)",[Height,Shelf_Thickness,Fixed_Shelf_Qty])

        fix_shelf.dim_x("Width",[Width])
        fix_shelf.dim_y("(Depth*-1)+Shelf_Setback",[Depth,Shelf_Setback])
        fix_shelf.dim_z("Shelf_Thickness",[Shelf_Thickness])

        fix_shelf.get_prompt('Hide').set_formula('IF(Fixed_Shelf_Qty==0,True,False)',[Fixed_Shelf_Qty])
        fix_shelf.get_prompt('Z Quantity').set_formula('Fixed_Shelf_Qty',[Fixed_Shelf_Qty])
        fix_shelf.get_prompt('Z Offset').set_formula('Height/(Fixed_Shelf_Qty+1)+(Shelf_Thickness/(Fixed_Shelf_Qty+1))',[Height,Fixed_Shelf_Qty,Shelf_Thickness])

        # fix_shelf.cutpart("Cabinet_Shelf")
        # fix_shelf.edgebanding('Cabinet_Interior_Edges',l1 = True)

    def draw(self):
        self.create_assembly()
        
        self.add_common_prompts()
        self.add_fixed_shelves()
        self.add_dividers()
        
        self.update()
        
class Divisions(sn_types.Assembly):
    
    library_name = "Cabinet Interiors"
    type_assembly = "INSERT"
    placement_type = "INTERIOR"
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".interior_prompts"
    mirror_y = False
    
    carcass_type = "" # Base, Tall, Upper, Sink, Suspended
    open_name = ""
    shelf_qty = 1
    add_adjustable_shelves = True
    add_fixed_shelves = False
    
    def add_common_prompts(self):
        self.add_prompt("Division Qty", 'QUANTITY', 2)
        self.add_prompt("Division Setback", 'DISTANCE', sn_unit.inch(0.25))
        self.add_prompt("Adj Shelf Rows", 'QUANTITY', 2)
        self.add_prompt("Fixed Shelf Rows", 'QUANTITY', 0)

        self.add_prompt("Division Thickness", 'DISTANCE', sn_unit.inch(0.75))
        self.add_prompt("Shelf Setback", 'DISTANCE', sn_unit.inch(0.25))
        self.add_prompt("Shelf Holes Space From Bottom", 'DISTANCE', sn_unit.inch(2.5))
        self.add_prompt("Shelf Holes Space From Top", 'DISTANCE', sn_unit.inch(0))
        self.add_prompt("Shelf Holes Front Setback", 'DISTANCE', sn_unit.inch(0))
        self.add_prompt("Shelf Holes Rear Setback", 'DISTANCE', sn_unit.inch(0))
        self.add_prompt("Adjustable Shelf Thickness", 'DISTANCE', sn_unit.inch(0.75))
        self.add_prompt("Fixed Shelf Thickness", 'DISTANCE', sn_unit.inch(0.75))
        self.add_prompt("Shelf Clip Gap", 'DISTANCE', sn_unit.inch(0.125))
        self.add_prompt("Shelf Hole Spacing", 'DISTANCE', sn_unit.inch(1.25))
        self.add_prompt("Shelf Pin Quantity", 'QUANTITY', 0)
        
        sgi = self.get_prompt('cabinetlib.spec_group_index').get_var('sgi')
        Adj_Shelf_Rows = self.get_prompt('Adj Shelf Rows').get_var()
        Division_Qty = self.get_prompt('Division Qty').get_var()
        
        self.get_prompt('Shelf Pin Quantity').set_formula('(Adj_Shelf_Rows*Division_Qty)*4',[Adj_Shelf_Rows,Division_Qty])
        self.get_prompt('Division Thickness').set_formula('THICKNESS(sgi,"Cabinet_Division' + self.open_name +'")',[sgi])
        self.get_prompt('Fixed Shelf Thickness').set_formula('THICKNESS(sgi,"Cabinet_Shelf' + self.open_name +'")',[sgi])
        self.get_prompt('Adjustable Shelf Thickness').set_formula('THICKNESS(sgi,"Cabinet_Shelf' + self.open_name +'")',[sgi])
    
    def add_divisions(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Height =self.obj_z.snap.get_var('location.z','Height')
        Depth = self.obj_y.snap.get_var('location.y','Depth')
        Division_Qty = self.get_prompt('Division Qty').get_var()   
        Division_Thickness = self.get_prompt('Division Thickness').get_var()
        Division_Setback = self.get_prompt('Division Setback').get_var()
        
        division = add_part(self, DIVISION)
        division.set_name("Division")
        
        division.loc_x("Width-(Width-(Division_Thickness*Division_Qty))/(Division_Qty+1)",[Width,Division_Thickness,Division_Qty])
        division.loc_y("Depth",[Depth])

        division.rot_y(value=math.radians(-90))

        division.dim_x("Height",[Height])
        division.dim_y("(Depth*-1)+Division_Setback",[Depth,Division_Setback])
        division.dim_z("Division_Thickness",[Division_Thickness])

        division.get_prompt('Hide').set_formula('IF(Division_Qty==0,True,False)',[Division_Qty])
        division.get_prompt('Z Quantity').set_formula('Division_Qty',[Division_Qty])
        division.get_prompt('Z Offset').set_formula('((Width-(Division_Thickness*Division_Qty))/(Division_Qty+1))+Division_Thickness',[Division_Qty,Width,Division_Thickness])

        # division.cutpart("Cabinet_Division")
        # division.edgebanding('Cabinet_Interior_Edges',l1 = True)

    def add_fixed_shelves(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Height =self.obj_z.snap.get_var('location.z','Height')
        Depth = self.obj_y.snap.get_var('location.y','Depth')
        Division_Qty = self.get_prompt('Division Qty').get_var()
        Division_Thickness = self.get_prompt('Division Thickness').get_var()  
        Division_Setback = self.get_prompt('Division Setback').get_var() 
        Shelf_Setback = self.get_prompt('Shelf Setback').get_var()
        Fixed_Shelf_Rows = self.get_prompt('Fixed Shelf Rows').get_var()
        Fixed_Shelf_Thickness = self.get_prompt('Fixed Shelf Thickness').get_var()
        
        fix_shelf = add_part(self, SHELF)
        fix_shelf.set_name("Fixed Shelf")
        
        fix_shelf.loc_y("Depth",[Depth]) 
        fix_shelf.loc_z("(Height-(Fixed_Shelf_Thickness*Fixed_Shelf_Rows))/(Fixed_Shelf_Rows+1)",[Height,Fixed_Shelf_Thickness,Fixed_Shelf_Rows]) 
        fix_shelf.dim_x("(Width-(Division_Thickness*Division_Qty))/(Division_Qty+1)",[Width,Division_Qty,Division_Thickness]) 
        fix_shelf.dim_y("(Depth*-1)+Shelf_Setback+Division_Setback",[Shelf_Setback,Depth,Division_Setback]) 
        fix_shelf.dim_z("Fixed_Shelf_Thickness",[Fixed_Shelf_Thickness]) 

        fix_shelf.get_prompt('Hide').set_formula('IF(Fixed_Shelf_Rows==0,True,False)',[Fixed_Shelf_Rows])
        fix_shelf.get_prompt('Z Quantity').set_formula('Fixed_Shelf_Rows',[Fixed_Shelf_Rows])
        fix_shelf.get_prompt('Z Offset').set_formula('Height/(Fixed_Shelf_Rows+1)+(Fixed_Shelf_Thickness/(Fixed_Shelf_Rows+1))',[Height,Fixed_Shelf_Thickness,Fixed_Shelf_Rows])
        fix_shelf.get_prompt('X Quantity').set_formula('Division_Qty+1',[Division_Qty])
        fix_shelf.get_prompt('X Offset').set_formula('((Width-(Division_Thickness*Division_Qty))/(Division_Qty+1))+Division_Thickness',[Width,Division_Qty,Division_Thickness])
        # fix_shelf.cutpart("Cabinet_Shelf")
        # fix_shelf.edgebanding('Cabinet_Interior_Edges',l1 = True)

    def add_adj_shelves(self):
        Width = self.obj_x.snap.get_var("location.x","Width")
        Height = self.obj_z.snap.get_var("location.z","Height")
        Depth = self.obj_y.snap.get_var("location.y","Depth")
        Division_Qty = self.get_prompt('Division Qty').get_var()
        Division_Thickness = self.get_prompt('Division Thickness').get_var()  
        Division_Setback = self.get_prompt('Division Setback').get_var() 
        Shelf_Clip_Gap = self.get_prompt('Shelf Clip Gap').get_var() 
        Shelf_Setback = self.get_prompt('Shelf Setback').get_var()
        Adj_Shelf_Rows = self.get_prompt('Adj Shelf Rows').get_var()
        Adjustable_Shelf_Thickness = self.get_prompt('Adjustable Shelf Thickness').get_var()
        
        adj_shelf = add_part(self, SHELF)
        adj_shelf.set_name("Adjustable Shelf")

        adj_shelf.loc_x("Shelf_Clip_Gap",[Shelf_Clip_Gap])
        adj_shelf.loc_y("Depth",[Depth])
        adj_shelf.loc_z("(Height-(Adjustable_Shelf_Thickness*Adj_Shelf_Rows))/(Adj_Shelf_Rows+1)",[Height,Adjustable_Shelf_Thickness,Adj_Shelf_Rows])
   
   
        adj_shelf.dim_x("(Width-(Division_Thickness*Division_Qty)-((Shelf_Clip_Gap*2)*(Division_Qty+1)))/(Division_Qty+1)",[Width,Division_Qty,Division_Thickness,Shelf_Clip_Gap])
        adj_shelf.dim_y("(Depth*-1)+Shelf_Setback+Division_Setback",[Depth,Shelf_Setback,Division_Setback])
        adj_shelf.dim_z("Adjustable_Shelf_Thickness",[Adjustable_Shelf_Thickness])

        adj_shelf.get_prompt('Hide').set_formula('IF(Adj_Shelf_Rows==0,True,False)',[Adj_Shelf_Rows])
        adj_shelf.get_prompt('Z Quantity').set_formula('Adj_Shelf_Rows',[Adj_Shelf_Rows])
        adj_shelf.get_prompt('Z Offset').set_formula('Height/(Adj_Shelf_Rows+1)+(Adjustable_Shelf_Thickness/(Adj_Shelf_Rows+1))',[Adj_Shelf_Rows,Height,Adjustable_Shelf_Thickness])
        adj_shelf.get_prompt('X Quantity').set_formula('Division_Qty+1',[Division_Qty])
        adj_shelf.get_prompt('X Offset').set_formula('((Width-(Division_Thickness*Division_Qty)-((Shelf_Clip_Gap*2)*(Division_Qty+1)))/(Division_Qty+1))+(Shelf_Clip_Gap*2)+Division_Thickness',[Width,Division_Thickness,Division_Qty,Shelf_Clip_Gap])
        
        # adj_shelf.cutpart("Cabinet_Shelf")
        # adj_shelf.edgebanding('Cabinet_Interior_Edges',l1 = True, w1 = True, l2 = True, w2 = True)

    # def add_adj_shelf_machining(self):
    #     Width = self.get_var('dim_x','Width')
    #     Height = self.get_var('dim_z','Height')
    #     Depth = self.get_var('dim_y','Depth')
    #     Division_Qty = self.get_var('Division Qty')   
    #     Division_Thickness = self.get_var('Division Thickness')  
    #     Division_Setback = self.get_var('Division Setback') 
    #     Shelf_Setback = self.get_var('Shelf Setback')
    #     Adj_Shelf_Rows = self.get_var('Adj Shelf Rows')

    #     holes = self.add_assembly(ADJ_MACHINING)
    #     holes.set_name("Adjustable Shelf Holes")
    #     holes.x_loc(value = 0)
    #     holes.y_loc("Division_Setback+Shelf_Setback",[Division_Setback,Shelf_Setback])
    #     holes.z_loc(value = 0)
    #     holes.x_rot(value = 0)
    #     holes.y_rot(value = 0)
    #     holes.z_rot(value = 0)
    #     holes.x_dim("(Width-(Division_Thickness*Division_Qty))/(Division_Qty+1)",[Width,Division_Thickness,Division_Qty])
    #     holes.y_dim("fabs(Depth)-Division_Setback-Shelf_Setback",[Depth,Division_Setback,Shelf_Setback])
    #     holes.z_dim("Height",[Height])
    #     holes.prompt('Hide','IF(Adj_Shelf_Rows==0,True,False)',[Adj_Shelf_Rows])
    #     holes.prompt('Opening Quantity','Division_Qty+1',[Division_Qty])
    #     holes.prompt('Opening X Offset','(Width-(Division_Thickness*Division_Qty))/(Division_Qty+1)+Division_Thickness',[Width,Division_Thickness,Division_Qty])

    def draw(self):
        self.create_assembly()
        
        self.add_common_prompts()
        self.add_divisions()
        self.add_fixed_shelves()
        self.add_adj_shelves()
#         self.add_adj_shelf_machining()
        
        self.update()
        
class Rollouts(sn_types.Assembly):
    
    library_name = "Cabinet Interiors"
    type_assembly = "INSERT"
    placement_type = "INTERIOR"
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    mirror_y = False
    
    rollout_qty = 3
    
    def draw(self):
        self.create_assembly()

        self.add_tab(name='Rollout Options',tab_type='VISIBLE')
        
        self.add_prompt(name="Rollout Quantity",
                        prompt_type='QUANTITY',
                        value=self.rollout_qty,
                        tab_index=0)
        
        self.add_prompt(name="Rollout 1 Z Dim",
                        prompt_type='DISTANCE',
                        value=sn_unit.inch(4),
                        tab_index=0)
        
        self.add_prompt(name="Rollout 2 Z Dim",
                        prompt_type='DISTANCE',
                        value=sn_unit.inch(4),
                        tab_index=0)
        
        self.add_prompt(name="Rollout 3 Z Dim",
                        prompt_type='DISTANCE',
                        value=sn_unit.inch(4),
                        tab_index=0)
        
        self.add_prompt(name="Rollout 4 Z Dim",
                        prompt_type='DISTANCE',
                        value=sn_unit.inch(4),
                        tab_index=0)
        
        self.add_prompt(name="Bottom Gap",
                        prompt_type='DISTANCE',
                        value=sn_unit.inch(1.7),
                        tab_index=0)
        
        self.add_prompt(name="Drawer Box Slide Gap",
                        prompt_type='DISTANCE',
                        value=sn_unit.inch(2),
                        tab_index=0)

        self.add_prompt(name="Rollout Setback",
                        prompt_type='DISTANCE',
                        value=sn_unit.inch(.5),
                        tab_index=0)
        
        self.add_prompt(name="Distance Between Rollouts",
                        prompt_type='DISTANCE',
                        value=sn_unit.inch(2),
                        tab_index=0)

        Width = self.get_var('dim_x','Width')
        Depth = self.get_var('dim_y','Depth')
        Rollout_1_Z_Dim = self.get_var('Rollout 1 Z Dim')
        Rollout_2_Z_Dim = self.get_var('Rollout 2 Z Dim')
        Rollout_3_Z_Dim = self.get_var('Rollout 3 Z Dim')
        Rollout_4_Z_Dim = self.get_var('Rollout 4 Z Dim')
        Bottom_Gap = self.get_var("Bottom Gap")
        Distance_Between_Rollouts = self.get_var("Distance Between Rollouts")
        Rollout_Quantity = self.get_var("Rollout Quantity")
        Rollout_Setback = self.get_var("Rollout Setback")
        Drawer_Box_Slide_Gap = self.get_var("Drawer Box Slide Gap")
        
        rollout_1 = drawer_boxes.Wood_Drawer_Box()
        rollout_1.draw()
        rollout_1.obj_bp.parent = self.obj_bp
        rollout_1.set_name("Rollout 1")
        rollout_1.x_loc('Distance_Between_Rollouts',[Distance_Between_Rollouts])
        rollout_1.y_loc('Rollout_Setback',[Rollout_Setback])
        rollout_1.z_loc('Bottom_Gap',[Bottom_Gap])
        rollout_1.x_rot(value = 0)
        rollout_1.y_rot(value = 0)
        rollout_1.z_rot(value = 0)
        rollout_1.x_dim('Width-(Drawer_Box_Slide_Gap*2)',[Width,Drawer_Box_Slide_Gap])
        rollout_1.y_dim('Depth',[Depth])
        rollout_1.z_dim('Rollout_1_Z_Dim',[Rollout_1_Z_Dim])
        
        rollout_2 = drawer_boxes.Wood_Drawer_Box()
        rollout_2.draw()
        rollout_2.obj_bp.parent = self.obj_bp
        rollout_2.set_name("Rollout 2")
        rollout_2.x_loc('Distance_Between_Rollouts',[Distance_Between_Rollouts])
        rollout_2.y_loc('Rollout_Setback',[Rollout_Setback])
        rollout_2.z_loc('Bottom_Gap+Rollout_1_Z_Dim+Distance_Between_Rollouts',[Bottom_Gap,Rollout_1_Z_Dim,Distance_Between_Rollouts])
        rollout_2.x_rot(value = 0)
        rollout_2.y_rot(value = 0)
        rollout_2.z_rot(value = 0)
        rollout_2.x_dim('Width-(Drawer_Box_Slide_Gap*2)',[Width,Drawer_Box_Slide_Gap])
        rollout_2.y_dim('Depth',[Depth])
        rollout_2.z_dim('Rollout_2_Z_Dim',[Rollout_2_Z_Dim])
        rollout_2.prompt('Hide','IF(Rollout_Quantity>1,False,True)',[Rollout_Quantity])
        
        rollout_3 = drawer_boxes.Wood_Drawer_Box()
        rollout_3.draw()
        rollout_3.obj_bp.parent = self.obj_bp
        rollout_3.set_name("Rollout 3")
        rollout_3.x_loc('Distance_Between_Rollouts',[Distance_Between_Rollouts])
        rollout_3.y_loc('Rollout_Setback',[Rollout_Setback])
        rollout_3.z_loc('Bottom_Gap+Rollout_1_Z_Dim+Rollout_2_Z_Dim+(Distance_Between_Rollouts*2)',[Bottom_Gap,Rollout_1_Z_Dim,Rollout_2_Z_Dim,Distance_Between_Rollouts])
        rollout_3.x_rot(value = 0)
        rollout_3.y_rot(value = 0)
        rollout_3.z_rot(value = 0)
        rollout_3.x_dim('Width-(Drawer_Box_Slide_Gap*2)',[Width,Drawer_Box_Slide_Gap])
        rollout_3.y_dim('Depth',[Depth])
        rollout_3.z_dim('Rollout_3_Z_Dim',[Rollout_3_Z_Dim])
        rollout_3.prompt('Hide','IF(Rollout_Quantity>2,False,True)',[Rollout_Quantity])

        rollout_4 = drawer_boxes.Wood_Drawer_Box()
        rollout_4.draw()
        rollout_4.obj_bp.parent = self.obj_bp
        rollout_4.set_name("Rollout 3")
        rollout_4.x_loc('Distance_Between_Rollouts',[Distance_Between_Rollouts])
        rollout_4.y_loc('Rollout_Setback',[Rollout_Setback])
        rollout_4.z_loc('Bottom_Gap+Rollout_1_Z_Dim+Rollout_2_Z_Dim+Rollout_3_Z_Dim+(Distance_Between_Rollouts*3)',[Bottom_Gap,Rollout_1_Z_Dim,Rollout_2_Z_Dim,Rollout_3_Z_Dim,Distance_Between_Rollouts])
        rollout_4.x_rot(value = 0)
        rollout_4.y_rot(value = 0)
        rollout_4.z_rot(value = 0)
        rollout_4.x_dim('Width-(Drawer_Box_Slide_Gap*2)',[Width,Drawer_Box_Slide_Gap])
        rollout_4.y_dim('Depth',[Depth])
        rollout_4.z_dim('Rollout_4_Z_Dim',[Rollout_4_Z_Dim])
        rollout_4.prompt('Hide','IF(Rollout_Quantity>3,False,True)',[Rollout_Quantity])
        
        self.update()
        
#---------INSERTS
        
class INSERT_Simple_Shelves(Simple_Shelves):
    
    def __init__(self):
        self.category_name = "Standard"
        self.assembly_name = "Simple Shelves"
        self.carcass_type = "Base"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.shelf_qty = 1        
        
class INSERT_Shelves(Shelves):
    
    def __init__(self):
        self.category_name = "Standard"
        self.assembly_name = "Shelves"
        self.carcass_type = "Base"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.shelf_qty = 1
        
class INSERT_Base_Dividers(Dividers):
    
    def __init__(self):
        self.category_name = "Standard"
        self.assembly_name = "Dividers"
        self.carcass_type = "Base"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.shelf_qty = 1

class INSERT_Base_Divisions(Divisions):
    
    def __init__(self):
        self.category_name = "Standard"
        self.assembly_name = "Divisions"
        self.carcass_type = "Base"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.shelf_qty = 1

class INSERT_Rollouts(Rollouts):
    
    def __init__(self):
        self.category_name = "Standard"
        self.assembly_name = "Rollouts"
        self.carcass_type = "Base"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.rollout_qty = 2
