import os
from snap import sn_unit
from . import appliance_types
from .appliance_paths import (
    WALL_APPLIANCE_PATH,
    COOKTOP_APPLIANCE_PATH,
    SINK_APPLIANCE_PATH,
    FAUCET_APPLIANCE_PATH,
    LAUNDRY_APPLIANCE_PATH
)


# ---------PRODUCT: PARAMETRIC APPLIANCES


class PRODUCT_Refrigerator(appliance_types.Parametric_Wall_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.assembly_name = "Refrigerator"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(84)
        self.depth = sn_unit.inch(27)
        self.appliance_path = os.path.join(WALL_APPLIANCE_PATH, "Professional Refrigerator Generic.blend")
        super().__init__()


class PRODUCT_Range(appliance_types.Parametric_Wall_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.assembly_name = "Range"
        self.width = sn_unit.inch(30)
        self.height = sn_unit.inch(42)
        self.depth = sn_unit.inch(28)
        self.appliance_path = os.path.join(WALL_APPLIANCE_PATH, "Professional Gas Range Generic.blend")
        super().__init__()


class PRODUCT_Dishwasher(appliance_types.Parametric_Wall_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.assembly_name = "Dishwasher"
        self.width = sn_unit.inch(24)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)
        self.appliance_path = os.path.join(WALL_APPLIANCE_PATH, "Professional Dishwasher Generic.blend")
        super().__init__()


class PRODUCT_Range_Hood(appliance_types.Parametric_Wall_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.assembly_name = "Range Hood"
        self.width = sn_unit.inch(30)
        self.height = sn_unit.inch(14)
        self.depth = sn_unit.inch(12.5)
        self.appliance_path = os.path.join(WALL_APPLIANCE_PATH, "Wall Mounted Range Hood 01.blend")
        self.height_above_floor = sn_unit.inch(60)
        super().__init__()


class PRODUCT_Washer(appliance_types.Parametric_Wall_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.width = sn_unit.inch(27)
        self.height = sn_unit.inch(38)
        self.depth = sn_unit.inch(34)
        self.appliance_path = os.path.join(WALL_APPLIANCE_PATH, "Washer Generic.blend")
        super().__init__()


class PRODUCT_Dryer(appliance_types.Parametric_Wall_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.width = sn_unit.inch(27)
        self.height = sn_unit.inch(38)
        self.depth = sn_unit.inch(34)
        self.appliance_path = os.path.join(WALL_APPLIANCE_PATH, "Dryer Generic.blend")
        super().__init__()


class PRODUCT_Wine_Cooler(appliance_types.Parametric_Wall_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(84)
        self.depth = sn_unit.inch(24)
        self.appliance_path = os.path.join(WALL_APPLIANCE_PATH, "Wine Cooler.blend")
        super().__init__()


# ---------PRODUCT: COOK TOPS
class PRODUCT_Wolf_CG152_Transitional_Gas_Cooktop(appliance_types.Countertop_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.appliance_path = os.path.join(COOKTOP_APPLIANCE_PATH, "Wolf CG152 Transitional Gas Cooktop.blend")
        super().__init__()


# ---------PRODUCT: SINKS
class PRODUCT_Bathroom_Sink(appliance_types.Countertop_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.appliance_path = os.path.join(SINK_APPLIANCE_PATH, "Bathroom Sink.blend")
        super().__init__()


class PRODUCT_Double_Basin_Sink(appliance_types.Countertop_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.appliance_path = os.path.join(SINK_APPLIANCE_PATH, "Double Basin Sink.blend")
        super().__init__()


class PRODUCT_Single_Basin_Sink(appliance_types.Countertop_Appliance):

    def __init__(self):
        self.category_name = "Appliances"
        self.appliance_path = os.path.join(SINK_APPLIANCE_PATH, "Single Basin Sink.blend")
        super().__init__()


