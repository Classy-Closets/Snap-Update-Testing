import bpy
import snap
from snap import sn_unit, sn_types, sn_paths, sn_utils
from snap.libraries.kitchen_bath.carcass_simple import Inside_Corner_Carcass, Standard_Carcass
from . import cabinet_properties
from . import cabinet_countertops
from .frameless_exteriors import Doors, Horizontal_Drawers, Vertical_Drawers
from snap.libraries.closets import closet_paths
import os
import math


LIBRARY_NAME_SPACE = "sn_kitchen_bath"
MICROWAVE =  os.path.join(os.path.dirname(__file__),"Appliances","Conventional Microwave.blend")
VENT =  os.path.join(os.path.dirname(__file__),"Appliances","Wall Mounted Range Hood.blend")
REFRIGERATOR = os.path.join(os.path.dirname(__file__),"Appliances", "Professional Refrigerator Generic.blend")
BLIND_PANEL = os.path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")

def add_product_width_dimension(product):
    Product_Width = product.obj_x.snap.get_var('location.x','Product_Width')
    Left_Side_Wall_Filler = product.carcass.get_prompt('Left Side Wall Filler').get_var()
    Right_Side_Wall_Filler = product.carcass.get_prompt('Right Side Wall Filler').get_var()
    
    dim = sn_types.Dimension()
    dim.parent(product.obj_bp)

    if hasattr(product, "mirror_z") and product.mirror_z:
        dim.start_z(value=sn_unit.inch(5))
    else:
        dim.start_z(value=-sn_unit.inch(5))
    if product.carcass.carcass_type == 'Upper':
        dim.start_y(value=sn_unit.inch(8))
    else:
        dim.start_y(value=sn_unit.inch(3))
    dim.start_x('Left_Side_Wall_Filler',[Left_Side_Wall_Filler])
    dim.end_x('Product_Width-Left_Side_Wall_Filler-Right_Side_Wall_Filler',[Product_Width,Left_Side_Wall_Filler,Right_Side_Wall_Filler])

def add_product_depth_dimension(product):
    hashmark = sn_types.Line(sn_unit.inch(6), (0, 45, 0))
    hashmark.parent(product.obj_bp)

    if hasattr(product, "mirror_z") and product.mirror_z:
        hashmark.anchor.location.z = product.obj_z.location.z

    dim = sn_types.Dimension()
    anchor_props = dim.anchor.snap_closet_dimensions
    end_point_props = dim.end_point.snap_closet_dimensions
    anchor_props.is_dim_obj = True
    end_point_props.is_dim_obj = True
    dim.anchor.parent = hashmark.end_point    

    dim.start_z(value=sn_unit.inch(2))
    abs_y_loc = math.fabs(sn_unit.meter_to_inch(product.obj_y.location.y))
    dim_y_label = str(round(abs_y_loc, 2)) + '\"'
    dim.set_label(dim_y_label)

def add_product_filler_dimension(product, filler_side):
    Product_Width = product.obj_x.snap.get_var('location.x','Product_Width')
    Filler = product.carcass.get_prompt(filler_side + " Side Wall Filler").get_var('Filler')

    dim = sn_types.Dimension()
    dim.parent(product.obj_bp)
    
    if hasattr(product, "mirror_z") and product.mirror_z:
        dim.start_z(value=sn_unit.inch(5))
    else:
        dim.start_z(value=-sn_unit.inch(5))

    if product.carcass.carcass_type == 'Upper':
        dim.start_y(value=sn_unit.inch(8))
    else:
        dim.start_y(value=sn_unit.inch(3))
    
    if filler_side == 'Left':
        # dim.start_x('-Filler',[Filler])
        dim.end_x('Filler',[Filler])
    else:
        dim.start_x('Product_Width-Filler',[Product_Width,Filler])
        dim.end_x('Filler',[Filler])
    

def update_dimensions(assembly):
    inserts = sn_utils.get_insert_bp_list(assembly.obj_bp, [])

    for obj_bp in inserts:
        if "IS_BP_CARCASS" in obj_bp:
            if "STANDARD_CARCASS" in obj_bp:
                carcass = Standard_Carcass(obj_bp)
            elif "INSIDE_CORNER_CARCASS" in obj_bp:
                carcass = Inside_Corner_Carcass(obj_bp)
            carcass.update_dimensions()
        elif "IS_BP_DOOR_INSERT" in obj_bp:
            door_insert = Doors(obj_bp)
            door_insert.update_dimensions()
        elif "IS_DRAWERS_BP" in obj_bp:
            if "VERTICAL_DRAWERS" in obj_bp:
                drawers_insert = Vertical_Drawers(obj_bp)
            elif "HORIZONTAL_DRAWERS" in obj_bp:
                drawers_insert = Horizontal_Drawers(obj_bp)
            drawers_insert.update_dimensions()

def add_countertop(product):
    product.add_prompt("Countertop Overhang Front",'DISTANCE',sn_unit.inch(1.5))
    product.add_prompt("Countertop Overhang Back",'DISTANCE',sn_unit.inch(0))
    product.add_prompt("Countertop Overhang Left",'DISTANCE',sn_unit.inch(0))
    product.add_prompt("Countertop Overhang Right",'DISTANCE',sn_unit.inch(0))
    Countertop_Overhang_Front = product.get_prompt('Countertop Overhang Front').get_var()
    Countertop_Overhang_Left = product.get_prompt('Countertop Overhang Left').get_var()
    Countertop_Overhang_Right = product.get_prompt('Countertop Overhang Right').get_var()
    Countertop_Overhang_Back = product.get_prompt('Countertop Overhang Back').get_var()

    Width = product.obj_x.snap.get_var('location.x', 'Width')
    Height = product.obj_z.snap.get_var('location.z', 'Height')
    Depth = product.obj_y.snap.get_var('location.y', 'Depth')

    ctop = cabinet_countertops.PRODUCT_Straight_Countertop()
    ctop.draw()
    ctop.obj_bp.snap.type_group = 'INSERT'
    
    ctop.obj_bp.parent = product.obj_bp
    ctop.loc_x('-Countertop_Overhang_Left',[Countertop_Overhang_Left])
    ctop.loc_y('Countertop_Overhang_Back',[Countertop_Overhang_Back])
    if product.carcass.carcass_type == "Suspended":
        ctop.loc_z(value = 0)
    else:
        ctop.loc_z('Height',[Height])

    ctop.dim_x('Width+Countertop_Overhang_Left+Countertop_Overhang_Right',
               [Width,Countertop_Overhang_Left,Countertop_Overhang_Right])
    ctop.dim_y('Depth-Countertop_Overhang_Front-Countertop_Overhang_Back',[Depth,Countertop_Overhang_Front,Countertop_Overhang_Back])
    ctop.dim_z(value = sn_unit.inch(4))
    return ctop


def create_cabinet(product):
    props = cabinet_properties.get_scene_props().carcass_defaults
    toe_kick_height = props.toe_kick_height
    product.create_assembly()
    product.dim_x(value=product.width)
    product.dim_y(value=-product.depth)
    
    if hasattr(product, "mirror_z"):
        if product.mirror_z:
            product.dim_z(value=sn_unit.millimeter(-float(product.height)))
    else:
        product.dim_z(value=sn_unit.millimeter(float(product.height)) + toe_kick_height)
        
def add_carcass(product):
    Product_Width = product.obj_x.snap.get_var('location.x', 'Product_Width')
    Product_Height = product.obj_z.snap.get_var('location.z', 'Product_Height')
    Product_Depth = product.obj_y.snap.get_var('location.y', 'Product_Depth')

    product.carcass.draw()
    product.carcass.obj_bp.parent = product.obj_bp
    Left_Side_Wall_Filler = product.carcass.get_prompt('Left Side Wall Filler').get_var()
    Right_Side_Wall_Filler = product.carcass.get_prompt('Right Side Wall Filler').get_var()

    product.carcass.loc_x("Left_Side_Wall_Filler", [Left_Side_Wall_Filler])
    product.carcass.dim_x('Product_Width-Left_Side_Wall_Filler-Right_Side_Wall_Filler', [Product_Width, Left_Side_Wall_Filler, Right_Side_Wall_Filler])
    product.carcass.dim_y('Product_Depth', [Product_Depth])
    product.carcass.dim_z('Product_Height', [Product_Height])
    product.obj_bp.lm_cabinets.product_sub_type = product.carcass.carcass_type

def add_insert(product, insert):
    if insert:
        if not insert.obj_bp:
            insert.draw()
            insert.obj_bp.parent = product.obj_bp

    Width = product.obj_x.snap.get_var('location.x', 'Width')
    Height = product.obj_z.snap.get_var('location.z', 'Height')
    Depth = product.obj_y.snap.get_var('location.y', 'Depth')
    Left_Side_Thickness = product.carcass.get_prompt("Left Side Thickness").get_var()
    Right_Side_Thickness = product.carcass.get_prompt("Right Side Thickness").get_var()
    Top_Thickness = product.carcass.get_prompt("Top Thickness").get_var()
    Bottom_Thickness = product.carcass.get_prompt("Bottom Thickness").get_var()
    Top_Inset = product.carcass.get_prompt("Top Inset").get_var()
    Bottom_Inset = product.carcass.get_prompt("Bottom Inset").get_var()
    Back_Inset = product.carcass.get_prompt("Back Inset").get_var()
    Left_Side_Wall_Filler = product.carcass.get_prompt('Left Side Wall Filler').get_var()
    Right_Side_Wall_Filler = product.carcass.get_prompt('Right Side Wall Filler').get_var()

    insert.loc_x('Left_Side_Thickness',[Left_Side_Thickness])

    if product.carcass.carcass_shape == 'RECTANGLE':
        insert.loc_y('Depth',[Depth])
    else:  # DIAGONAL or NOTCHED...
        insert.loc_y('Depth+Left_Side_Thickness',[Depth,Left_Side_Thickness])
    if product.carcass.carcass_type in {"Base","Tall","Sink"}:
        insert.loc_z('Bottom_Inset',[Bottom_Inset])
    if product.carcass.carcass_type in {"Upper","Suspended"}:
        product.mirror_z = True
        insert.loc_z('Height+Bottom_Inset',[Height,Bottom_Inset])
    insert.dim_x('Width-(Left_Side_Thickness+Right_Side_Thickness)',[Width,Left_Side_Thickness,Right_Side_Thickness])

    if product.carcass.carcass_shape == 'RECTANGLE':
        insert.dim_y('fabs(Depth)-Back_Inset',[Depth,Back_Inset])
    else:
        insert.dim_y('fabs(Depth)-(Left_Side_Thickness+Right_Side_Thickness)',[Depth,Left_Side_Thickness,Right_Side_Thickness])

    insert.dim_z('fabs(Height)-Bottom_Inset-Top_Inset',[Height,Bottom_Inset,Top_Inset])

    if product.carcass.carcass_shape != 'RECTANGLE':
        Cabinet_Depth_Left = product.carcass.get_prompt("Cabinet Depth Left").get_var()
        Cabinet_Depth_Right = product.carcass.get_prompt("Cabinet Depth Right").get_var()
        insert.get_prompt("Left Depth").set_formula('Cabinet_Depth_Left',[Cabinet_Depth_Left])
        insert.get_prompt("Right Depth").set_formula('Cabinet_Depth_Right',[Cabinet_Depth_Right])

    # ALLOW DOOR TO EXTEND TO TOP FOR VALANCE
    extend_top_amount = insert.get_prompt("Extend Top Amount")
    valance_height_top = product.carcass.get_prompt("Valance Height Top")
    top_reveal = insert.get_prompt("Top Reveal")
      
    if extend_top_amount and valance_height_top and top_reveal:
        Valance_Height_Top = product.carcass.get_prompt("Valance Height Top").get_var()
        Door_Valance_Top = product.carcass.get_prompt("Door Valance Top").get_var()
        Top_Reveal = top_reveal.get_var()

        insert.get_prompt('Extend Top Amount').set_formula('IF(AND(Door_Valance_Top,Valance_Height_Top>0),Valance_Height_Top+Top_Thickness-Top_Reveal,0)',[Valance_Height_Top,Door_Valance_Top,Top_Thickness,Top_Reveal])

    # ALLOW DOOR TO EXTEND TO BOTTOM FOR VALANCE
    extend_bottom_amount = insert.get_prompt("Extend Bottom Amount")
    valance_height_bottom = product.carcass.get_prompt("Valance Height Bottom")
    bottom_reveal = insert.get_prompt("Bottom Reveal")

    if extend_bottom_amount and valance_height_bottom and bottom_reveal:
        Valance_Height_Bottom = product.carcass.get_prompt("Valance Height Bottom").get_var()
        Door_Valance_Bottom = product.carcass.get_prompt("Door Valance Bottom").get_var()
        Bottom_Reveal = insert.get_prompt("Bottom Reveal").get_var()

        insert.get_prompt('Extend Bottom Amount').set_formula('IF(AND(Door_Valance_Bottom,Valance_Height_Bottom>0),Valance_Height_Bottom+Bottom_Thickness-Bottom_Reveal,0)',[Valance_Height_Bottom,Door_Valance_Bottom,Bottom_Thickness,Bottom_Reveal])

    # ALLOR DOOR TO EXTEND WHEN SUB FRONT IS FOUND
    sub_front_height = product.carcass.get_prompt("Sub Front Height")

    if extend_bottom_amount and sub_front_height and top_reveal:
        Sub_Front_Height = product.carcass.get_prompt("Sub Front Height").get_var()
        Top_Reveal = top_reveal.get_var()

        insert.get_prompt('Extend Top Amount').set_formula('Sub_Front_Height-Top_Reveal',[Sub_Front_Height,Top_Reveal])

def add_opening(product):
    opening = product.add_opening()
    opening.obj_bp.name = 'Open'
    opening.obj_bp["IS_BP_OPENING"] = True
    opening.add_prompt("Left Side Thickness", 'DISTANCE', sn_unit.inch(.75))
    opening.add_prompt("Right Side Thickness", 'DISTANCE', sn_unit.inch(.75))
    opening.add_prompt("Top Thickness", 'DISTANCE', sn_unit.inch(.75))
    opening.add_prompt("Bottom Thickness", 'DISTANCE', sn_unit.inch(.75))
    opening.add_prompt("Extend Top Amount", 'DISTANCE', sn_unit.inch(0))
    opening.add_prompt("Extend Bottom Amount", 'DISTANCE', sn_unit.inch(0))
    add_insert(product,opening)

def add_undercabinet_appliance(product,insert):
    Product_Width = product.obj_x.snap.get_var('location.x','Product_Width')
    Product_Height = product.obj_z.snap.get_var('location.z','Product_Height')
    Product_Depth = product.obj_y.snap.get_var('location.y','Product_Depth')
    insert.loc_z('Product_Height',[Product_Height])
    insert.dim_x('Product_Width',[Product_Width])
    insert.dim_y('Product_Depth',[Product_Depth])

class Standard(sn_types.Assembly):
    """ Standard Frameless Cabinet
    """
    type_assembly = "PRODUCT"
    category_name = "Base Cabinets"
    show_in_library = True
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    id_update = cabinet_properties.LIBRARY_NAME_SPACE + ".update"

    """ Type:sn_types.Assembly - The main carcass used
        The carcass must implement These Prompts:
        Left Side Thickness
        Right Side Thickness
        Top Thickness
        Bottom Thickness
        Top Inset
        Bottom Inset
        Back Inset 
        Left Side Wall Filler
        Right Side Wall Filler
    """
    carcass = None

    """ Type:sn_types.Assembly - Splitter insert to add to the cabinet """
    splitter = None

    """ Type:sn_types.Assembly - Interior insert to add to the cabinet """
    interior = None

    """ Type:sn_types.Assembly - Exterior insert to add to the cabinet """
    exterior = None

    """ Type:bool - This adds an empty opening to the carcass for starter products """
    add_empty_opening = False

    """ Type:bool - This adds a microwave below the cabinet.
                        This is typically only used for upper cabinets """
    add_microwave = False

    """ Type:bool - This adds a vent below the cabinet.
                        This is typically only used for upper cabinets """
    add_vent_hood = False

    """ Type:bool - This adds a countertop to the product. """
    add_countertop = True

    """ Type:float - This is the base price for the product. """
    product_price = 0

    def update_dimensions(self):
        update_dimensions(self)  # Call module level function to find and update door/drawer dim labels

    def update(self):
        props = cabinet_properties.get_scene_props().size_defaults
        carcass_props = cabinet_properties.get_scene_props().carcass_defaults
        
        super().update()

        if hasattr(self, "mirror_z") and self.mirror_z:
            self.obj_z['IS_MIRROR'] = True
        if self.carcass.carcass_type == "Upper":
            self.obj_bp.location.z = props.height_above_floor
        elif self.carcass.carcass_type == "Suspended":
            self.obj_bp.location.z = sn_unit.millimeter(float(props.base_cabinet_height))
            self.obj_bp.location.z = sn_unit.millimeter(float(props.base_cabinet_height)) + carcass_props.toe_kick_height

        self.obj_bp.lm_cabinets.product_shape = 'RECTANGLE'
 
        self.obj_bp["IS_BP_CLOSET"] = True
        self.obj_bp["IS_BP_CABINET"] = True
        self.obj_y['IS_MIRROR'] = True
        self.obj_bp.snap.type_group = self.type_assembly

    def draw(self):
        create_cabinet(self)
        add_carcass(self)

        if self.add_countertop and self.carcass.carcass_type in {"Base","Sink","Suspended"}:
            add_countertop(self)

        if self.splitter:
            add_insert(self,self.splitter)

        if self.interior:
            add_insert(self,self.interior)

        if self.exterior:
            add_insert(self, self.exterior)

        if self.add_empty_opening:
            add_opening(self)

        if self.add_vent_hood:
            vent_bp = self.add_assembly_from_file(VENT)
            vent = sn_types.Assembly(vent_bp)
            vent.set_name("Vent")
            add_undercabinet_appliance(self,vent)

        if self.add_microwave:
            microwave_bp = self.add_assembly_from_file(MICROWAVE)
            microwave = sn_types.Assembly(microwave_bp)
            microwave.set_name("Microwave")
            add_undercabinet_appliance(self,microwave)

        add_product_width_dimension(self)
        add_product_depth_dimension(self)
        add_product_filler_dimension(self, 'Left')
        add_product_filler_dimension(self, 'Right')

        self.update()

class Refrigerator(sn_types.Assembly):
    """ Tall Frameless Refrigerator Cabinet
    """
  
    type_assembly = "PRODUCT"
    show_in_library = True
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    id_update = cabinet_properties.LIBRARY_NAME_SPACE + ".update"
    category_name = "Tall Cabinets"
    
    """ Type:fd_types.Assembly - The main carcass used """
    carcass = None
    
    """ Type:fd_types.Assembly - Splitter insert to add to the cabinet """
    splitter = None
    
    """ Type:fd_types.Assembly - Interior insert to add to the cabinet """
    interior = None
    
    """ Type:fd_types.Assembly - Exterior insert to add to the cabinet """
    exterior = None
    
    """ Type:bool - This adds an empty opening to the carcass for starter products """
    add_empty_opening = False
    
    """ Type:bool - This adds a microwave below the cabinet. 
                        This is typically only used for upper cabinets """
    add_microwave = False
    
    """ Type:bool - This adds a vent below the cabinet. 
                        This is typically only used for upper cabinets """
    add_vent_hood = False
    
    """ Type:float - This is the base price for the product. """   
    product_price = 0

    def update_dimensions(self):
        update_dimensions(self)  # Call module level function to find and update door/drawer dim labels

    def update(self):
        props = cabinet_properties.get_scene_props().size_defaults

        super().update()
        if self.carcass.carcass_type == "Upper":
            self.obj_bp.location.z = props.height_above_floor

        self.obj_bp.lm_cabinets.product_shape = 'RECTANGLE'
        self.obj_bp["IS_BP_CLOSET"] = True
        self.obj_bp["IS_BP_CABINET"] = True
        self.obj_y['IS_MIRROR'] = True
        self.obj_bp.snap.type_group = self.type_assembly

    def draw(self):
        create_cabinet(self)
        self.obj_bp.lm_cabinets.product_shape = 'RECTANGLE'
        
        add_carcass(self)

        if self.splitter:
            add_insert(self,self.splitter)
            Product_Width = self.obj_x.snap.get_var('location.x', 'Product_Width')
            Product_Depth = self.obj_y.snap.get_var('location.y', 'Product_Depth')

            Left_Side_Thickness = self.carcass.get_prompt("Left Side Thickness").get_var()
            Right_Side_Thickness = self.carcass.get_prompt("Right Side Thickness").get_var()     
            Opening_2_Height = self.splitter.obj_z.snap.get_var("location.z", "Opening_2_Height")

            ref_bp = self.add_assembly_from_file(REFRIGERATOR)
            ref = sn_types.Assembly(ref_bp)
            ref.set_name("Refrigerator")

            ref.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
            ref.loc_y("Product_Depth", [Product_Depth])
           
            ref.dim_x('Product_Width-(Left_Side_Thickness+Right_Side_Thickness)',[Product_Width,Left_Side_Thickness,Right_Side_Thickness])
            ref.dim_y('-Product_Depth',[Product_Depth])
            ref.dim_y('-INCH(1.5)')
            # ref.dim_z('Opening_2_Height+INCH(4)',[Opening_2_Height])     
            ref.dim_z('INCH(71.5)')       
            
        add_product_width_dimension(self)
        add_product_depth_dimension(self)
        add_product_filler_dimension(self, 'Left')
        add_product_filler_dimension(self, 'Right')

        self.update()

class Blind_Corner(sn_types.Assembly):
    type_assembly = "PRODUCT"
    show_in_library = True
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    id_update = cabinet_properties.LIBRARY_NAME_SPACE + ".update"
    category_name = "Blind Corner Cabinets"
    blind_side = "Left" # {Left, Right}
    
    carcass = None
    splitter = None
    interior = None
    exterior = None
    add_countertop = True
    
    """ Type:float - This is the base price for the product. """   
    product_price = 0    
    
    def update_dimensions(self):
        update_dimensions(self)  # Call module level function to find and update door/drawer dim labels
    
    def update(self):
        props = cabinet_properties.get_scene_props().size_defaults

        super().update()
        if self.carcass.carcass_type == "Upper":
            self.obj_bp.location.z = props.height_above_floor
            self.obj_z['IS_MIRROR'] = True

        self.obj_bp.lm_cabinets.product_shape = 'RECTANGLE'
        self.obj_bp["IS_BP_CLOSET"] = True
        self.obj_bp["IS_BP_CABINET"] = True
        self.obj_bp["IS_CORNER"] = True
        self.obj_y['IS_MIRROR'] = True
        self.obj_bp.snap.type_group = self.type_assembly

    def add_part(self, path):
        part_bp = self.add_assembly_from_file(path)
        part = sn_types.Assembly(part_bp)
        part.obj_bp.sn_closets.is_panel_bp = True
        return part
        
    def draw(self):
        props = cabinet_properties.get_scene_props().size_defaults
        create_cabinet(self)
        self.obj_bp.lm_cabinets.product_shape = 'RECTANGLE'
        add_carcass(self)

        if self.carcass.carcass_type == 'Base':
            self.add_prompt("Blind Panel Width", 'DISTANCE', props.base_cabinet_depth)
        if self.carcass.carcass_type == 'Tall':
            self.add_prompt("Blind Panel Width", 'DISTANCE', props.tall_cabinet_depth)
        if self.carcass.carcass_type == 'Upper':
            self.mirror_z = True
            self.add_prompt("Blind Panel Width", 'DISTANCE', props.upper_cabinet_depth)
        self.add_prompt("Blind Panel Reveal", 'DISTANCE', props.blind_panel_reveal)
        self.add_prompt("Inset Blind Panel", 'CHECKBOX', props.inset_blind_panel)
        self.add_prompt("Blind Panel Thickness", 'DISTANCE', sn_unit.inch(.75))
                
        Blind_Panel_Width = self.get_prompt('Blind Panel Width').get_var()
        Blind_Panel_Reveal = self.get_prompt('Blind Panel Reveal').get_var()
        Inset_Blind_Panel = self.get_prompt('Inset Blind Panel').get_var()
        Blind_Panel_Thickness = self.get_prompt('Blind Panel Thickness').get_var()
        Carcass_Width = self.carcass.obj_x.snap.get_var("location.x",'Carcass_Width')
        Carcass_Depth = self.carcass.obj_y.snap.get_var("location.y",'Carcass_Depth')
        Carcass_Height = self.carcass.obj_z.snap.get_var("location.z",'Carcass_Height')
        Top_Thickness = self.carcass.get_prompt("Top Thickness").get_var()
        Bottom_Thickness = self.carcass.get_prompt("Bottom Thickness").get_var()
        Right_Side_Thickness = self.carcass.get_prompt("Right Side Thickness").get_var()
        Left_Side_Thickness = self.carcass.get_prompt("Left Side Thickness").get_var()
        Top_Inset = self.carcass.get_prompt("Top Inset").get_var('Top_Inset')
        Bottom_Inset = self.carcass.get_prompt("Bottom Inset").get_var('Bottom_Inset')
        Back_Inset = self.carcass.get_prompt("Back Inset").get_var('Back_Inset')
        
        if self.add_countertop and self.carcass.carcass_type in {"Base","Sink","Suspended"}:
            ctop = add_countertop(self)
            ctop.get_prompt('Side Splash Setback').set_value(value=0)
            if self.blind_side == "Left":
                ctop.get_prompt('Add Left Backsplash').set_value(value=True)
            if self.blind_side == "Right":
                ctop.get_prompt('Add Right Backsplash').set_value(value=True)
        
        blind_panel = self.add_part(BLIND_PANEL)
        blind_panel.obj_bp.snap.name_object = "Blind Panel"
        if self.blind_side == "Left":
            blind_panel.loc_x('IF(Inset_Blind_Panel,Left_Side_Thickness,0)',[Inset_Blind_Panel,Left_Side_Thickness])
            blind_panel.dim_y('(Blind_Panel_Width+Blind_Panel_Reveal-IF(Inset_Blind_Panel,Left_Side_Thickness,0))*-1',[Blind_Panel_Width,Blind_Panel_Reveal,Inset_Blind_Panel,Left_Side_Thickness])
        if self.blind_side == "Right":
            blind_panel.loc_x('Carcass_Width-IF(Inset_Blind_Panel,Right_Side_Thickness,0)',[Carcass_Width,Inset_Blind_Panel,Right_Side_Thickness])
            blind_panel.dim_y('Blind_Panel_Width+Blind_Panel_Reveal-IF(Inset_Blind_Panel,Right_Side_Thickness,0)',[Blind_Panel_Width,Blind_Panel_Reveal,Right_Side_Thickness,Inset_Blind_Panel])
        blind_panel.loc_y('Carcass_Depth+IF(Inset_Blind_Panel,Blind_Panel_Thickness,0)',[Carcass_Depth,Inset_Blind_Panel,Blind_Panel_Thickness])
        if self.carcass.carcass_type in {"Base","Tall","Sink"}:
            Toe_Kick_Height = self.carcass.get_prompt("Toe Kick Height").get_var()
            blind_panel.loc_z('Toe_Kick_Height+IF(Inset_Blind_Panel,Bottom_Thickness,0)',[Toe_Kick_Height,Inset_Blind_Panel,Bottom_Thickness])
            blind_panel.dim_x('Carcass_Height-Toe_Kick_Height-IF(Inset_Blind_Panel,Top_Thickness+Bottom_Thickness,0)',[Carcass_Height,Toe_Kick_Height,Inset_Blind_Panel,Top_Thickness,Bottom_Thickness])
        if self.carcass.carcass_type in {"Upper","Suspended"}:
            blind_panel.loc_z('Carcass_Height+Bottom_Inset-IF(Inset_Blind_Panel,0,Bottom_Thickness)',[Carcass_Height,Bottom_Inset,Inset_Blind_Panel,Bottom_Thickness])
            blind_panel.dim_x('fabs(Carcass_Height)-Top_Inset-Bottom_Inset+IF(Inset_Blind_Panel,0,Top_Thickness+Bottom_Thickness)',[Carcass_Height,Top_Inset,Bottom_Inset,Inset_Blind_Panel,Top_Thickness,Bottom_Thickness])
        blind_panel.rot_y(value=math.radians(-90))
        blind_panel.rot_z(value=math.radians(90))
        blind_panel.dim_z('Blind_Panel_Thickness',[Blind_Panel_Thickness])
        # blind_panel.cutpart("Cabinet_Blind_Panel")
        
        if self.splitter:
            self.splitter.draw()
            self.splitter.obj_bp.parent = self.obj_bp
            if self.blind_side == "Left":
                self.splitter.loc_x('Blind_Panel_Width+Blind_Panel_Reveal',[Blind_Panel_Width,Blind_Panel_Reveal])
            if self.blind_side == "Right":
                self.splitter.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
            self.splitter.loc_y('Carcass_Depth',[Carcass_Depth])
            if self.carcass.carcass_type in {"Base","Tall","Sink"}:
                self.splitter.loc_z('Bottom_Inset',[Bottom_Inset])
            if self.carcass.carcass_type in {"Upper","Suspended"}:
                self.splitter.z_loc('Carcass_Height+Bottom_Inset',[Carcass_Height,Bottom_Inset])
            if self.blind_side == "Left":
                self.splitter.dim_x('Carcass_Width-(Blind_Panel_Width+Blind_Panel_Reveal+Right_Side_Thickness)',[Carcass_Width,Blind_Panel_Width,Blind_Panel_Reveal,Right_Side_Thickness])
            else:
                self.splitter.dim_x('Carcass_Width-(Blind_Panel_Width+Blind_Panel_Reveal+Left_Side_Thickness)',[Carcass_Width,Blind_Panel_Width,Blind_Panel_Reveal,Left_Side_Thickness])
            self.splitter.dim_y('fabs(Carcass_Depth)-Back_Inset-IF(Inset_Blind_Panel,Blind_Panel_Thickness,0)',[Carcass_Depth,Back_Inset,Inset_Blind_Panel,Blind_Panel_Thickness])
            self.splitter.dim_z('fabs(Carcass_Height)-Bottom_Inset-Top_Inset',[Carcass_Height,Bottom_Inset,Top_Inset])
            
        if self.interior:
            self.interior.draw()
            self.interior.obj_bp.parent = self.obj_bp
            self.interior.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
            self.interior.loc_y('Carcass_Depth+IF(Inset_Blind_Panel,Blind_Panel_Thickness,0)',[Carcass_Depth,Inset_Blind_Panel,Blind_Panel_Thickness])
            if self.carcass.carcass_type in {"Base","Tall","Sink"}:
                self.interior.loc_z('Bottom_Inset',[Bottom_Inset])
            if self.carcass.carcass_type in {"Upper","Suspended"}:
                self.interior.loc_z('Carcass_Height+Bottom_Inset',[Carcass_Height,Bottom_Inset])
            self.interior.dim_x('Carcass_Width-(Left_Side_Thickness+Right_Side_Thickness)',[Carcass_Width,Left_Side_Thickness,Right_Side_Thickness])
            self.interior.dim_y('fabs(Carcass_Depth)-Back_Inset-IF(Inset_Blind_Panel,Blind_Panel_Thickness,0)',[Carcass_Depth,Back_Inset,Inset_Blind_Panel,Blind_Panel_Thickness])
            self.interior.dim_z('fabs(Carcass_Height)-Bottom_Inset-Top_Inset',[Carcass_Height,Bottom_Inset,Top_Inset])
            
        if self.exterior:
            self.exterior.draw()
            self.exterior.obj_bp.parent = self.obj_bp
            if self.blind_side == "Left":
                self.exterior.loc_x('Blind_Panel_Width+Blind_Panel_Reveal',[Blind_Panel_Width,Blind_Panel_Reveal])
            if self.blind_side == "Right":
                self.exterior.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
            self.exterior.loc_y('Carcass_Depth',[Carcass_Depth])
            if self.carcass.carcass_type in {"Base","Tall","Sink"}:
                self.exterior.loc_z('Bottom_Inset',[Bottom_Inset])
            if self.carcass.carcass_type in {"Upper","Suspended"}:
                self.exterior.loc_z('Carcass_Height+Bottom_Inset',[Carcass_Height,Bottom_Inset])
            if self.blind_side == "Left":
                self.exterior.dim_x('Carcass_Width-(Blind_Panel_Width+Blind_Panel_Reveal+Right_Side_Thickness)',[Carcass_Width,Blind_Panel_Width,Blind_Panel_Reveal,Right_Side_Thickness])
            else:
                self.exterior.dim_x('Carcass_Width-(Blind_Panel_Width+Blind_Panel_Reveal+Left_Side_Thickness)',[Carcass_Width,Blind_Panel_Width,Blind_Panel_Reveal,Left_Side_Thickness])
            self.exterior.dim_y('fabs(Carcass_Depth)-Back_Inset-IF(Inset_Blind_Panel,Blind_Panel_Thickness,0)',[Carcass_Depth,Back_Inset,Inset_Blind_Panel,Blind_Panel_Thickness])
            self.exterior.dim_z('fabs(Carcass_Height)-Bottom_Inset-Top_Inset',[Carcass_Height,Bottom_Inset,Top_Inset])
            
        add_product_width_dimension(self)
        add_product_depth_dimension(self)
        add_product_filler_dimension(self, 'Left')
        add_product_filler_dimension(self, 'Right')

        self.update()


class Inside_Corner(sn_types.Assembly):
    type_assembly = "PRODUCT"
    show_in_library = True
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    id_update = cabinet_properties.LIBRARY_NAME_SPACE + ".update"
    category_name = "Inside Corner Cabinets"
 
    carcass = None
    interior = None
    exterior = None
    
    add_countertop = True
    
    """ Type:float - This is the base price for the product. """   
    product_price = 0

    def update_dimensions(self):
        update_dimensions(self)  # Call module level function to find and update door/drawer dim labels

    def add_pie_cut_doors(self):
        Width = self.carcass.obj_x.snap.get_var("location.x",'Width')
        Height = self.carcass.obj_z.snap.get_var("location.z",'Height')
        Depth = self.carcass.obj_y.snap.get_var("location.y",'Depth')

        Top_Inset = self.carcass.get_prompt("Top Inset").get_var()
        Bottom_Inset = self.carcass.get_prompt("Bottom Inset").get_var()
        Cabinet_Depth_Left = self.carcass.get_prompt("Cabinet Depth Left").get_var()
        Cabinet_Depth_Right = self.carcass.get_prompt("Cabinet Depth Right").get_var()
        Left_Side_Thickness = self.carcass.get_prompt("Left Side Thickness").get_var()
        Right_Side_Thickness = self.carcass.get_prompt("Right Side Thickness").get_var()
        
        self.exterior.draw()
        self.exterior.obj_bp.parent = self.obj_bp
        self.exterior.loc_x('Cabinet_Depth_Left',[Cabinet_Depth_Left])
        self.exterior.loc_y('-Cabinet_Depth_Right',[Cabinet_Depth_Right])
        if self.carcass.carcass_type == "Base":
            self.exterior.loc_z('Bottom_Inset',[Bottom_Inset])
        if self.carcass.carcass_type == "Upper":
            self.exterior.loc_z('Height+Bottom_Inset',[Height,Bottom_Inset])
        self.exterior.dim_x('Width-Cabinet_Depth_Left-Left_Side_Thickness',[Width,Cabinet_Depth_Left,Left_Side_Thickness])
        self.exterior.dim_y('Depth+Cabinet_Depth_Right+Right_Side_Thickness',[Depth,Cabinet_Depth_Right,Right_Side_Thickness])
        self.exterior.dim_z('fabs(Height)-Bottom_Inset-Top_Inset',[Height,Bottom_Inset,Top_Inset])
        
    def add_diagonal_doors(self):
        Width = self.carcass.obj_x.snap.get_var("location.x",'Width')
        Height = self.carcass.obj_z.snap.get_var("location.z",'Height')
        Depth = self.carcass.obj_y.snap.get_var("location.y",'Depth')

        Top_Inset = self.carcass.get_prompt("Top Inset").get_var()
        Bottom_Inset = self.carcass.get_prompt("Bottom Inset").get_var()
        Cabinet_Depth_Left = self.carcass.get_prompt("Cabinet Depth Left").get_var()
        Cabinet_Depth_Right = self.carcass.get_prompt("Cabinet Depth Right").get_var()
        Left_Side_Thickness = self.carcass.get_prompt("Left Side Thickness").get_var()
        Right_Side_Thickness = self.carcass.get_prompt("Right Side Thickness").get_var()
        
        self.exterior.draw()
        self.exterior.obj_bp.parent = self.obj_bp
        self.exterior.loc_x('Cabinet_Depth_Left',[Cabinet_Depth_Left])
        self.exterior.loc_y('Depth+Left_Side_Thickness',[Depth,Left_Side_Thickness])
        if self.carcass.carcass_type == "Base":
            self.exterior.loc_z('Bottom_Inset',[Bottom_Inset])
        if self.carcass.carcass_type == "Upper":
            self.exterior.loc_z('Height+Bottom_Inset',[Height,Bottom_Inset])
        self.exterior.rot_z('atan((fabs(Depth)-Left_Side_Thickness-Cabinet_Depth_Right)/(fabs(Width)-Right_Side_Thickness-Cabinet_Depth_Left))',[Depth,Left_Side_Thickness,Cabinet_Depth_Right,Width,Right_Side_Thickness,Cabinet_Depth_Left])
        self.exterior.dim_x('sqrt(((fabs(Depth)-Left_Side_Thickness-Cabinet_Depth_Right)**2)+((fabs(Width)-Right_Side_Thickness-Cabinet_Depth_Left)**2))',[Depth,Left_Side_Thickness,Cabinet_Depth_Right,Width,Right_Side_Thickness,Cabinet_Depth_Left])
        self.exterior.dim_y('Depth+Cabinet_Depth_Right+Right_Side_Thickness',[Depth,Cabinet_Depth_Right,Right_Side_Thickness])
        self.exterior.dim_z('fabs(Height)-Bottom_Inset-Top_Inset',[Height,Bottom_Inset,Top_Inset])
        
    def update(self):
        props = cabinet_properties.get_scene_props().size_defaults

        super().update()
        if self.carcass.carcass_type == "Upper":

            self.obj_bp.location.z = props.height_above_floor
            self.obj_z['IS_MIRROR'] = True

        self.obj_bp["IS_BP_CLOSET"] = True
        self.obj_bp["IS_BP_CABINET"] = True
        self.obj_bp["IS_CORNER"] = True
        self.obj_y['IS_MIRROR'] = True
        self.obj_bp.snap.type_group = self.type_assembly

    def draw(self):
        create_cabinet(self)
        add_carcass(self)
        
        Product_Width = self.obj_x.snap.get_var('location.x', 'Product_Width')
        Product_Height = self.obj_z.snap.get_var('location.z', 'Product_Height')
        Product_Depth = self.obj_y.snap.get_var('location.y', 'Product_Depth')
        
        add_product_depth_dimension(self)
        
        if self.add_countertop and self.carcass.carcass_type in {"Base","Sink","Suspended"}:
            self.add_prompt("Countertop Overhang Right Front",'DISTANCE',sn_unit.inch(1.5))
            self.add_prompt("Countertop Overhang Left Front",'DISTANCE',sn_unit.inch(1.5))
            self.add_prompt("Countertop Overhang Right Back",'DISTANCE',sn_unit.inch(0))
            self.add_prompt("Countertop Overhang Left Back",'DISTANCE',sn_unit.inch(0))
            self.add_prompt("Countertop Overhang Left",'DISTANCE',sn_unit.inch(0))
            self.add_prompt("Countertop Overhang Right",'DISTANCE',sn_unit.inch(0))
            Countertop_Overhang_Right_Front = self.get_prompt('Countertop Overhang Right Front').get_var()
            Countertop_Overhang_Left_Front = self.get_prompt('Countertop Overhang Left Front').get_var()
            Countertop_Overhang_Right_Back = self.get_prompt('Countertop Overhang Right Back').get_var()
            Countertop_Overhang_Left_Back = self.get_prompt('Countertop Overhang Left Back').get_var()
            Countertop_Overhang_Left = self.get_prompt('Countertop Overhang Left').get_var()
            Countertop_Overhang_Right = self.get_prompt('Countertop Overhang Right').get_var()
            
            Left_Side_Wall_Filler = self.carcass.get_prompt('Left Side Wall Filler').get_var()
            Right_Side_Wall_Filler = self.carcass.get_prompt('Right Side Wall Filler').get_var()
            Cabinet_Depth_Left = self.carcass.get_prompt('Cabinet Depth Left').get_var()
            Cabinet_Depth_Right = self.carcass.get_prompt('Cabinet Depth Right').get_var()
            
            if self.carcass.carcass_shape == "Notched":
                ctop = cabinet_countertops.PRODUCT_Notched_Corner_Countertop()
            else:
                ctop = cabinet_countertops.PRODUCT_Diagonal_Corner_Countertop()
            ctop.draw()
            ctop.obj_bp.snap.type_group = 'INSERT'
            ctop.obj_bp.parent = self.obj_bp

            ctop.loc_x('-Countertop_Overhang_Left_Back',[Countertop_Overhang_Left_Back])
            ctop.loc_y('Countertop_Overhang_Right_Back',[Countertop_Overhang_Right_Back])
            ctop.loc_z('Product_Height',[Product_Height])
            ctop.dim_x('Product_Width+Countertop_Overhang_Left_Back+Countertop_Overhang_Right+Right_Side_Wall_Filler',
                        [Product_Width,Countertop_Overhang_Left_Back,Countertop_Overhang_Right,Right_Side_Wall_Filler])
            ctop.dim_y('Product_Depth-Countertop_Overhang_Right_Back-Countertop_Overhang_Left-Left_Side_Wall_Filler',
                        [Product_Depth,Countertop_Overhang_Right_Back,Countertop_Overhang_Left,Left_Side_Wall_Filler])
            ctop.dim_z(value=sn_unit.inch(4))
            ctop.get_prompt("Left Side Depth").set_formula('Cabinet_Depth_Left+Countertop_Overhang_Left_Back+Countertop_Overhang_Left_Front',
                        [Cabinet_Depth_Left,Countertop_Overhang_Left_Back,Countertop_Overhang_Left_Front])
            ctop.get_prompt("Right Side Depth").set_formula('Cabinet_Depth_Right+Countertop_Overhang_Right_Back+Countertop_Overhang_Right_Front',
                        [Cabinet_Depth_Right,Countertop_Overhang_Right_Back,Countertop_Overhang_Right_Front])

        if self.interior:
            add_insert(self,self.interior)

        if self.carcass.carcass_shape == 'Notched':
            self.obj_bp.lm_cabinets.product_shape = 'INSIDE_NOTCH'
            if self.exterior:
                self.add_pie_cut_doors()
        
        if self.carcass.carcass_shape == 'Diagonal':
            self.obj_bp.lm_cabinets.product_shape = 'INSIDE_DIAGONAL'
            if self.exterior:
                self.add_diagonal_doors()

        # self.obj_bp.lm_cabinets.product_shape = 'RECTANGLE'
        add_product_width_dimension(self)
        add_product_depth_dimension(self)
        add_product_filler_dimension(self, 'Left')
        add_product_filler_dimension(self, 'Right')

        self.update()