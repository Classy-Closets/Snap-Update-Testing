import os
import math
import bpy
from bpy.props import FloatProperty, EnumProperty
from snap import sn_types, sn_unit, sn_utils
from . import cabinet_countertops

LIBRARY_FOLDER_NAME = "Appliance - Sample"

from .appliance_paths import MATERIAL_FILE


def get_file_name(path):
    file_name = os.path.basename(path)
    return os.path.splitext(file_name)[0]


class Parametric_Wall_Appliance(sn_types.Assembly):
    category_name = "Appliances"
    show_in_library = True
    library_name = LIBRARY_FOLDER_NAME
    type_assembly = "PRODUCT"
    id_prompt = "sn_appliances.parametric_wall_appliance"

    """ Path to blend file that contains a group of the appliance """
    appliance_path = ""

    def draw(self):
        self.create_assembly()
        self.obj_bp["ID_PROMPT"] = "sn_appliances.parametric_wall_appliance"
        self.obj_bp["IS_BP_APPLIANCE"] = True

        dim_x = self.obj_x.snap.get_var('location.x', 'dim_x')
        dim_y = self.obj_y.snap.get_var('location.y', 'dim_y')
        dim_z = self.obj_z.snap.get_var('location.z', 'dim_z')
        obj = self.add_assembly_from_file(self.appliance_path)
        part = sn_types.Part(obj_bp=obj)
        part.dim_x("dim_x", [dim_x])
        part.dim_y("dim_y", [dim_y])
        part.dim_z("dim_z", [dim_z])

        self.obj_x.location.x = part.obj_x.location.x
        self.obj_y.location.y = part.obj_y.location.y
        self.obj_z.location.z = part.obj_z.location.z

        part.set_name(get_file_name(self.appliance_path))
        part.assign_material("Chrome", MATERIAL_FILE, "Chrome")
        part.assign_material("Stainless Steel", MATERIAL_FILE, "Stainless Steel")
        part.assign_material("Black Anodized Metal", MATERIAL_FILE, "Black Anodized Metal")

        self.update()

        if hasattr(self, "height_above_floor"):
            self.loc_z(value=self.height_above_floor)


class PROMPTS_Parametric_Wall_Appliance(sn_types.Prompts_Interface):
    bl_idname = "sn_appliances.parametric_wall_appliance"
    bl_label = "Appliance Prompt"
    bl_options = {'UNDO'}

    width: FloatProperty(name="Width", unit='LENGTH', precision=4)
    height: FloatProperty(name="Height", unit='LENGTH', precision=4)
    depth: FloatProperty(name="Depth", unit='LENGTH', precision=4)

    placement_on_wall: EnumProperty(
        name="Placement on Wall",
        items=[
            ('SELECTED_POINT', "Selected Point", ""),
            ('FILL', "Fill", ""),
            ('FILL_LEFT', "Fill Left", ""),
            ('LEFT', "Left", ""),
            ('CENTER', "Center", ""),
            ('RIGHT', "Right", ""),
            ('FILL_RIGHT', "Fill Right", "")],
        default='SELECTED_POINT')

    current_location: FloatProperty(name="Current Location", default=0, subtype='DISTANCE', precision=4)
    left_offset: FloatProperty(name="Left Offset", default=0, subtype='DISTANCE')
    right_offset: FloatProperty(name="Right Offset", default=0, subtype='DISTANCE')

    product = None

    def invoke(self, context, event):
        wm = context.window_manager
        self.product = None
        self.top_shelf = None
        obj_product_bp = sn_utils.get_bp(context.object, 'PRODUCT')
        self.product = Parametric_Wall_Appliance(obj_product_bp)
        self.current_location = self.product.obj_bp.location.x
        self.width = self.product.obj_x.location.x
        self.depth = -self.product.obj_y.location.y
        self.height = self.product.obj_z.location.z
        self.placement_on_wall = 'SELECTED_POINT'
        self.left_offset = 0
        self.right_offset = 0

        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(400))

    def check(self, context):
        self.product.obj_x.location.x = self.width
        self.product.obj_y.location.y = -self.depth
        self.product.obj_z.location.z = self.height
        self.update_placement(context)
        return True

    def update_placement(self, context):
        left_x = self.product.get_collision_location('LEFT')
        right_x = self.product.get_collision_location('RIGHT')
        offsets = self.left_offset + self.right_offset

        if self.placement_on_wall == 'SELECTED_POINT':
            self.product.obj_bp.location.x = self.current_location
        if self.placement_on_wall == 'LEFT':
            self.product.obj_bp.location.x = left_x + self.left_offset
            self.product.obj_x.location.x = self.width
        if self.placement_on_wall == 'RIGHT':
            if self.product.obj_bp.snap.placement_type == 'Corner':
                self.product.obj_bp.rotation_euler.z = math.radians(-90)
            self.product.obj_x.location.x = self.width
            self.product.obj_bp.location.x = (right_x - self.product.calc_width()) - self.right_offset
        if self.placement_on_wall == 'FILL':
            self.product.obj_bp.location.x = left_x + self.left_offset
            self.product.obj_x.location.x = (right_x - left_x - offsets)
        if self.placement_on_wall == 'CENTER':
            self.product.obj_x.location.x = self.width
            x_loc = left_x + (right_x - left_x) / 2 - (self.product.calc_width() / 2)
            self.product.obj_bp.location.x = x_loc        

    def execute(self, context):
        return {'FINISHED'}

    def draw_product_placement(self, layout):
        box = layout.box()
        row = box.row()
        row.label(text='Placement', icon='LATTICE_DATA')
        row = box.row()
        row.label(text='Height Above Floor:')
        row.prop(self.product.obj_bp, 'location', index=2, text="")
        row = box.row()
        col = row.column(align=True)
        col.prop_enum(self, "placement_on_wall", 'SELECTED_POINT', icon='RESTRICT_SELECT_OFF', text="Selected Point")
        row = col.row(align=True)
        row.prop_enum(self, "placement_on_wall", 'FILL', icon='ARROW_LEFTRIGHT', text="Fill")
        row.prop_enum(self, "placement_on_wall", 'LEFT', icon='TRIA_LEFT', text="Left")
        row.prop_enum(self, "placement_on_wall", 'CENTER', icon='TRIA_UP_BAR', text="Center")
        row.prop_enum(self, "placement_on_wall", 'RIGHT', icon='TRIA_RIGHT', text="Right")

        if self.placement_on_wall == 'FILL':
            row = box.row()
            row.label(text='Offset', icon='ARROW_LEFTRIGHT')
            row.prop(self, "left_offset", icon='TRIA_LEFT', text="Left")
            row.prop(self, "right_offset", icon='TRIA_RIGHT', text="Right")

        if self.placement_on_wall in 'LEFT':
            row = box.row()
            row.label(text='Offset', icon='BACK')
            row.prop(self, "left_offset", icon='TRIA_LEFT', text="Left")

        if self.placement_on_wall in 'CENTER':
            row = box.row()

        if self.placement_on_wall in 'RIGHT':
            row = box.row()
            row.label(text='Offset', icon='FORWARD')
            row.prop(self, "right_offset", icon='TRIA_RIGHT', text="Right")

        if self.placement_on_wall == 'SELECTED_POINT':
            row = box.row()
            row.label(text='Location:')
            row.prop(self, 'current_location', text="")

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        col = row.column(align=True)
        row = col.row()
        row.label(text='Width:')
        row.prop(self, 'width', text="")
        row = col.row()
        row.label(text='Height:')
        row.prop(self, 'height', text="")
        row = col.row()
        row.label(text='Depth:')
        row.prop(self, 'depth', text="")
        row = col.row()
        row.label(text='Rotation:')
        row.prop(self.product.obj_bp, 'rotation_euler', index=2, text="")

        self.draw_product_placement(layout)


bpy.utils.register_class(PROMPTS_Parametric_Wall_Appliance)


class Countertop_Appliance(sn_types.Assembly):
    category_name = "Appliances"
    show_in_library = True
    library_name = LIBRARY_FOLDER_NAME
    type_assembly = "INSERT"
    id_prompt = "sn_appliances.countertop_appliance"

    """ Path to blend file that contains a group of the appliance """
    appliance_path = ""
    drop_id = "sn_appliances.place_countertop_appliance"

    def update(self):
        self.obj_bp["ID_PROMPT"] = self.id_prompt
        self.obj_bp["IS_BP_APPLIANCE"] = True
        super().update()

    def draw(self):
        self.create_assembly()
        dim_x = self.obj_x.snap.get_var('location.x', 'dim_x')
        dim_y = self.obj_y.snap.get_var('location.y', 'dim_y')
        dim_z = self.obj_z.snap.get_var('location.z', 'dim_z')
        obj = self.add_assembly_from_file(self.appliance_path)
        part = sn_types.Part(obj_bp=obj)
        part.dim_x("dim_x", [dim_x])
        part.dim_y("dim_y", [dim_y])
        part.dim_z("dim_z", [dim_z])
        self.obj_x.location.x = part.obj_x.location.x
        self.obj_y.location.y = part.obj_y.location.y
        self.obj_z.location.z = part.obj_z.location.z
        part.set_name(get_file_name(self.appliance_path))
        self.obj_prompts = part.obj_prompts
        self.width = part.obj_x.location.x
        self.height = part.obj_z.location.z
        self.depth = part.obj_y.location.y
        part.assign_material("Chrome", MATERIAL_FILE, "Chrome")
        part.assign_material("Stainless Steel", MATERIAL_FILE, "Stainless Steel")
        part.assign_material("Black Anodized Metal", MATERIAL_FILE, "Black Anodized Metal")

        self.add_prompt("Left Offset", 'DISTANCE', sn_unit.inch(2))
        self.add_prompt("Right Offset", 'DISTANCE', sn_unit.inch(2))
        self.add_prompt("Front Offset", 'DISTANCE', sn_unit.inch(2))
        self.add_prompt("Back Offset", 'DISTANCE', sn_unit.inch(2))

        self.update()


class PROMPTS_Countertop_Appliance(sn_types.Prompts_Interface):
    bl_idname = "sn_appliances.countertop_appliance"
    bl_label = "Countertop Appliance Prompt"
    bl_options = {'UNDO'}

    x_loc: FloatProperty(name="X Location", unit='LENGTH', precision=4)
    y_loc: FloatProperty(name="Y Location", unit='LENGTH', precision=4)
    width: FloatProperty(name="Width", unit='LENGTH', precision=4)
    depth: FloatProperty(name="Depth", unit='LENGTH', precision=4)

    insert = None

    def invoke(self, context, event):
        wm = context.window_manager
        self.insert = None
        self.top_shelf = None
        obj_product_bp = sn_utils.get_bp(context.object, 'INSERT')
        self.insert = Parametric_Wall_Appliance(obj_product_bp)
        self.x_loc = self.insert.obj_bp.location.x
        self.y_loc = math.fabs(self.insert.obj_bp.location.y)
        self.width = self.insert.obj_x.location.x
        self.depth = math.fabs(self.insert.obj_y.location.y)

        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(400))

    def check(self, context):
        self.insert.obj_bp.location.x = self.x_loc
        self.insert.obj_bp.location.y = -self.y_loc
        self.insert.obj_x.location.x = self.width
        self.insert.obj_y.location.y = -self.depth
        return True

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        row = box.row()
        col = row.column(align=True)
        row = col.row()
        row.label(text="X Location:")
        row.prop(self, 'x_loc', index=0, text="")
        row = col.row()
        row.label(text='Y Location:')
        row.prop(self, 'y_loc', index=1, text="")

        # Bathroom sink is not set up for parametric width and depth
        if "Bathroom" not in self.insert.obj_bp.name:
            row = col.row()
            row.label(text='Width:')
            row.prop(self, 'width', text="")
            row = col.row()
            row.label(text='Depth:')
            row.prop(self, 'depth', text="")


bpy.utils.register_class(PROMPTS_Countertop_Appliance)
