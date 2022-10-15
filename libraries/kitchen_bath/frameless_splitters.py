

import bpy
import math
from os import path
from snap import sn_types, sn_unit, sn_utils
from . import cabinet_properties
from snap.libraries.closets import closet_paths

LIBRARY_NAME_SPACE = "sn_kitchen_bath"
LIBRARY_NAME = "Cabinets"
INSERT_SPLITTER_CATEGORY_NAME = "Starter Splitters"

ROOT_DIR = path.dirname(__file__)
PART_WITH_EDGEBANDING = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")

        
def add_part(assembly, path):
    part_bp = assembly.add_assembly_from_file(path)
    part = sn_types.Assembly(part_bp)
    part.obj_bp.sn_closets.is_panel_bp = True
    return part  

class Vertical_Splitters(sn_types.Assembly):
    
    library_name = LIBRARY_NAME
    category_name = INSERT_SPLITTER_CATEGORY_NAME
    type_assembly = "INSERT"
    placement_type = "SPLITTER"
    show_in_library = True
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    drop_id = "sn_closets.drop_insert"

    mirror_y = False

    calculator = None
    calculator_name = "Opening Heights Calculator"
    calculator_obj_name = "Shelf Stack Calc Distance Obj"    
  
    open_name = ""

    vertical_openings = 2 #1-10
    opening_1_height = 0
    opening_2_height = 0
    opening_3_height = 0
    opening_4_height = 0
    opening_5_height = 0
    opening_6_height = 0
    opening_7_height = 0
    opening_8_height = 0
    opening_9_height = 0
    opening_10_height = 0
    
    remove_splitter_1 = False
    remove_splitter_2 = False
    remove_splitter_3 = False
    remove_splitter_4 = False
    remove_splitter_5 = False
    remove_splitter_6 = False
    remove_splitter_7 = False
    remove_splitter_8 = False
    remove_splitter_9 = False
    
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
        self.add_prompt("Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Left Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Right Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Top Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Bottom Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Extend Top Amount", 'DISTANCE', sn_unit.inch(0))
        self.add_prompt("Extend Bottom Amount", 'DISTANCE', sn_unit.inch(0))
        
    def add_insert(self, insert, index, z_loc_vars=[], z_loc_expression=""):
        Width = self.obj_x.snap.get_var("location.x","Width")
        Depth = self.obj_y.snap.get_var("location.y","Depth")
        height_prompt = eval("self.calculator.get_calculator_prompt('Opening {} Height')".format(str(index)))
        opening_height = eval("height_prompt.get_var(self.calculator.name, 'Opening_{}_Height')".format(str(index)))
        z_dim_expression = "Opening_" + str(index) + "_Height"
        
        if insert:
            if not insert.obj_bp:
                insert.draw()
            insert.obj_bp.parent = self.obj_bp
            if index == self.vertical_openings:
                insert.loc_z(value = 0)
            else:
                insert.loc_z(z_loc_expression,z_loc_vars)

            insert.dim_x('Width',[Width])
            insert.dim_y('Depth',[Depth])
            insert.dim_z(z_dim_expression,[opening_height])

            if index == 1:
                # ALLOW DOOR TO EXTEND TO TOP OF VALANCE
                extend_top_amount = insert.get_prompt("Extend Top Amount")
                if extend_top_amount:
                    Extend_Top_Amount = self.get_prompt("Extend Top Amount").get_var()
                    insert.get_prompt('Extend Top Amount').set_formula('Extend_Top_Amount',[Extend_Top_Amount])
            
            if index == self.vertical_openings:
                # ALLOW DOOR TO EXTEND TO BOTTOM OF VALANCE
                extend_bottom_amount = insert.get_prompt("Extend Bottom Amount")
                if extend_bottom_amount:
                    Extend_Bottom_Amount = self.get_prompt("Extend Bottom Amount").get_var()
                    insert.get_prompt('Extend Bottom Amount').set_formula('Extend_Bottom_Amount',[Extend_Bottom_Amount])
        
    def get_opening(self,index):
        opening = self.add_opening()
        opening.add_prompt("Left Side Thickness", 'DISTANCE', sn_unit.inch(.75))
        opening.add_prompt("Right Side Thickness", 'DISTANCE', sn_unit.inch(.75))
        opening.add_prompt("Top Thickness", 'DISTANCE', sn_unit.inch(.75))
        opening.add_prompt("Bottom Thickness", 'DISTANCE', sn_unit.inch(.75))
        opening.add_prompt("Extend Top Amount", 'DISTANCE', sn_unit.inch(0))
        opening.add_prompt("Extend Bottom Amount", 'DISTANCE', sn_unit.inch(0))
        
        exterior = eval('self.exterior_' + str(index))
        interior = eval('self.interior_' + str(index))
        
        if interior:
            opening.obj_bp.snap.interior_open = False
        
        if exterior:
            opening.obj_bp.snap.exterior_open = False
            
        return opening

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
            prompt = self.calculator.add_calculator_prompt("Opening " + str(i) + " Height")
            size = eval("self.opening_" + str(i) + "_height")
            if size > 0:
                prompt.set_value(size)
                prompt.equal = False

    def add_splitters(self):
        Width = self.obj_x.snap.get_var("location.x","Width")
        Height = self.obj_z.snap.get_var("location.z","Height")
        Depth = self.obj_y.snap.get_var("location.y","Depth")
        Thickness = self.get_prompt('Thickness').get_var()
        previous_splitter = None

        if not self.calculator:
            self.add_calculator(self.vertical_openings)

        self.add_calculator_prompts(self.vertical_openings)        
        
        for i in range(1,self.vertical_openings):
            height_prompt = eval("self.calculator.get_calculator_prompt('Opening {} Height')".format(str(i)))
            opening_height = eval("height_prompt.get_var(self.calculator.name, 'Opening_{}_Height')".format(str(i)))            

            z_loc_vars = []
            z_loc_vars.append(opening_height)
            
            if previous_splitter:
                z_loc = previous_splitter.obj_bp.snap.get_var("location.z", "Splitter_Z_Loc")
                z_loc_vars.append(z_loc)
                
            splitter = add_part(self, PART_WITH_EDGEBANDING)
            splitter.set_name("Splitter " + str(i))
            if previous_splitter:
                z_loc_vars.append(Thickness)
                splitter.loc_z('Splitter_Z_Loc-Opening_' + str(i) + '_Height-Thickness',z_loc_vars)
            else:
                z_loc_vars.append(Height)
                splitter.loc_z('Height-Opening_' + str(i) + '_Height',z_loc_vars)
            splitter.dim_x('Width',[Width])
            splitter.dim_y('Depth',[Depth])
            splitter.dim_z('-Thickness',[Thickness])
            remove_splitter = eval("self.remove_splitter_" + str(i))
            if remove_splitter:
                splitter.get_prompt('Hide').set_fomula(value=True)
            # splitter.cutpart("Cabinet_Shelf")
            # splitter.edgebanding('Cabinet_Body_Edges',l2 = True)
            # cabinet_machining.add_drilling(splitter)
            
            previous_splitter = splitter
            
            opening_z_loc_vars = []
            opening_z_loc = previous_splitter.obj_bp.snap.get_var("location.z", "Splitter_Z_Loc")
            opening_z_loc_vars.append(opening_z_loc)
            
            exterior = eval('self.exterior_' + str(i))
            self.add_insert(exterior, i, opening_z_loc_vars, "Splitter_Z_Loc")
            
            interior = eval('self.interior_' + str(i))
            self.add_insert(interior, i, opening_z_loc_vars, "Splitter_Z_Loc")
            
            opening = self.get_opening(i)
            self.add_insert(opening, i, opening_z_loc_vars, "Splitter_Z_Loc")

        #ADD LAST INSERT
        bottom_exterior = eval('self.exterior_' + str(self.vertical_openings))
        self.add_insert(bottom_exterior, self.vertical_openings)
        
        bottom_interior = eval('self.interior_' + str(self.vertical_openings))
        self.add_insert(bottom_interior, self.vertical_openings)

        bottom_opening = self.get_opening(self.vertical_openings)
        self.add_insert(bottom_opening, self.vertical_openings)

    def draw(self):
        self.create_assembly()
        self.obj_bp['IS_BP_SPLITTER'] = True
        self.add_prompts()
        self.add_splitters()
        self.update()

class Horizontal_Splitters(sn_types.Assembly):
    
    library_name = LIBRARY_NAME
    category_name = INSERT_SPLITTER_CATEGORY_NAME
    type_assembly = "INSERT"
    placement_type = "SPLITTER"
    show_in_library = True
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    drop_id = "sn_closets.drop_insert"
    
    mirror_y = False
    open_name = ""

    horizontal_openings = 2 #1-10
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
        
        for i in range(1,self.horizontal_openings+1):
            size = eval("self.opening_" + str(i) + "_width")
            self.add_prompt("Opening " + str(i) + " Width", 'DISTANCE', size, True if size == 0 else False)
    
        self.add_prompt("Thickness", 'DISTANCE', sn_unit.inch(.75))
        
        Thickness = self.get_prompts('Thickness').get_var()
        
        # self.calculator_deduction("Thickness*(" + str(self.horizontal_openings) +"-1)",[Thickness])
        
    def add_insert(self,insert,index,x_loc_vars=[],x_loc_expression=""):
        Height = self.obj_z.snap.get_var("location.z","Height")
        Depth = self.obj_y.snap.get_var("location.y","Depth")
        open_var = eval("self.get_prompt('Opening " + str(index) + " Width').get_var()")
        x_dim_expression = "Opening_" + str(index) + "_Width"
        
        if insert:
            if not insert.obj_bp:
                insert.draw()

            insert.obj_bp.parent = self.obj_bp
            if index == 1:
                insert.loc_x(value = 0)
            else:
                insert.loc_x(x_loc_expression,x_loc_vars)
            insert.dim_x(x_dim_expression,[open_var])
            insert.dim_y('Depth',[Depth])
            insert.dim_z('Height',[Height])
        
    def get_opening(self,index):
        opening = self.add_opening()
        opening.set_name("Opening " + str(index))

        opening.add_prompt("Left Side Thickness", 'DISTANCE', sn_unit.inch(.75))
        opening.add_prompt("Right Side Thickness", 'DISTANCE', sn_unit.inch(.75))
        opening.add_prompt("Top Thickness", 'DISTANCE', sn_unit.inch(.75))
        opening.add_prompt("Bottom Thickness", 'DISTANCE', sn_unit.inch(.75))
        opening.add_prompt("Extend Top Amount", 'DISTANCE', sn_unit.inch(0))
        opening.add_prompt("Extend Bottom Amount", 'DISTANCE', sn_unit.inch(0))
        
        exterior = eval('self.exterior_' + str(index))
        interior = eval('self.interior_' + str(index))
        
        if interior:
            opening.obj_bp.mv.interior_open = False
        
        if exterior:
            opening.obj_bp.mv.exterior_open = False
            
        return opening
        
    def add_splitters(self):
        Height = self.obj_z.snap.get_var("location.z","Height")
        Depth = self.obj_y.snap.get_var("location.y","Depth")
        Thickness = self.get_prompt('Thickness').get_var()
        
        previous_splitter = None
        
        for i in range(1,self.horizontal_openings):
            
            x_loc_vars = []
            open_var = eval("self.get_prompt('Opening " + str(i) + " Width').get_var()")
            x_loc_vars.append(open_var)
            
            if previous_splitter:
                x_loc = previous_splitter.obj_x.snap.get_var("loc_x","Splitter_X_Loc")
                x_loc_vars.append(x_loc)
                x_loc_vars.append(Thickness)

            splitter = add_part(self, PART_WITH_EDGEBANDING)
            splitter.set_name("Splitter " + str(i))
            if previous_splitter:
                splitter.loc_x("Splitter_X_Loc+Thickness+Opening_" + str(i) + "_Width",x_loc_vars)
            else:
                splitter.loc_x("Opening_" + str(i) + "_Width",[open_var])
            splitter.rot_y(value=math.radians(-90))
            splitter.dim_x('Height',[Height])
            splitter.dim_y('Depth',[Depth])
            splitter.dim_z('-Thickness',[Thickness])
            # splitter.cutpart("Cabinet_Shelf")
            # splitter.edgebanding('Cabinet_Body_Edges',l2 = True)

            previous_splitter = splitter

            exterior = eval('self.exterior_' + str(i))
            self.add_insert(exterior, i, x_loc_vars, "Splitter_X_Loc+Thickness")
            
            interior = eval('self.interior_' + str(i))
            self.add_insert(interior, i, x_loc_vars, "Splitter_X_Loc+Thickness")
            
            opening = self.get_opening(i)
            self.add_insert(opening, i, x_loc_vars, "Splitter_X_Loc+Thickness")
            
        insert_x_loc_vars = []
        insert_x_loc = previous_splitter.obj_x.snap.get_var("loc_x","Splitter_X_Loc")
        insert_x_loc_vars.append(insert_x_loc)
        insert_x_loc_vars.append(Thickness)

        #ADD LAST INSERT
        last_exterior = eval('self.exterior_' + str(self.horizontal_openings))
        self.add_insert(last_exterior, self.horizontal_openings,insert_x_loc_vars, "Splitter_X_Loc+Thickness")
          
        last_interior = eval('self.interior_' + str(self.horizontal_openings))
        self.add_insert(last_interior, self.horizontal_openings,insert_x_loc_vars, "Splitter_X_Loc+Thickness")

        last_opening = self.get_opening(self.horizontal_openings)
        self.add_insert(last_opening, self.horizontal_openings,insert_x_loc_vars, "Splitter_X_Loc+Thickness")
        
    def draw(self):
        self.create_assembly()
        self.obj_bp['IS_BP_SPLITTER'] = True
        self.add_prompts()
        self.add_splitters()
        self.update()
        
#---------SPLITTER INSERTS        
class INSERT_2_Horizontal_Openings(Horizontal_Splitters):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_SPLITTER_CATEGORY_NAME
        self.assembly_name = "2 Horizontal Openings"
        self.horizontal_openings = 2
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        
class INSERT_3_Horizontal_Openings(Horizontal_Splitters):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_SPLITTER_CATEGORY_NAME
        self.assembly_name = "3 Horizontal Openings"
        self.horizontal_openings = 3
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        
class INSERT_4_Horizontal_Openings(Horizontal_Splitters):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_SPLITTER_CATEGORY_NAME
        self.assembly_name = "4 Horizontal Openings"
        self.horizontal_openings = 4
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        
class INSERT_5_Horizontal_Openings(Horizontal_Splitters):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_SPLITTER_CATEGORY_NAME
        self.assembly_name = "5 Horizontal Openings"
        self.horizontal_openings = 5
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        
class INSERT_2_Vertical_Openings(Vertical_Splitters):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_SPLITTER_CATEGORY_NAME
        self.assembly_name = "2 Vertical Openings"
        self.vertical_openings = 2
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)

class INSERT_3_Vertical_Openings(Vertical_Splitters):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_SPLITTER_CATEGORY_NAME
        self.assembly_name = "3 Vertical Openings"
        self.vertical_openings = 3
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        
class INSERT_4_Vertical_Openings(Vertical_Splitters):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_SPLITTER_CATEGORY_NAME
        self.assembly_name = "4 Vertical Openings"
        self.vertical_openings = 4
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        
class INSERT_5_Vertical_Openings(Vertical_Splitters):
    
    def __init__(self):
        self.library_name = LIBRARY_NAME
        self.category_name = INSERT_SPLITTER_CATEGORY_NAME
        self.assembly_name = "5 Vertical Openings"
        self.vertical_openings = 5
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
