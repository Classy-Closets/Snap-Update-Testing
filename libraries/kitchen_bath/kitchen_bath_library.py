from snap import sn_unit
from . import cabinets
from . import carcass_simple
from . import frameless_exteriors
from . import cabinet_interiors
from . import frameless_splitters
from . import cabinet_properties
from . import frameless_appliances


LIBRARY_NAME = "Cabinets"
BASE_CATEGORY_NAME = "Base Cabinets"
TALL_CATEGORY_NAME = "Tall Cabinets"
UPPER_CATEGORY_NAME = "Upper Cabinets"
STARTER_CATEGORY_NAME = "Starter Cabinets"
DRAWER_CATEGORY_NAME = "Drawer Cabinets"
BLIND_CORNER_CATEGORY_NAME = "Blind Corner Cabinets"
INSIDE_CORNER_CATEGORY_NAME = "Inside Corner Cabinets"


class PRODUCT_1_Door_Base(cabinets.Standard):

    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.base_adj_shelf_qty

class PRODUCT_2_Door_Base(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.base_adj_shelf_qty
        
class PRODUCT_2_Door_Sink(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.sink_cabinet_height
        self.depth = props.sink_cabinet_depth
        self.carcass = carcass_simple.INSERT_Sink_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = 0
         
class PRODUCT_2_Door_with_False_Front_Sink(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.sink_cabinet_height
        self.depth = props.sink_cabinet_depth
        self.carcass = carcass_simple.INSERT_Sink_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Double_Door_with_False_Front()
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = 0
        
class PRODUCT_2_Door_2_False_Front_Sink(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.sink_cabinet_height
        self.depth = props.sink_cabinet_depth
        self.carcass = carcass_simple.INSERT_Sink_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Double_Door_with_2_False_Front()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = 0
         
class PRODUCT_1_Door_Sink(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.sink_cabinet_height
        self.depth = props.sink_cabinet_depth
        self.carcass = carcass_simple.INSERT_Sink_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = 0

class PRODUCT_1_Door_1_Drawer_Base(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_1_height = sn_unit.millimeter(float(props.top_drawer_front_height)) - sn_unit.inch(0.8)
        self.splitter.exterior_1 = frameless_exteriors.INSERT_1_Drawer()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Base_Single_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()
        self.splitter.interior_2.shelf_qty = int_props.base_adj_shelf_qty

class PRODUCT_2_Door_2_Drawer_Base(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_1_height = sn_unit.millimeter(float(props.top_drawer_front_height)) - sn_unit.inch(0.8)
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Horizontal_Drawers()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Base_Double_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()
        self.splitter.interior_2.shelf_qty = int_props.base_adj_shelf_qty
class PRODUCT_2_Door_1_Drawer_Base(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_1_height = sn_unit.millimeter(float(props.top_drawer_front_height)) - sn_unit.inch(0.8)
        self.splitter.exterior_1 = frameless_exteriors.INSERT_1_Drawer()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Base_Double_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()
        self.splitter.interior_2.shelf_qty = int_props.base_adj_shelf_qty

class PRODUCT_Microwave_2_Door_Base(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_1_height = sn_unit.inch(14.61)
        self.splitter.exterior_1 = frameless_appliances.INSERT_Microwave()
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Base_Double_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':False}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()
        self.splitter.interior_2.shelf_qty = 0
 
class PRODUCT_Microwave_1_Drawer_Base(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BASE_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_1_height = sn_unit.inch(14.61)
        self.splitter.exterior_1 = frameless_appliances.INSERT_Microwave()
        self.splitter.exterior_2 = frameless_exteriors.INSERT_1_Drawer()

class PRODUCT_4_Door_Oven_Tall(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = TALL_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.splitter = frameless_splitters.INSERT_3_Vertical_Openings()
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Upper_Double_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Top':False}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_2 = frameless_appliances.INSERT_Single_Oven()
        self.splitter.interior_3 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_3 = frameless_exteriors.INSERT_Base_Double_Door()
        self.splitter.exterior_3.prompts = {'Half Overlay Top':False}
        self.splitter.interior_3 = cabinet_interiors.INSERT_Shelves()

class PRODUCT_4_Door_Micro_and_Oven_Tall(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = TALL_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.splitter = frameless_splitters.INSERT_4_Vertical_Openings()
        self.splitter.opening_3_height = sn_unit.inch(30)
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Upper_Double_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Top':False}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_2 = frameless_appliances.INSERT_Microwave()
        self.splitter.exterior_3 = frameless_appliances.INSERT_Single_Oven()
        self.splitter.interior_4 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_4 = frameless_exteriors.INSERT_Base_Double_Door()
        self.splitter.exterior_4.prompts = {'Half Overlay Top':False}
        self.splitter.interior_4 = cabinet_interiors.INSERT_Shelves()

class PRODUCT_Refrigerator_Tall(cabinets.Refrigerator):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = TALL_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.carcass.prompts = {'Remove Bottom':True}
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_1_height = sn_unit.inch(10)
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Upper_Double_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Top':False}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.interior_1.shelf_qty = 0
        
        
class PRODUCT_1_Door_Tall(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = TALL_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.exterior = frameless_exteriors.INSERT_Tall_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.tall_adj_shelf_qty
        
class PRODUCT_2_Door_Tall(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = TALL_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.exterior = frameless_exteriors.INSERT_Tall_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.tall_adj_shelf_qty
        
class PRODUCT_1_Double_Door_Tall(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = TALL_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Upper_Single_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Base_Single_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()
   
class PRODUCT_2_Double_Door_Tall(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = TALL_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Upper_Double_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Base_Double_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()
        
class PRODUCT_2_Door_2_Drawer_Tall(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = TALL_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_2_height = sn_unit.inch(20)
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Tall_Double_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_2 = frameless_exteriors.INSERT_2_Drawer_Stack()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}

class PRODUCT_2_Door_3_Drawer_Tall(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = TALL_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_2_height = sn_unit.inch(20)
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Tall_Double_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_2 = frameless_exteriors.INSERT_3_Drawer_Stack()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}

class PRODUCT_1_Door_Upper(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = UPPER_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.mirror_z = True
        self.height_above_floor = props.height_above_floor
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.upper_adj_shelf_qty
        
class PRODUCT_2_Door_Upper(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = UPPER_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.mirror_z = True
        self.height_above_floor = props.height_above_floor
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.upper_adj_shelf_qty

class PRODUCT_1_Double_Door_Upper(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = UPPER_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.mirror_z = True
        self.height_above_floor = props.height_above_floor
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Upper_Single_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Upper_Single_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.exterior_2 = cabinet_interiors.INSERT_Shelves()

class PRODUCT_2_Double_Door_Upper(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = UPPER_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.mirror_z = True
        self.height_above_floor = props.height_above_floor
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Upper_Double_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Upper_Double_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()

class PRODUCT_Microwave_2_Door_Upper(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = UPPER_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.mirror_z = True
        self.height_above_floor = props.height_above_floor
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Upper_Double_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Top':False}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_2 = frameless_appliances.INSERT_Microwave()

class PRODUCT_2_Door_Upper_with_Microwave(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = UPPER_CATEGORY_NAME
        self.width = sn_unit.inch(30)
        self.height = str(float(props.upper_cabinet_height) - 512)
        self.depth = props.upper_cabinet_depth
        self.mirror_z = True
        self.height_above_floor = props.height_above_floor
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.add_microwave = True
         
class PRODUCT_2_Door_Upper_with_Vent(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = UPPER_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = str(float(props.upper_cabinet_height) - 512)
        self.depth = props.upper_cabinet_depth
        self.mirror_z = True
        self.height_above_floor = props.height_above_floor
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.add_vent_hood = True
        
class PRODUCT_2_Door_2_Drawer_Upper(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = UPPER_CATEGORY_NAME
        self.width = props.width_2_door
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.mirror_z = True
        self.height_above_floor = props.height_above_floor
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Upper_Double_Door()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.interior_1 = cabinet_interiors.INSERT_Shelves()
        self.splitter.exterior_2 = frameless_exteriors.INSERT_2_Drawer_Stack()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        
class PRODUCT_1_Drawer_Base(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = DRAWER_CATEGORY_NAME
        self.width = props.width_drawer
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = frameless_exteriors.INSERT_1_Drawer()

class PRODUCT_2_Drawer_Base(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = DRAWER_CATEGORY_NAME
        self.width = props.width_drawer
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = frameless_exteriors.INSERT_2_Drawer_Stack()
        if not props.equal_drawer_stack_heights:
            self.exterior.top_drawer_front_height = props.top_drawer_front_height

class PRODUCT_3_Drawer_Base(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = DRAWER_CATEGORY_NAME
        self.width = props.width_drawer
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = frameless_exteriors.INSERT_3_Drawer_Stack()
        if not props.equal_drawer_stack_heights:
            self.exterior.top_drawer_front_height = props.top_drawer_front_height
            
class PRODUCT_4_Drawer_Base(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = DRAWER_CATEGORY_NAME
        self.width = props.width_drawer
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = frameless_exteriors.INSERT_4_Drawer_Stack()
        if not props.equal_drawer_stack_heights:
            self.exterior.top_drawer_front_height = props.top_drawer_front_height
            
class PRODUCT_1_Drawer_Suspended(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = DRAWER_CATEGORY_NAME
        self.width = props.width_drawer
        self.height = props.suspended_cabinet_height
        self.depth = props.suspended_cabinet_depth
        self.mirror_z = True
        self.carcass = carcass_simple.INSERT_Suspended_Carcass()
        self.height_above_floor = props.base_cabinet_height
        self.exterior = frameless_exteriors.INSERT_1_Drawer()
        
class PRODUCT_2_Drawer_Suspended(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = DRAWER_CATEGORY_NAME
        self.width = props.width_drawer * 2
        self.height = props.suspended_cabinet_height
        self.depth = props.suspended_cabinet_depth
        self.mirror_z = True
        self.carcass = carcass_simple.INSERT_Suspended_Carcass()
        self.height_above_floor = props.base_cabinet_height
        self.exterior = frameless_exteriors.INSERT_Horizontal_Drawers()

class PRODUCT_1_Door_Blind_Left_Corner_Base(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Left"
        self.width = props.base_width_blind
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.base_adj_shelf_qty

class PRODUCT_1_Door_Blind_Right_Corner_Base(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Right"
        self.width = props.base_width_blind
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.base_adj_shelf_qty

class PRODUCT_1_Door_Blind_Left_Corner_Tall(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Left"
        self.width = props.tall_width_blind
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.exterior = frameless_exteriors.INSERT_Tall_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.tall_adj_shelf_qty

class PRODUCT_1_Door_Blind_Right_Corner_Tall(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Right"
        self.width = props.tall_width_blind
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.exterior = frameless_exteriors.INSERT_Tall_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.tall_adj_shelf_qty

class PRODUCT_1_Door_Blind_Left_Corner_Upper(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Left"
        self.height_above_floor = props.height_above_floor
        self.mirror_z = True
        self.width = props.upper_width_blind
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.upper_adj_shelf_qty

class PRODUCT_1_Door_Blind_Right_Corner_Upper(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Right"
        self.height_above_floor = props.height_above_floor
        self.mirror_z = True
        self.width = props.upper_width_blind
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.upper_adj_shelf_qty

class PRODUCT_2_Door_Blind_Left_Corner_Base(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Left"
        self.width = props.base_width_blind
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Double_Door()
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.base_adj_shelf_qty

class PRODUCT_2_Door_Blind_Right_Corner_Base(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Right"
        self.width = props.base_width_blind
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.base_adj_shelf_qty

class PRODUCT_2_Door_Blind_Left_Corner_Tall(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Left"
        self.width = props.tall_width_blind
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.exterior = frameless_exteriors.INSERT_Tall_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.tall_adj_shelf_qty

class PRODUCT_2_Door_Blind_Right_Corner_Tall(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Right"
        self.width = props.tall_width_blind
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.exterior = frameless_exteriors.INSERT_Tall_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.tall_adj_shelf_qty

class PRODUCT_2_Door_Blind_Left_Corner_Upper(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Left"
        self.height_above_floor = props.height_above_floor
        self.mirror_z = True
        self.width = props.upper_width_blind
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.upper_adj_shelf_qty

class PRODUCT_2_Door_Blind_Right_Corner_Upper(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Right"
        self.height_above_floor = props.height_above_floor
        self.mirror_z = True
        self.width = props.upper_width_blind
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.shelf_qty = int_props.upper_adj_shelf_qty

class PRODUCT_1_Door_1_Drawer_Blind_Right_Corner_Base(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Right"
        self.width = props.base_width_blind
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_1_height = sn_unit.millimeter(float(props.top_drawer_front_height)) - sn_unit.inch(0.8)
        self.splitter.exterior_1 = frameless_exteriors.INSERT_1_Drawer()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Base_Single_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()
        self.splitter.interior_2.shelf_qty = int_props.base_adj_shelf_qty
        
class PRODUCT_1_Door_1_Drawer_Blind_Left_Corner_Base(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Left"
        self.width = props.base_width_blind
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_1_height = sn_unit.millimeter(float(props.top_drawer_front_height)) - sn_unit.inch(0.8)
        self.splitter.exterior_1 = frameless_exteriors.INSERT_1_Drawer()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Base_Single_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()
        self.splitter.interior_2.shelf_qty = int_props.base_adj_shelf_qty
        
class PRODUCT_2_Door_2_Drawer_Blind_Right_Corner_Base(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Right"
        self.width = props.base_width_blind
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_1_height = sn_unit.millimeter(float(props.top_drawer_front_height)) - sn_unit.inch(0.8)
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Horizontal_Drawers()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Base_Double_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()
        self.splitter.interior_2.shelf_qty = int_props.base_adj_shelf_qty
        
class PRODUCT_2_Door_2_Drawer_Blind_Left_Corner_Base(cabinets.Blind_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = BLIND_CORNER_CATEGORY_NAME
        self.blind_side = "Left"
        self.width = props.base_width_blind
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.splitter = frameless_splitters.INSERT_2_Vertical_Openings()
        self.splitter.opening_1_height = sn_unit.millimeter(float(props.top_drawer_front_height)) - sn_unit.inch(0.8)
        self.splitter.exterior_1 = frameless_exteriors.INSERT_Horizontal_Drawers()
        self.splitter.exterior_1.prompts = {'Half Overlay Bottom':True}
        self.splitter.exterior_2 = frameless_exteriors.INSERT_Base_Double_Door()
        self.splitter.exterior_2.prompts = {'Half Overlay Top':True}
        self.splitter.interior_2 = cabinet_interiors.INSERT_Shelves()
        self.splitter.interior_2.shelf_qty = int_props.base_adj_shelf_qty

class PRODUCT_Pie_Cut_Corner_Base(cabinets.Inside_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = INSIDE_CORNER_CATEGORY_NAME
        self.width = props.base_inside_corner_size
        self.height = props.base_cabinet_height
        self.depth = props.base_inside_corner_size
        self.carcass = carcass_simple.INSERT_Base_Inside_Corner_Notched_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Pie_Cut_Door()
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.carcass_type = "Base"
        self.interior.carcass_shape = "NOTCHED"
        self.interior.shelf_qty = int_props.base_adj_shelf_qty
     
        
class PRODUCT_Pie_Cut_Corner_Upper(cabinets.Inside_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = INSIDE_CORNER_CATEGORY_NAME
        self.width = props.upper_inside_corner_size
        self.height = props.upper_cabinet_height
        self.depth = props.upper_inside_corner_size
        self.height_above_floor = props.height_above_floor
        self.mirror_z = True
        self.carcass = carcass_simple.INSERT_Upper_Inside_Corner_Notched_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Pie_Cut_Door()
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.carcass_type = "Upper"
        self.interior.carcass_shape = "NOTCHED"
        self.interior.shelf_qty = int_props.upper_adj_shelf_qty
        
class PRODUCT_1_Door_Diagonal_Corner_Base(cabinets.Inside_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = INSIDE_CORNER_CATEGORY_NAME
        self.width = props.base_inside_corner_size
        self.height = props.base_cabinet_height
        self.depth = props.base_inside_corner_size
        self.carcass = carcass_simple.INSERT_Base_Inside_Corner_Diagonal_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Single_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.carcass_type = "Base"
        self.interior.carcass_shape = "DIAGONAL"
        self.interior.shelf_qty = int_props.base_adj_shelf_qty
        
class PRODUCT_2_Door_Diagonal_Corner_Base(cabinets.Inside_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = INSIDE_CORNER_CATEGORY_NAME
        self.width = props.base_inside_corner_size
        self.height = props.base_cabinet_height
        self.depth = props.base_inside_corner_size
        self.carcass = carcass_simple.INSERT_Base_Inside_Corner_Diagonal_Carcass()
        self.exterior = frameless_exteriors.INSERT_Base_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.carcass_type = "Base"
        self.interior.carcass_shape = "DIAGONAL"
        self.interior.shelf_qty = int_props.base_adj_shelf_qty
        
class PRODUCT_1_Door_Diagonal_Corner_Upper(cabinets.Inside_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = INSIDE_CORNER_CATEGORY_NAME
        self.width = props.upper_inside_corner_size
        self.height = props.upper_cabinet_height
        self.depth = props.upper_inside_corner_size
        self.height_above_floor = props.height_above_floor
        self.mirror_z = True
        self.carcass = carcass_simple.INSERT_Upper_Inside_Corner_Diagonal_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Single_Door()
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.carcass_type = "Upper"
        self.interior.carcass_shape = "DIAGONAL"
        self.interior.shelf_qty = int_props.upper_adj_shelf_qty
        
class PRODUCT_2_Door_Diagonal_Corner_Upper(cabinets.Inside_Corner):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        int_props = cabinet_properties.get_scene_props().interior_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = INSIDE_CORNER_CATEGORY_NAME
        self.width = props.upper_inside_corner_size
        self.height = props.upper_cabinet_height
        self.depth = props.upper_inside_corner_size
        self.height_above_floor = props.height_above_floor
        self.mirror_z = True
        self.carcass = carcass_simple.INSERT_Upper_Inside_Corner_Diagonal_Carcass()
        self.exterior = frameless_exteriors.INSERT_Upper_Double_Door()
        self.exterior.prompts = {'Half Overlay Top':False}
        self.interior = cabinet_interiors.INSERT_Shelves()
        self.interior.carcass_type = "Upper"
        self.interior.carcass_shape = "DIAGONAL"
        self.interior.shelf_qty = int_props.upper_adj_shelf_qty


class PRODUCT_Base_Starter(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = STARTER_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.base_cabinet_height
        self.depth = props.base_cabinet_depth
        self.carcass = carcass_simple.INSERT_Base_Carcass()
        self.exterior = None
        self.interior = None
        self.add_empty_opening = True

class PRODUCT_Tall_Starter(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = STARTER_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.tall_cabinet_height
        self.depth = props.tall_cabinet_depth
        self.carcass = carcass_simple.INSERT_Tall_Carcass()
        self.exterior = None
        self.interior = None
        self.add_empty_opening = True

class PRODUCT_Upper_Starter(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = STARTER_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.upper_cabinet_height
        self.depth = props.upper_cabinet_depth
        self.mirror_z = True
        self.carcass = carcass_simple.INSERT_Upper_Carcass()
        self.exterior = None
        self.interior = None
        self.height_above_floor = props.height_above_floor
        self.add_empty_opening = True

class PRODUCT_Sink_Starter(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = STARTER_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.sink_cabinet_height
        self.depth = props.sink_cabinet_depth
        self.carcass = carcass_simple.INSERT_Sink_Carcass()
        self.exterior = None
        self.interior = None
        self.add_empty_opening = True

class PRODUCT_Suspended_Starter(cabinets.Standard):
    
    def __init__(self):
        props = cabinet_properties.get_scene_props().size_defaults
        self.library_name = LIBRARY_NAME
        self.category_name = STARTER_CATEGORY_NAME
        self.width = props.width_1_door
        self.height = props.suspended_cabinet_height
        self.depth = props.suspended_cabinet_depth
        self.carcass = carcass_simple.INSERT_Suspended_Carcass()
        self.mirror_z = True
        self.exterior = None
        self.interior = None
        self.height_above_floor = props.base_cabinet_height
        self.add_empty_opening = True




        