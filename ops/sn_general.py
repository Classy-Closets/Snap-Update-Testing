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


class SNAP_GEN_OT_place_product(bpy.types.Operator):
    bl_idname = "sn_general.product_placement_options"
    bl_label = "Product Placement Options"
    bl_options = {'UNDO'}
    
    #READONLY
    object_name: StringProperty(name="Object Name")
    
    placement_on_wall: EnumProperty(name="Placement on Wall",items=[('SELECTED_POINT',"Selected Point",""),
                                                                     ('FILL',"Fill",""),
                                                                     ('FILL_LEFT',"Fill Left",""),
                                                                     ('LEFT',"Left",""),
                                                                     ('CENTER',"Center",""),
                                                                     ('RIGHT',"Right",""),
                                                                     ('FILL_RIGHT',"Fill Right","")],default = 'SELECTED_POINT')
    
    quantity: IntProperty(name="Quantity",default=1)
    left_offset: FloatProperty(name="Left Offset", default=0,subtype='DISTANCE')
    right_offset: FloatProperty(name="Right Offset", default=0,subtype='DISTANCE')
    product_width: FloatProperty(name="Product Width", default=0,subtype='DISTANCE')
    
    library_type = 'PRODUCT'
    product = None
    default_width = 0
    selected_location = 0
    
    allow_quantites = True
    allow_fills = True
    
    def set_product_defaults(self):
        self.product.obj_bp.location.x = self.selected_location + self.left_offset
        self.product.obj_x.location.x = self.default_width - (self.left_offset + self.right_offset)
    
    def check(self,context):
        left_x = self.product.get_collision_location('LEFT')
        right_x = self.product.get_collision_location('RIGHT')
        offsets = self.left_offset + self.right_offset
        self.set_product_defaults()
        if self.placement_on_wall == 'FILL':
            self.product.obj_bp.location.x = left_x + self.left_offset
            self.product.obj_x.location.x = (right_x - left_x - offsets) / self.quantity
        if self.placement_on_wall == 'FILL_LEFT':
            self.product.obj_bp.location.x = left_x + self.left_offset
            self.product.obj_x.location.x = (self.default_width + (self.selected_location - left_x) - offsets) / self.quantity
        if self.placement_on_wall == 'LEFT':
            if self.product.obj_bp.snap.placement_type == 'Corner':
                self.product.obj_bp.rotation_euler.z = math.radians(0)
            self.product.obj_bp.location.x = left_x + self.left_offset
            self.product.obj_x.location.x = self.product_width
        if self.placement_on_wall == 'CENTER':
            self.product.obj_x.location.x = self.product_width
            self.product.obj_bp.location.x = left_x + (right_x - left_x)/2 - ((self.product.calc_width()/2) * self.quantity)
        if self.placement_on_wall == 'RIGHT':
            if self.product.obj_bp.snap.placement_type == 'Corner':
                self.product.obj_bp.rotation_euler.z = math.radians(-90)
            self.product.obj_x.location.x = self.product_width
            self.product.obj_bp.location.x = (right_x - self.product.calc_width()) - self.right_offset
        if self.placement_on_wall == 'FILL_RIGHT':
            self.product.obj_bp.location.x = self.selected_location + self.left_offset
            self.product.obj_x.location.x = ((right_x - self.selected_location) - offsets) / self.quantity
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
        # cage.select = True
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
        self.selected_location = self.product.obj_bp.location.x
        self.default_width = self.product.obj_x.location.x
        self.product_width = self.product.obj_x.location.x
        self.placement_on_wall = 'SELECTED_POINT'
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
    
    def draw(self, context):
        layout = self.layout
        if self.product.obj_bp.snap.placement_type == 'Corner':
            self.allow_fills = False
            self.allow_quantites = False
        
        if self.product.obj_x.lock_location[0]:
            self.allow_fills = False
        box = layout.box()
        row = box.row(align=False)
        row.label(text='Placement Options',icon='LATTICE_DATA')

        row = box.row(align=True)
        row.prop_enum(self, "placement_on_wall", 'SELECTED_POINT', icon='RESTRICT_SELECT_OFF', text="Selected")
        if self.allow_fills:
            row.prop_enum(self, "placement_on_wall", 'FILL', icon='ARROW_LEFTRIGHT', text="Fill")
        row.prop_enum(self, "placement_on_wall", 'LEFT', icon='TRIA_LEFT', text="Left") 
        row.prop_enum(self, "placement_on_wall", 'CENTER', icon='TRIA_DOWN', text="Center")
        row.prop_enum(self, "placement_on_wall", 'RIGHT', icon='TRIA_RIGHT', text="Right") 

        # if self.allow_quantites:
        #     row = box.row(align=True)
        #     row.prop(self,'quantity')
        # split = box.split(factor=0.5)
        # col = split.column(align=True)
        # col.label(text="Dimensions:")
        # if self.placement_on_wall in {'LEFT','RIGHT','CENTER'}:
        #     col.prop(self,"product_width",text="Width")
        # else:
        #     col.label(text='Width: ' + str(round(sn_unit.meter_to_active_unit(self.product.obj_x.location.x),4)))
        # col.prop(self.product.obj_y,"location",index=1,text="Depth")
        # col.prop(self.product.obj_z,"location",index=2,text="Height")

        # col = split.column(align=True)
        # col.label(text="Offset:")
        # col.prop(self,"left_offset",text="Left")
        # col.prop(self,"right_offset",text="Right")
        # col.prop(self.product.obj_bp,"location",index=2,text="Height From Floor")


classes = (
    SN_GEN_OT_change_file_browser_path,
    SN_GEN_OT_update_library_xml,
    SN_GEN_OT_open_new_window,
    SN_GEN_OT_select_all_elevation_scenes,
    SN_GEN_OT_project_info,
    SNAP_GEN_OT_viewport_shade_mode,
    SNAP_GEN_OT_enable_ruler_mode,
    SNAP_MT_viewport_shade_mode
)

register, unregister = bpy.utils.register_classes_factory(classes)
