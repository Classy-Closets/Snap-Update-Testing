import math
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, FloatProperty, EnumProperty

from snap import sn_types, sn_unit, sn_utils
from ..ops.drop_closet import PlaceClosetInsert
from .. import closet_props
from ..common import common_parts
from ..common import common_prompts
from ..common import common_lists


class Wall_Bed(sn_types.Assembly):
    """Wall Bed"""

    type_assembly = "PRODUCT"
    id_prompt = "sn_closets.prompts_wall_bed"

    show_in_library = True

    library_name = ""
    category_name = ""
    bed_make = 0

    def add_prompts(self):
        common_prompts.add_thickness_prompts(self)
        self.add_prompt("Bed Make", "COMBOBOX", self.bed_make, ['Eurobed', '24/7', 'Murphy'])
        self.add_prompt("Bed Type", "COMBOBOX", 0, ['Twin', 'Double', 'Queen', 'Double XL'])
        self.add_prompt("Wall Bed Panel Thickness", 'DISTANCE', sn_unit.inch(1))
        #TODO Remove Extend Height and Depth, change to just Height and Depth
        # self.add_prompt("Extend Height", 'DISTANCE', 0)
        # self.add_prompt("Extend Depth", 'DISTANCE', 0)
        self.add_prompt("Wall Bed Height", 'DISTANCE', sn_unit.inch(82.13))
        self.add_prompt("Wall Bed Depth", 'DISTANCE', sn_unit.inch(24))
        self.add_prompt("Open", 'CHECKBOX', False)
        self.add_prompt("Add Doors And Drawers", 'CHECKBOX', True)
        self.add_prompt("Door Overlay Amount", 'DISTANCE', sn_unit.inch(0.215))
        self.add_prompt("Second Row Of Doors", 'CHECKBOX', False)
        self.add_prompt("Door Space", 'DISTANCE', self.height - sn_unit.inch(5.38))
        # self.add_prompt("Left Door Space", 'DISTANCE', self.obj_z.location.z - sn_unit.inch(5.38))
        # self.add_prompt("Right Door Space", 'DISTANCE', self.obj_z.location.z - sn_unit.inch(5.38))
        self.add_prompt("Drawer Stack Quantity", 'QUANTITY', 0)
        # self.add_prompt("Left Drawer Stack Quantity", 'QUANTITY', 0)
        # self.add_prompt("Right Drawer Stack Quantity", 'QUANTITY', 0)
        self.add_prompt("Drawer Stack Height", 'DISTANCE', 0)
        # self.add_prompt("Left Drawer Stack Height", 'DISTANCE', 0)
        # self.add_prompt("Right Drawer Stack Height", 'DISTANCE', 0)
        self.add_prompt("Pull Location", 'DISTANCE', sn_unit.inch(30))
        self.add_prompt("Top Door Height", 'DISTANCE', sn_unit.millimeter(877.316))
        # self.add_prompt("Top Left Door Height", 'DISTANCE', sn_unit.millimeter(877.316))
        # self.add_prompt("Top Right Door Height", 'DISTANCE', sn_unit.millimeter(877.316))
        self.add_prompt("Decorative Melamine Doors", 'CHECKBOX', False)
        self.add_prompt("Decoration Width", 'DISTANCE', sn_unit.inch(7.5))
        self.add_prompt("Placement on Wall", 'COMBOBOX', 0, ['SELECTED_POINT', 'LEFT', 'CENTER', 'RIGHT'])
        self.add_prompt("Left Offset", 'DISTANCE', 0)
        self.add_prompt("Right Offset", 'DISTANCE', 0)

        for i in range(1, 5):
            self.add_prompt("Drawer " + str(i) + " Height", 'DISTANCE', sn_unit.millimeter(187.96))
            # self.add_prompt("Left Drawer " + str(i) + " Height", 'DISTANCE', sn_unit.millimeter(187.96))
            # self.add_prompt("Right Drawer " + str(i) + " Height", 'DISTANCE', sn_unit.millimeter(187.96))

    def update(self):
        self.obj_x.location.x = self.width
        self.obj_y.location.y = -self.depth
        self.obj_z.location.z = self.height

        self.obj_bp["IS_BP_WALL_BED"] = True
        self.obj_bp["ID_PROMPT"] = self.id_prompt
        self.obj_y['IS_MIRROR'] = True
        self.obj_bp.snap.type_group = self.type_assembly
        self.obj_bp.snap.export_as_subassembly = True  # May need to change to False
        self.set_prompts()
        super().update()

    def draw(self):
        self.create_assembly()
        # we are adding a master hide for everything
        hide_prompt = self.add_prompt('Hide', 'CHECKBOX', False)
        self.hide_var = hide_prompt.get_var()
        self.add_prompts()

        bed_make = self.get_prompt("Bed Make")
        if bed_make:
            if bed_make.get_value() == 0:
                self.add_eurobed_parts()
            elif bed_make.get_value() == 1:
                self.add_247_parts()
            elif bed_make.get_value() == 2:
                self.add_murphy_parts()
        self.update()

    def add_eurobed_parts(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Wall_Bed_Depth = self.get_prompt("Wall Bed Depth").get_var()
        Wall_Bed_Height = self.get_prompt("Wall Bed Height").get_var()
        Bed_Type = self.get_prompt("Bed Type").get_var()
        PT = self.get_prompt("Wall Bed Panel Thickness").get_var('PT')
        ST = self.get_prompt("Shelf Thickness").get_var('ST')
        # Extend_Height = self.get_prompt("Extend Height").get_var()
        # Extend_Depth = self.get_prompt("Extend Depth").get_var()
        Open = self.get_prompt("Open").get_var()
        Add_Doors_And_Drawers = self.get_prompt("Add Doors And Drawers").get_var()

        left_panel = common_parts.add_panel(self)
        left_panel.set_name("Wall Bed Partition")
        left_panel.loc_x('PT', [PT])
        left_panel.loc_y(value=0)
        left_panel.loc_z(value=0)
        left_panel.dim_x("Wall_Bed_Height", [Wall_Bed_Height])
        left_panel.dim_y("-Wall_Bed_Depth", [Wall_Bed_Depth])
        left_panel.dim_z("PT", [PT])
        # left_panel.rot_x(value=math.radians(90))
        left_panel.rot_y(value=math.radians(-90))
        # left_panel.rot_z(value=math.radians(90))

        right_panel = common_parts.add_panel(self)
        right_panel.set_name("Wall Bed Partition")
        right_panel.loc_x("Width", [Width])
        right_panel.loc_y(value=0)
        right_panel.loc_z(value=0)
        right_panel.dim_x("Wall_Bed_Height", [Wall_Bed_Height])
        right_panel.dim_y("-Wall_Bed_Depth", [Wall_Bed_Depth])
        right_panel.dim_z("PT", [PT])
        # right_panel.rot_x(value=math.radians(90))
        right_panel.rot_y(value=math.radians(-90))
        # right_panel.rot_z(value=math.radians(90))

        bottom_valance = common_parts.add_wall_bed_valance(self)
        bottom_valance.set_name("Wall Bed Valance")
        bottom_valance.loc_x('PT', [PT])
        bottom_valance.loc_y(value=0)
        bottom_valance.loc_z("Height-INCH(3.25)", [Height])
        bottom_valance.dim_x("Width-(PT*2)", [Width, PT])
        bottom_valance.dim_y("-Wall_Bed_Depth+ST", [Wall_Bed_Depth, ST])
        bottom_valance.dim_z("ST", [ST])

        face_valance = common_parts.add_wall_bed_valance(self)
        face_valance.set_name("Wall Bed Valance")
        face_valance.loc_x('PT', [PT])
        face_valance.loc_y("-Wall_Bed_Depth+ST", [Wall_Bed_Depth, ST])
        face_valance.loc_z("Height-INCH(3.25)", [Height])
        face_valance.dim_x("Width-(PT*2)", [Width, PT])
        face_valance.dim_y(value=sn_unit.inch(3.25))
        face_valance.dim_z("ST", [ST])
        face_valance.rot_x(value=math.radians(90))

        left_valance = common_parts.add_wall_bed_valance(self)
        left_valance.set_name("Wall Bed Valance")
        left_valance.loc_x('PT', [PT])
        left_valance.loc_y(value=sn_unit.inch(-6.5 + 0.75))
        left_valance.loc_z("Height-INCH(2.5)", [Height])
        left_valance.dim_x("(-Wall_Bed_Depth+INCH(6.5))*-1", [Wall_Bed_Depth])
        left_valance.dim_y("INCH(2.5)-Height+Wall_Bed_Height", [Height, Wall_Bed_Height])
        left_valance.dim_z("-ST", [ST])
        left_valance.rot_x(value=math.radians(90))
        left_valance.rot_z(value=math.radians(-90))

        right_valance = common_parts.add_wall_bed_valance(self)
        right_valance.set_name("Wall Bed Valance")
        right_valance.loc_x("Width-PT", [Width, PT])
        right_valance.loc_y(value=sn_unit.inch(-6.5 + 0.75))
        right_valance.loc_z("Height-INCH(2.5)", [Height])
        right_valance.dim_x("(-Wall_Bed_Depth+INCH(6.5))*-1", [Wall_Bed_Depth])
        right_valance.dim_y("INCH(2.5)-Height+Wall_Bed_Height", [Height, Wall_Bed_Height])
        right_valance.dim_z("ST", [ST])
        right_valance.rot_x(value=math.radians(90))
        right_valance.rot_z(value=math.radians(-90))

        top_cleat = common_parts.add_cleat(self)
        top_cleat.set_name("Wall Bed Cleat")
        top_cleat.loc_x('PT', [PT])
        top_cleat.loc_y(value=0)
        top_cleat.loc_z("Height-INCH(3.25)", [Height])
        top_cleat.dim_x("Width-(PT*2)", [Width, PT])
        top_cleat.dim_y(value=sn_unit.inch(8))
        top_cleat.dim_z("-ST", [ST])
        top_cleat.rot_x(value=math.radians(-90))
        top_cleat.get_prompt("Use Cleat Cover").set_value(False)

        slab_door_panel = common_parts.add_door(self)
        slab_door_panel.set_name("Backing Panel")
        slab_door_panel.loc_x('PT', [PT])
        slab_door_panel.loc_y("-Wall_Bed_Depth+IF(Add_Doors_And_Drawers,ST,0)", [Wall_Bed_Depth, Add_Doors_And_Drawers, ST])
        slab_door_panel.loc_z(value=sn_unit.inch(2.13))
        slab_door_panel.dim_x("Width-(PT*2)", [Width, PT])
        slab_door_panel.dim_y("Height-INCH(5.38)", [Height])
        slab_door_panel.dim_z("-ST", [ST])
        slab_door_panel.rot_x("IF(Open,radians(180),radians(90))", [Open])
        self.add_door_and_drawer_fronts(slab_door_panel)
        self.add_door_pulls(slab_door_panel)

    def add_247_parts(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Wall_Bed_Depth = self.get_prompt("Wall Bed Depth").get_var()
        Wall_Bed_Height = self.get_prompt("Wall Bed Height").get_var()
        Bed_Type = self.get_prompt("Bed Type").get_var()
        PT = self.get_prompt("Wall Bed Panel Thickness").get_var('PT')
        ST = self.get_prompt("Shelf Thickness").get_var('ST')
        # Extend_Height = self.get_prompt("Extend Height").get_var()
        # Extend_Depth = self.get_prompt("Extend Depth").get_var()
        Open = self.get_prompt("Open").get_var()
        Add_Doors_And_Drawers = self.get_prompt("Add Doors And Drawers").get_var()

        left_panel = common_parts.add_panel(self)
        left_panel.set_name("Wall Bed Partition")
        left_panel.loc_x('PT', [PT])
        left_panel.loc_y(value=0)
        left_panel.loc_z(value=0)
        left_panel.dim_x("Wall_Bed_Height", [Wall_Bed_Height])
        left_panel.dim_y("-Wall_Bed_Depth", [Wall_Bed_Depth])
        left_panel.dim_z("PT", [PT])
        # left_panel.rot_x(value=math.radians(90))
        left_panel.rot_y(value=math.radians(-90))
        # left_panel.rot_z(value=math.radians(90))

        right_panel = common_parts.add_panel(self)
        right_panel.set_name("Wall Bed Partition")
        right_panel.loc_x("Width", [Width])
        right_panel.loc_y(value=0)
        right_panel.loc_z(value=0)
        right_panel.dim_x("Wall_Bed_Height", [Wall_Bed_Height])
        right_panel.dim_y("-Wall_Bed_Depth", [Wall_Bed_Depth])
        right_panel.dim_z("PT", [PT])
        # right_panel.rot_x(value=math.radians(90))
        right_panel.rot_y(value=math.radians(-90))
        # right_panel.rot_z(value=math.radians(90))

        bottom_valance = common_parts.add_wall_bed_valance(self)
        bottom_valance.set_name("Wall Bed Valance")
        bottom_valance.loc_x('PT', [PT])
        bottom_valance.loc_y(value=0)
        bottom_valance.loc_z("Height-INCH(3.25)", [Height])
        bottom_valance.dim_x("Width-(PT*2)", [Width, PT])
        bottom_valance.dim_y("-Wall_Bed_Depth+ST", [Wall_Bed_Depth, ST])
        bottom_valance.dim_z("ST", [ST])

        face_valance = common_parts.add_wall_bed_valance(self)
        face_valance.set_name("Wall Bed Valance")
        face_valance.loc_x('PT', [PT])
        face_valance.loc_y("-Wall_Bed_Depth+ST", [Wall_Bed_Depth, ST])
        face_valance.loc_z("Height-INCH(3.25)", [Height])
        face_valance.dim_x("Width-(PT*2)", [Width, PT])
        face_valance.dim_y(value=sn_unit.inch(3.25))
        face_valance.dim_z("ST", [ST])
        face_valance.rot_x(value=math.radians(90))

        left_valance = common_parts.add_wall_bed_valance(self)
        left_valance.set_name("Wall Bed Valance")
        left_valance.loc_x('PT', [PT])
        left_valance.loc_y(value=sn_unit.inch(-6.5 + 0.75))
        left_valance.loc_z("Height-INCH(2.5)", [Height])
        left_valance.dim_x("(-Wall_Bed_Depth+INCH(6.5))*-1", [Wall_Bed_Depth])
        left_valance.dim_y("INCH(2.5)-Height+Wall_Bed_Height", [Height, Wall_Bed_Height])
        left_valance.dim_z("-ST", [ST])
        left_valance.rot_x(value=math.radians(90))
        left_valance.rot_z(value=math.radians(-90))

        right_valance = common_parts.add_wall_bed_valance(self)
        right_valance.set_name("Wall Bed Valance")
        right_valance.loc_x("Width-(PT)", [Width, PT])
        right_valance.loc_y(value=sn_unit.inch(-6.5 + 0.75))
        right_valance.loc_z("Height-INCH(2.5)", [Height])
        right_valance.dim_x("(-Wall_Bed_Depth+INCH(6.5))*-1", [Wall_Bed_Depth])
        right_valance.dim_y("INCH(2.5)-Height+Wall_Bed_Height", [Height, Wall_Bed_Height])
        right_valance.dim_z("ST", [ST])
        right_valance.rot_x(value=math.radians(90))
        right_valance.rot_z(value=math.radians(-90))

        top_cleat = common_parts.add_cleat(self)
        top_cleat.set_name("Wall Bed Cleat")
        top_cleat.loc_x('PT', [PT])
        top_cleat.loc_y(value=0)
        top_cleat.loc_z("Height-INCH(3.25)", [Height])
        top_cleat.dim_x("Width-(PT*2)", [Width, PT])
        top_cleat.dim_y(value=sn_unit.inch(7.25))
        top_cleat.dim_z("-ST", [ST])
        top_cleat.rot_x(value=math.radians(-90))
        top_cleat.get_prompt("Use Cleat Cover").set_value(False)

        slab_door_panel = common_parts.add_door(self)
        slab_door_panel.set_name("Backing Panel")
        slab_door_panel.loc_x('PT', [PT])
        slab_door_panel.loc_y("-Wall_Bed_Depth+IF(Add_Doors_And_Drawers,ST,0)", [Wall_Bed_Depth, Add_Doors_And_Drawers, ST])
        slab_door_panel.loc_z(value=sn_unit.inch(2.13))
        slab_door_panel.dim_x("Width-(PT*2)", [Width, PT])
        slab_door_panel.dim_y("Height-INCH(5.38)", [Height])
        slab_door_panel.dim_z("-ST", [ST])
        slab_door_panel.rot_x("IF(Open,radians(180),radians(90))", [Open])
        self.add_door_and_drawer_fronts(slab_door_panel)
        self.add_door_pulls(slab_door_panel)

    def add_murphy_parts(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Wall_Bed_Depth = self.get_prompt("Wall Bed Depth").get_var()
        Wall_Bed_Height = self.get_prompt("Wall Bed Height").get_var()
        Bed_Type = self.get_prompt("Bed Type").get_var()
        # PT = self.get_prompt("Shelf_Thickness").get_var('PT')
        ST = self.get_prompt("Shelf Thickness").get_var('ST') # Panels for murphy beds are 0.75" rather than 1"
        # Extend_Height = self.get_prompt("Extend Height").get_var()
        # Extend_Depth = self.get_prompt("Extend Depth").get_var()
        Open = self.get_prompt("Open").get_var()
        Add_Doors_And_Drawers = self.get_prompt("Add Doors And Drawers").get_var()

        left_panel = common_parts.add_panel(self)
        left_panel.set_name("Wall Bed Partition")
        left_panel.loc_x('ST', [ST])
        left_panel.loc_y(value=0)
        left_panel.loc_z(value=0)
        left_panel.dim_x("Wall_Bed_Height", [Wall_Bed_Height])
        left_panel.dim_y("-Wall_Bed_Depth", [Wall_Bed_Depth])
        left_panel.dim_z("ST", [ST])
        # left_panel.rot_x(value=math.radians(90))
        left_panel.rot_y(value=math.radians(-90))
        # left_panel.rot_z(value=math.radians(90))

        right_panel = common_parts.add_panel(self)
        right_panel.set_name("Wall Bed Partition")
        right_panel.loc_x("Width", [Width])
        right_panel.loc_y(value=0)
        right_panel.loc_z(value=0)
        right_panel.dim_x("Wall_Bed_Height", [Wall_Bed_Height])
        right_panel.dim_y("-Wall_Bed_Depth", [Wall_Bed_Depth])
        right_panel.dim_z("ST", [ST])
        # right_panel.rot_x(value=math.radians(90))
        right_panel.rot_y(value=math.radians(-90))
        # right_panel.rot_z(value=math.radians(90))

        bottom_support = common_parts.add_shelf(self)
        bottom_support.obj_bp['IS_SHELF'] = False
        props = bottom_support.obj_bp.sn_closets
        props.is_shelf_bp = False
        bottom_support.set_name("Bottom Support")
        bottom_support.loc_x('ST', [ST])
        bottom_support.loc_y(value=0)
        bottom_support.loc_z(value=0)
        bottom_support.dim_x("Width-(ST*2)", [Width, ST])
        bottom_support.dim_y("-Wall_Bed_Depth+ST", [Wall_Bed_Depth, ST])
        bottom_support.dim_z("ST", [ST])

        top_support = common_parts.add_shelf(self)
        top_support.set_name("Top Support")
        top_support.obj_bp['IS_SHELF'] = False
        props = top_support.obj_bp.sn_closets
        props.is_shelf_bp = False
        top_support.loc_x('ST', [ST])
        top_support.loc_y(value=0)
        top_support.loc_z("Wall_Bed_Height-ST", [Wall_Bed_Height, ST])
        top_support.dim_x("Width-(ST*2)", [Width, ST])
        top_support.dim_y("-Wall_Bed_Depth+(ST*2)", [Wall_Bed_Depth, ST])
        top_support.dim_z("ST", [ST])

        bottom_facia = common_parts.add_wall_bed_valance(self)
        bottom_facia.set_name("Bottom Facia")
        bottom_facia.loc_x('ST', [ST])
        bottom_facia.loc_y("-Wall_Bed_Depth+ST", [Wall_Bed_Depth, ST])
        bottom_facia.loc_z(value=0)
        bottom_facia.dim_x("Width-(ST*2)", [Width, ST])
        bottom_facia.dim_y(value=sn_unit.inch(4.38))
        bottom_facia.dim_z("ST", [ST])
        bottom_facia.rot_x(value=math.radians(90))

        top_facia = common_parts.add_wall_bed_valance(self)
        top_facia.set_name("Top Facia")
        top_facia.loc_x('ST', [ST])
        top_facia.loc_y("-Wall_Bed_Depth+(ST*2)", [Wall_Bed_Depth, ST])
        top_facia.loc_z("Wall_Bed_Height", [Wall_Bed_Height, ST])
        top_facia.dim_x("Width-(ST*2)", [Width, ST])
        top_facia.dim_y("INCH(6)-Height+Wall_Bed_Height", [Height, Wall_Bed_Height])
        top_facia.dim_z("-ST", [ST])
        top_facia.rot_x(value=math.radians(-90))

        head_board = common_parts.add_wall_bed_valance(self)
        head_board.set_name("Head Board")
        head_board.loc_x('ST + INCH(0.1)', [ST])
        head_board.loc_y("-Wall_Bed_Depth", [Wall_Bed_Depth])
        head_board.loc_z(value=sn_unit.inch(4.38))
        head_board.dim_x("Width-INCH(0.2)-(ST*2)", [Width, ST])
        head_board.dim_y("(-Wall_Bed_Depth-INCH(0.25))*-1", [Wall_Bed_Depth])
        head_board.dim_z("ST", [ST])
        head_board.rot_x("IF(Open,radians(90),radians(0))", [Open])

        # backing = common_parts.add_back(self)
        # What is the sizing for this? The width given is always really small so I am unsure where it fits in

        slab_door_panel = common_parts.add_door(self)
        slab_door_panel.set_name("Backing Panel")
        slab_door_panel.loc_x('ST', [ST])
        slab_door_panel.loc_y("-Wall_Bed_Depth+IF(Add_Doors_And_Drawers,ST,0)", [Wall_Bed_Depth, Add_Doors_And_Drawers, ST])
        slab_door_panel.loc_z(value=sn_unit.inch(4.38))
        slab_door_panel.dim_x("Width-(ST*2)", [Width, ST])
        slab_door_panel.dim_y("Height-INCH(5.93)", [Height])
        slab_door_panel.dim_z("-ST", [ST])
        slab_door_panel.rot_x("IF(Open,radians(180),radians(90))", [Open])
        self.add_door_and_drawer_fronts(slab_door_panel)
        self.add_door_pulls(slab_door_panel)

    def add_door_and_drawer_fronts(self, assembly):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Bed_Type = self.get_prompt("Bed Type").get_var()
        BM = self.get_prompt("Bed Make").get_var('BM')
        PT = self.get_prompt("Wall Bed Panel Thickness").get_var('PT')
        ST = self.get_prompt("Shelf Thickness").get_var('ST')
        # Extend_Height = self.get_prompt("Extend Height").get_var()
        # Extend_Depth = self.get_prompt("Extend Depth").get_var()
        Open = self.get_prompt("Open").get_var()
        ADAD = self.get_prompt("Add Doors And Drawers").get_var('ADAD')
        DOA = self.get_prompt("Door Overlay Amount").get_var('DOA')
        SROD = self.get_prompt("Second Row Of Doors").get_var('SROD')
        DS = self.get_prompt("Door Space").get_var('DS')
        # LDS = self.get_prompt("Left Door Space").get_var('LDS')
        # RDS = self.get_prompt("Right Door Space").get_var('RDS')
        DSH = self.get_prompt("Drawer Stack Height").get_var('DSH')
        DSQ = self.get_prompt("Drawer Stack Quantity").get_var('DSQ')
        # LDSH = self.get_prompt("Left Drawer Stack Height").get_var('LDSH')
        # LDSQ = self.get_prompt("Left Drawer Stack Quantity").get_var('LDSQ')
        # RDSH = self.get_prompt("Right Drawer Stack Height").get_var('RDSH')
        # RDSQ = self.get_prompt("Right Drawer Stack Quantity").get_var('RDSQ')
        TDH = self.get_prompt("Top Door Height").get_var('TDH')
        # TLDH = self.get_prompt("Top Left Door Height").get_var('TLDH')
        # TRDH = self.get_prompt("Top Right Door Height").get_var('TRDH')
        DMD = self.get_prompt("Decorative Melamine Doors").get_var('DMD')
        DW = self.get_prompt("Decoration Width").get_var('DW')

        top_left_door = common_parts.add_door(assembly)
        top_left_door.set_name("False Door Front")
        top_left_door.loc_x("DOA", [DOA])
        top_left_door.loc_y("IF(SROD,(DS-TDH)+(DOA/2),DOA)+DSH", [SROD, DS, DOA, DSH, TDH])
        top_left_door.loc_z(value=0)
        top_left_door.dim_x("((Width-(IF(BM==2,ST,PT)*2))/2)-(DOA*2)", [Width, DOA, BM, ST, PT])
        top_left_door.dim_y("IF(SROD,TDH,DS)-DOA*2", [DS, SROD, TDH, DOA])
        top_left_door.dim_z("ST", [ST])
        top_left_door.get_prompt('Hide').set_formula("IF(ADAD,False,True)", [ADAD])

        top_right_door = common_parts.add_door(assembly)
        top_right_door.set_name("False Door Front")
        top_right_door.loc_x("((Width-(IF(BM==2,ST,PT)*2))/2)+DOA", [Width, DOA, BM, ST, PT])
        top_right_door.loc_y("IF(SROD,(DS-TDH)+(DOA/2),DOA)+DSH", [SROD, DS, DOA, DSH, TDH])
        top_right_door.loc_z(value=0)
        top_right_door.dim_x("((Width-(IF(BM==2,ST,PT)*2))/2)-(DOA*2)", [Width, DOA, BM, ST, PT])
        top_right_door.dim_y("IF(SROD,TDH,DS)-DOA*2", [DS, SROD, TDH, DOA])
        top_right_door.dim_z("ST", [ST])
        top_right_door.get_prompt('Hide').set_formula("IF(ADAD,False,True)", [ADAD])

        bottom_left_door = common_parts.add_door(assembly)
        bottom_left_door.set_name("False Door Front")
        bottom_left_door.loc_x("DOA", [DOA])
        bottom_left_door.loc_y("DOA+DSH", [DOA, DSH])
        bottom_left_door.loc_z(value=0)
        bottom_left_door.dim_x("((Width-(IF(BM==2,ST,PT)*2))/2)-(DOA*2)", [Width, DOA, BM, ST, PT])
        bottom_left_door.dim_y("(DS-TDH)-DOA", [DS, SROD, DOA, TDH])
        bottom_left_door.dim_z("ST", [ST])
        bottom_left_door.get_prompt('Hide').set_formula("IF(ADAD,IF(SROD,False,True),True)", [ADAD, SROD])

        bottom_right_door = common_parts.add_door(assembly)
        bottom_right_door.set_name("False Door Front")
        bottom_right_door.loc_x("((Width-(IF(BM==2,ST,PT)*2))/2)+DOA", [Width, DOA, BM, ST, PT])
        bottom_right_door.loc_y("DOA+DSH", [DOA, DSH])
        bottom_right_door.loc_z(value=0)
        bottom_right_door.dim_x("((Width-(IF(BM==2,ST,PT)*2))/2)-(DOA*2)", [Width, DOA, BM, ST, PT])
        bottom_right_door.dim_y("(DS-TDH)-DOA", [DS, SROD, DOA, TDH])
        bottom_right_door.dim_z("ST", [ST])
        bottom_right_door.get_prompt('Hide').set_formula("IF(ADAD,IF(SROD,False,True),True)", [ADAD, SROD])

        left_decoration_piece = common_parts.add_wall_bed_decoration(assembly)
        left_decoration_piece.set_name("Melamine Decoration")
        left_decoration_piece.loc_x("DOA", [DOA])
        left_decoration_piece.loc_y("DOA+DSH", [DOA, DSH])
        left_decoration_piece.loc_z("ST", [ST])
        left_decoration_piece.dim_x("DW", [DW])
        left_decoration_piece.dim_y("DS", [DS])
        left_decoration_piece.dim_z("ST", [ST])
        left_decoration_piece.get_prompt('Hide').set_formula("IF(ADAD,IF(DMD,False,True),True)", [ADAD, DMD])

        right_decoration_piece = common_parts.add_wall_bed_decoration(assembly)
        right_decoration_piece.set_name("Melamine Decoration")
        right_decoration_piece.loc_x("(Width-(IF(BM==2,ST,PT)*2))-DOA-DW", [Width, DW, DOA, BM, ST, PT])
        right_decoration_piece.loc_y("DOA+DSH", [DOA, DSH])
        right_decoration_piece.loc_z("ST", [ST])
        right_decoration_piece.dim_x("DW", [DW])
        right_decoration_piece.dim_y("DS", [DS])
        right_decoration_piece.dim_z("ST", [ST])
        right_decoration_piece.get_prompt('Hide').set_formula("IF(ADAD,IF(DMD,False,True),True)", [ADAD, DMD])

        middle_decoration_piece = common_parts.add_wall_bed_decoration(assembly)
        middle_decoration_piece.set_name("Melamine Decoration")
        middle_decoration_piece.loc_x("((Width-(IF(BM==2,ST,PT)*2))-DW)/2", [DW, Width, BM, ST, PT])
        middle_decoration_piece.loc_y("DOA+DW+DSH", [DOA, DW, DSH])
        middle_decoration_piece.loc_z("ST", [ST])
        middle_decoration_piece.dim_x("DW", [DW])
        middle_decoration_piece.dim_y("DS-(DW*2)", [DS, DW])
        middle_decoration_piece.dim_z("ST", [ST])
        middle_decoration_piece.get_prompt('Hide').set_formula("IF(ADAD,IF(DMD,False,True),True)", [ADAD, DMD])

        top_decoration_piece = common_parts.add_wall_bed_decoration(assembly)
        top_decoration_piece.set_name("Melamine Decoration")
        top_decoration_piece.loc_x("DOA+DW", [DW, DOA])
        top_decoration_piece.loc_y("Height+ST-DW-INCH(5.93)", [Height, DOA, DW, ST])
        top_decoration_piece.loc_z("ST", [ST])
        top_decoration_piece.dim_x("(Width-(IF(BM==2,ST,PT)*2))-(DW*2)-(DOA*2)", [Width, DOA, DW, BM, ST, PT])
        top_decoration_piece.dim_y("DW", [DW])
        top_decoration_piece.dim_z("ST", [ST])
        top_decoration_piece.get_prompt('Hide').set_formula("IF(ADAD,IF(DMD,False,True),True)", [ADAD, DMD])

        bottom_decoration_piece = common_parts.add_wall_bed_decoration(assembly)
        bottom_decoration_piece.set_name("Melamine Decoration")
        bottom_decoration_piece.loc_x("DOA+DW", [DW, DOA])
        bottom_decoration_piece.loc_y("DOA+DSH", [DOA, DSH])
        bottom_decoration_piece.loc_z("ST", [ST])
        bottom_decoration_piece.dim_x("(Width-(IF(BM==2,ST,PT)*2))-(DW*2)-(DOA*2)", [Width, DOA, DW, BM, ST, PT])
        bottom_decoration_piece.dim_y("DW", [DW])
        bottom_decoration_piece.dim_z("ST", [ST])
        bottom_decoration_piece.get_prompt('Hide').set_formula("IF(ADAD,IF(DMD,False,True),True)", [ADAD, DMD])

        left_middle_decoration_piece = common_parts.add_wall_bed_decoration(assembly)
        left_middle_decoration_piece.set_name("Melamine Decoration")
        left_middle_decoration_piece.loc_x("DOA+DW", [DW, DOA])
        left_middle_decoration_piece.loc_y("Height+ST-(DW/2)-INCH(5.93)-TDH", [TDH, DW, ST, Height])
        left_middle_decoration_piece.loc_z("ST", [ST])
        left_middle_decoration_piece.dim_x("((Width-(IF(BM==2,ST,PT)*2))/2)-(DW*1.5)-(DOA)", [Width, DOA, DW, BM, ST, PT])
        left_middle_decoration_piece.dim_y("DW", [DW])
        left_middle_decoration_piece.dim_z("ST", [ST])
        left_middle_decoration_piece.get_prompt('Hide').set_formula("IF(ADAD,IF(DMD,IF(SROD,False,True),True),True)", [ADAD, DMD, SROD])

        right_middle_decoration_piece = common_parts.add_wall_bed_decoration(assembly)
        right_middle_decoration_piece.set_name("Melamine Decoration")
        right_middle_decoration_piece.loc_x("((Width-(IF(BM==2,ST,PT)*2))+DW)/2", [Width, DW, BM, ST, PT])
        right_middle_decoration_piece.loc_y("Height+ST-(DW/2)-INCH(5.93)-TDH", [TDH, DW, ST, Height])
        right_middle_decoration_piece.loc_z("ST", [ST])
        right_middle_decoration_piece.dim_x("((Width-(IF(BM==2,ST,PT)*2))/2)-(DW*1.5)-(DOA)", [Width, DOA, DW, BM, ST, PT])
        right_middle_decoration_piece.dim_y("DW", [DW])
        right_middle_decoration_piece.dim_z("ST", [ST])
        right_middle_decoration_piece.get_prompt('Hide').set_formula("IF(ADAD,IF(DMD,IF(SROD,False,True),True),True)", [ADAD, DMD, SROD])

        left_prev_drawer_empty = None
        for i in range(1, 5):
            DF_Height = self.get_prompt("Drawer " + str(i) + " Height").get_var("DF_Height")

            left_front_empty = self.add_empty("Left Drawer Front Height")
            if left_prev_drawer_empty:
                prev_drawer_y_loc = left_prev_drawer_empty.snap.get_var('location.y', 'prev_drawer_y_loc')
                left_front_empty.snap.loc_y('prev_drawer_y_loc+DF_Height+DOA', [prev_drawer_y_loc, DF_Height, DOA])
            else:
                left_front_empty.snap.loc_y('DOA+DF_Height', [DOA, DF_Height])
            df_y_loc = left_front_empty.snap.get_var('location.y', 'df_y_loc')
            left_prev_drawer_empty = left_front_empty

            left_front = common_parts.add_drawer_front(assembly)
            left_front.set_name("False Drawer Front")
            left_front.obj_bp["DRAWER_NUM"] = i
            left_front.loc_x('DOA', [DOA])
            left_front.loc_y('df_y_loc', [df_y_loc])
            left_front.loc_z(value=0)
            left_front.dim_x("((Width-(IF(BM==2,ST,PT)*2))/2)-(DOA*2)", [Width, DOA, BM, ST, PT])
            left_front.dim_y('-DF_Height', [DF_Height])
            left_front.dim_z('ST', [ST])
            left_front.get_prompt('Hide').set_formula("IF(ADAD,IF(DSQ>=" + str(i) + ",False,True),True)", [ADAD, DSQ])

            left_pull = common_parts.add_drawer_pull(assembly)
            left_pull.set_name("Drawer Pull")
            left_pull.obj_bp["DRAWER_NUM"] = i
            left_pull.loc_x('DOA+((((Width-(IF(BM==2,ST,PT)*2))/2)-(DOA*2))/2)', [Width, DOA, BM, ST, PT])
            left_pull.loc_y('df_y_loc-(DF_Height/2)', [df_y_loc, DF_Height])
            left_pull.loc_z("ST", [ST])
            left_pull.dim_x(value=0)
            left_pull.dim_y(value=0)
            left_pull.dim_z(value=0)
            left_pull.get_prompt('Hide').set_formula("IF(ADAD,IF(DSQ>=" + str(i) + ",False,True),True)", [ADAD, DSQ])
            # left_pull.rot_y(value=math.radians(90))

        right_prev_drawer_empty = None
        for i in range(1, 5):
            DF_Height = self.get_prompt("Drawer " + str(i) + " Height").get_var("DF_Height")

            right_front_empty = self.add_empty("Right Drawer Front Height")
            if right_prev_drawer_empty:
                prev_drawer_y_loc = right_prev_drawer_empty.snap.get_var('location.y', 'prev_drawer_y_loc')
                right_front_empty.snap.loc_y('prev_drawer_y_loc+DF_Height+DOA', [prev_drawer_y_loc, DF_Height, DOA])
            else:
                right_front_empty.snap.loc_y('DOA+DF_Height', [DOA, DF_Height])
            df_y_loc = right_front_empty.snap.get_var('location.y', 'df_y_loc')
            right_prev_drawer_empty = right_front_empty

            right_front = common_parts.add_drawer_front(assembly)
            right_front.set_name("False Drawer Front")
            right_front.obj_bp["DRAWER_NUM"] = i
            right_front.loc_x("((Width-(IF(BM==2,ST,PT)*2))/2)+DOA", [Width, DOA, BM, ST, PT])
            right_front.loc_y('df_y_loc', [df_y_loc])
            right_front.loc_z(value=0)
            right_front.dim_x("((Width-(IF(BM==2,ST,PT)*2))/2)-(DOA*2)", [Width, DOA, BM, ST, PT])
            right_front.dim_y('-DF_Height', [DF_Height])
            right_front.dim_z('ST', [ST])
            right_front.get_prompt('Hide').set_formula("IF(ADAD,IF(DSQ>=" + str(i) + ",False,True),True)", [ADAD, DSQ])

            right_pull = common_parts.add_drawer_pull(assembly)
            right_pull.set_name("Drawer Pull")
            right_pull.obj_bp["DRAWER_NUM"] = i
            right_pull.loc_x('((Width-(IF(BM==2,ST,PT)*2))/2)+DOA+((((Width-(IF(BM==2,ST,PT)*2))/2)-(DOA*2))/2)', [Width, DOA, BM, ST, PT])
            right_pull.loc_y('df_y_loc-(DF_Height/2)', [df_y_loc, DF_Height])
            right_pull.loc_z("ST", [ST])
            right_pull.dim_x(value=0)
            right_pull.dim_y(value=0)
            right_pull.dim_z(value=0)
            right_pull.get_prompt('Hide').set_formula("IF(ADAD,IF(DSQ>=" + str(i) + ",False,True),True)", [ADAD, DSQ])

    def add_door_pulls(self, assembly):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Wall_Bed_Depth = self.get_prompt("Wall Bed Depth").get_var()
        Wall_Bed_Height = self.get_prompt("Wall Bed Height").get_var()
        BM = self.get_prompt("Bed Make").get_var('BM')
        Bed_Type = self.get_prompt("Bed Type").get_var()
        PT = self.get_prompt("Wall Bed Panel Thickness").get_var('PT')
        ST = self.get_prompt("Shelf Thickness").get_var('ST')
        # Extend_Height = self.get_prompt("Extend Height").get_var()
        # Extend_Depth = self.get_prompt("Extend Depth").get_var()
        Open = self.get_prompt("Open").get_var()
        Add_Doors_And_Drawers = self.get_prompt("Add Doors And Drawers").get_var()
        Pull_Location = self.get_prompt("Pull Location").get_var()
        DOA = self.get_prompt("Door Overlay Amount").get_var('DOA')
        DMD = self.get_prompt("Decorative Melamine Doors").get_var('DMD')

        left_pull = common_parts.add_door_pull(assembly)
        left_pull.loc_x("((Width-(IF(BM==2,ST,PT)*2))/2)-(ST*2)", [Width, BM, PT, ST])
        left_pull.loc_y("Height-Pull_Location", [Height, Pull_Location])
        left_pull.loc_z("IF(DMD,ST,0)", [DMD, ST])
        left_pull.dim_x(value=0)
        left_pull.dim_y(value=0)
        left_pull.dim_z(value=0)
        left_pull.rot_z(value=math.radians(90))

        right_pull = common_parts.add_door_pull(assembly)
        right_pull.loc_x("((Width-(IF(BM==2,ST,PT)*2))/2)+(ST*2)", [Width, BM, PT, ST])
        right_pull.loc_y("Height-Pull_Location", [Height, Pull_Location])
        right_pull.loc_z("IF(DMD,ST,0)", [DMD, ST])
        right_pull.dim_x(value=0)
        right_pull.dim_y(value=0)
        right_pull.dim_z(value=0)
        right_pull.rot_z(value=math.radians(90))


class PROMPTS_prompts_wall_bed(sn_types.Prompts_Interface):
    bl_idname = "sn_closets.prompts_wall_bed"
    bl_label = "Wall Bed Prompt"
    bl_options = {'UNDO'}

    width: FloatProperty(name="Width", unit='LENGTH', precision=4)
    height: FloatProperty(name="Height", unit='LENGTH', precision=4)
    depth: FloatProperty(name="Depth", unit='LENGTH', precision=4)

    tabs: EnumProperty(
        name="Tabs",
        items=[
            ('BED', 'Bed Options', 'Options for the wall bed'),
            ('DOORS', 'Door and Drawer Options', 'Options for the doors and drawers')],
        default='BED')

    placement_on_wall: EnumProperty(
        name="Placement on Wall",
        items=[
            ('0', "Selected Point", ""),
            ('1', "Left", ""),
            ('2', "Center", ""),
            ('3', "Right", "")],
        default='0')
    
    left_offset: FloatProperty(name="Left Offset", default=0, subtype='DISTANCE', precision=4)
    right_offset: FloatProperty(name="Right Offset", default=0, subtype='DISTANCE', precision=4)
    current_location: FloatProperty(name="Current Location", default=0, subtype='DISTANCE', precision=4)

    drawer_stack_quantity: EnumProperty(
        name="Drawer Stack Quantity",
        items=[
            ('0', "0", '0'),
            ('1', "1", '1'),
            ('2', "2", '2'),
            ('3', "3", '3'),
            ('4', "4", '4')],
        default='2')
    Drawer_1_Height: EnumProperty(
        name="Drawer 1 Height",
        items=common_lists.FRONT_HEIGHTS)
    Drawer_2_Height: EnumProperty(
        name="Drawer 2 Height",
        items=common_lists.FRONT_HEIGHTS)
    Drawer_3_Height: EnumProperty(
        name="Drawer 3 Height",
        items=common_lists.FRONT_HEIGHTS)
    Drawer_4_Height: EnumProperty(
        name="Drawer 4 Height",
        items=common_lists.FRONT_HEIGHTS)
    drawer_stack_quantity_prompt = None

    # left_drawer_stack_quantity: EnumProperty(
    #     name="Left Drawer Stack Quantity",
    #     items=[
    #         ('0', "0", '0'),
    #         ('1', "1", '1'),
    #         ('2', "2", '2'),
    #         ('3', "3", '3'),
    #         ('4', "4", '4')],
    #     default='2')
    # Left_Drawer_1_Height: EnumProperty(
    #     name="Left Drawer 1 Height",
    #     items=common_lists.FRONT_HEIGHTS)
    # Left_Drawer_2_Height: EnumProperty(
    #     name="Left Drawer 2 Height",
    #     items=common_lists.FRONT_HEIGHTS)
    # Left_Drawer_3_Height: EnumProperty(
    #     name="Left Drawer 3 Height",
    #     items=common_lists.FRONT_HEIGHTS)
    # Left_Drawer_4_Height: EnumProperty(
    #     name="Left Drawer 4 Height",
    #     items=common_lists.FRONT_HEIGHTS)
    # left_drawer_stack_quantity_prompt = None

    # right_drawer_stack_quantity: EnumProperty(
    #     name="Right Drawer Stack Quantity",
    #     items=[
    #         ('0', "0", '0'),
    #         ('1', "1", '1'),
    #         ('2', "2", '2'),
    #         ('3', "3", '3'),
    #         ('4', "4", '4')],
    #     default='2')
    # Right_Drawer_1_Height: EnumProperty(
    #     name="Right Drawer 1 Height",
    #     items=common_lists.FRONT_HEIGHTS)
    # Right_Drawer_2_Height: EnumProperty(
    #     name="Right Drawer 2 Height",
    #     items=common_lists.FRONT_HEIGHTS)
    # Right_Drawer_3_Height: EnumProperty(
    #     name="Right Drawer 3 Height",
    #     items=common_lists.FRONT_HEIGHTS)
    # Right_Drawer_4_Height: EnumProperty(
    #     name="Right Drawer 4 Height",
    #     items=common_lists.FRONT_HEIGHTS)
    # right_drawer_stack_quantity_prompt = None

    top_door_height: EnumProperty(
        name="Top Door Height",
        items=common_lists.OPENING_HEIGHTS,
        default='877.316'
    )
    # top_left_door_height: EnumProperty(
    #     name="Top Left Door Height",
    #     items=common_lists.OPENING_HEIGHTS,
    #     default='877.316'
    # )
    # top_right_door_height: EnumProperty(
    #     name="Top Right Door Height",
    #     items=common_lists.OPENING_HEIGHTS,
    #     default='877.316'
    # )
    top_door_height_prompt = None
    # top_left_door_height_prompt = None
    # top_right_door_height_prompt = None

    assembly = None

    def check(self, context):
        """ This is called everytime a change is made in the UI """
        self.set_prompts_from_properties()
        self.update_placement(context)
        self.set_minimum_height_and_depth()
        closet_props.update_render_materials(self, context)
        return True

    def set_prompts_from_properties(self):
        placement_on_wall = self.assembly.get_prompt("Placement on Wall")
        left_offset = self.assembly.get_prompt("Left Offset")
        right_offset = self.assembly.get_prompt("Right Offset")
        prompts = [placement_on_wall, left_offset, right_offset]

        if all(prompts):
            placement_on_wall.set_value(int(self.placement_on_wall))
            left_offset.set_value(self.left_offset)
            right_offset.set_value(self.right_offset)

        if self.drawer_stack_quantity_prompt:
            self.drawer_stack_quantity_prompt.set_value(int(self.drawer_stack_quantity))
        # if self.left_drawer_stack_quantity_prompt:
        #     self.left_drawer_stack_quantity_prompt.set_value(int(self.left_drawer_stack_quantity))
        # if self.right_drawer_stack_quantity_prompt:
        #     self.right_drawer_stack_quantity_prompt.set_value(int(self.right_drawer_stack_quantity))

        if self.top_door_height_prompt:
            self.top_door_height_prompt.distance_value = sn_unit.inch(float(self.top_door_height) / 25.4)
        # if self.top_left_door_height_prompt:
        #     self.top_left_door_height_prompt.distance_value = sn_unit.inch(float(self.top_left_door_height) / 25.4)
        # if self.top_right_door_height_prompt:
        #     self.top_right_door_height_prompt.distance_value = sn_unit.inch(float(self.top_right_door_height) / 25.4)
        
        door_space = self.assembly.get_prompt("Door Space")
        # left_door_space = self.assembly.get_prompt("Left Door Space")
        # right_door_space = self.assembly.get_prompt("Right Door Space")
        door_overlay_amount = self.assembly.get_prompt("Door Overlay Amount")
        if door_space:

            drawer_stack_height_prompt = self.assembly.get_prompt("Drawer Stack Height")
            drawer_stack_height = 0
            for i in range(1, int(self.drawer_stack_quantity) + 1):
                drawer_height = self.assembly.get_prompt("Drawer " + str(i) + " Height")
                if drawer_height:
                    exec("drawer_height.set_value(sn_unit.inch(float(self.Drawer_" + str(i) + "_Height) / 25.4))")
                    drawer_stack_height += (drawer_height.get_value() + door_overlay_amount.get_value())
            drawer_stack_height_prompt.set_value(drawer_stack_height)
            door_space.set_value(self.assembly.obj_z.location.z - sn_unit.inch(5.38) - drawer_stack_height)

            # left_drawer_stack_height_prompt = self.assembly.get_prompt("Left Drawer Stack Height")
            # left_drawer_stack_height = 0
            # for i in range(1, int(self.left_drawer_stack_quantity) + 1):
            #     left_drawer_height = self.assembly.get_prompt("Left Drawer " + str(i) + " Height")
            #     if left_drawer_height:
            #         exec("left_drawer_height.set_value(sn_unit.inch(float(self.Left_Drawer_" + str(i) + "_Height) / 25.4))")
            #         left_drawer_stack_height += (left_drawer_height.get_value() + door_overlay_amount.get_value())
            # left_drawer_stack_height_prompt.set_value(left_drawer_stack_height)
            # door_space.set_value(self.assembly.obj_z.location.z - sn_unit.inch(5.38) - left_drawer_stack_height)

            # right_drawer_stack_height_prompt = self.assembly.get_prompt("Right Drawer Stack Height")
            # right_drawer_stack_height = 0
            # for i in range(1, int(self.right_drawer_stack_quantity) + 1):
            #     right_drawer_height = self.assembly.get_prompt("Right Drawer " + str(i) + " Height")
            #     if right_drawer_height:
            #         exec("right_drawer_height.set_value(sn_unit.inch(float(self.Right_Drawer_" + str(i) + "_Height) / 25.4))")
            #         right_drawer_stack_height += (right_drawer_height.get_value() + door_overlay_amount.get_value())
            # right_drawer_stack_height_prompt.set_value(right_drawer_stack_height)
            # right_door_space.set_value(self.assembly.obj_z.location.z - sn_unit.inch(5.38) - right_drawer_stack_height)

    def set_minimum_height_and_depth(self):
        wall_bed_height = self.assembly.get_prompt("Wall Bed Height")
        wall_bed_depth = self.assembly.get_prompt("Wall Bed Depth")
        height = self.assembly.obj_z.location.z
        depth = self.assembly.obj_y.location.y

        if wall_bed_height:
            if wall_bed_height.get_value() < height:
                wall_bed_height.set_value(height)

        if wall_bed_depth:
            if wall_bed_depth.get_value() < (depth * -1):
                wall_bed_depth.set_value(depth * -1)

    def update_placement(self, context):
        left_x = self.assembly.get_collision_location('LEFT')
        right_x = self.assembly.get_collision_location('RIGHT')
        if self.placement_on_wall == '0':
            self.assembly.obj_bp.location.x = self.current_location
        if self.placement_on_wall == '1':
            self.assembly.obj_bp.location.x = left_x + self.left_offset
        if self.placement_on_wall == '2':
            x_loc = (left_x + (right_x)) / 2 - (self.assembly.obj_x.location.x / 2)
            self.assembly.obj_bp.location.x = x_loc
        if self.placement_on_wall == '3':
            self.assembly.obj_bp.location.x = (right_x - self.assembly.obj_x.location.x) - self.right_offset

    def execute(self, context):
        """ This is called when the OK button is clicked """
        self.tabs = 'BED'
        return {'FINISHED'}

    def invoke(self, context, event):
        """ This is called before the interface is displayed """
        self.assembly = self.get_product()
        self.set_properties_from_prompts()
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(450))

    def set_properties_from_prompts(self):
        placement_on_wall = self.assembly.get_prompt("Placement on Wall")
        left_offset = self.assembly.get_prompt("Left Offset")
        right_offset = self.assembly.get_prompt("Right Offset")
        prompts = [placement_on_wall, left_offset, right_offset]

        if all(prompts):
            self.current_location = self.assembly.obj_bp.location.x
            self.placement_on_wall = str(placement_on_wall.get_value())
            self.left_offset = left_offset.get_value()
            self.right_offset = right_offset.get_value()

        self.drawer_stack_quantity_prompt = self.assembly.get_prompt("Drawer Stack Quantity")
        if self.drawer_stack_quantity_prompt:
            self.drawer_stack_quantity = str(self.drawer_stack_quantity_prompt.quantity_value)
        for i in range(1, 5):
            drawer = self.assembly.get_prompt("Drawer " + str(i) + " Height")
            if drawer:
                value = round(drawer.get_value() * 1000, 3)
                for index, height in enumerate(common_lists.FRONT_HEIGHTS):
                    if not value >= float(height[0]):
                        exec("self.Drawer_" + str(i) + "_Height = common_lists.FRONT_HEIGHTS[index - 1][0]")
                        break

        # self.left_drawer_stack_quantity_prompt = self.assembly.get_prompt("Left Drawer Stack Quantity")
        # if self.left_drawer_stack_quantity_prompt:
        #     self.left_drawer_stack_quantity = str(self.left_drawer_stack_quantity_prompt.quantity_value)
        # for i in range(1, 5):
        #     left_drawer = self.assembly.get_prompt("Left Drawer " + str(i) + " Height")
        #     if left_drawer:
        #         value = round(left_drawer.get_value() * 1000, 3)
        #         for index, height in enumerate(common_lists.FRONT_HEIGHTS):
        #             if not value >= float(height[0]):
        #                 exec("self.Left_Drawer_" + str(i) + "_Height = common_lists.FRONT_HEIGHTS[index - 1][0]")
        #                 break

        # self.right_drawer_stack_quantity_prompt = self.assembly.get_prompt("Right Drawer Stack Quantity")
        # if self.right_drawer_stack_quantity_prompt:
        #     self.right_drawer_stack_quantity = str(self.right_drawer_stack_quantity_prompt.quantity_value)
        # for i in range(1, 5):
        #     right_drawer = self.assembly.get_prompt("Right Drawer " + str(i) + " Height")
        #     if right_drawer:
        #         value = round(right_drawer.get_value() * 1000, 3)
        #         for index, height in enumerate(common_lists.FRONT_HEIGHTS):
        #             if not value >= float(height[0]):
        #                 exec("self.Right_Drawer_" + str(i) + "_Height = common_lists.FRONT_HEIGHTS[index - 1][0]")
        #                 break

        self.top_door_height_prompt = self.assembly.get_prompt("Top Door Height")
        if self.top_door_height_prompt:
            value = round(self.top_door_height_prompt.distance_value * 1000, 3)
            for index, height in enumerate(common_lists.OPENING_HEIGHTS):
                if not value >= float(height[0]):
                    self.top_door_height = common_lists.OPENING_HEIGHTS[index - 1][0]
                    break

        # self.top_left_door_height_prompt = self.assembly.get_prompt("Top Left Door Height")
        # self.top_right_door_height_prompt = self.assembly.get_prompt("Top Right Door Height")
        # if self.top_left_door_height_prompt and self.top_right_door_height_prompt:
        #     value = round(self.top_left_door_height_prompt.distance_value * 1000, 3)
        #     for index, height in enumerate(common_lists.OPENING_HEIGHTS):
        #         if not value >= float(height[0]):
        #             self.top_left_door_height = common_lists.OPENING_HEIGHTS[index - 1][0]
        #             break
        #     value = round(self.top_right_door_height_prompt.distance_value * 1000, 3)
        #     for index, height in enumerate(common_lists.OPENING_HEIGHTS):
        #         if not value >= float(height[0]):
        #             self.top_right_door_height = common_lists.OPENING_HEIGHTS[index - 1][0]
        #             break

    def draw_product_placment(self, layout):
        box = layout.box()

        row = box.row(align=True)
        row.label(text='Placement', icon='LATTICE_DATA')
        row.prop_enum(self, "placement_on_wall", '0', icon='RESTRICT_SELECT_OFF', text="Selected Point")
        row.prop_enum(self, "placement_on_wall", '1', icon='TRIA_LEFT', text="Left")
        row.prop_enum(self, "placement_on_wall", '2', icon='TRIA_UP_BAR', text="Center")
        row.prop_enum(self, "placement_on_wall", '3', icon='TRIA_RIGHT', text="Right")

        if self.placement_on_wall in '1':
            row = box.row()
            row.label(text='Offset', icon='BACK')
            row.prop(self, "left_offset", icon='TRIA_LEFT', text="Left")

        if self.placement_on_wall in '2':
            row = box.row()

        if self.placement_on_wall in '3':
            row = box.row()
            row.label(text='Offset', icon='FORWARD')
            row.prop(self, "right_offset", icon='TRIA_RIGHT', text="Right")

        if self.placement_on_wall == '0':
            row = box.row()
            row.label(text='Location:')
            row.prop(self, 'current_location', text="")

    def draw(self, context):
        """ This is where you draw the interface """
        layout = self.layout
        layout.label(text=self.assembly.obj_bp.name)

        # extend_height = self.assembly.get_prompt("Extend Height")
        # extend_depth = self.assembly.get_prompt("Extend Depth")
        wall_bed_height = self.assembly.get_prompt("Wall Bed Height")
        wall_bed_depth = self.assembly.get_prompt("Wall Bed Depth")
        height = self.assembly.obj_z.location.z
        depth = self.assembly.obj_y.location.y
        open = self.assembly.get_prompt("Open")
        add_doors_and_drawers = self.assembly.get_prompt("Add Doors And Drawers")
        second_row_of_doors = self.assembly.get_prompt("Second Row Of Doors")
        drawer_stack_quantity = self.assembly.get_prompt("Drawer Stack Quantity")
        # left_drawer_stack_quantity = self.assembly.get_prompt("Left Drawer Stack Quantity")
        # right_drawer_stack_quantity = self.assembly.get_prompt("Right Drawer Stack Quantity")
        pull_location = self.assembly.get_prompt("Pull Location")
        top_door_height = self.assembly.get_prompt("Top Door Height")
        # top_left_door_height = self.assembly.get_prompt("Top Left Door Height")
        # top_right_door_height = self.assembly.get_prompt("Top Right Door Height")
        decorative_melamine_doors = self.assembly.get_prompt("Decorative Melamine Doors")

        box = layout.box()
        row = box.row()
        row.prop(self, 'tabs', expand=True)

        if self.tabs == 'BED':
            if wall_bed_height:
                row = box.row()
                row.label(text="Height")
                row.prop(wall_bed_height, 'distance_value', text="")
                row.label(text="Minimum Height: " + str(round(sn_unit.meter_to_inch(height), 2)) + '"')

            if wall_bed_depth:
                row = box.row()
                row.label(text="Depth")
                row.prop(wall_bed_depth, 'distance_value', text="")
                row.label(text="Minimum Depth: " + str(sn_unit.meter_to_inch(depth) * -1) + '"')

            if open:
                row = box.row()
                row.label(text="Open")
                row.prop(open, 'checkbox_value', text="")
            
            self.draw_product_placment(layout)

        elif self.tabs == 'DOORS':
            if pull_location:
                row = box.row()
                row.label(text="Pull Distance From Top")
                row.prop(pull_location, 'distance_value', text="")

            if add_doors_and_drawers:
                row = box.row()
                row.label(text="Add Decorative Door/Drawer Faces")
                row.prop(add_doors_and_drawers, 'checkbox_value', text="")
                if add_doors_and_drawers.get_value():
                    box = layout.box()
                    box.label(text="Door Options: ")
                    row = box.row()
                    row.label(text="Second Row of Doors")
                    row.prop(second_row_of_doors, 'checkbox_value', text="")
                    if second_row_of_doors:
                        if second_row_of_doors.get_value():
                            if top_door_height:
                                row = box.row()
                                row.label(text="Top Door Height")
                                row.prop(self, 'top_door_height', text="")
                                # row.label(text="Top Left Door Height")
                                # row.prop(self, 'top_left_door_height', text="")
                                # row.label(text="Top Right Door Height")
                                # row.prop(self, 'top_right_door_height', text="")

                    if decorative_melamine_doors:
                        row = box.row()
                        row.label(text='Decorative Melamine Doors: ')
                        row.prop(decorative_melamine_doors, 'checkbox_value', text="")

                    box = layout.box()
                    box.label(text="Drawer Options: ")
                    row = box.row()
                    
                    if drawer_stack_quantity:
                        row.label(text="False Front Qty:")
                        row.prop(self, "drawer_stack_quantity", expand=True)

                        for i in range(1, int(self.drawer_stack_quantity) + 1):
                            drawer = self.assembly.get_prompt("Drawer " + str(i) + " Height")
                            if drawer:
                                row = box.row()
                                row.label(text="Drawer " + str(i) + " Height")
                                row.prop(self, "Drawer_" + str(i) + "_Height", text="")
                    # left_box = row.box()
                    # right_box = row.box()
                    # if left_drawer_stack_quantity:
                    #     col1 = left_box.column(align=True)
                    #     row = col1.row()
                    #     row.label(text="Left False Front Qty:")
                    #     row = col1.row()
                    #     row.prop(self, "left_drawer_stack_quantity", expand=True)

                    #     for i in range(1, int(self.left_drawer_stack_quantity) + 1):
                    #         left_drawer = self.assembly.get_prompt("Left Drawer " + str(i) + " Height")
                    #         if left_drawer:
                    #             row = col1.row()
                    #             row.label(text="Drawer " + str(i) + " Height")
                    #             row.prop(self, "Left_Drawer_" + str(i) + "_Height", text="")
                    #     col1.separator()

                    # if right_drawer_stack_quantity:
                    #     col2 = right_box.column(align=True)
                    #     row = col2.row()
                    #     row.label(text="Right False Front Qty:")
                    #     row = col2.row()
                    #     row.prop(self, "right_drawer_stack_quantity", expand=True)

                    #     for i in range(1, int(self.right_drawer_stack_quantity) + 1):
                    #         right_drawer = self.assembly.get_prompt("Right Drawer " + str(i) + " Height")
                    #         if right_drawer:
                    #             row = col2.row()
                    #             row.label(text="Drawer " + str(i) + " Height")
                    #             row.prop(self, "Right_Drawer_" + str(i) + "_Height", text="")


bpy.utils.register_class(PROMPTS_prompts_wall_bed)
