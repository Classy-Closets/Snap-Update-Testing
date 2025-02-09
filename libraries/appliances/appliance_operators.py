import bpy
import math
from snap import sn_types, sn_unit, sn_utils
from bpy.props import StringProperty
from bpy.types import Operator
import os


class PlaceApplianceAsset():
    filepath: StringProperty(name="Filepath", default="Error")
    obj_bp_name: bpy.props.StringProperty(name="Assembly Base Point", default="")

    asset = None
    drawing_plane = None

    placement = ''

    assembly = None
    obj = None
    exclude_objects = []
    selected_obj = None
    selected_point = None

    def invoke(self, context, event):
        self.reset_properties()
        self.get_asset(context)

        if self.asset:
            return self.execute(context)
        else:
            return self.cancel_drop(context)

    def reset_selection(self):
        self.placement = ''

    def reset_properties(self):
        self.asset = None
        self.drawing_plane = None
        self.placement = ''
        self.assembly = None
        self.exclude_objects = []

    def set_child_properties(self, obj):
        if obj.type == 'EMPTY':
            obj.hide_viewport = True
        if obj.type == 'MESH':
            obj.display_type = 'WIRE'

        if self.drawing_plane and obj.name != self.drawing_plane.name:
            self.exclude_objects.append(obj)
        for child in obj.children:
            self.set_child_properties(child)

    def set_placed_properties(self, obj):
        if obj.type == 'MESH':
            obj.display_type = 'TEXTURED'
        for child in obj.children:
            self.set_placed_properties(child)

    def set_screen_defaults(self, context):
        context.window.cursor_set('DEFAULT')
        context.area.header_text_set(None)        

    def hide_cages(self, context):
        for obj in context.visible_objects:
            if 'IS_CAGE' in obj:
                obj.hide_viewport = True

    def get_asset(self, context):
        wm_props = context.window_manager.snap
        self.asset = wm_props.get_asset(self.filepath)

    def draw_asset(self):
        directory, file = os.path.split(self.filepath)
        filename, ext = os.path.splitext(file)

        if hasattr(self.asset, 'pre_draw'):
            self.asset.pre_draw()
        else:
            self.asset.draw()

        self.asset.set_name(filename)
        self.set_child_properties(self.asset.obj_bp)

    def create_drawing_plane(self, context):
        bpy.ops.mesh.primitive_plane_add()
        plane = context.active_object
        plane.location = (0, 0, 0)
        self.drawing_plane = context.active_object
        self.drawing_plane.display_type = 'WIRE'
        self.drawing_plane.dimensions = (100, 100, 1)

    def cancel_drop(self, context):
        self.set_screen_defaults(context)
        if self.asset:
            sn_utils.delete_object_and_children(self.asset.obj_bp)
        if self.drawing_plane:
            sn_utils.delete_object_and_children(self.drawing_plane)
        self.hide_cages(context)
        return {'CANCELLED'}

    def add_to_wall_collection(self, context):
        collections = bpy.data.collections
        scene_coll = context.scene.collection
        wall_bp = sn_utils.get_wall_bp(self.asset.obj_bp)

        if self.asset and wall_bp:
            wall_name = wall_bp.snap.name_object
            if wall_name in collections:
                wall_coll = collections[wall_name]
                sn_utils.add_assembly_to_collection(self.asset.obj_bp, wall_coll, recursive=True)
                sn_utils.remove_assembly_from_collection(self.asset.obj_bp, scene_coll, recursive=True)

    def finish(self, context):
        self.set_screen_defaults(context)
        if self.drawing_plane:
            sn_utils.delete_obj_list([self.drawing_plane])
        if self.asset.obj_bp:
            self.set_placed_properties(self.asset.obj_bp)
            self.add_to_wall_collection(context)
            context.view_layer.objects.active = self.asset.obj_bp
        self.hide_cages(context)
        bpy.ops.object.select_all(action='DESELECT')
        context.area.tag_redraw()
        bpy.ops.closet_materials.assign_materials()
        return {'FINISHED'}

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type in {'ESC'}:
            self.cancel_drop(context)
            return {'FINISHED'}

        return self.drop(context, event)

    def execute(self, context):
        self.create_drawing_plane(context)
        self.draw_asset()
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


class SN_OT_Place_Countertop_Appliance(bpy.types.Operator, PlaceApplianceAsset):
    bl_idname = "sn_appliances.place_countertop_appliance"
    bl_label = "Place Sink"
    bl_description = "This allows you to place a countertop appliance. The object that you select will\
        automatically have a cutout for the appliance."
    bl_options = {'UNDO'}

    assembly = None

    def search_for_countertops(self, obj):
        counter_list = []
        for child in obj.children:
            parts = (
                'IS_BP_COUNTERTOP' in child,
                'IS_BP_CABINET_COUNTERTOP' in child,
                'IS_BP_HPL_TOP' in child,
                'IS_BP_TOP_KD_SHELF' in child)

            if any(parts):
                counter_list.append(child)
            else:
                if len(child.children) > 0:
                    counter_list.extend(self.search_for_countertops(child))
        return counter_list

    def assign_boolean(self, obj):
        if obj:
            objs = sn_utils.get_child_objects(self.asset.obj_bp)
            for obj_bool in objs:
                if obj_bool.get('use_as_bool_obj'):
                    obj_bool.hide_viewport = True
                    mod = obj.modifiers.new(obj_bool.name, 'BOOLEAN')
                    mod.object = obj_bool
                    mod.operation = 'DIFFERENCE'

    def drop(self, context, event):
        selected_point, selected_obj, _ = sn_utils.get_selection_point(context, event, exclude_objects=self.exclude_objects)
        bpy.ops.object.select_all(action='DESELECT')
        sel_product_bp = sn_utils.get_bp(selected_obj, 'PRODUCT')
        sel_assembly_bp = sn_utils.get_assembly_bp(selected_obj)

        if sel_product_bp and sel_assembly_bp:
            countertop_bps = self.search_for_countertops(sel_product_bp)
            sel_assembly = sn_types.Assembly(sel_assembly_bp)
            closet_countertop = 'IS_BP_COUNTERTOP' in sel_assembly_bp
            cabinet_countertop = 'IS_BP_CABINET_COUNTERTOP' in sel_assembly_bp

            if sel_assembly.obj_bp.rotation_euler.x == 0:
                if closet_countertop or cabinet_countertop:
                    assembly_width = self.asset.obj_x.location.x
                    assembly_depth = self.asset.obj_y.location.y
                    sel_assembly_width = sel_assembly.obj_x.location.x
                    sel_assembly_depth = sel_assembly.obj_y.location.y
                    dim_z = sel_assembly.obj_z.snap.get_var('location.z', 'dim_z')

                    self.asset.obj_bp.parent = sel_assembly.obj_bp
                    self.asset.obj_bp.location.x = math.fabs(sel_assembly_width / 2 - assembly_width / 2)
                    self.asset.obj_bp.location.y = sel_assembly_depth / 2 - assembly_depth / 2
                    self.asset.loc_z("dim_z", [dim_z])

                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    if closet_countertop:
                        for countertop_bp in countertop_bps:
                            for child in countertop_bp.children:
                                if child.type == 'MESH':
                                    self.assign_boolean(selected_obj)
                                    self.assign_boolean(child)
                    if cabinet_countertop:
                        for child in sel_assembly.obj_bp.children:
                            if child.type == 'MESH':
                                self.assign_boolean(selected_obj)
                                self.assign_boolean(child)

                    sn_utils.set_wireframe(self.asset.obj_bp, False)
                    bpy.context.window.cursor_set('DEFAULT')
                    bpy.ops.object.select_all(action='DESELECT')
                    context.view_layer.objects.active = self.asset.obj_bp
                    self.asset.obj_bp.select_set(True)
                    self.finish(context)
                    return {'FINISHED'}

        return {'RUNNING_MODAL'}


class SN_OT_place_appliance(bpy.types.Operator, PlaceApplianceAsset):
    bl_idname = "sn_appliances.place_appliance"
    bl_label = "Place Appliance Object"
    bl_description = "This allows you to place an appliance object into the scene."
    bl_options = {'UNDO'}

    def drop(self, context, event):
        selected_point, selected_obj, _ = sn_utils.get_selection_point(context, event, exclude_objects=self.exclude_objects)
        bpy.ops.object.select_all(action='DESELECT')

        if selected_obj:
            wall_bp = sn_utils.get_wall_bp(selected_obj)
            if wall_bp:
                self.asset.obj_bp.rotation_euler.z = wall_bp.rotation_euler.z

        self.asset.obj_bp.location = selected_point

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.asset.display_type = 'TEXTURED'
            bpy.context.window.cursor_set('DEFAULT')
            bpy.ops.object.select_all(action='DESELECT')
            sn_utils.set_wireframe(self.asset.obj_bp, False)
            context.view_layer.objects.active = self.asset.obj_bp
            self.asset.obj_bp.select_set(True)
            self.finish(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}


class SN_OT_drop_appliance(Operator, PlaceApplianceAsset):
    bl_idname = "sn_appliances.drop"
    bl_label = "Drag and Drop"
    bl_description = "This is called when an asset is dropped from the Product library"
    bl_options = {'UNDO'}

    filepath: StringProperty(name="Library Name")

    def execute(self, context):
        directory, file = os.path.split(self.filepath)
        filename, ext = os.path.splitext(file)

        if hasattr(self.asset, 'drop_id'):
            drop_id = self.asset.drop_id
            eval('bpy.ops.{}("INVOKE_DEFAULT", filepath=self.filepath)'.format(drop_id))
            return {'FINISHED'}

        bpy.ops.windows_and_doors.place_product('INVOKE_DEFAULT', filepath=self.filepath)

        return {'FINISHED'}


class SN_OT_delete_appliance(Operator):
    bl_idname = "sn_closets.delete_appliance"
    bl_label = "Delete Appliance"

    obj_bp = None

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column()
        col.label(text="'{}'".format(self.obj_bp.snap.name_object))
        col.label(text="Are you sure you want to delete this?")

    def invoke(self, context, event):
        self.obj_bp = sn_utils.get_closet_bp(context.object)
        if not self.obj_bp:
            self.obj_bp = sn_utils.get_appliance_bp(context.object)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def execute(self, context):
        sn_utils.delete_object_and_children(self.obj_bp)

        return {'FINISHED'}


classes = (
    SN_OT_Place_Countertop_Appliance,
    SN_OT_place_appliance,
    SN_OT_drop_appliance,
    SN_OT_delete_appliance
)

register, unregister = bpy.utils.register_classes_factory(classes)
