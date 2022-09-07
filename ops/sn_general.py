import bpy
from bpy.types import Operator, Menu
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    IntProperty,
    FloatProperty
    )
from snap import sn_utils, sn_types, sn_unit
import math
from snap.libraries.closets.ui.closet_prompts_ui import get_panel_heights


class SN_GEN_OT_change_file_browser_path(Operator):
    bl_idname = "sn_general.change_file_browser_path"
    bl_label = "Change File Browser Path"
    bl_description = "Changes the file browser path"
    bl_options = {'UNDO'}

    file_path: StringProperty(name='File Path')

    def execute(self, context):
        sn_utils.update_file_browser_path(context, self.file_path)
        return {'FINISHED'}


class SN_GEN_OT_update_library_xml(Operator):
    """ This will load all of the products from the products module.
    """
    bl_idname = "sn_general.update_library_xml"
    bl_label = "Update Library XML"
    bl_description = "This will Update the Library XML file that stores the library paths"
    bl_options = {'UNDO'}

    def execute(self, context):
        xml = sn_types.MV_XML()
        root = xml.create_tree()
        paths = xml.add_element(root, 'LibraryPaths')

        wm = context.window_manager
        packages = xml.add_element(paths, 'Packages')
        for package in wm.snap.library_packages:
            if os.path.exists(package.lib_path):
                lib_package = xml.add_element(packages, 'Package', package.lib_path)
                xml.add_element_with_text(lib_package, 'Enabled', str(package.enabled))

        if os.path.exists(wm.snap.library_module_path):
            xml.add_element_with_text(paths, 'Modules', wm.snap.library_module_path)
        else:
            xml.add_element_with_text(paths, 'Modules', "")

        if os.path.exists(wm.snap.assembly_library_path):
            xml.add_element_with_text(paths, 'Assemblies', wm.snap.assembly_library_path)
        else:
            xml.add_element_with_text(paths, 'Assemblies', "")

        if os.path.exists(wm.snap.object_library_path):
            xml.add_element_with_text(paths, 'Objects', wm.snap.object_library_path)
        else:
            xml.add_element_with_text(paths, 'Objects', "")

        if os.path.exists(wm.snap.material_library_path):
            xml.add_element_with_text(paths, 'Materials', wm.snap.material_library_path)
        else:
            xml.add_element_with_text(paths, 'Materials', "")

        if os.path.exists(wm.snap.world_library_path):
            xml.add_element_with_text(paths, 'Worlds', wm.snap.world_library_path)
        else:
            xml.add_element_with_text(paths, 'Worlds', "")

        xml.write(sn_utils.get_library_path_file())

        return {'FINISHED'}


class SN_GEN_OT_open_new_window(Operator):
    bl_idname = "sn_general.open_new_window"
    bl_label = "Open New Window"

    space_type: bpy.props.StringProperty(name="Space Type")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        for window in context.window_manager.windows:
            if len(window.screen.areas) == 1 and window.screen.areas[0].type == 'PREFERENCES':
                window.screen.areas[0].type = self.space_type
        return {'FINISHED'}


class SN_GEN_OT_select_all_elevation_scenes(Operator):
    bl_idname = "sn_general.select_all_elevation_scenes"
    bl_label = "Select All Elevation Scenes"
    bl_description = "This will select all of the scenes in the elevation scenes list"

    select_all: BoolProperty(name="Select All", default=True)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        for scene in bpy.data.scenes:
            is_elv = scene.snap.scene_type == 'ELEVATION'
            is_pvs = scene.snap.scene_type == 'PLAN_VIEW'
            is_acc = scene.snap.scene_type == 'ACCORDION'
            is_island = scene.snap.scene_type == 'ISLAND'
            if is_elv or is_pvs or is_acc or is_island:
                scene.snap.elevation_selected = self.select_all

        return{'FINISHED'}


class SN_GEN_OT_project_info(Operator):
    bl_idname = "sn_general.project_info"
    bl_label = "Project Info (Fill In All Fields)"

    def check(self, context):
        active_props = context.scene.snap
        for scene in bpy.data.scenes:
            props = scene.snap
            props.job_name = active_props.job_name
            props.job_number = active_props.job_number
            props.install_date = active_props.install_date
            props.designer_name = active_props.designer_name
            props.designer_phone = active_props.designer_phone
            props.client_name = active_props.client_name
            props.client_phone = active_props.client_phone
            props.client_email = active_props.client_email
            props.client_number = active_props.client_number
            props.job_comments = active_props.job_comments
            props.tear_out = active_props.tear_out
            props.touch_up = active_props.touch_up
            props.block_wall = active_props.block_wall
            props.new_construction = active_props.new_construction
            props.elevator = active_props.elevator
            props.stairs = active_props.stairs
            props.floor = active_props.floor
            props.door = active_props.door
            props.base_height = active_props.base_height
            props.parking = active_props.parking

        return True

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(350))

    def draw(self, context):
        props = context.scene.snap
        layout = self.layout
        layout.prop(props, "job_name")
        layout.prop(props, "job_number")
        layout.prop(props, "install_date")
        layout.prop(props, "designer_name")
        layout.prop(props, "designer_phone")
        layout.prop(props, "client_name")
        layout.prop(props, "client_number")
        layout.prop(props, "client_phone")
        layout.prop(props, "client_email")
        layout.prop(props, "job_comments")
        layout.prop(props, "tear_out")
        layout.prop(props, "touch_up")
        layout.prop(props, "block_wall")
        layout.prop(props, "new_construction")
        layout.prop(props, "elevator")
        layout.prop(props, "stairs")
        layout.prop(props, "floor")
        layout.prop(props, "door")
        layout.prop(props, "base_height")
        layout.prop(props, "parking")


class SNAP_GEN_OT_viewport_shade_mode(Operator):
    bl_idname = "sn_general.change_shade_mode"
    bl_label = "Change Viewport Shading Mode"

    mode: EnumProperty(
        name="Shade Mode",
        items=(
            ('WIREFRAME', "Wire Frame", "WIREFRAME", 'SHADING_WIRE', 1),
            ('SOLID', "Solid", "SOLID", 'SHADING_SOLID', 2),
            ('MATERIAL', "Material", "MATERIAL", 'MATERIAL', 3),
            ('RENDERED', "Rendered", "RENDERED", 'SHADING_RENDERED', 4)))

    def execute(self, context):
        context.area.spaces.active.shading.type = self.mode
        return {'FINISHED'}


class SNAP_GEN_OT_enable_ruler_mode(Operator):
    bl_idname = "sn_general.enable_ruler"
    bl_label = "Enable/Disable Ruler"

    enable: BoolProperty(name="Enable Ruler Mode", default=False)

    def execute(self, context):
        if self.enable:
            context.scene.tool_settings.use_snap = True
            context.scene.tool_settings.snap_elements = {'VERTEX'}
            bpy.ops.wm.tool_set_by_id(name="builtin.measure")

        else:
            context.scene.tool_settings.use_snap = False
            context.scene.tool_settings.snap_elements = {'EDGE'}
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}


class SNAP_MT_viewport_shade_mode(Menu):
    bl_label = "Viewport Shade Mode"

    def draw(self, context):
        layout = self.layout
        layout.operator("sn_general.change_shade_mode", text="")


class SNAP_GEN_OT_place_product(sn_types.Prompts_Interface):
    bl_idname = "sn_general.product_placement_options"
    bl_label = "Product Placement Options"
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")

    width: FloatProperty(name="Width",unit='LENGTH',precision=4)
    height: EnumProperty(name="Default Hanging Panel Height", items=get_panel_heights)
    depth: FloatProperty(name="Depth",unit='LENGTH',precision=4)
    
    placement_on_wall: EnumProperty(name="Placement on Wall",items=[('SELECTED_POINT',"Selected Point",""),
                                                                    ('FILL',"Fill",""),
                                                                    ('LEFT',"Left",""),
                                                                    ('CENTER',"Center",""),
                                                                    ('RIGHT',"Right","")],
                                                                    default = 'SELECTED_POINT')
    
    left_offset: FloatProperty(name="Left Offset", default=0,subtype='DISTANCE')
    right_offset: FloatProperty(name="Right Offset", default=0,subtype='DISTANCE')
    quantity: IntProperty(name="Quantity",default=1)

    
    selected_location = 0
    last_placement = 'SELECTED_POINT'
    default_width = 0
    allow_quantites = True
    allow_fills = True
    allow_height_above_floor = False
    
    product = None

    def update_overall_width(self):
 
        if not self.placement_on_wall == 'FILL':
            # self.width = self.default_width
            self.product.obj_x.location.x = self.width
        else:
            self.width = self.product.obj_x.location.x

    def update_product_size(self):
        self.product.obj_x.location.x = self.width
        toe_kick_offset = 0

        if self.carcass:
            toe_kick_ppt = self.carcass.get_prompt("Toe Kick Height")
            if toe_kick_ppt:
                toe_kick_offset = toe_kick_ppt.get_value()

        if 'IS_MIRROR' in self.product.obj_y:
            self.product.obj_y.location.y = -self.depth
        else:
            self.product.obj_y.location.y = self.depth

        if 'IS_MIRROR' in self.product.obj_z:
            self.product.obj_z.location.z = sn_unit.millimeter(-float(self.height))+toe_kick_offset
        else:
            self.product.obj_z.location.z = sn_unit.millimeter(float(self.height))+toe_kick_offset

        sn_utils.run_calculators(self.product.obj_bp)

    def update_placement(self):
        left_x = self.product.get_collision_location('LEFT')
        right_x = self.product.get_collision_location('RIGHT')
        offsets = self.left_offset + self.right_offset

        if self.placement_on_wall == 'FILL':
            self.product.obj_bp.location.x = left_x + self.left_offset
            self.product.obj_x.location.x = (right_x - left_x - offsets) / self.quantity
        if self.placement_on_wall == 'LEFT':
            if self.product.obj_bp.snap.placement_type == 'Corner':
                self.product.obj_bp.rotation_euler.z = math.radians(0)
            self.product.obj_bp.location.x = left_x + self.left_offset
            self.product.obj_x.location.x = self.width
        if self.placement_on_wall == 'CENTER':
            self.product.obj_x.location.x = self.width
            self.product.obj_bp.location.x = left_x + (right_x - left_x)/2 - ((self.product.calc_width()/2) * self.quantity)
        if self.placement_on_wall == 'RIGHT':
            if self.product.obj_bp.snap.placement_type == 'Corner':
                self.product.obj_bp.rotation_euler.z = math.radians(-90)
            self.product.obj_x.location.x = self.width
            self.product.obj_bp.location.x = (right_x - self.product.calc_width()) - self.right_offset
        if self.placement_on_wall == 'SELECTED_POINT' and self.last_placement != 'SELECTED_POINT':
                self.product.obj_bp.location.x = self.selected_location
        elif self.placement_on_wall == 'SELECTED_POINT' and self.last_placement == 'SELECTED_POINT':
            self.selected_location = self.product.obj_bp.location.x

        self.last_placement = self.placement_on_wall

    def check(self,context):
        self.update_overall_width()
        self.update_product_size()
        self.update_placement()

        sn_utils.run_calculators(self.product.obj_bp)
        self.update_quantity_cage()
        return True

    def hide_empties_and_boolean_meshes(self, obj):
        if obj.type == 'EMPTY' or obj.hide_render:
            obj.hide_viewport = True
            self.mute_hide_viewport_driver(obj, mute=False)
        for child in obj.children:
            self.hide_empties_and_boolean_meshes(child)

    def mute_hide_viewport_driver(self, obj, mute=True):
        if obj.animation_data:
            for driver in obj.animation_data.drivers:
                if driver.data_path == "hide_viewport":
                    driver.mute = mute

    def select_obj_and_children(self, obj):
        self.mute_hide_viewport_driver(obj, mute=True)
        obj.hide_viewport = False
        obj.hide_set(False)
        obj.select_set(True)
        for child in obj.children:
            obj.hide_viewport = False
            obj.hide_set(False)
            child.select_set(True)
            self.select_obj_and_children(child)

    def copy_product(self,product):
        bpy.ops.object.select_all(action='DESELECT')
        self.select_obj_and_children(product.obj_bp)
        bpy.ops.object.duplicate_move()
        self.hide_empties_and_boolean_meshes(product.obj_bp)

        obj = bpy.data.objects[bpy.context.object.name]
        new_product = sn_types.Assembly(sn_utils.get_bp(obj,'PRODUCT'))
        self.hide_empties_and_boolean_meshes(new_product.obj_bp)
        return new_product

    def update_quantity_cage(self):
        cage = self.product.get_cage()
        cage.hide_viewport = False
        cage.hide_select = False
        if 'QTY ARRAY' in cage.modifiers:
            mod = cage.modifiers['QTY ARRAY']
        else:
            mod = cage.modifiers.new('QTY ARRAY','ARRAY')
        mod.count = self.quantity
        mod.use_constant_offset = True
        mod.use_relative_offset = False
        if self.placement_on_wall in {'RIGHT'}:
            mod.constant_offset_displace = ((self.product.obj_x.location.x) *-1,0,0)
        else:
            mod.constant_offset_displace = (self.product.obj_x.location.x,0,0)
    
    def invoke(self, context, event):
        obj = bpy.data.objects[self.object_name]
        self.product = sn_types.Assembly(sn_utils.get_bp(obj,'PRODUCT'))
        self.inserts = sn_utils.get_insert_bp_list(self.product.obj_bp,[])

        if 'IS_MIRROR' in self.product.obj_z:
            self.allow_height_above_floor = True 

        for insert in self.inserts:
            if "IS_BP_CARCASS" in insert:
                self.carcass = sn_types.Assembly(insert) 
                toe_kick_ppt = self.carcass.get_prompt("Toe Kick Height")
                if toe_kick_ppt:
                    self.height = str(round(math.fabs(sn_unit.meter_to_millimeter(self.product.obj_z.location.z-toe_kick_ppt.get_value()))))
                else:
                    self.height = str(round(math.fabs(sn_unit.meter_to_millimeter(self.product.obj_z.location.z))))
        self.width = math.fabs(self.product.obj_x.location.x)
        self.depth = math.fabs(self.product.obj_y.location.y)

        self.selected_location = self.product.obj_bp.location.x
        self.default_width = math.fabs(self.product.obj_x.location.x)
        self.placement_on_wall = 'SELECTED_POINT'
        self.last_placement = 'SELECTED_POINT'
        self.left_offset = 0
        self.right_offset = 0
        self.quantity = 1
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=550)
    
    def execute(self,context):
        x_placement = self.product.obj_bp.location.x + self.product.obj_x.location.x
        self.product.delete_cage()
        self.product.obj_x.hide_viewport = True
        self.product.obj_y.hide_viewport = True 
        self.product.obj_z.hide_viewport = True
        self.product.obj_bp.select_set(True)  
        context.view_layer.objects.active = self.product.obj_bp
        previous_product = None
        products = []
        products.append(self.product.obj_bp)
        if self.quantity > 1:
            for i in range(self.quantity - 1):
                if previous_product:
                    next_product = self.copy_product(previous_product)
                else:
                    next_product = self.copy_product(self.product)

                if self.placement_on_wall == 'RIGHT':
                    next_product.loc_x(value = x_placement - self.product.obj_x.location.x - next_product.obj_x.location.x)
                else:
                    next_product.loc_x(value = x_placement)
                next_product.loc_z(value=self.product.obj_bp.location.z)
                next_product.dim_x(value=self.product.obj_x.location.x)
                next_product.dim_y(value=self.product.obj_y.location.y)
                next_product.dim_z(value=self.product.obj_z.location.z)
                next_product.delete_cage()
                next_product.obj_x.hide_viewport = True
                next_product.obj_y.hide_viewport = True
                next_product.obj_z.hide_viewport = True
                previous_product = next_product
                products.append(next_product.obj_bp)
                if self.placement_on_wall == 'RIGHT':
                    x_placement -= self.product.obj_x.location.x
                else:
                    x_placement += self.product.obj_x.location.x
                
        for product_bp in products:
            sn_utils.init_objects(product_bp)
            
        return {'FINISHED'}
    
    def draw_product_placment(self,layout):
        box = layout.box()

        
        row = box.row(align=True)
        row.label(text="Quantity:")
        if self.allow_quantites:
            row.prop(self,'quantity', text="")
        else:
            row.label(text='Quantity: 1')

        box = layout.box()
        row = box.row(align=True)
        row.label(text='Placement',icon='LATTICE_DATA')
        row.prop_enum(self, "placement_on_wall", 'SELECTED_POINT', icon='RESTRICT_SELECT_OFF', text="Selected")
        row.prop_enum(self, "placement_on_wall", 'FILL', icon='ARROW_LEFTRIGHT', text="Fill")
        row.prop_enum(self, "placement_on_wall", 'LEFT', icon='TRIA_LEFT', text="Left") 
        row.prop_enum(self, "placement_on_wall", 'CENTER', icon='TRIA_UP_BAR', text="Center") 
        row.prop_enum(self, "placement_on_wall", 'RIGHT', icon='TRIA_RIGHT', text="Right") 
        
        if self.placement_on_wall == 'FILL':
            row = box.row()
            row.label(text='Offset',icon='ARROW_LEFTRIGHT')
            row.prop(self, "left_offset", icon='TRIA_LEFT', text="Left") 
            row.prop(self, "right_offset", icon='TRIA_RIGHT', text="Right") 
        
        if self.placement_on_wall in 'LEFT':
            row = box.row()
            row.label(text='Offset',icon='BACK')
            row.prop(self, "left_offset", icon='TRIA_LEFT', text="Left")
 
        if self.placement_on_wall in {'SELECTED_POINT','CENTER'}:
            row = box.row()
        
        if self.placement_on_wall in 'RIGHT':
            row = box.row()
            row.label(text='Offset',icon='FORWARD')
            row.prop(self, "right_offset", icon='TRIA_RIGHT', text="Right")  
    
    def draw_product_size(self, layout, alt_height="", use_rot_z=True):
        box = layout.box()
        row = box.row()

        col = row.column(align=True)
        row1 = col.row(align=True)
        if self.object_has_driver(self.product.obj_x):
            row1.label(text='Width: ' + str(sn_unit.meter_to_active_unit(math.fabs(self.product.obj_x.location.x))))
        elif self.placement_on_wall == 'FILL':
            width = round(sn_unit.meter_to_inch(self.product.obj_x.location.x), 2)
            label = str(width).replace(".0", "") + '"'
            row1.label(text="Width:")
            row1.label(text=label)
        else:
            row1.label(text='Width:')
            row1.prop(self,'width',text="")

        row1 = col.row(align=True)
        if sn_utils.object_has_driver(self.product.obj_z):
            row1.label(text='Height: ' + str(round(sn_unit.meter_to_active_unit(math.fabs(self.product.obj_z.location.z)), 3)))
        else:
            row1.label(text='Height:')

            if alt_height == "":
                pass
                row1.prop(self, 'height', text="")
            else:
                row1.prop(self, alt_height, text="")

        row1 = col.row(align=True)
        if sn_utils.object_has_driver(self.product.obj_y):
            row1.label(text='Depth: ' + str(round(sn_unit.meter_to_active_unit(math.fabs(self.product.obj_y.location.y)), 3)))
        else:
            row1.label(text='Depth:')
            row1.prop(self, 'depth', text="")

        col = row.column(align=True)
        col.label(text="Location X:")
        col.label(text="Location Y:")
        col.label(text="Location Z:")

        col = row.column(align=True)
        col.prop(self.product.obj_bp, 'location', text="")

        if use_rot_z:
            row = box.row()
            row.label(text='Rotation Z:')
            row.prop(self.product.obj_bp, 'rotation_euler', index=2, text="")

    def object_has_driver(self,obj):
        if obj.animation_data:
            if len(obj.animation_data.drivers) > 0:
                return True

    def draw(self, context):
        layout = self.layout
        if self.product.obj_bp.snap.placement_type == 'Corner':
            self.allow_fills = False
            self.allow_quantites = False
        if self.product.obj_x.lock_location[0]:
            self.allow_fills = False

        box = layout.box()
        self.draw_product_size(box)
        self.draw_product_placment(box)



classes = (
    SN_GEN_OT_change_file_browser_path,
    SN_GEN_OT_update_library_xml,
    SN_GEN_OT_open_new_window,
    SN_GEN_OT_select_all_elevation_scenes,
    SN_GEN_OT_project_info,
    SNAP_GEN_OT_viewport_shade_mode,
    SNAP_MT_viewport_shade_mode,
    SNAP_GEN_OT_place_product,
    SNAP_GEN_OT_enable_ruler_mode
)

register, unregister = bpy.utils.register_classes_factory(classes)
