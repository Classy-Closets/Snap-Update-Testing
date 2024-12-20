from re import T
from typing import List
from numpy.core.fromnumeric import cumsum
import psutil
import time
import os
import subprocess
import math
import mathutils
from bpy.types import Operator
from bpy.props import (BoolProperty,
                       EnumProperty,
                       StringProperty,
                       FloatProperty,
                       CollectionProperty,
                       IntProperty)
from snap.views import view_props
from snap.libraries.closets.common import common_lists
import bpy
from snap import sn_unit as unit, sn_utils
from snap import sn_utils as utils
from snap import sn_types
from snap import sn_paths
from snap import sn_xml
from . import opengl_dim
from . import freestyle_exclusion_types as fet
from . import view_icons
from snap.libraries.closets import closet_props
from snap.libraries.closets.data import data_drawers
from snap.libraries.closets.data import data_closet_carcass
import numpy as np
import re
import xml.etree.ElementTree as ET


"""
Spread a nested list into a single list

**Returns** List
"""
def spread(arg):
    ret = []
    for i in arg:
        ret.extend(i) if isinstance(i, list) else ret.append(i)
    return ret

def to_inch(measure):
    return round(measure / unit.inch(1), 2)

def get_dimension_props():
    """
    This is a function to get access to all of the scene properties that are registered in this library
    """
    props = eval("bpy.context.scene.snap_closet_dimensions")
    return props


def hide_dim_handles():
    """
    HACK: Needed to achieve the same look as previous SNaP version. Given that
    opengl_dims don't render in the correct place if their handles'
    hide_viewport is True on creation, Dimension objects are now created with
    visible handles to let opengl_dims render, and handles are hidden afterward
    """
    for obj in bpy.data.objects:
        if obj.get('IS_VISDIM_A') or obj.get('IS_VISDIM_B'):
            obj.hide_viewport = True

def fetch_attach_walls(self, context):
    walls = [('', '', '')]
    snap = context.window_manager.snap
    wall_qty = snap.main_scene_wall_qty
    if wall_qty > 0:
        walls = []
        for i in range(wall_qty):
            current_letter = chr(65+i)
            wall_str = f'Wall {current_letter}'
            walls.append((wall_str, wall_str, wall_str))
    return walls

class VIEW_OT_move_image_list_item(Operator):
    bl_idname = "sn_2d_views.move_2d_image_item"
    bl_label = "Move an item in the 2D image list"

    direction: EnumProperty(items=(('UP', 'Up', "Move Item Up"),
                                   ('DOWN', 'Down', "Move Item Down")))

    @classmethod
    def poll(self, context):
        return len(bpy.context.window_manager.snap.image_views) > 0

    def execute(self, context):
        wm = context.window_manager.snap
        img_list = wm.image_views
        crt_index = wm.image_view_index
        list_length = len(wm.image_views) - 1
        move_to_index = crt_index - 1 if self.direction == 'UP' else crt_index + 1

        if self.direction == 'UP' and crt_index == 0 or \
           self.direction == 'DOWN' and crt_index == list_length:
            return {'FINISHED'}
        else:
            img_list.move(crt_index, move_to_index)
            wm.image_view_index = move_to_index

        return{'FINISHED'}


class VIEW_OT_create_new_view(Operator):
    bl_idname = "sn_2d_views.create_new_view"
    bl_label = "Create New 2d View"
    bl_description = "Create New 2d View"
    bl_options = {'UNDO'}

    view_name: StringProperty(name="View Name",
                              description="Name for New View",
                              default="")

    view_products = []

    def invoke(self, context, event):
        wm = context.window_manager
        self.view_products.clear()

        # For now only products are selected,
        # could include walls or other objects
        for obj in context.view_layer.objects.selected:
            product_bp = utils.get_bp(obj, 'PRODUCT')

            if product_bp and product_bp not in self.view_products:
                self.view_products.append(product_bp)

        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, 'view_name', text="View Name")
        box.label(text="Selected Products:")
        prod_box = box.box()

        if len(self.view_products) > 0:
            for obj in self.view_products:
                row = prod_box.row()
                row.label(obj.snap.name_object, icon='OUTLINER_OB_LATTICE')

        else:
            row = prod_box.row()
            row.label(text="No Products Selected!", icon='ERROR')
            warn_box = box.box()
            row = warn_box.row()
            row.label(text="Create Empty View?", icon='QUESTION')

    def execute(self, context):
        packed_bps = [{"name": obj_bp.name,
                       "obj_name": obj_bp.snap.name_object}
                      for obj_bp in self.view_products]
        bpy.ops.sn_2d_views.generate_2d_views('INVOKE_DEFAULT',
                                              use_single_scene=True,
                                              single_scene_name=self.view_name,
                                              single_scene_objs=packed_bps)
        return {'FINISHED'}


class VIEW_OT_append_to_view(Operator):
    bl_idname = "sn_2d_views.append_to_view"
    bl_label = "Append Product to 2d View"
    bl_description = "Append Product to 2d View"
    bl_options = {'UNDO'}

    products = []

    objects = []

    scenes: CollectionProperty(type=view_props.single_scene_objs,
                               name="Objects for Single Scene",
                               description="Objects to Include When Creating a Single View")

    scene_index: IntProperty(name="Scene Index")

    def invoke(self, context, event):
        wm = context.window_manager
        self.products.clear()
        self.objects.clear()

        for i in self.scenes:
            self.scenes.remove(0)

        for scene in bpy.data.scenes:
            scene_col = self.scenes.add()
            scene_col.name = scene.name

        for obj in context.view_layer.objects.selected:
            product_bp = utils.get_bp(obj, 'PRODUCT')

            if product_bp and product_bp not in self.products:
                self.products.append(product_bp)

        if len(self.products) == 0:
            for obj in context.view_layer.objects.selected:
                self.objects.append(obj)

        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Selected View to Append To:")
        box.template_list("LIST_2d_images", " ", self,
                          "scenes", self, "scene_index")

        if len(self.products) > 0:
            box.label(text="Selected Products:")
            prod_box = box.box()
            for obj in self.products:
                row = prod_box.row()
                row.label(obj.snap.name_object, icon='OUTLINER_OB_LATTICE')
        else:
            if len(self.objects) > 0:
                box.label(text="Selected Objects:")
                prod_box = box.box()
                for obj in self.objects:
                    row = prod_box.row()
                    row.label(obj.name, icon='OBJECT_DATA')
            else:
                warn_box = box.box()
                row = warn_box.row()
                row.label(text="Nothing to Append.", icon='ERROR')

    def link_children_to_scene(self, scene, obj_bp):
        scene.collection.objects.link(obj_bp)
        for child in obj_bp.children:
            self.link_children_to_scene(scene, child)

    def execute(self, context):
        scene = bpy.data.scenes[self.scene_index]

        for product in self.products:
            self.link_children_to_scene(scene, product)

        print("OBJS", self.objects)

        for obj in self.objects:
            print('LINK', obj, scene)
            self.link_children_to_scene(scene, obj)

        return {'FINISHED'}


class VIEW_OT_generate_2d_views(Operator):
    bl_idname = "sn_2d_views.generate_2d_views"
    bl_label = "Generate 2d Views"
    bl_description = "Generates 2D Views"
    bl_options = {'UNDO'}

    VISIBLE_LINESET_NAME = "Visible Lines"
    HIDDEN_LINESET_NAME = "Hidden Lines"
    ICONS_LINESET_NAME = "Icons"

    FS_VIS_EXCLUSION_COLL = None
    FS_HIDE_EXCLUSION_COLL = None
    ICONS_COLL = None

    ENV_2D_NAME = "2D Environment"
    HIDDEN_LINE_DASH_PX = 5
    HIDDEN_LINE_GAP_PX = 5

    current_ctx = None

    ev_pad: FloatProperty(name="Elevation View Padding",
                          default=0.75)

    pv_pad: FloatProperty(name="Plan View Padding",
                          default=5)
    
    isl_pad: FloatProperty(name="Island View Padding",
                          default=2)

    ac_pad: FloatProperty(name="Accordion View Padding",
                          default=3.5)

    main_scene = None

    ignore_obj_list = []

    hashmarks = []

    use_single_scene: BoolProperty(name="Use for Creating Single View",
                                   default=False)

    single_scene_name: StringProperty(name="Single Scene Name")

    single_scene_objs: CollectionProperty(type=view_props.single_scene_objs,
                                          name="Objects for Single Scene",
                                          description="Objects to Include When Creating a Single View")

    # orphan_products = []
    def get_object_global_location(self, obj):
        if obj.type == 'MESH':
            return obj.matrix_world @ obj.data.vertices[0].co
        elif obj.type == 'EMPTY':
            return obj.location

    def to_inch(self, measure):
        return round(measure / unit.inch(1), 2)

    def to_inch_str(self, measure):
        return str(self.to_inch(measure))

    def to_inch_lbl(self, measure):
        return self.to_inch_str(measure) + "\""

    def list_mode(self, lst):
        return max(set(lst), key=lst.count)

    def get_world(self):
        if self.ENV_2D_NAME in bpy.data.worlds:
            return bpy.data.worlds[self.ENV_2D_NAME]
        else:
            world = bpy.data.worlds.new(self.ENV_2D_NAME)
            world.color = (1.0, 1.0, 1.0)
            return world

    def create_linestyles(self):
        linestyles = bpy.data.linestyles
        linestyles.new(self.VISIBLE_LINESET_NAME)
        linestyles[self.VISIBLE_LINESET_NAME].use_chaining = False

        hidden_linestyle = linestyles.new(self.HIDDEN_LINESET_NAME)
        hidden_linestyle.use_dashed_line = True
        hidden_linestyle.dash1 = self.HIDDEN_LINE_DASH_PX
        hidden_linestyle.dash2 = self.HIDDEN_LINE_DASH_PX
        hidden_linestyle.dash3 = self.HIDDEN_LINE_DASH_PX
        hidden_linestyle.gap1 = self.HIDDEN_LINE_GAP_PX
        hidden_linestyle.gap2 = self.HIDDEN_LINE_GAP_PX
        hidden_linestyle.gap3 = self.HIDDEN_LINE_GAP_PX

        icons_linestyle = linestyles.new('Icons Linestyle')
        icons_linestyle.use_chaining = False
        icons_linestyle.color = (0.5, 0.5, 0.5)

    def create_freestyle_collections(self):
        """
        These collections are used to exclude certain objects from either the
        Visible Line lineset or the Hidden Line lineset to prevent these
        objects from rendering.
        """
        fs_vis_coll = 'FS Visible Exclude'
        fs_hid_coll = 'FS Hidden Exclude'
        icons_coll = 'Icons'

        if fs_vis_coll not in bpy.data.collections:
            self.FS_VIS_EXCLUSION_COLL = bpy.data.collections.new(fs_vis_coll)
        else:
            self.FS_VIS_EXCLUSION_COLL = bpy.data.collections[fs_vis_coll]

        if fs_hid_coll not in bpy.data.collections:
            self.FS_HIDE_EXCLUSION_COLL = bpy.data.collections.new(fs_hid_coll)
        else:
            self.FS_HIDE_EXCLUSION_COLL = bpy.data.collections[fs_hid_coll]

        if icons_coll not in bpy.data.collections:
            self.ICONS_COLL = bpy.data.collections.new(icons_coll)
        else:
            self.ICONS_COLL = bpy.data.collections[icons_coll]

    def create_linesets(self, scene):
        f_settings = scene.view_layers[0].freestyle_settings
        linestyles = bpy.data.linestyles

        icons_lineset = f_settings.linesets.new('Icons Lines')
        icons_lineset.linestyle = linestyles['Icons Linestyle']

        icons_lineset.select_by_visibility = False
        icons_lineset.select_by_edge_types = False
        icons_lineset.select_by_face_marks = False
        icons_lineset.select_by_collection = True
        icons_lineset.select_by_image_border = True
        icons_lineset.collection = self.ICONS_COLL
        icons_lineset.collection_negation = 'INCLUSIVE'

        visible_lineset = f_settings.linesets.new(self.VISIBLE_LINESET_NAME)
        visible_lineset.linestyle = linestyles[self.VISIBLE_LINESET_NAME]

        # Collection settings to exclude objects from visible lines
        visible_lineset.select_by_collection = True
        visible_lineset.collection = self.FS_VIS_EXCLUSION_COLL
        visible_lineset.collection_negation = 'EXCLUSIVE'

        hidden_lineset = f_settings.linesets.new(self.HIDDEN_LINESET_NAME)
        hidden_lineset.linestyle = linestyles[self.HIDDEN_LINESET_NAME]

        hidden_lineset.select_by_visibility = True
        hidden_lineset.visibility = 'HIDDEN'
        hidden_lineset.select_by_edge_types = True
        hidden_lineset.select_by_face_marks = False
        hidden_lineset.select_by_collection = True
        hidden_lineset.select_by_image_border = False

        hidden_lineset.select_silhouette = True
        hidden_lineset.select_border = False
        hidden_lineset.select_contour = True
        hidden_lineset.select_suggestive_contour = False
        hidden_lineset.select_ridge_valley = False
        hidden_lineset.select_crease = False
        hidden_lineset.select_edge_mark = True
        hidden_lineset.select_external_contour = False
        hidden_lineset.select_material_boundary = False

        # Collection settings to exclude objects from hidden lines
        hidden_lineset.collection = self.FS_HIDE_EXCLUSION_COLL
        hidden_lineset.collection_negation = 'EXCLUSIVE'

    def clear_unused_linestyles(self):
        for linestyle in bpy.data.linestyles:
            if linestyle.users == 0:
                bpy.data.linestyles.remove(linestyle)

    def create_camera(self, scene):
        camera_data = bpy.data.cameras.new(scene.name)
        camera_obj = bpy.data.objects.new(name=scene.name, object_data=camera_data)
        camera_obj["ID_PROMPT"] = "sn_object.camera_properties"
        scene.collection.objects.link(camera_obj)
        scene.camera = camera_obj
        camera_obj.data.type = 'PERSP'
        scene.render.resolution_y = 1280
        scene.snap.ui.render_type_tabs = 'NPR'
        scene.world = self.get_world()
        bpy.context.preferences.view.render_display_type = 'NONE'
        scene.render.use_lock_interface = True
        scene.render.image_settings.file_format = 'JPEG'

        return camera_obj

    def link_dims_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            if child not in self.ignore_obj_list:
                if child.get('IS_VISDIM_A') or child.get('IS_VISDIM_B'):
                    scene.collection.objects.link(child)
                if len(child.children) > 0:
                    self.link_dims_to_scene(scene, child)

    def has_render_comment(self, obj):
        if obj.snap.comment == "render":
            return True
        return False

    def link_tagged_dims_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            comment = self.has_render_comment(child)
            obstacle = child.get('IS_OBSTACLE')
            if 'hashmark' in child.name.lower():
                scene.collection.objects.link(child)
            if (child not in self.ignore_obj_list or comment) and not obstacle:
                if child.get('IS_VISDIM_A'):
                    obj_parent = child.parent
                    if 'hanging' not in obj_parent.name.lower():
                        scene.collection.objects.link(child)
                if child.get('IS_VISDIM_B'):
                    obj_grandpa = child.parent.parent
                    if 'hanging' not in obj_grandpa.name.lower():
                        scene.collection.objects.link(child)
                if len(child.children) > 0:
                    self.link_tagged_dims_to_scene(scene, child)
            if 'LABEL' in child.name.upper():
                scene.collection.objects.link(child)

    def link_custom_entities_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            if 'PARTHGT' in child.name:
                scene.collection.objects.link(child)
            if 'CSHLSH' in child.name:
                scene.collection.objects.link(child)
            if len(child.children) > 0:
                self.link_custom_entities_to_scene(scene, child)

    def link_desired_dims_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            if child not in self.ignore_obj_list:
                if child.get('IS_VISDIM_A'):
                    obj_parent = child.parent
                    if 'hanging' not in obj_parent.name.lower():
                        scene.collection.objects.link(child)
                if child.get('IS_VISDIM_B'):
                    obj_grandpa = child.parent.parent
                    if 'hanging' not in obj_grandpa.name.lower():
                        scene.collection.objects.link(child)
                if len(child.children) > 0:
                    self.link_desired_dims_to_scene(scene, child)

    def get_obj_mesh(self, obj):
        children = obj.children
        for child in children:
            if "mesh" in child.name.lower():
                return child

    def door_style_materials(self, obj):
        door_mesh = self.get_obj_mesh(obj)
        materials = []
        if door_mesh:
            for slot in door_mesh.snap.material_slots:
                if "Wood_Door_Surface" == slot.pointer_name:
                    materials.append("wood")
                elif "Door_Surface" == slot.pointer_name:
                    pass
                elif "Five_Piece_Melamine_Door_Surface" == slot.pointer_name:
                    materials.append("five_piece_melamine")
                elif "Moderno_Door" == slot.pointer_name:
                    materials.append("moderno")
                elif "Glass" == slot.pointer_name:
                    materials.append("glass")
        return materials

    def create_replaced_mesh(self, obj, materials=[]):
        is_styled = len(materials) > 0
        thick = 2.25
        cover_dim_x, cover_dim_y, cover_dim_z, y_loc_offset = 0, 0, 0, 0
        skipped_name = f"skipped_{obj.name}"
        cover_mesh_name = f"skipped_{obj.name}_cover"
        cover_mesh = None
        obj_assy = sn_types.Assembly(obj)
        obj_loc = obj.location
        dim_x = obj_assy.obj_x.location.x # actually Z
        dim_y = obj_assy.obj_y.location.y # actually X
        dim_z = obj_assy.obj_z.location.z # actually Y
        cover_dim_x = abs(obj_assy.obj_x.location.x) - (unit.inch(thick) * 2)
        cover_dim_y = abs(obj_assy.obj_y.location.y) - (unit.inch(thick) * 2)
        cover_dim_z = obj_assy.obj_z.location.z
        y_loc_offset = unit.inch(thick)
        if dim_y < 0:
            cover_dim_y = cover_dim_y * -1
            y_loc_offset = y_loc_offset * -1
        skipped_mesh = utils.create_cube_mesh(skipped_name, 
                                    (dim_x, dim_y, dim_z))
        utils.copy_world_loc(obj, skipped_mesh)
        utils.copy_world_rot(obj, skipped_mesh)
        if is_styled:
            cover_dims = (cover_dim_x, cover_dim_y, cover_dim_z)
            cover_location = (unit.inch(thick), y_loc_offset, abs(dim_z))
            cover_mesh = utils.create_cube_mesh(cover_mesh_name, cover_dims)
            utils.copy_world_loc(obj, cover_mesh, cover_location)
            utils.copy_world_rot(obj, cover_mesh)
        if is_styled and "glass" in materials and cover_mesh:
            glass_x, glass_y, glass_z = cover_mesh.dimensions
            if dim_y < 0:
                glass_y = glass_y * -1
            glass_label = sn_types.Dimension()
            utils.copy_world_loc(
                cover_mesh, glass_label.anchor, (glass_x/2, glass_y/2, 0))
            utils.copy_world_rot(cover_mesh, glass_label.anchor)
            glass_label.set_label("Glass")
            glass_label.anchor.rotation_euler[1] += math.radians(45)
            cover_mesh["GLASS_SHADING_MESH"] = True

    def group_children(self, grp, obj):
        not_cage = not bool(obj.get('IS_CAGE'))
        ignore = self.ignore_obj_list
        group_list = [item for item in grp.objects]
        not_empty_group = len(group_list) > 0
        if not_cage and obj not in ignore and not_empty_group and obj not in group_list:
            grp.objects.link(obj)
        for child in obj.children:
            shown = any(
                [True for c in child.children \
                    if c.type == 'MESH' and not c.hide_viewport])
            is_door = child.sn_closets.is_door_bp
            is_hamper_door = child.sn_closets.is_hamper_front_bp
            is_drawer_door = child.sn_closets.is_drawer_front_bp
            skippable = (is_door or is_hamper_door or is_drawer_door) and shown
            wallbed_bp = sn_utils.get_wallbed_bp(child)
            if len(child.children) > 0:
                if child.get('IS_OBSTACLE') and child.get('SHOW_ON_ELEVATIONS', True):
                    for cc in child.children: 
                        if cc.get('IS_CAGE'):
                            cc.hide_render = False
                            grp.objects.link(cc)
                elif skippable and not wallbed_bp:
                    style_materials = self.door_style_materials(child)
                    self.create_replaced_mesh(child, style_materials)
                    continue
                else:
                    self.group_children(grp, child)
            else:
                if not child.snap.is_wall_mesh:
                    if not child.get('IS_CAGE') and obj not in self.ignore_obj_list:
                        if not grp.objects.get(child.name):
                            grp.objects.link(child)
        return grp

    def group_children_island(self, grp, obj):
        not_cage = not bool(obj.get('IS_CAGE'))
        ignore = self.ignore_obj_list
        group_list = [item for item in grp.objects]
        not_empty_group = len(group_list) > 0
        if not_cage and obj not in ignore and not_empty_group and obj not in group_list:
            grp.objects.link(obj)
        for child in obj.children:
            shown = any(
                [True for c in child.children \
                    if c.type == 'MESH' and not c.hide_viewport])
            if len(child.children) > 0:
                if child.get('IS_OBSTACLE'):
                    for cc in child.children:
                        if cc.get('IS_CAGE'):
                            cc.hide_render = False
                            grp.objects.link(cc)
                else:
                    self.group_children_island(grp, child)
            else:
                if not child.snap.is_wall_mesh:
                    if not child.get('IS_CAGE') and obj not in self.ignore_obj_list:
                        if not grp.objects.get(child.name):
                            grp.objects.link(child)
        return grp
    
    def group_every_children_on_acc(self, grp, obj):
        ignore = self.ignore_obj_list
        group_list = [item for item in grp.objects]
        not_empty_group = len(group_list) > 0
        is_door = obj.sn_closets.is_door_bp
        shown = any(
                [True for c in obj.children \
                    if c.type == 'MESH' and not c.hide_viewport])
        is_hamper_door = obj.sn_closets.is_hamper_front_bp
        is_drawer_door = obj.sn_closets.is_drawer_front_bp
        not_acc_cross_sec =  'left' not in grp.name and 'right' not in grp.name
        skippable = (is_door or is_hamper_door or is_drawer_door) and not_acc_cross_sec and shown
        if skippable:
            style_materials = self.door_style_materials(obj)
            self.create_replaced_mesh(obj, style_materials)
        if obj not in ignore and not_empty_group and obj not in group_list and not skippable:
            grp.objects.link(obj)
        if hasattr(obj, 'children'):
            for child in obj.children:
                if len(child.children) > 0:
                    self.group_every_children_on_acc(grp, child)
                else:
                    if not grp.objects.get(child.name) and not skippable:
                        grp.objects.link(child)
        return grp

    def group_every_children_elv_cross_sections(self, grp, obj):
        ignore = self.ignore_obj_list
        group_list = [item for item in grp.objects]
        not_empty_group = len(group_list) > 0
        is_door = obj.sn_closets.is_door_bp
        is_hamper_door = obj.sn_closets.is_hamper_front_bp
        is_drawer_door = obj.sn_closets.is_drawer_front_bp
        shown = any(
                [True for c in obj.children \
                    if c.type == 'MESH' and not c.hide_viewport])
        skippable = (is_door or is_hamper_door or is_drawer_door) and shown
        if skippable:
            style_materials = self.door_style_materials(obj)
            self.create_replaced_mesh(obj, style_materials)
        if obj not in ignore and not_empty_group and obj not in group_list and not skippable:
            grp.objects.link(obj)
        if hasattr(obj, 'children'):
            for child in obj.children:
                if len(child.children) > 0:
                    self.group_every_children_elv_cross_sections(grp, child)
                else:
                    if not grp.objects.get(child.name):
                        grp.objects.link(child)
        return grp

    def create_island_new_scene(self, context, grp, name, island):
        bpy.ops.scene.new('INVOKE_DEFAULT', type='EMPTY')
        new_scene = context.scene
        new_scene.name = grp.name
        new_scene.snap.name_scene = name
        new_scene.snap.elevation_img_name = island.name
        new_scene.snap.scene_type = 'ISLAND'
        new_scene.snap.island_index = int(island.get("ISLAND_INDEX", 0))
        self.create_linesets(new_scene)

        return new_scene

    def add_children_to_ignore(self, obj):
        if obj not in self.ignore_obj_list:
            self.ignore_obj_list.append(obj)
        if (len(obj.children) > 0):
            for child in obj.children:
                if child not in self.ignore_obj_list:
                    self.add_children_to_ignore(child)

    def create_new_scene(self, context, grp, obj_bp):
        bpy.ops.scene.new('INVOKE_DEFAULT', type='EMPTY')
        new_scene = context.scene
        new_scene.name = grp.name
        new_scene.snap.name_scene = "Product - " + \
            obj_bp.snap.name_object if obj_bp.get('IS_BP_ASSEMBLY') else obj_bp.snap.name_object
        new_scene.snap.elevation_img_name = obj_bp.name
        new_scene.snap.scene_type = 'ELEVATION'
        self.create_linesets(new_scene)

        return new_scene

    def is_just_door_wall(self, wall):
        wall_obj = sn_types.Wall(obj_bp=wall)
        wall_groups_list = wall_obj.get_wall_groups() 
        door_toggle = False
        for item in wall_groups_list:
            if 'BPASSEMBLY.' in item.name:
                for door in item.children:
                    if 'door frame' in door.name.lower():
                        door_toggle = True
        just_doors = door_toggle and len(wall_groups_list) == 1
        return just_doors
    
    def empty_wall(self, wall):
        sections = 0
        corner_shelves = 0
        l_shelves = 0
        accessories = 0
        wall_cleat = 0
        wall_beds = 0
        wall_islands = 0
        cabinets = 0

        for item in wall.children:
            if 'IS_BP_CABINET' in item:
                cabinets += 1
            if 'section' in item.name.lower():
                sections += 1
            elif 'corner shelves' in item.name.lower():
                corner_shelves += 1
            elif 'l shelves' in item.name.lower():
                l_shelves += 1
            elif 'wall cleat' in item.name.lower():
                l_shelves += 1
            elif 'IS_TOPSHELF_SUPPORT_CORBELS' in item:
                l_shelves += 1
            elif item.sn_closets.is_accessory_bp:
                accessories += 1
            elif item.get("IS_BP_WALL_BED"):
                wall_beds += 1
            elif item.get("IS_BP_ISLAND"):
                wall_islands += 1
        no_cabinets = cabinets == 0
        no_sections = sections == 0
        no_csh = corner_shelves == 0
        no_lsh = l_shelves == 0
        no_acc = accessories == 0
        no_wall_cleat = wall_cleat == 0
        no_beds = wall_beds == 0
        no_isl = wall_islands == 0
        if no_sections and no_csh and no_lsh and no_acc and no_beds and no_isl and no_cabinets:
            return True
        return False

    def find_matching_partition_cutpart(self, opening):
        tolerance = unit.inch(6)
        hanging_opening = opening.parent
        for item in hanging_opening.children:
            if 'partition' in item.name.lower():
                opng_pos = opening.location[0]
                item_pos = item.location[0]
                lower_end = round((opng_pos - tolerance), 2)
                upper_end = round((opng_pos + tolerance), 2)
                if lower_end <= item_pos <= upper_end:
                    for cutpart in item.children:
                        is_cutpart = cutpart.type == 'MESH'
                        hidden = cutpart.hide_viewport
                        if is_cutpart and not hidden:
                            return cutpart
    
    def get_partition_props(self, wall, partition, opening):
        if wall:
            opng_bp_height = opening.location[2]
            wall_height = sn_types.Assembly(wall).obj_z.location.z
            part_height = partition.dimensions[0]
            part_height_midpoint = part_height / 2
            wall_half = wall_height / 2
            part_midpoint_height = part_height_midpoint + opng_bp_height
            is_upper = part_midpoint_height >= wall_half
            is_lower = part_midpoint_height < wall_half
            is_full_upper = opening.location[2] > wall_half
            return ((is_upper, is_full_upper, is_lower))
        return None

    def query_openings_data(self, wall_bp):
        wall_dict = {}
        for obj in wall_bp.children:
            section = 'section' in obj.name.lower()
            opng_dict = {}
            if section:
                openings = []
                sorted_openings = []
                for op in obj.children:
                    inner_opng = 'opening' in op.name.lower()
                    if inner_opng:
                        x_loc = self.to_inch(op.location[0])
                        openings.append((x_loc, op))
                sorted_openings = sorted(openings, key=lambda tup: tup[0])
                filtered_openings = []
                for sorted_opng in sorted_openings:
                    if sn_types.Assembly(sorted_opng[1]).obj_x is not None:
                        filtered_openings.append(sorted_opng)
                obj_assy = sn_types.Assembly(obj)
                hang_opng_width = obj_assy.obj_x.location.x
                start_point = obj.location[0]
                end_point = start_point + hang_opng_width
                for i in range(1, 10):
                    floor_pmpt_query = "Opening " + str(i) + " Floor Mounted"
                    height_pmpt_query = "Opening " + str(i) + " Height"
                    floor_mounted = obj_assy.get_prompt(floor_pmpt_query)
                    opng_height_pmpt = obj_assy.get_prompt(height_pmpt_query)
                    has_floor_value = floor_mounted is not None
                    if has_floor_value:
                        opng_props = None
                        is_floor = floor_mounted.get_value()
                        opng_height = opng_height_pmpt.get_value()
                        matching_opng = filtered_openings[i-1]
                        opng = matching_opng[1]
                        matching = self.find_matching_partition_cutpart(opng)
                        if matching is not None:
                            opng_props = self.get_partition_props(wall_bp,
                                                                  matching,
                                                                  opng)
                        elif matching is None:
                            opng_props = (False, False, True)

                        opening_width = obj_assy.get_prompt("Opening " + str(i) + " Width")
                        opng_width = self.to_inch(opening_width.get_value())
                        opng_height_meas = self.to_inch(opng_height)
                        opng_x_loc = matching_opng[0]
                        opng_dict[opng] = {
                            "width": opng_width,
                            "height": opng_height_meas,
                            "x_loc": opng_x_loc,
                            "is_floor": is_floor,
                            "is_upper": opng_props[0],
                            "is_full_upper": opng_props[1],
                            "is_lower": opng_props[2]
                        }
                result = sorted(opng_dict.items(), key=lambda x: x[1]["x_loc"])
                wall_dict[obj] = {"start": round(start_point, 4),
                                  "end": round(end_point, 4),
                                  "openings": result}
        return wall_dict

    def opening_absolute_start_end(self, opening):
        width = self.get_opening_width(opening)
        opng_width = to_inch(width)
        opng_start = to_inch(opening.location[0])
        section_start = to_inch(opening.parent.location[0])
        actual_start = opng_start + section_start
        opng_end = actual_start + opng_width
        return (actual_start, opng_end)

    def get_opening_width(self, opening):
        opening_number = opening.sn_closets.opening_name
        bp = sn_utils.get_closet_bp(opening)
        closet = data_closet_carcass.Closet_Carcass(bp)
        calculator = closet.get_calculator('Opening Widths Calculator')
        width_calc = eval(
            "calculator.get_calculator_prompt('Opening {} Width')".format(
                str(opening_number)))
        width = width_calc.get_value()
        return width

    def has_occluding_opening(self, opening, opng_data):
        opngs_at_wall = []
        querying_opng = opening
        op_start, op_end = self.opening_absolute_start_end(querying_opng)
        tolrnc = 2 # 2 inches
        for value in opng_data.values():
            openings = value["openings"]
            for item in openings:
                curr_opng = item[0]
                already_in = curr_opng not in opngs_at_wall
                not_same = curr_opng != querying_opng
                not_same_parent = curr_opng.parent != querying_opng.parent
                if already_in and not_same and not_same_parent:
                    opngs_at_wall.append(curr_opng)
        for item in opngs_at_wall:
            oth_start, oth_end = self.opening_absolute_start_end(item)
            match_end = oth_end - tolrnc <= op_end <= oth_end + tolrnc
            match_start = oth_start - tolrnc <= op_start <= oth_start + tolrnc
            if match_start and match_end:
                return True
        return False

    def elv_wall_labels(self, wall_assembly, text_loc=(-unit.inch(2), 
                                                       0, 
                                                       -unit.inch(10))):
        text = sn_types.Dimension()
        utils.copy_world_loc(wall_assembly.obj_bp, text.anchor, text_loc)
        utils.copy_world_rot(wall_assembly.obj_bp, text.anchor)
        text.set_label(wall_assembly.obj_bp.snap.name_object)

    def apply_planview_opening_tag(self, wall_assembly, opening, tags, parent):
        wall_assembly_bp = sn_types.Assembly(wall_assembly.obj_bp)
        wall_angle = round(math.degrees(
            wall_assembly_bp.obj_bp.rotation_euler.z))
        opng_assembly = sn_types.Assembly(opening)
        opng_width = self.get_opening_width(opening)
        pos_x = opng_width
        pos_y = opng_assembly.obj_y.location.y
        parent_height = parent.location.z
        lbl_lines = [tag[0] for tag in tags]
        label = '|'.join(lbl_lines)
        loc_x = pos_x / 2
        # TODO: Adjust loc_y value when plan view cages are rendering again
        # loc_y = (pos_y / (len(tags) + 1)) + unit.inch(3)
        loc_y = pos_y / 2
        loc_z = -parent_height
        text_rotation = (-90, 0, 0)
        if abs(wall_angle) == 180:
            text_rotation = (-90, 180, 0)
        text = sn_types.Dimension()
        # Rotation mode for anchor needs to be changed to allow
        # Y-axis rotation in Plan View
        text.anchor.rotation_mode = 'YZX'
        delta_y = self.get_tag_delta_y(wall_assembly, opening, loc_y)
        text.set_label(label)
        utils.copy_world_loc(parent, text.anchor, (loc_x, delta_y, loc_z))
        utils.copy_world_rot(parent, text.anchor, text_rotation)
        return text.anchor

    def get_tag_delta_y(self, wall_assembly, opening, loc_y):
        has_upper_above = False
        closet = opening.parent
        closet_assembly = sn_types.Assembly(obj_bp=closet)
        is_floor_mounted = self.is_closet_floor_mounted(closet)
        opng_data = self.query_openings_data(wall_assembly.obj_bp)
        has_occlusion_opng = self.has_occluding_opening(opening, opng_data)

        if not has_occlusion_opng:
            return loc_y
        elif has_occlusion_opng:
            uppers_depth = self.get_uppers_depth(wall_assembly)
            lowers_depth = self.get_lowers_depth(wall_assembly)
            if uppers_depth and lowers_depth:
                if uppers_depth == lowers_depth and is_floor_mounted:
                    delta = loc_y - (lowers_depth / 4)
                    return delta
                if uppers_depth == lowers_depth and not is_floor_mounted:
                    delta = loc_y - (-lowers_depth / 4) 
                    return delta
                if uppers_depth < lowers_depth and is_floor_mounted:
                    return (lowers_depth - uppers_depth) / 2
                if uppers_depth < lowers_depth and not is_floor_mounted:
                    return loc_y
            return loc_y
        return loc_y

    def get_uppers_depth(self, wall_assembly):
        wall_children = wall_assembly.obj_bp.children
        for child in wall_children:
            if 'section' in child.name.lower():
                is_wall_mounted = not self.is_closet_floor_mounted(child)
                if is_wall_mounted:
                    closet = child
                    return self.get_closet_depth(closet)

    def get_lowers_depth(self, wall_assembly):
        wall_children = wall_assembly.obj_bp.children
        for child in wall_children:
            if 'section' in child.name.lower():
                is_floor_mounted = self.is_closet_floor_mounted(child)
                if is_floor_mounted:
                    closet = child
                    return self.get_closet_depth(closet)

    def get_closet_depth(self, closet):
        closet_assembly = sn_types.Assembly(obj_bp=closet)
        depth = 0
        opening_qty =\
            closet_assembly.get_prompt("Opening Quantity").get_value()
        for i in range(1, opening_qty + 1):
            opening_depth = abs(closet_assembly.get_prompt(
                    "Opening " + str(i) + " Depth").get_value())
            if opening_depth > depth:
                depth = opening_depth
        return depth

    def get_hang_shelves_count(self, assembly):
        shelves_dict = {}
        shelves_dict["dust"] = 0
        hang_assembly = sn_types.Assembly(assembly)
        top_dust_shelf = hang_assembly.get_prompt("Add Top Shelf").get_value()
        bottom_dust_shelf = hang_assembly.get_prompt(
            "Add Bottom Shelf").get_value()
        top_shelves = hang_assembly.get_prompt(
            "Add Shelves In Top Section").get_value()
        middle_shelves = hang_assembly.get_prompt(
            'Add Shelves In Middle Section').get_value()
        bottom_shelves = hang_assembly.get_prompt(
            'Add Shelves In Bottom Section').get_value()
        if top_shelves:
            shelves_dict["top"] = hang_assembly.get_prompt(
                "Top Shelf Quantity").get_value()
        else:
            shelves_dict["top"] = 0
        if middle_shelves:
            shelves_dict["middle"] = hang_assembly.get_prompt(
                "Middle Shelf Quantity").get_value()
        else:
            shelves_dict["middle"] = 0
        if bottom_shelves:
            shelves_dict["bottom"] = hang_assembly.get_prompt(
                "Bottom Shelf Quantity").get_value()
        else:
            shelves_dict["bottom"] = 0
        if top_dust_shelf:
            shelves_dict["dust"] += 1
        if bottom_dust_shelf:
            shelves_dict["dust"] += 1
        return shelves_dict

    def shelf_count_vertical_splitters(self, assembly):
        shelf_count = 0
        shelves = [o for o in assembly.children if 'shelf' in o.name.lower()]
        for shelf in shelves:
            [mesh] = [c for c in shelf.children if c.type == 'MESH']
            if not mesh.hide_render:
                shelf_count += 1
        return shelf_count

    def get_glass_shelves_count(self, assembly):
        glass_sh_assembly = sn_types.Assembly(assembly)
        sh_qty = glass_sh_assembly.get_prompt("Shelf Qty").get_value()
        return str(sh_qty)

    def get_sss_count(self, assembly):
        sh_qty = 0
        sss_assembly = sn_types.Assembly(assembly)
        sh_pmpt_new = sss_assembly.get_prompt("Shelf Quantity")
        sh_pmpt_old = sss_assembly.get_prompt("Adj Shelf Qty")
        if sh_pmpt_new:
            sh_qty = sh_pmpt_new.get_value()
        elif sh_pmpt_old:
            sh_qty = sh_pmpt_old.get_value()
        sss_version = assembly.get("SNAP_VERSION")
        if sss_version is None:
            return str(sh_qty)
        elif sss_version is not None:
            sss_version = sss_version.replace(".", "")
            version_number = int(sss_version)
            if version_number >= 214:
                bottom_pmpt = sn_types.Assembly(assembly).get_prompt(
                    "Remove Bottom Shelf")
                if bottom_pmpt:
                    if bottom_pmpt.get_value():
                        sh_qty -= 1
                    return str(sh_qty)
        return str(sh_qty)

    def get_shelf_stack_count(self, assembly):
        shlf_qty = 0
        stack_shelves = 'stack' in assembly.name.lower()
        if stack_shelves:
            shlf_qty += sn_types.Assembly(assembly).get_prompt('Shelf Quantity').get_value()
        return shlf_qty

    def get_door_count(self, assembly):
        door_count = 0
        for obj in assembly.children:
            if obj.sn_closets.is_door_bp:
                for o in obj.children:
                    if ((o.snap.type_mesh == 'CUTPART' or
                         o.snap.type_mesh == 'BUYOUT') and not o.hide_viewport):
                        door_count += 1
        return door_count

    def get_drawer_count(self, assembly):
        drawers_assembly = sn_types.Assembly(assembly)
        drawers_qty = drawers_assembly.get_prompt("Drawer Quantity").get_value()
        # It's needed to count minus one drawer to get the correct
        # drawers count over it's prompt.
        drawers_qty -= 1
        return str(drawers_qty)

    def check_sibling_shelf_stack_bottom_shelf(self, assembly, assemblies):
        hasnt_bottom_shelf = False
        for each in assemblies:
            not_same = assembly != each
            stack_shelves = 'stack' in each.name.lower()
            if not_same and stack_shelves:
                hasnt_bottom_shelf = sn_types.Assembly(each).get_prompt(
                     'Remove Bottom Shelf').get_value()
        return hasnt_bottom_shelf

    def check_for_drawer_children_in_shelves(self, assembly):
        name = assembly.name.lower()
        drw_qty = 0
        is_shelf = 'shelf' in name
        not_sss = 'shoe' not in name and 'slanted' not in name
        if is_shelf and not_sss:
            drw_qty = len([c for c in assembly.children\
                 if 'drawer' in c.name.lower()])
        return drw_qty

    def get_assembly_tag(self, assemblies, opening):
        opening_assembly = sn_types.Assembly(opening)
        opening_assembly_height = opening_assembly.obj_z.location.z
        has_any_hang = False
        tags = []
        shelf_count = 0
        for assembly in assemblies:
            shelves_dict = {}
            name = assembly.name.lower()
            dad_name = assembly.parent.name.lower()
            gloc_height = assembly.matrix_world.translation.z
            gloc_inches = self.to_inch(abs(gloc_height))
            # Hangs
            sss_name_one = 'shoe shelf stack' in name
            sss_name_two = 'slanted shoe shelves' in name
            sss_name_three = 'slanted shoe shelf' in name
            not_sss = 'shoe' not in name and 'slanted' not in name
            drw_ch_qty = self.check_for_drawer_children_in_shelves(assembly)
            if 'vertical' in name and 'splitters' in name:
                shelf_count += self.shelf_count_vertical_splitters(assembly)
            if 'hang' in name and 'hanging rod' not in name:
                shelves_dict = self.get_hang_shelves_count(assembly)
                has_any_hang = True
            if 'hang' in name and 'double' in name:
                tags.append(('DH', gloc_inches)) 
                shelf_count += shelves_dict["dust"]
            elif 'hang' in name and 'long' in name:
                tags.append(('LH', gloc_inches))
                shelf_count += shelves_dict["dust"]
                shelf_count += shelves_dict["top"]
            elif 'hang' in name and 'medium' in name:
                tags.append(('MH', gloc_inches))
                shelf_count += shelves_dict["dust"]
                shelf_count += shelves_dict["top"]
            elif 'hang' in name and 'short' in name:
                tags.append(('SH', gloc_inches))
                shelf_count += shelves_dict["dust"]
                shelf_count += shelves_dict["middle"]
            # Hampers
            elif 'hamper' in name:
                tags.append(('Hamp.', gloc_inches))
            # Shelves
            elif 'glass' in name:
                qty = self.get_glass_shelves_count(assembly)
                tag = qty + ' Glass Shlvs'
                tags.append((tag, gloc_inches))
            elif 'shelf' in name and not_sss and drw_ch_qty == 0:
                if not assembly.get("IS_BP_CLOSET_TOP"): 
                    opng_number = str(opening.sn_closets.opening_name)
                    parent_assy = sn_types.Assembly(assembly.parent) 
                    floor = parent_assy.get_prompt("Opening " + opng_number + " Floor Mounted")
                    is_floor_mounted = False

                    if floor:
                        is_floor_mounted = floor.get_value()

                    qty = self.get_shelf_stack_count(assembly)
                    rmvd_bottom_shelf = sn_types.Assembly(
                        assembly).get_prompt('Remove Bottom Shelf')
                    if rmvd_bottom_shelf:
                        is_rmvd = rmvd_bottom_shelf.get_value()
                        if is_rmvd and not is_floor_mounted:
                            shelf_count += (qty - 1)
                        elif is_rmvd and is_floor_mounted:
                            shelf_count += qty 
                        elif not is_rmvd:
                            shelf_count += qty
            elif sss_name_one or sss_name_two or sss_name_three:
                qty = self.get_sss_count(assembly)
                tag = qty + ' SSS'
                tags.append((tag, gloc_inches))
            # Doors
            elif 'doors' in name:
                tag = ()
                door_assy = sn_types.Assembly(assembly)
                door_height = door_assy.obj_z.location.z
                qty = self.get_door_count(assembly)
                shf_pmt = sn_types.Assembly(assembly).get_prompt('Add Shelves')
                shf_qty = sn_types.Assembly(assembly).get_prompt('Shelf Quantity')
                bot_kd = sn_types.Assembly(assembly).get_prompt('Bottom KD')
                door_type = sn_types.Assembly(
                    assembly).get_prompt('Door Type').get_value()
                hang_presumption = door_height > (opening_assembly_height / 2)
                # HACK we are presuming once there is a tall door and it is
                #      higher than the middle of respective opening, the hang
                #      is behind the door
                if hang_presumption and door_type == "Tall":
                    shelf_count -= 1
                if bot_kd:
                    if bot_kd.get_value():
                        shelf_count += 1
                if shf_pmt:
                    if shf_pmt.get_value():
                        if bot_kd:
                            shelf_count += shf_qty.get_value() - 1
                        else:
                            shelf_count += shf_qty.get_value()
                if qty == 1:
                    tag = ('1 Door', gloc_inches)
                else:
                    tag = ('2 Doors', gloc_inches)
                tags.append(tag)
            # Drawers
            elif 'drawer' in name and 'shelf' not in dad_name and drw_ch_qty == 0:
                hasnt_bottom_shf = self.check_sibling_shelf_stack_bottom_shelf(
                    assembly, assemblies)
                top_kd = sn_types.Assembly(assembly).get_prompt(
                    'Remove Top Shelf')
                if top_kd:
                    if top_kd.get_value() and hasnt_bottom_shf:
                        shelf_count += 1
                qty = self.get_drawer_count(assembly)
                tag = qty + ' Drws.'
                tags.append((tag, gloc_inches))
            elif drw_ch_qty > 0:
                tag = str(drw_ch_qty) + ' Drws.'
                tags.append((tag, gloc_inches))

        tags.sort(key=lambda x: x[1], reverse=True)

        if shelf_count > 1:
            shelf_tag = str(shelf_count) + " Shlvs."
            tags.insert(0, (shelf_tag, 0.0))
        elif shelf_count > 0:
            shelf_tag = str(shelf_count) + " Shelf"
            tags.insert(0, (shelf_tag, 0.0))
        return tags

    def find_matching_inserts(self, hanging_opening, location):
        def is_insert(obj):
            return hasattr(obj, 'snap') and obj.snap.type_group == 'INSERT'
        matches = []
        for child in hanging_opening.children:
            if is_insert(child):
                measure = self.to_inch(child.location[0])
                if measure == location:
                    matches.append(child)
                    for nested in child.children:
                        if is_insert(nested):
                            matches.append(nested)
                            for nested_a in nested.children:
                                if is_insert(nested_a):
                                    matches.append(nested_a)
        return matches

    def find_matching_topshelves(self, section, location, opening_at):
        hang_opng_obj = 'section' in section.name.lower()
        if not hang_opng_obj:
            return None
        result = []
        for child in section.children:
            if 'top shelf' in child.name.lower():
                tshelf_assy = sn_types.Assembly(child)
                section_assy = sn_types.Assembly(section)
                tshelf_x_loc = self.to_inch(child.location[0])
                section_width = self.to_inch(section_assy.obj_x.location.x)
                tshelf_width = self.to_inch(tshelf_assy.obj_x.location.x)
                tshelf_at_start = tshelf_x_loc == location
                tshelf_end_pos = tshelf_width + tshelf_x_loc
                tshelf_at_end = tshelf_end_pos == section_width
                if opening_at == 'MIN' and tshelf_at_start:
                    result.append(child)
                elif opening_at == 'MAX' and tshelf_at_end:
                    result.append(child)
        return result

    def find_matching_partitions(self, section, location, 
                                 op_width_metric, opening_at):
        op_width = self.to_inch(op_width_metric)
        cpart_width = 3
        hang_opng_obj = 'section' in section.name.lower()
        if not hang_opng_obj:
            return None
        if opening_at == 'MAX':
            location += op_width
        left_offset = location - cpart_width
        right_offset = location + cpart_width
        partitions = {}
        parts = []
        virtual_items = []
        virtual_parts = []
        next_ptt = None
        for child in section.children:
            if child.sn_closets.is_panel_bp:
                x_loc = self.to_inch(child.location[0])
                has_no_entry = partitions.get(x_loc) is None
                if has_no_entry:
                    partitions[x_loc] = child
                if left_offset <= x_loc <= right_offset and has_no_entry:
                    parts.append(child)
        partition_keys = sorted(partitions.keys())
        for item, value in enumerate(partition_keys):
            if left_offset <= value <= right_offset:
                next_ptt = None
                if opening_at == 'MIN' and len(partitions) > item + 1:
                    next_ptt = partitions.get(partition_keys[item + 1])
                elif opening_at == 'MAX':
                    next_ptt = partitions.get(partition_keys[item])
                if next_ptt is not None:
                    virtual_items.append(next_ptt)
        cross_parts = list(zip(parts, virtual_items))
        for part in cross_parts:
            x_offset = 0
            if opening_at == 'MAX':
                x_offset = op_width_metric + unit.inch(1.5)
            original_part = part[0]
            right_next_part = part[1]
            mesh = None
            original_part_assy = sn_types.Assembly(original_part)
            x_dim = abs(original_part_assy.obj_x.location.x)
            y_dim = abs(original_part_assy.obj_y.location.y)
            z_dim = abs(original_part_assy.obj_z.location.z)
            for obj in part[1].children:
                if obj.type == 'MESH':
                    mesh = obj
            part_dict = {"dimension": (x_dim, y_dim, z_dim),
                         "name": right_next_part.name,
                         "x_offset": x_offset,
                         "original": original_part.name,
                         "mesh": mesh,
                         }
            virtual_parts.append(part_dict)
        all_parts = (parts, virtual_parts)
        return all_parts

    def find_matching_toe_kick(self, section, location, opening_at):
        section_width = sn_types.Assembly(section).obj_x.location.x
        toe_kicks = []
        tlrnc = unit.inch(1.5)
        op_loc_metric = unit.inch(location)
        left_offset = op_loc_metric - tlrnc
        right_offset = op_loc_metric + tlrnc
        left_max_offset = (section_width - tlrnc)
        right_max_offset = (section_width + tlrnc)
        for child in section.children:
            if 'toe kick' in child.name.lower():
                tk_width = sn_types.Assembly(child).obj_x.location.x
                tk_x_loc = child.location[0]
                ending_tk = tk_width + tk_x_loc
                tk_at_start = left_offset <= tk_x_loc < right_offset
                tk_at_end = left_max_offset < ending_tk < right_max_offset
                if tk_at_start and opening_at == 'MIN':
                    toe_kicks.append(child)
                elif tk_at_end and opening_at == 'MAX':
                    toe_kicks.append(child)
                
        return toe_kicks

    def group_openings_by_euclidean_distance(self, tags_dict, wall_angle):
        positions_dict = {}
        groups = []
        group_max_distance = unit.inch(5)
        skip_on_merge = []
        # Fetch the global position of each opening, it will be compared in
        # X-axis later
        for opening, value in tags_dict.items():
            # Depending on wall angle, our "X-axis" is diferent.
            if wall_angle == 0:
                opng_x_pos = self.get_object_global_location(opening)[0]
                continue
            if wall_angle > 0:
                opng_x_pos = self.get_object_global_location(
                    opening)[0] * math.sin(wall_angle)
                continue
            if wall_angle < 0:
                opng_x_pos = self.get_object_global_location(
                    opening)[1] * math.cos(wall_angle)
                continue
            positions_dict[opening] = opng_x_pos
        # Now compare each opening with all others to find matching groups
        for opening, x_pos in positions_dict.items():
            for key, position in positions_dict.items():
                # get euclidean distance
                distance = abs(x_pos - position)
                # compare to get the ones that matters
                if opening != key and distance < group_max_distance:
                    local_group = []
                    local_group.append(opening.name)
                    local_group.append(key.name)
                    local_group.sort()
                    groups.append(local_group)
        results = list(set(tuple(sorted(group)) for group in groups))
        if len(groups) > 0:
            grouped_dict = {}
            for result in results:
                group_body = []
                heights = []
                openings = list(result)
                for opening in openings:
                    blender_obj = bpy.data.objects[opening]
                    global_height = self.get_object_global_location(
                        blender_obj)[2]
                    global_height_val = self.to_inch(global_height)
                    for tag in tags_dict[blender_obj][0]:
                        group_body.append(tag)
                    heights.append((blender_obj, global_height_val))
                    skip_on_merge.append(blender_obj.name)
                heights.sort(key=lambda x: x[1])
                desired_blender_obj = heights[0][0]
                associated_obj = tags_dict[desired_blender_obj][1]
                grouped_dict[desired_blender_obj] = (
                    group_body, associated_obj)
            skip_on_merge = list(set(skip_on_merge))
            for key, value in tags_dict.items():
                if key.name not in skip_on_merge:
                    grouped_dict[key] = value
            return grouped_dict
        return tags_dict

    def ts_support_corbel_pv_tag(self, item):
        label = "Corbelled Top Shelf"
        assy = sn_types.Assembly(item)
        assembly_below = assy.get_adjacent_assembly(direction='BELOW')

        if assembly_below and assembly_below.obj_bp.get("IS_BP_CLOSET"):
            return

        loc_x = assy.obj_x.location.x / 2
        loc_y = -assy.obj_y.location.y / 2

        label_offset = (abs(loc_y / 3) * 2) - unit.inch(1)
        parent_height = item.parent.location.z
        loc_z = -parent_height

        rotation = round(math.degrees(item.rotation_euler[2]))
        text = sn_types.Dimension()
        text.anchor.rotation_mode = 'YZX'
        text_rotation = (-90, -rotation, 0)
        if 0 < rotation <= 90:
            y_wall_angle = -rotation
            y_wall_angle += 90
            text_rotation = (0, y_wall_angle, 0)
        elif -90 <= rotation < 0:
            y_wall_angle = -rotation
            y_wall_angle -= 90
            text_rotation = (0, y_wall_angle, 0)

        text.set_label(label)
        utils.copy_world_loc(item, text.anchor, (loc_x, loc_y, loc_z))
        utils.copy_world_rot(item, text.anchor, text_rotation)
        if rotation in [90, 180]:
            text.anchor.location[1] -= label_offset
        elif rotation in [0,-90]:
            text.anchor.location[1] += label_offset
    
    def wallbed_pv_tag(self, item):
        assy = sn_types.Assembly(item)
        loc_x = assy.obj_x.location.x / 2
        loc_y = assy.obj_y.location.y / 2
        loc_offset = min([abs(loc_x), abs(loc_y)])
        label_offset = ((loc_offset / 3) * 2) - unit.inch(1)
        parent_height = item.parent.location.z
        loc_z = -parent_height
        wall_rotation = round(math.degrees(item.parent.rotation_euler[2]))
        text = sn_types.Dimension()
        text.anchor.rotation_mode = 'YZX'
        text_rotation = (-90, -wall_rotation, 0)
        label = str(item.name).replace("Wall Bed", "| Wall Bed")
        text.set_label(label)
        utils.copy_world_loc(item, text.anchor, (loc_x, loc_y, loc_z))
        utils.copy_world_rot(item, text.anchor, text_rotation)

    def strict_corner_pv_tag(self, item):
        label = ""
        assy = sn_types.Assembly(item)
        pmpt_dict = assy.get_prompt_dict()
        is_lsh = 'l shelves' in item.name.lower()
        is_csh = 'corner shelves' in item.name.lower()
        if is_lsh:
            shelf_pmpt = assy.get_prompt("Shelf Quantity")
            shelf_qty = shelf_pmpt.quantity_value
            has_door = pmpt_dict.get("Door")
            if has_door:
                assy_pmpt = assy.get_prompt("Door Type")
                door_type_list = [i.name for i in assy_pmpt.combobox_items]
                door_str = door_type_list[assy_pmpt.combobox_index]
                label = f'L Shelves|{shelf_qty} Shlvs.|{door_str} Door'
            elif not has_door:
                label = f'L Shelves|{shelf_qty} Shlvs.'
        elif is_csh:
            shelf_qty = pmpt_dict.get("Shelf Quantity")
            has_door = pmpt_dict.get("Door")
            double_doors_pmpt = assy.get_prompt("Force Double Doors") 
            double_doors = double_doors_pmpt.checkbox_value
            if has_door and not double_doors:
                label = f'Corner|Shelves|{shelf_qty} Shlvs.|1 Door'
            if has_door and double_doors:
                label = f'Corner|Shelves|{shelf_qty} Shlvs.|2 Doors'
            elif not has_door:
                label = f'Corner|Shelves|{shelf_qty} Shlvs.'
        loc_x = assy.obj_x.location.x / 2
        loc_y = assy.obj_y.location.y / 2
        loc_offset = min([abs(loc_x), abs(loc_y)])
        label_offset = ((loc_offset / 3) * 2) - unit.inch(1)
        parent_height = item.parent.location.z
        loc_z = -parent_height
        wall_rotation = round(math.degrees(item.parent.rotation_euler[2]))
        text = sn_types.Dimension()
        text.anchor.rotation_mode = 'YZX'
        text_rotation = (-90, -wall_rotation, 0)
        if 0 < wall_rotation <= 90:
            y_wall_angle = -wall_rotation
            y_wall_angle += 90
            text_rotation = (0, y_wall_angle, 0)
        elif -90 <= wall_rotation < 0:
            y_wall_angle = -wall_rotation
            y_wall_angle -= 90
            text_rotation = (0, y_wall_angle, 0)
        text.set_label(label)
        utils.copy_world_loc(item.parent, text.anchor, (loc_x, loc_y, loc_z))
        utils.copy_world_rot(item.parent, text.anchor, text_rotation)
        if wall_rotation in [90, 180]:
            text.anchor.location[1] -= label_offset
        elif wall_rotation in [0,-90]:
            text.anchor.location[1] += label_offset

    def is_closet_floor_mounted(self, closet):
        closet_assembly = sn_types.Assembly(obj_bp=closet)
        if closet_assembly.obj_bp.get("IS_BP_ISLAND"):
            return True

        is_clt_floor_mounted = True
        opening_qty =\
            closet_assembly.get_prompt("Opening Quantity").get_value()
        for i in range(1, opening_qty + 1):
            is_floor_mounted =\
                closet_assembly.get_prompt(
                    "Opening " + str(i) + " Floor Mounted").get_value()
            is_clt_floor_mounted = is_clt_floor_mounted and is_floor_mounted
        return is_clt_floor_mounted

    def is_closet_wall_mounted(self, closet):
        closet_assembly = sn_types.Assembly(obj_bp=closet)
        is_clt_wall_mounted = True
        opening_qty =\
            closet_assembly.get_prompt("Opening Quantity").get_value()
        for i in range(1, opening_qty + 1):
            is_wall_mounted =\
                not closet_assembly.get_prompt(
                    "Opening " + str(i) + " Floor Mounted").get_value()
            is_clt_wall_mounted = is_clt_wall_mounted and is_wall_mounted
        return is_clt_wall_mounted

    def is_wall_with_uppers_lowers(self, wall_assembly):
        closets_floor_mounted = 0
        closets_wall_mounted = 0
        children = wall_assembly.obj_bp.children
        for child in children:
            if 'section' in child.name.lower():
                is_floor_mounted = self.is_closet_floor_mounted(child)
                is_wall_mounted = self.is_closet_wall_mounted(child)
                if is_floor_mounted:
                    closets_floor_mounted += 1
                if is_wall_mounted:
                    closets_wall_mounted += 1
        if closets_floor_mounted == 1 and closets_wall_mounted == 1:
            return True
        else:
            return False

    def plan_view_products_labels(self, context, wall_assembly):
        tags_dict = {}
        wall = wall_assembly.obj_bp.children
        wall_angle = round(math.degrees(
            wall_assembly.obj_bp.rotation_euler[2]))
        for item in wall:
            is_lsh = 'l shelves' in item.name.lower()
            is_csh = 'corner shelves' in item.name.lower()
            if is_lsh or is_csh:
                self.strict_corner_pv_tag(item)
            elif item.get("IS_TOPSHELF_SUPPORT_CORBELS"):
                self.ts_support_corbel_pv_tag(item)
            elif sn_utils.get_wallbed_bp(item):
                self.wallbed_pv_tag(item)
            elif item.get('IS_BP_ASSEMBLY') and not is_lsh and not is_csh:
                for opening in item.children:
                    if hasattr(opening, 'snap') and opening.snap.type_group == 'OPENING':
                        opng_position = self.to_inch(opening.location[0])
                        matches = self.find_matching_inserts(item,
                                                             opng_position)
                        if (len(matches) > 0):
                            tags = self.get_assembly_tag(matches, opening)
                            tags_dict[opening] = (tags, matches)
        grouped = self.group_openings_by_euclidean_distance(
            tags_dict, wall_angle)
        for opening, value in grouped.items():
            tags = value[0]
            parent = value[1][0]
            self.apply_planview_opening_tag(wall_assembly, opening, tags, parent)

    def plan_view_hashmarks(self, context, walls_info):
        room_type = context.scene.sn_roombuilder.room_type
        walls_sort = sorted(walls_info, key=lambda x: x['wall'].name)
        heights = [w['obj_z'].location.z for w in walls_info]
        heights_mode = self.list_mode(heights)
        show_all_hashmarks = any(h != heights_mode for h in heights)

        hsh_len = unit.inch(4)
        lbl_off = unit.inch(1.75)

        for i, wall in enumerate(walls_sort):
            obj = wall['wall']
            obj_x = wall['obj_x']
            depth = wall['obj_y'].location.y
            height = wall['obj_z'].location.z

            hsh_rot = 45
            hsh_x = depth
            hsh_y = depth

            if room_type == 'CUSTOM':
                self.pv_pad += hsh_len * 0.375

                wall_mtx = obj.matrix_world
                obj_x_mtx = obj_x.matrix_world

                wall_pt_a_x, wall_pt_a_y = wall_mtx.translation[:2]
                wall_pt_b_x, wall_pt_b_y = obj_x_mtx.translation[:2]

                dx_wall = wall_pt_b_x - wall_pt_a_x
                dy_wall = wall_pt_b_y - wall_pt_a_y

                vec_wall = mathutils.Vector((dx_wall, dy_wall))

                if i + 1 < len(walls_info):
                    next_wall = walls_info[i + 1]['wall']
                    next_obj_x = walls_info[i + 1]['obj_x']

                    next_wall_mtx = next_wall.matrix_world
                    next_obj_x_mtx = next_obj_x.matrix_world

                    next_pt_a_x, next_pt_a_y = next_wall_mtx.translation[:2]
                    next_pt_b_x, next_pt_b_y = next_obj_x_mtx.translation[:2]

                    dx_next = next_pt_b_x - next_pt_a_x
                    dy_next = next_pt_b_y - next_pt_a_y

                    vec_next = mathutils.Vector((dx_next, dy_next))

                else:
                    vec_next = vec_wall

                if vec_next.length > 0:
                    vec_angle = vec_next.angle_signed(vec_wall)
                    turn_angle = round(math.degrees(vec_angle))

                    if turn_angle > 0:
                        hsh_rot *= -1
                        hsh_x = 0
                        hsh_y = 0

                    elif -90 < turn_angle <= 0:
                        hsh_x = 0

            elif room_type == 'SINGLE':
                self.pv_pad += hsh_len * 2
                hsh_x = 0

            hsh_loc = (hsh_x, hsh_y, height)

            hashmark = sn_types.Line(length=hsh_len, axis='X')
            hashmark.anchor.name = 'Hashmark_PV'
            utils.copy_world_loc(obj_x, hashmark.anchor, hsh_loc)
            utils.copy_world_rot(obj, hashmark.anchor, (0, 0, hsh_rot))

            text = sn_types.Dimension()
            text.parent(hashmark.end_point)
            text.set_label(self.to_inch_lbl(height))
            text.start_y(value=lbl_off)

            if not show_all_hashmarks:
                break
    
    def annotate_switchs_plan_view(self, context, wall, obj):
        # Add Outlets/Switched PV location
        wall_thickness = sn_types.Assembly(wall.obj_bp).obj_y.location.y
        wall_angle = round(math.degrees(wall.obj_bp.rotation_euler.z))
        text_label =\
            self.to_inch_lbl(obj.location.x) + " - " +\
            self.to_inch_lbl(obj.location.x + obj.dimensions[0])
        x_loc = obj.location.x + obj.dimensions[0] / 2
        y_loc = obj.location.y 
        z_loc = wall.obj_z.location.z
        text = sn_types.Dimension()
        text.anchor.rotation_mode = 'YZX'
        text.parent(wall.obj_bp)
        text.start_x(value=x_loc)
        text.start_y(value=y_loc + unit.inch(9))
        text.start_z(value=z_loc)
        lbl_rot_x = math.radians(-90)
        if wall_angle == 180:
            lbl_rot_y = 0
        else:
            lbl_rot_y = math.radians(-wall_angle)
        text.anchor.rotation_euler = (lbl_rot_x, lbl_rot_y, 0)
        text.set_label(text_label)
        self.ignore_obj_list.append(text.anchor)
        self.ignore_obj_list.append(text.end_point)
        # Draw Outlet/Switch Circle on PV location
        cyl_y = y_loc + wall_thickness / 2
        cyl_radius = (wall_thickness / 2) * 0.9
        bpy.ops.mesh.primitive_cylinder_add(
            radius=cyl_radius,
            depth=0.001,
            location=(x_loc, cyl_y, z_loc),
            rotation=(0,0,0)
        )
        cyl = context.active_object
        cyl.parent = wall.obj_bp


    def plan_view_add_switches(self, context, wall):
        wall_children = wall.obj_bp.children
        for obj in wall_children:
            name = obj.name
            split_name = name.split(".")
            category = split_name[0]
            if category == "Outlets and Switches":
                self.annotate_switchs_plan_view(context, wall, obj)

    def add_island_to_plan_view(self, island):
        island_assembly = sn_types.Assembly(obj_bp=island)
        dim_x = island_assembly.obj_x.location.x
        dim_y = island_assembly.obj_y.location.y
        dim_z = island_assembly.obj_z.location.z

        cube_dims = (dim_x, dim_y, dim_z)
        x_loc, y_loc, z_loc = island.location

        island_mesh = utils.create_cube_mesh(
            island.name, cube_dims)
        island_mesh.parent = island.parent
        island_mesh.location = (x_loc, y_loc, z_loc)
        island_mesh.rotation_euler = island.rotation_euler
        island_mesh['IS_CAGE'] = True

    def link_children_to_scene(self, scene, obj_bp):
        scene.collection.objects.link(obj_bp)
        for child in obj_bp.children:
            self.link_children_to_scene(scene, child)

    def get_island_corners(self, island):
        island_assembly = sn_types.Assembly(obj_bp=island)
        dim_x = abs(island_assembly.obj_x.location.x)
        dim_y = abs(island_assembly.obj_y.location.y)
        loc_x = island.location.x
        loc_y = island.location.y
        theta = island.rotation_euler.z
        p1_x = loc_x + dim_y*np.sin(theta)
        p1_y = loc_y - dim_y*np.cos(theta)
        p2_x = loc_x + dim_y*np.sin(theta) + dim_x*np.cos(theta)
        p2_y = p1_y + dim_x*np.sin(theta)
        p3_x = loc_x + dim_x*np.cos(theta)
        p3_y = loc_y + dim_x*np.sin(theta)
        p4_x = loc_x
        p4_y = loc_y
        return [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y), (p4_x, p4_y)]

    def pv_wall_labels(self, wall):
        x_loc = self.wall_largest_part_xloc(wall)
        wall_width = wall.obj_x.location.x
        if wall_width > 0.0:
            wall_depth = wall.obj_y.location.y
            wall_height = wall.obj_z.location.z
            wall_angle = round(math.degrees(wall.obj_bp.rotation_euler.z))

            # Dimension line
            dim = sn_types.Dimension()
            dim_label = f'{self.to_inch_str(wall_width)}"'
            dim.parent(wall.obj_bp)
            if wall_angle == 180:
                dim.start_x(value=wall_width)
                dim.end_x(value=-wall_width)
            else:
                dim.end_x(value=wall_width)
            dim.start_y(value=unit.inch(4) + wall_depth)
            dim.start_z(value=wall_height + unit.inch(8))
            dim.set_label(dim_label)

            self.ignore_obj_list.append(dim.anchor)
            self.ignore_obj_list.append(dim.end_point)

            # Wall name label
            wall_label = sn_types.Dimension()
            # Rotation mode for anchor needs to be changed to allow
            # Y-axis rotation in Plan View
            wall_label.anchor.rotation_mode = 'YZX'
            wall_label.parent(wall.obj_bp)
            if not x_loc:
                wall_label.start_x(value=wall_width / 2)
            elif x_loc:
                wall_label.start_x(value=x_loc)
            wall_label.start_y(value=wall_depth / 2)
            wall_label.start_z(value=wall_height)
            lbl_rot_x = math.radians(-90)
            if wall_angle == 180:
                lbl_rot_y = 0
            else:
                lbl_rot_y = math.radians(-wall_angle)
            wall_label.anchor.rotation_euler = (lbl_rot_x, lbl_rot_y, 0)
            wall_label.set_label(wall.obj_bp.snap.name_object)

    def wall_largest_part_xloc(self, wall):
        wall_ch = wall.obj_bp.children
        wall_start, wall_end = 0, round(wall.obj_x.location.x, 2)
        entries_data = []
        wall_segments = []
        entries = [c for c in wall_ch if c.get('IS_BP_ENTRY_DOOR')]
        if len(entries) == 0:
            return None
        for entry in entries:
            entry_assy = sn_types.Assembly(entry)
            if entry_assy:
                door_width = entry_assy.obj_x.location.x
                door_start = entry.location[0]
                door_end = door_start + door_width
                door_start, door_end = round(door_start, 2), round(door_end, 2) 
                entries_data.append((door_start, door_end))
        entries_data = sorted(entries_data, key=lambda tup: tup[0])
        if len(entries_data) == 0:
            return None
        for i, datum in enumerate(entries_data):
            entry_start, entry_end = datum
            if len(wall_segments) == 0:
                wall_segments.append((wall_start, entry_start))
            if len(wall_segments) > 0 and i < len(entries_data) - 1:
                next_entry_start, _ = entries_data[i+1]
                wall_segments.append((entry_end, next_entry_start))
            if len(wall_segments) > 0 and i == len(entries_data) - 1:
                wall_segments.append((entry_end, wall_end))
        largest_space = 0
        x_loc = 0
        for segment in wall_segments:
            start, end = segment
            segment_space = end - start
            if segment_space > largest_space:
                largest_space = segment_space
                x_loc = round(((end - start) / 2) + start, 2)
        return x_loc

    def add_plan_view_cages(self, wall, obj_bp):
        pv_parts = []
        obj_bp_chldrn = obj_bp.children
        self.pv_cage(wall, obj_bp)
        if len(obj_bp_chldrn) > 0:
            for ch in obj_bp_chldrn:
                is_partition = ch.sn_closets.is_panel_bp
                is_opening = 'opening' in ch.name.lower()
                if is_partition or is_opening:
                    self.pv_cage(wall, ch)
                    pv_parts.append(ch)
        undesired_scene_objs = []
        for obj in bpy.context.scene.collection.objects:
            is_blind_corner = 'blind corner' in obj.name.lower()
            not_already_in = obj.name not in undesired_scene_objs
            if is_blind_corner and not_already_in:
                undesired_scene_objs.append(obj.name)
        for obj_name in undesired_scene_objs:
            bpy.data.objects[obj_name].hide_viewport = True
            bpy.data.objects[obj_name].hide_render = True

    def pv_cage(self, wall, obj_bp):
        assembly = sn_types.Assembly(obj_bp)
        object_name = assembly.obj_bp.snap.name_object
        mesh_location = (assembly.obj_x.location.x,
                         assembly.obj_y.location.y,
                         assembly.obj_z.location.z)
        assembly_mesh = utils.create_cube_mesh(object_name, mesh_location)
        assembly_mesh.parent = wall.obj_bp
        assembly_mesh.location = assembly.obj_bp.location
        assembly_mesh.rotation_euler = assembly.obj_bp.rotation_euler
        assembly_mesh['IS_CAGE'] = True

    def return_wall_labels(self, entry_wall, entry_door, elv=False, acc=False):
        wall_assy = sn_types.Assembly(entry_wall)
        door_assy = sn_types.Assembly(entry_door)

        wall_a = wall_assy.obj_x
        door_a = door_assy.obj_x
        door_b = door_assy.obj_bp
        wall_b = wall_assy.obj_bp
        door_h = door_assy.obj_z

        dims_pts = [[wall_a, door_a], [door_a, door_b], [door_b, wall_b]]

        py, pz = 0, 0
        pz = wall_assy.obj_z.location.z + unit.inch(4)

        if elv:
            door_h_dim = sn_types.Dimension()
            door_h_dim_loc = (door_a.location.x - unit.inch(10), 0, 0)
            utils.copy_world_loc(door_h, door_h_dim.anchor, door_h_dim_loc)
            utils.copy_world_loc(door_b, door_h_dim.end_point, door_h_dim_loc)
            door_h_lbl = self.to_inch_lbl(abs(door_h_dim.end_point.location.z))
            door_h_dim.set_label(door_h_lbl)

            for d in dims_pts:
                d.reverse()
            pz = wall_assy.obj_z.location.z + unit.inch(4)
        elif acc:
            door_h_dim = sn_types.Dimension()
            door_h_dim_loc = (door_a.location.x - unit.inch(10), 0, 0)
            utils.copy_world_loc(door_b, door_h_dim.anchor, door_h_dim_loc)
            utils.copy_world_loc(door_b, door_h_dim.end_point, door_h_dim_loc)
            door_h_dim.end_point.location.z = door_h.location.z
            door_h_lbl = self.to_inch_lbl(abs(door_h_dim.end_point.location.z))
            door_h_dim.set_label(door_h_lbl)

            for d in dims_pts:
                d.reverse()
            pz = wall_assy.obj_z.location.z + unit.inch(4)
        else:
            py = wall_assy.obj_y.location.y + unit.inch(14)

        if not elv and not acc:
            wall_b_offset = door_a.location[0] + door_b.location[0]
            wall_b_width = wall_a.location[0] - wall_b_offset
            self.pv_break_dim(entry_wall, door_b.location[0], 0)
            self.pv_break_dim(entry_wall, door_a.location[0], 
                              door_b.location[0])
            self.pv_break_dim(entry_wall, wall_b_width, wall_b_offset)
        elif elv or acc:
            for d in dims_pts:
                dim = sn_types.Dimension()
                dim_loc = (0, py, pz)
                utils.copy_world_loc(d[0], dim.anchor, dim_loc)
                utils.copy_world_loc(d[1], dim.end_point, dim_loc)
                dim_lbl = self.to_inch_lbl(abs(dim.end_point.location.x))
                dim.set_label(dim_lbl)
                self.ignore_obj_list.append(dim.anchor)
                self.ignore_obj_list.append(dim.end_point)


    def pv_break_dim(self, entry_wall, width, x_offset):
        mesh_thickness = 0.001
        wall_brk = sn_utils.create_floor_mesh("pv_wallbreak_msh", 
                                             (width, mesh_thickness))
        wall_brk.rotation_euler[0] = math.radians(-90)
        wall_brk.location[0] = x_offset
        wall_brk.location[1] = unit.inch(20)
        wall_brk.parent = entry_wall
        wall_brk_dim = sn_types.Dimension()
        wall_brk_dim.anchor.parent = wall_brk
        wall_brk_dim.start_x(value = 0)
        wall_brk_dim.end_x(value = width)
        wall_brk_dim.set_label(" ")
        lbl_dim = sn_types.Dimension()
        lbl_dim.anchor.parent = wall_brk_dim.anchor
        lbl_dim.start_x(value = wall_brk.dimensions[0] / 2)
        lbl_dim.start_z(value = unit.inch(-1.5))
        lbl_dim.set_label(self.to_inch_lbl(wall_brk.dimensions[0]))
        self.ignore_obj_list.append(wall_brk_dim.anchor)
        self.ignore_obj_list.append(wall_brk_dim.end_point)
        self.ignore_obj_list.append(lbl_dim.anchor)
        self.ignore_obj_list.append(lbl_dim.end_point)

    def pv_return_wall_break(self, wall_mesh, wall_assy, entry_door_bp):
        entry_assy = sn_types.Assembly(entry_door_bp)

        bool_grow = unit.inch(0.125)
        break_w = entry_assy.obj_x.location.x
        break_d = wall_assy.obj_y.location.y + (bool_grow * 2)
        break_h = wall_assy.obj_z.location.z + (bool_grow * 2)
        break_size = (break_w, break_d, break_h)

        entry_break_mesh = utils.create_cube_mesh('PV Entry Break', break_size)
        entry_break_mesh.snap.type = 'CAGE'
        entry_break_mesh.parent = entry_door_bp
        entry_break_mesh.location = (0, -bool_grow, -bool_grow)
        entry_break_mesh.hide_viewport = True
        entry_break_mesh.hide_render = True

        bool_modifier = [m for m in wall_mesh.modifiers if 'MESH' in m.name][0]
        bool_modifier.object = entry_break_mesh

    def plan_view_cleats_accys(self, obj_bp, scene):
        all_child = utils.get_child_objects(obj_bp)
        meshes = [c for c in all_child if c.type == 'MESH'
                  and not c.hide_viewport]
        for m in meshes:
            scene.collection.objects.link(m)

    def plan_view_ts_corbels(self, obj_bp, scene):
        """Adds topshelf support corbels to plan view scene"""
        all_child = utils.get_child_objects(obj_bp)
        topshelf = [c for c in all_child if "IS_BP_CLOSET_TOP" in c.parent and c.type == 'MESH'][0]
        if topshelf:
            scene.collection.objects.link(topshelf)

    def create_plan_view_scene(self, context):
        WIDE_ROOM_THRES = 200 # 200 inches
        SMALL_ROOM_THRES = 100
        room_type = context.scene.sn_roombuilder.room_type
        bpy.ops.scene.new('INVOKE_DEFAULT', type='EMPTY')
        pv_scene = context.scene
        pv_scene.name = "Plan View"
        pv_scene.snap.name_scene = "Plan View"
        pv_scene.snap.scene_type = 'PLAN_VIEW'
        self.create_linesets(pv_scene)
        walls_info = []
        grp = bpy.data.collections.new("Plan View")
        walls = []
        for obj in self.main_scene.objects:
            # Add Floor and Ceiling Obstacles to Plan View
            if obj.get('IS_OBSTACLE') and obj.get('SHOW_ON_PLANVIEW', True):
                pv_scene.collection.objects.link(obj)
                for child in obj.children:
                    pv_scene.collection.objects.link(child)
                    child.hide_render = False

            if obj.get("IS_BP_WALL"):
                wall = sn_types.Wall(obj_bp=obj)
                rtn_wall_pv = None
                has_entry = any('Door Frame' in e.name for c in obj.children
                                for e in c.children)
                pv_scene.collection.objects.link(obj)
                # Only link all of the wall meshes
                for child in obj.children:
                    if child.snap.is_wall_mesh:
                        walls_info.append({'wall': obj,
                                           'obj_x': wall.obj_x,
                                           'obj_y': wall.obj_y,
                                           'obj_z': wall.obj_z})
                        if has_entry:
                            rtn_wall_pv = child.copy()
                            rtn_wall_pv.data = child.data.copy()
                            rtn_wall_pv.name = 'Return Wall PV'
                            rtn_wall_pv.snap.is_wall_mesh = False
                            rtn_wall_pv.parent = None
                            utils.copy_world_loc(obj, rtn_wall_pv)
                            pv_scene.collection.objects.link(rtn_wall_pv)
                        else:
                            pv_scene.collection.objects.link(child)
                            grp.objects.link(child)
                            child.select_set(True)

                walls.append(wall)

                self.plan_view_products_labels(context, wall)
                self.plan_view_add_switches(context, wall)

                # Add countertop cutparts to plan view
                for child in obj.children:
                    for item in child.children:
                        if item.sn_closets.is_counter_top_insert_bp:
                            for c in item.children:
                                for cc in c.children:
                                    if not cc.hide_viewport:
                                        cube_dims = cc.dimensions
                                        altered_dims = (cube_dims[0] + unit.inch(0.06),
                                                        cube_dims[1],
                                                        cube_dims[2])
                                        parent_assy = sn_types.Assembly(c)
                                        x_loc = 0 - unit.inch(0.03)
                                        y_loc = parent_assy.obj_y.location.y
                                        z_loc = cc.parent.parent.location[2] * -1
                                        ctop_mesh = utils.create_cube_mesh(
                                            cc.name, altered_dims)
                                        ctop_mesh.parent = cc.parent
                                        ctop_mesh.location = (x_loc,
                                                              y_loc,
                                                              z_loc)
                                        ctop_mesh.rotation_euler = cc.rotation_euler
                                        ctop_mesh['IS_CAGE'] = True

                if wall.obj_bp and wall.obj_x and wall.obj_y and wall.obj_z:
                    self.pv_wall_labels(wall)
                    obj_bps = wall.get_wall_groups()
                    wall_mesh = wall.get_wall_mesh()
                    # Create Cubes for all products
                    for obj_bp in obj_bps:
                        if obj_bp.get("IS_BP_CABINET"):
                            eval('bpy.ops.sn_cabinets.draw_plan' + '(object_name=obj_bp.name)')
                        else:
                            eval('bpy.ops.sn_closets.draw_plan' + '(object_name=obj_bp.name)')
                        is_entry_assy = any('Door Frame' in e.name for c in
                                            obj_bp.children for e in c.children)

                        if is_entry_assy and rtn_wall_pv:
                            self.pv_return_wall_break(rtn_wall_pv, wall, obj_bp)
                            self.return_wall_labels(wall.obj_bp, obj_bp)

                            # Add icons for entry doors
                            entry_class = obj_bp.snap.class_name
                            entry_sgl = 'PRODUCT_Entry_Door_Double_Panel'
                            entry_dbl = 'PRODUCT_Entry_Double_Door_Double_Panel'
                            swing_door = ((entry_class == entry_sgl) or
                                          (entry_class == entry_dbl))
                            if swing_door:
                                view_icons.pv_swing_door_icons(
                                    context, obj_bp, wall.obj_bp)

                        if (obj_bp.sn_closets.is_accessory_bp or
                           'wall cleat' in obj_bp.name.lower()):
                            self.plan_view_cleats_accys(obj_bp, pv_scene)

                        if obj_bp.get("IS_TOPSHELF_SUPPORT_CORBELS"):
                            self.plan_view_ts_corbels(obj_bp, pv_scene)

                    if wall and wall_mesh:
                        if wall_mesh.name in context.scene.objects:
                            wall_mesh.select_set(True)

            name = obj.name
            if "Island" in name:
                self.add_pulls_to_plan_view(obj, pv_scene)
                self.add_island_to_plan_view(obj)

        for obj in self.main_scene.collection.objects:
            self.link_tagged_dims_to_plan_view(obj, pv_scene)

        self.plan_view_hashmarks(context, walls_info)
        floor = [o for o in bpy.data.objects if o.sn_roombuilder.is_floor][0]
        x_axis_len = floor.dimensions[0]
        y_axis_len = floor.dimensions[1]
        floor_length = unit.meter_to_inch(x_axis_len)
        floor_height = unit.meter_to_inch(y_axis_len)
        wide_room = floor_length > WIDE_ROOM_THRES or floor_height > WIDE_ROOM_THRES
        small_room = floor_length <= SMALL_ROOM_THRES or floor_height <= SMALL_ROOM_THRES
        camera = self.create_camera(pv_scene)
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.view3d.camera_to_view_selected()
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale += self.pv_pad
        custom_wide = room_type == 'CUSTOM' and wide_room
        square_tall = room_type == 'SQUARE' and floor_height > floor_length 
        if room_type == 'USHAPE':
            camera.data.ortho_scale += 1
        elif not custom_wide and small_room:
            camera.data.ortho_scale = self.pv_pad
        elif custom_wide or square_tall:
            width_ratio = 1
            wider_measure = max([x_axis_len, y_axis_len])
            if wider_measure == y_axis_len:
                x_resolution = pv_scene.render.resolution_x
                y_resolution = pv_scene.render.resolution_y
                width_ratio = x_resolution / y_resolution
            scene_width = width_ratio * wider_measure
            ratio = self.planview_orthoscale_ratio(scene_width)
            camera.data.ortho_scale = ratio



    def add_pulls_to_plan_view(self, obj, pv_scene):
        children = obj.children
        for child in children:
            child_assembly = sn_types.Assembly(obj_bp=child)
            pull_len = child_assembly.get_prompt("Pull Length")
            is_pull = pull_len is not None
            is_door =\
                "Drawer Face" in child.name or "Hamper Door" in child.name
            if is_pull or is_door:
                self.add_pulls_to_plan_view(child, pv_scene)
                for item in child.children:
                    if "Mesh" in item.name and is_door:
                        pv_scene.collection.objects.link(item)
                    elif is_pull and "OBJ" not in item.name:
                        pv_scene.collection.objects.link(item)
            else:
                self.add_pulls_to_plan_view(child, pv_scene)

    def link_tagged_dims_to_plan_view(self, obj, pv_scene):
        children = obj.children
        for child in children:
            if child.snap.comment == "render_plan":
                pv_scene.collection.objects.link(obj)
                pv_scene.collection.objects.link(child)
            if len(child.children) > 0:
                self.link_tagged_dims_to_plan_view(child, pv_scene)

    def get_walls_joints(self, walls):
        wall_joints = {}
        joints = []
        first_wall = [wall[0] for wall in walls][0]
        last_wall = [wall[0] for wall in walls][-1]
        # Getting wall connections
        connected_walls = [[wall for wall in group if wall is not None]
                           for group in walls]
        [connected_walls.remove(conn)
         for conn in connected_walls if len(conn) == 1]
        for conn in connected_walls:
            current_wall = round(math.degrees(
                conn[0].obj_bp.rotation_euler[2]))
            previous_wall = round(math.degrees(
                conn[1].obj_bp.rotation_euler[2]))
            cnctd_wall_angle_check = (
                previous_wall - current_wall) in [90, -270]
            # To know if a corner is a right angle the subtraction between
            # the previous and the current wall need to be 90 or -270 degrees
            if cnctd_wall_angle_check:
                joints.append((conn[0].obj_bp, conn[1].obj_bp))
        joints.append((first_wall.obj_bp, last_wall.obj_bp))
        wall_joints["first_wall"] = first_wall.obj_bp
        wall_joints["last_wall"] = last_wall.obj_bp
        wall_joints["joints"] = joints
        if len(joints) > 0:
            return wall_joints
        if len(joints) == 0:
            return None

    def get_lsh_csh_assemblies(self, wall):
        assemblies = []
        for candidate in wall.children:
            if 'corner shelves' in candidate.name.lower():
                assemblies.append(candidate)
            if 'triangle shelves' in candidate.name.lower():
                assemblies.append(candidate)
            if 'l shelves' in candidate.name.lower():
                assemblies.append(candidate)
        if len(assemblies) > 0:
            return assemblies
        if len(assemblies) == 0:
            return None

    def get_wall_sections_assemblies(self, wall):
        assemblies = []
        for candidate in wall.children:
            if 'section' in candidate.name.lower():
                assemblies.append(candidate)
        if len(assemblies) > 0:
            return assemblies
        if len(assemblies) == 0:
            return None

    def lookup_openings_at_same_position(self, assembly,
                                         lookup_position,
                                         opening_at, comparing_opening):
        # As we get the sections, it's parent is the wall
        # we are looking for other openings at the same wall that start
        # or end at the same position of assembly
        cmprg_parent_loc = comparing_opening.parent.location[0]
        ptt_thick = 0.75
        gap = unit.inch(3)
        wall = assembly.parent
        sections = []
        for child in wall.children:
            section = 'section' in child.name.lower()
            if section:
                sections.append(child)
        if len(sections) > 1:
            for each in sections:
                openings = []
                if each is not assembly:
                    for opening_ch in each.children:
                        if opening_ch.snap.type_group == 'OPENING':
                            x_loc = self.to_inch(opening_ch.location[0])
                            openings.append((x_loc, opening_ch))
                    openings = sorted(openings, key=lambda tup: tup[0])
                    for opening in openings:
                        position, part = opening
                        opening_parent_loc = part.parent.location[0]
                        opng_assy = sn_types.Assembly(part)
                        opng_width = self.to_inch(opng_assy.obj_x.location.x)
                        opening_start = position
                        opening_end = round(position + opng_width + ptt_thick,
                                            2)
                        above_bellow = abs(cmprg_parent_loc - opening_parent_loc) < gap
                        same_start = opening_start == (lookup_position + ptt_thick)
                        same_end = opening_end == lookup_position
                        if opening_at == 'MIN' and same_start and above_bellow:
                            return part
                        if opening_at == 'MAX' and same_end and above_bellow:
                            return part
        return None
        
    def get_opening_parts(self, assembly, opening_at, lookup_position):
        openings = []
        for child in assembly.children:
            if child.snap.type_group == 'OPENING':
                x_loc = self.to_inch(child.location[0])
                openings.append((x_loc, child))
        openings = sorted(openings, key=lambda tup: tup[0])
        if len(openings) > 0 and opening_at == 'MIN':
            desired_opening = openings[0][1]
            result = self.lookup_openings_at_same_position(assembly,
                                                           lookup_position,
                                                           opening_at,
                                                           desired_opening)
            if result is not None:
                return [desired_opening, result]
            elif result is None:
                return [desired_opening]
        elif len(openings) > 0 and opening_at == 'MAX':
            desired_opening = openings[-1][1]
            result = self.lookup_openings_at_same_position(assembly,
                                                           lookup_position,
                                                           opening_at,
                                                           desired_opening)
            if result is not None:
                return [desired_opening, result]
            elif result is None:
                return [desired_opening]
        return None

    def get_assembly_parts(self, assembly, opening_at, lookup_pos):
        parts = []
        virtual_parts = []
        # Partition standard cutpart in inches
        cpart_width = 0.75
        if opening_at not in ('MIN', 'MAX'):
            return
        section = 'section' in assembly.name.lower()
        # corner_shelves = 'corner shelves' in assembly.name.lower()
        # l_shelves = 'l shelves' in assembly.name.lower()
        # triangular_shelves = 'corner shelves' in assembly.name.lower()
        if section:
            opng_parts = self.get_opening_parts(assembly,
                                                opening_at,
                                                lookup_pos)
            if opng_parts is not None:
                result_parts = []
                insert_parts = []
                top_shelves_parts = []
                partition_parts = []
                toe_kicks_parts = []
                partitions, virtual_partitions = None, None
                for part in opng_parts:
                    part_pos = abs(self.to_inch(part.location[0]))
                    part_width_m = sn_types.Assembly(part).obj_x.location.x
                    ts_pos = abs(self.to_inch(part.location[0]) - cpart_width)
                    inserts = self.find_matching_inserts(part.parent, part_pos)
                    top_shelves = self.find_matching_topshelves(part.parent,
                                                                ts_pos,
                                                                opening_at)
                    all_partitions = self.find_matching_partitions(part.parent,
                                                                   part_pos,
                                                                   part_width_m,
                                                                   opening_at)
                    if all_partitions is not None:
                        partitions, virtual_partitions = all_partitions 
                    elif all_partitions is None:
                        partitions, virtual_partitions = None, None
                    toe_kicks = self.find_matching_toe_kick(part.parent, 
                                                            part_pos,
                                                            opening_at)
                    for insert in inserts:
                        insert_parts.append(insert)
                    for top_shelf in top_shelves:
                        top_shelves_parts.append(top_shelf)
                    for partition in partitions:
                        partition_parts.append(partition)
                    for tk in toe_kicks:
                        toe_kicks_parts.append(tk)
                opng_parts.append(spread(partition_parts))
                opng_parts.append(spread(top_shelves_parts))
                opng_parts.append(spread(insert_parts))
                opng_parts.append(spread(toe_kicks_parts))
                result_parts = spread(opng_parts)
                parts.append(result_parts)
                virtual_parts.append(spread(virtual_partitions))
        # if corner_shelves or l_shelves or triangular_shelves:
        #     parts.append(assembly)
        result = parts, virtual_parts
        return result

    def get_partition_max_depth(self, parts):
        depths = []
        for part in parts:
            if part.sn_closets.is_panel_bp:
                ptt_assy = sn_types.Assembly(part)
                ptt_depth = abs(ptt_assy.obj_y.location.y)
                depths.append((ptt_depth, part))
            # if 'corner shelves' in part.name.lower():
            #     csh_assy = sn_types.Assembly(part)
            #     csh_depth = abs(csh_assy.obj_y.location.y)
            #     depths.append((csh_depth, part))
            # if 'l shelves' in part.name.lower():
            #     lsh_assy = sn_types.Assembly(part)
            #     lsh_depth = abs(lsh_assy.obj_y.location.y)
            #     depths.append((lsh_depth, part))
        if len(depths) > 0:
            result = sorted(depths, key=lambda tup: tup[0])
            deepest_partition = self.to_inch(result[-1][0])
            return deepest_partition
        return None

    def get_assy_min_max_loc(self, assemblies):
        assy_loc_dict = {}
        if assemblies is None:
            return (None, None)
        for assembly in assemblies:
            assy_obj = sn_types.Assembly(assembly)
            assy_width = self.to_inch(assy_obj.obj_x.location.x)
            start_position = self.to_inch(assembly.location[0])
            end_position = start_position + assy_width
            assy_loc_dict[start_position] = assembly
            assy_loc_dict[end_position] = assembly
        if len(assy_loc_dict) > 0:
            parts, virtual_parts = None, None
            min_assembly_loc = min(assy_loc_dict.items(), key=lambda x: x[0])
            # Assemblies at min position (start of wall)
            min_assy = sn_types.Assembly(min_assembly_loc[1])
            min_assy_width = self.to_inch(min_assy.obj_x.location.x)
            min_assy_start = self.to_inch(min_assembly_loc[1].location[0])
            min_assy_end = min_assy_start + min_assy_width
            min_assy_data = {}
            min_assy_data["start"] = min_assy_start
            min_assy_data["end"] = min_assy_end
            min_assy_data["width"] = min_assy_width
            result = self.get_assembly_parts(min_assembly_loc[1],
                                             'MIN', min_assy_data["start"])
            if result is not None:
                parts, virtual_parts = result
            if virtual_parts is None or len(virtual_parts) == 0:
                min_assy_data["virtual_parts"] = []
            min_assy_data["parts"] = spread(parts)
            min_assy_data["virtual_parts"] = spread(virtual_parts)
            pieces = min_assy_data["parts"]
            min_assy_data["depth"] = self.get_partition_max_depth(pieces)
            # Assemblies at max position (end of wall)
            max_assembly_loc = max(assy_loc_dict.items(), key=lambda x: x[0])
            max_assy = sn_types.Assembly(max_assembly_loc[1])
            max_assy_width = self.to_inch(max_assy.obj_x.location.x)
            max_assy_start = self.to_inch(max_assembly_loc[1].location[0])
            max_assy_end = max_assy_start + max_assy_width
            max_assy_data = {}
            max_assy_data["start"] = max_assy_start
            max_assy_data["end"] = max_assy_end
            max_assy_data["width"] = max_assy_width
            result = self.get_assembly_parts(max_assembly_loc[1],
                                             'MAX', max_assy_data["end"])
            if result is not None:
                parts, virtual_parts = result
            if virtual_parts is None or len(virtual_parts) == 0:
                max_assy_data["virtual_parts"] = []
            max_assy_data["parts"] = spread(parts)
            max_assy_data["virtual_parts"] = spread(virtual_parts)
            pieces = max_assy_data["parts"]
            max_assy_data["depth"] = self.get_partition_max_depth(pieces)
            return (min_assy_data, max_assy_data)
        if len(assy_loc_dict) == 0:
            return (None, None)

    def get_walls_assys_arrangement(self, walls_groups):
        assemblies = {}
        for wall_name in walls_groups.keys():
            real_wall_name = wall_name.replace("CSwall-", "")
            if real_wall_name in bpy.data.objects:
                wall_obj = bpy.data.objects[real_wall_name]
                wall_assemblies = self.get_wall_sections_assemblies(wall_obj)
                wall_width = sn_types.Assembly(wall_obj).obj_x.location.x
                min_assy, max_assy = self.get_assy_min_max_loc(wall_assemblies)
                assemblies[wall_obj] = {}
                assemblies[wall_obj]["width"] = self.to_inch(wall_width)
                assemblies[wall_obj]["min_loc_data"] = min_assy
                assemblies[wall_obj]["max_loc_data"] = max_assy
        if len(assemblies) > 0:
            return assemblies
        if len(assemblies) == 0:
            return None
    
    def get_joint_parts(self, current_wall, left_wall, assemblies_dict):
        offset = 6
        current_wall_record = assemblies_dict.get(current_wall)
        left_wall_record = assemblies_dict.get(left_wall)
        if current_wall_record is None and left_wall_record is None:
            return None
        # finding the crosses
        if current_wall_record is not None and left_wall_record is not None:
            current_wall_data = current_wall_record.get("min_loc_data")
            left_wall_data = left_wall_record.get("max_loc_data")

            if current_wall_data is not None and left_wall_data is None:
                left_wall_width = left_wall_record.get("width")
                return (left_wall, left_wall_width, current_wall_data["parts"])
            
            if left_wall_data is not None and current_wall_data is None:
                return (current_wall, 0.0, left_wall_data["parts"])

            if current_wall_data is not None and left_wall_data is not None:
                current_assy_start = current_wall_data.get("start")
                current_assy_depth = current_wall_data.get("depth")
                left_wall_width = left_wall_record.get("width")
                left_assy_end = left_wall_data.get("end")
                left_assy_depth = left_wall_data.get("depth")

                left_avail_space = (left_wall_width - left_assy_end)
                slot_at_current = left_assy_depth <= current_assy_start
                slot_at_left = left_avail_space >= current_assy_depth
                if slot_at_current and left_avail_space <= offset:
                    return (current_wall, 
                            0.0, 
                            left_wall_data["parts"])
                if slot_at_left and current_assy_start <= offset:
                    return (left_wall, 
                            left_wall_width, 
                            current_wall_data["parts"])
        return None

    def place_cross_sections_instances(self, joint_parts_dict):
        counter = 1
        for collection, datum in joint_parts_dict.items():
            for data in datum:
                position, parts = data
                target_name = collection.name.replace("CSwall-", "")
                joint_name = f'SN-CS-Joint-{counter}'
                instance_name = f'{joint_name}-instance'
                parent_name = f'{target_name} Instance'
                grp = bpy.data.collections.new(joint_name)
                for part in parts:
                    self.group_every_children_elv_cross_sections(grp, part)
                for item in grp.objects:
                    csh_msh = 'csh_mesh' in item.name.lower()
                    lsh_msh = 'lsh_msh' in item.name.lower()
                    tsh_mesh = 'tsh_mesh' in item.name.lower()
                    if csh_msh or lsh_msh or tsh_mesh:
                        grp.objects.unlink(item)
                target_scene = bpy.data.scenes[f"CSwall-{target_name}"]
                target_parent = bpy.data.objects[parent_name]
                target_position = (0, 0, 0)
                instance = bpy.data.objects.new(instance_name, None)
                instance.instance_type = 'COLLECTION'
                instance.instance_collection = grp
                instance.parent = target_parent
                instance.location = target_position
                collection.objects.link(instance)
                target_scene.collection.objects.link(instance)
                counter += 1
    
    def get_virtual_parts_dict(self, assemblies_dict):
        virtual_parts = {}
        for wall, items in assemblies_dict.items():
            min_loc_data = items.get('min_loc_data')
            max_loc_data = items.get('max_loc_data')
            virtual_parts[wall] = {}
            if min_loc_data is not None:
                if min_loc_data.get('virtual_parts'):
                    parts = min_loc_data['virtual_parts']
                    virtual_parts[wall]["min"] = parts[0]
            if max_loc_data is not None:
                if max_loc_data.get('virtual_parts'):
                    parts = max_loc_data['virtual_parts']
                    virtual_parts[wall]["max"] = parts[0]
        return virtual_parts

    def process_virtual_objects(self, virtual_objects_dict, joint_parts_dict):
        parts_destiny = self.cs_virtual_objects(virtual_objects_dict, 
                                                joint_parts_dict)
        for part in parts_destiny:
            if part.get('partition') is not None:
                mesh = part.get('mesh')
                partition = part.get('partition')
                dimension = part.get('dimension')
                location = part.get('location')
                x_offset = part.get('x_offset')
                wall_collection = part.get('wall_collection')
                curr_wall = bpy.data.objects[wall_collection.name]
                wall_angle_radians = math.degrees(curr_wall.rotation_euler[2])
                wall_angle = round((wall_angle_radians), 2)
                oclusion = utils.create_cube_mesh(
                        f'{partition}_occl', dimension)
                utils.copy_world_loc(mesh, oclusion)
                utils.copy_world_rot(mesh, oclusion)
                oclusion.location[2] = location[2]
                if wall_angle in [90, -90]:
                    oclusion.location[0] -= x_offset
                if wall_angle == 0:
                    oclusion.location[1] -= x_offset
                if wall_angle == 180:
                    oclusion.location[1] += x_offset
                oclusion.rotation_euler[2] = math.radians(180)
                wall_collection.objects.link(oclusion)

    def cs_virtual_objects(self, virtual_objects_dict, joint_parts_dict):
        parts_collection_dict = {}
        for key, values in joint_parts_dict.items():
            for value in values:
                parts = value[1]
                position = value[0]
                for part in parts:
                    parts_collection_dict[part.name] = (key, position)
        parts_destiny = []
        for wall, parts in virtual_objects_dict.items():
            min_parts = parts.get('min')
            max_parts = parts.get('max')
            self.parts_preparation(parts_collection_dict, parts_destiny, 
                                   min_parts)
            self.parts_preparation(parts_collection_dict, parts_destiny, 
                                   max_parts)
        return parts_destiny

    def parts_preparation(self, parts_coll_dict, parts_destiny, parts):
        if parts is not None:
            original_part = parts.get('original')
            if original_part is not None:
                partition_part = parts.get('name')
                dimension = parts.get('dimension')
                mesh = parts.get('mesh')
                x_offset = parts.get('x_offset')
                original_part_obj = bpy.data.objects[original_part]
                current_wall = original_part_obj.parent.parent
                wall_rotation_z = current_wall.rotation_euler[2]
                y_partition = original_part_obj.rotation_euler[1]
                destiny = parts_coll_dict.get(original_part)
                if destiny is not None:
                    wall_destination, wall_width_in = destiny
                    wall_width = unit.inch(wall_width_in)
                    location = (0, 0, original_part_obj.location[2])
                    rotation = (0, 0,
                        (wall_rotation_z - y_partition) + math.radians(90))
                    dest_data = {
                        "partition" : partition_part,
                        "wall_collection" : wall_destination,
                        "wall_width": wall_width, 
                        "location" : location, 
                        "dimension" : dimension, 
                        "rotation" : rotation,
                        "mesh": mesh,
                        "x_offset": x_offset
                    }
                    parts_destiny.append(dest_data)
    
    def add_remaining_space_dims(self, assemblies_dict, wall_groups):
        for wall, assemblies_data in assemblies_dict.items():
            wall_left_corner, wall_right_corner = None, None
            right_wall = sn_types.Wall(wall).get_connected_wall('RIGHT')
            wall_left_corner = self.get_lsh_csh_assemblies(wall)
            wall_right_corner = self.get_lsh_csh_assemblies(right_wall.obj_bp)
            wall_length = self.to_inch(
                sn_types.Assembly(wall).obj_x.location.x)
            start_data = assemblies_data.get('min_loc_data')
            end_data = assemblies_data.get('max_loc_data')
            if start_data and not wall_left_corner:
                assys_start = start_data.get('start', 0)
                if assys_start > 0:
                    wall_grp = wall_groups[wall.name]
                    dim = self.add_remaining_space_lbl_elv(
                        wall_grp, wall, assys_start, "left")
                    wall_grp.objects.link(dim.anchor)
            if end_data and not wall_right_corner:
                assys_end = end_data.get('end', wall_length)
                rem_space = wall_length - assys_end
                if rem_space > 0:
                    wall_grp = wall_groups[wall.name]
                    dim = self.add_remaining_space_lbl_elv(
                        wall_grp, wall, rem_space, "right")
                    wall_grp.objects.link(dim.anchor)

    def add_cross_sections(self, walls, wall_groups):
        joints = self.get_walls_joints(walls)
        joints_result = []
        corner = {}
        corner_ends = {}
        joint_parts_dict = {}
        corner_starts = {}
        if joints is not None:
            assemblies_dict = self.get_walls_assys_arrangement(wall_groups)
            virtual_parts = self.get_virtual_parts_dict(assemblies_dict)
            if assemblies_dict is not None:
                wall_joints = joints["joints"]
                for joint in wall_joints:
                    current_wall, left_wall = joint
                    joint_parts = self.get_joint_parts(current_wall,
                                                       left_wall,
                                                       assemblies_dict)
                    corner_result = self.get_lsh_csh_assemblies(current_wall)
                    if corner_result:
                        for each in corner_result:
                            if wall_groups.get(left_wall.name):
                                collection = wall_groups[left_wall.name]
                                left_wall_assy = sn_types.Assembly(left_wall)
                                width = left_wall_assy.obj_x.location.x
                                width_inches = self.to_inch(width)
                                corner[collection] = (width_inches,
                                                      corner_result)
                    # Before apply the cross-sections we need to take note
                    # if section parts won't appear when not expected due
                    # 2 steps cross section parts applying
                    for key, value in corner.items():
                        cn_position, cn_parts = value
                        cn_assys = [sn_types.Assembly(a) for a in cn_parts]
                        cn_starts = [a.obj_x.location.x for a in cn_assys]
                        corner_starts[key] = round(max(cn_starts), 2)
                    for each in joints_result:
                        wall, position, parts = each
                        if wall.name in wall_groups.keys():
                            parnt_x = min([p.parent.location.x for p in parts])
                            collection = wall_groups[wall.name]
                            joint_res = joint_parts_dict.get(collection)
                    
                    if joint_parts is not None:
                        joints_result.append(joint_parts)
                if len(joints_result) > 0:
                    # Adding the cross-section parts
                    # 1st pass - L-shelves/Corner Shelves
                    for key, value in corner.items():
                        cn_position, cn_parts = value
                        if joint_parts_dict.get(key) is not None:
                            joint_parts_dict[key].append(
                                (cn_position, cn_parts))
                        if joint_parts_dict.get(key) is None:
                            joint_parts_dict[key] = []
                            joint_parts_dict[key].append(
                                (cn_position, cn_parts))
                    # 2nd pass - other assemblies
                    for each in joints_result:
                        wall, position, parts = each
                        parts_wall = None
                        parts_ending = {}
                        has_ending = False
                        parts_wall_list = list(
                            set([sn_utils.get_wall_bp(p) for p in parts]))
                        wall_width = sn_types.Assembly(
                                wall).obj_x.location.x
                        wall_width_inches = round(
                            unit.meter_to_inch(wall_width), 2)
                        parts_ending = wall_width_inches
                        if len(parts_wall_list) > 0:
                            parts_wall = parts_wall_list[0]
                            wall_assys = assemblies_dict.get(parts_wall)
                            if wall_assys:
                                max_data = wall_assys.get('max_loc_data')
                                if max_data:
                                    parts_ending = max_data.get('end')
                        has_ending = parts_ending != wall_width_inches
                        if wall.name in wall_groups.keys():
                            parts_after, parts_before = False, False
                            max_curr_end = 0
                            parnt_x = min([p.parent.location.x for p in parts])
                            collection = wall_groups[wall.name]
                            joint_res = joint_parts_dict.get(collection)
                            equiv_corner = corner_starts.get(collection)
                            curr_corner = self.get_lsh_csh_assemblies(wall)
                            wall_assys = assemblies_dict.get(wall)
                            if curr_corner:
                                cn_assys = [sn_types.Assembly(p) \
                                    for p in curr_corner]
                                cn_ends = [round(abs(a.obj_y.location.y), 2) \
                                    for a in cn_assys]
                                max_curr_end = max(cn_ends)
                                max_curr_end = round(
                                    unit.meter_to_inch(max_curr_end), 2)
                            has_cn_end = max_curr_end != 0
                            if has_ending and has_cn_end:
                                parts_cn_sum = (parts_ending + max_curr_end)
                                diff = abs(wall_width_inches - parts_cn_sum)
                                parts_before = diff < unit.inch(2)
                            if equiv_corner:
                                parts_diff = abs(equiv_corner - parnt_x)
                                parts_after = parts_diff < unit.inch(1.5)
                            will_skip = any([parts_after, parts_before])
                            if joint_res is not None and not will_skip:
                                joint_parts_dict[collection].append((position,
                                                                     parts))
                            if joint_res is None and not will_skip:
                                joint_parts_dict[collection] = []
                                joint_parts_dict[collection].append((position,
                                                                     parts))
                    self.place_cross_sections_instances(joint_parts_dict)
                    self.process_virtual_objects(virtual_parts,
                                                 joint_parts_dict)
                return assemblies_dict

    def create_acordion_scene(self, context, grp):
        bpy.ops.scene.new('INVOKE_DEFAULT', type='EMPTY')
        new_scene = context.scene
        new_scene.name = grp.name
        new_scene.snap.name_scene = grp.name
        new_scene.snap.elevation_img_name = grp.name
        new_scene.snap.accordion_view_scene = True
        self.create_linesets(new_scene)
        return new_scene

    def create_virtual_scene(self):
        bpy.ops.scene.new('INVOKE_DEFAULT', type='EMPTY')
        virtual = bpy.context.scene
        virtual.name = 'z_virtual'
        virtual.snap.name_scene = 'z_virtual'
        virtual.snap.elevation_img_name = 'z_virtual'
        virtual.snap.scene_type = 'VIRTUAL'
        self.create_linesets(virtual)
        return virtual

    def get_acordion_indexes(self, walls, acordions):
        indexed_acordions = []
        for acordion in acordions:
            indexed_acordion = []
            for item in acordion:
                index = walls.index(item)
                indexed_acordion.append(index)
            indexed_acordions.append(indexed_acordion)
        return indexed_acordions

    def fetch_valid_flagged_indexes(self, tmp_dict, tmp_keys):
        result = []
        for i, key in enumerate(tmp_keys):
            idx = i + 1
            is_first = idx == 1
            is_last = idx == len(tmp_keys)
            previous_true = tmp_dict.get(idx - 1)
            next_true = tmp_dict.get(idx + 1)
            current_true = tmp_dict.get(idx)
            first_rule = is_first and next_true
            last_rule = is_last and previous_true
            true_neighbor = previous_true or next_true
            middle_rule = not is_first and not is_last and true_neighbor
            if current_true and first_rule:
                result.append(key)
            elif current_true and last_rule:
                result.append(key)
            elif current_true and middle_rule:
                result.append(key)
        return result

    def break_flagged_walls(self, data_dict):
        result = []
        accordions = []
        indexes = []
        data = data_dict['data']
        ordered_keys = sorted(data.keys())
        tmp_dict = {}
        for key in ordered_keys:
            entry = data_dict['data'].get(key)
            if entry is not None:
                tmp_dict[key] = entry.get('show')
        tmp_keys = sorted(tmp_dict.keys())
        result = self.fetch_valid_flagged_indexes(tmp_dict, tmp_keys)
        acc_division = []
        idx_division = []
        for i, res in enumerate(result):
            is_first = i == 0
            is_last = i == len(result) - 1
            in_between = 0 < i < len(result) - 1
            has_next = res + 1 in result
            has_previous = res - 1 in result
            st_next = is_first and has_next
            bw_next = in_between and has_next
            lt_next = is_last and has_previous
            st_n_next = is_first and not has_next
            bw_n_next = in_between and not has_next
            lt_n_next = is_last and not has_previous
            add_to_exstng_div = st_next or bw_next or lt_next
            add_to_new_div = st_n_next or bw_n_next or lt_n_next
            if add_to_exstng_div:
                acc_division.append(data[res]['wall_bp'])
                idx_division.append(res)
            elif add_to_new_div:
                acc_division.append(data[res]['wall_bp'])
                idx_division.append(res)
                accordions.append(acc_division)
                indexes.append(idx_division)
                acc_division = []
                idx_division = []
        if len(acc_division) > 0:
            accordions.append(acc_division)
            indexes.append(idx_division)
        return (accordions, indexes) 


    def width_breakdown(self, data_dict, accordions, indexes):
        break_width = data_dict['settings']['break_width']
        final_accordions = []
        positive_overlays = []
        any_overlay = False
        for i, index in enumerate(indexes):
            curr_acc_width = 0
            for idx in index:
                width = data_dict['data'][idx]['width_inches']
                pos_overlay = data_dict['data'][idx]['overlay']
                curr_acc_width += width
                positive_overlays.append(pos_overlay)
            any_overlay = any(positive_overlays)
            # 1st case, walls under break limit, no positive overlays 
            if curr_acc_width <= break_width and not any_overlay:
                final_accordions.append(accordions[i])
            # 2nd case, walls under break limit, positive overlays
            elif curr_acc_width <= break_width and any_overlay:
                final_acc = []
                for j, idx in enumerate(index):
                    prvs_over = None
                    will_overlay = False
                    width = data_dict['data'][idx]['width_inches']
                    overlay = data_dict['data'][idx]['overlay']
                    left_overlay = data_dict['data'][idx]['left_overlay']
                    if left_overlay:
                        prvs_over = data_dict['data'][idx - 1]['overlay_side'] 
                    overlay_side = data_dict['data'][idx]['overlay_side']
                    starting = overlay_side == "start"
                    ending = prvs_over == "end"
                    start_overlay = overlay and overlay_side and starting
                    end_overlay = left_overlay and ending
                    will_overlay = (overlay and start_overlay) or (left_overlay and end_overlay)
                    if will_overlay:
                        final_accordions.append(final_acc)
                        final_acc = []
                        final_acc.append(accordions[i][j])
                    elif not will_overlay:
                        final_acc.append(accordions[i][j])
                final_accordions.append(final_acc)
            # 3rd case, walls beyond break limit having or not positive overlay
            elif break_width <= curr_acc_width:
                final_acc = []
                curr_break = break_width
                for j, idx in enumerate(index):
                    prvs_over = None
                    will_overlay = False
                    width = data_dict['data'][idx]['width_inches']
                    overlay = data_dict['data'][idx]['overlay']
                    left_overlay = data_dict['data'][idx]['left_overlay']
                    if left_overlay:
                        prvs_over = data_dict['data'][idx - 1]['overlay_side'] 
                    overlay_side = data_dict['data'][idx]['overlay_side']
                    starting = overlay_side == "start"
                    ending = prvs_over == "end"
                    start_overlay = overlay and overlay_side and starting
                    end_overlay = left_overlay and ending
                    will_overlay = (overlay and start_overlay) or (left_overlay and end_overlay)
                    if width <= curr_break and not will_overlay:
                        final_acc.append(accordions[i][j])
                        curr_break -= width
                    elif width > curr_break or will_overlay:
                        curr_break = break_width
                        final_accordions.append(final_acc)
                        final_acc = []
                        final_acc.append(accordions[i][j])
                        curr_break -= width
                final_accordions.append(final_acc)
        return final_accordions


    def divide_walls_to_acordions(self, scene, data_dict):
        # 1st pass - Apply the logic for empty walls, just door walls and 
        #            intermediate walls
        self.incl_or_excl_accordions(data_dict)
        # 2nd pass - Once the logic is applied form the accordions regardless
        #            the wall width break
        accordions, indexes = self.break_flagged_walls(data_dict)
        # 3rd pass - With the accordions formed, apply the 
        #            wall width breakdown
        final_accordions = self.width_breakdown(data_dict, accordions, indexes)
        return final_accordions


    def incl_or_excl_accordions(self, data_dict):
        walls_length_sum = 0
        walls_flags_dict = {}
        settings = data_dict['settings']
        data = data_dict['data']
        intermediates = settings['intermediate_qty']
        break_width = settings['break_width']
        # 1st pass - General Rules
        for idx, datum in data.items():
            walls_length_sum += datum['width_inches']
            wall = datum['wall_bp']
            empty = datum['empty']
            just_doors = datum['just_doors']
            within_intem = datum['within_intermediate_space']
            has_lsh_csh = datum['has_lsh_csh']
            empty_skip = (empty or just_doors) and intermediates == 0
            interm_skip = (empty or just_doors) and intermediates >= 1
            having_assy_wall = not empty and not just_doors
            if empty_skip and not has_lsh_csh:
                datum['show'] = False
                self.hide_accordion_wall(wall)
                datum['rule'] = "empty skip and not has_lsh_csh"
            elif interm_skip and within_intem:
                datum['show'] = True
                intermediates -= 1
                datum['rule'] = "interm_skip and within_intem"
            elif empty and not within_intem:
                datum['show'] = False
                datum['rule'] = "empty and not within_intem"
            elif having_assy_wall:
                datum['show'] = True
                datum['rule'] = "having_assy_wall"
            walls_flags_dict[idx] = datum['show']
        # 2nd pass - Exceptions
        # Now dealing with a having assy wall with empty neighboors
        for idx, datum in data.items():
            has_wall = ""
            wall_bp = datum.get('wall_bp')
            empty = datum.get('empty')
            rule = datum.get('rule')
            if empty:
                has_wall = "Don\'t Show Wall"
            elif not empty:
                has_wall = "Show Wall"
                

    def hide_every_children(self, child):
        child.hide_viewport = True
        child.hide_render = True
        for ch in child.children:
            ch.hide_viewport = True
            ch.hide_render = True
            if len(ch.children) > 0:
                self.hide_every_children(ch)

    def hide_accordion_wall(self, wall):
        self.hide_every_children(wall)

    def wall_assys_has_positive_overlay(self, wall):
        overlay_result = []
        for child in wall.children:
            overlay = self.has_positive_overlay(child)
            overlay_result.append(overlay)
        return any(overlay_result)

    def has_positive_overlay(self, item):
        if not item.get("IS_BP_ASSEMBLY"):
            return False
        wall_length, item_length = math.inf, 0
        wall_assy = None
        wall_bp = utils.get_wall_bp(item)
        if wall_bp:
            wall_assy = sn_types.Assembly(wall_bp)
            item_assy = sn_types.Assembly(item)
            if not wall_assy and not item_assy:
                return
            wall_length = wall_assy.obj_x.location.x
            item_length = item_assy.obj_x.location.x
        negative_x_loc = item.location[0] < 0
        positive_x_loc = (item_length + item.location[0]) > wall_length
        if negative_x_loc or positive_x_loc:
            return True
        return False

    def positive_overlay(self, wall_bp):
        overlays = []
        for item in wall_bp.children:
            if self.has_positive_overlay(item):
                assy = sn_types.Assembly(item)
                height = assy.obj_z.location.z
                overlays.append((item.location[0], height))
        if len(overlays) > 0:
            higher_overlay = sorted(
                overlays, key=lambda tup: tup[0], reverse=True)[0]
            return higher_overlay
        return (0, 0)

    def overlay_side(self, wall_bp):
        START, END = "start", "end"
        wall_assy = sn_types.Assembly(wall_bp)
        if not wall_assy:
            return None
        for item in wall_bp.children:
            if item.get("IS_BP_ASSEMBLY"):
                item_assy = sn_types.Assembly(item)
                wall_length = wall_assy.obj_x.location.x
                item_length = item_assy.obj_x.location.x
                start_x_loc = item.location[0] < 0
                end_x_loc = (item_length + item.location[0]) > wall_length
                if start_x_loc:
                    return START
                elif end_x_loc:
                    return END
        return None


    def fetch_accordions_walls_data(self, scene, walls):
        main_acc_walls = [o for o in scene.objects if o.get("IS_BP_WALL")]
        acc_props = bpy.context.scene.snap.accordion_view
        break_width = acc_props.break_width
        enable_intermediate = acc_props.enable_intermediate_walls
        intermediate_space_inches = acc_props.intermediate_space
        intermediate_space_metric = unit.inch(intermediate_space_inches)
        intermediate_qty = acc_props.intermediate_qty
        walls_data = {}
        walls_dict = {}
        walls_list = [wall.obj_bp.name for wall in walls]
        walls_data['data'] = walls_dict
        for i, wall in enumerate(walls):
            idx = i + 1
            left_overlay, right_overlay = False, False
            left_wall = wall.get_connected_wall('LEFT')
            right_wall = wall.get_connected_wall('RIGHT')
            if left_wall:
                left_overlay = self.wall_assys_has_positive_overlay(
                    left_wall.obj_bp)
            if right_wall:
                right_overlay = self.wall_assys_has_positive_overlay(
                    right_wall.obj_bp)
            width = sn_types.Assembly(wall.obj_bp).obj_x.location.x
            just_doors = self.is_just_door_wall(wall.obj_bp)
            is_empty = self.empty_wall(wall.obj_bp)
            has_lsh_csh = self.next_wall_has_lsh_csh(walls_list, wall.obj_bp)
            has_overlay = self.wall_assys_has_positive_overlay(wall.obj_bp)
            within_iw = width <= intermediate_space_metric
            walls_dict[idx] = {}
            walls_dict[idx]['wall_bp'] = main_acc_walls[i]
            walls_dict[idx]['width_metric'] = width
            walls_dict[idx]['width_inches'] = self.to_inch(width)
            walls_dict[idx]['just_doors'] = just_doors
            walls_dict[idx]['empty'] = is_empty
            walls_dict[idx]['within_intermediate_space'] = within_iw
            walls_dict[idx]['has_lsh_csh'] = has_lsh_csh
            walls_dict[idx]['show'] = True
            walls_dict[idx]['left_overlay'] = left_overlay
            walls_dict[idx]['overlay'] = has_overlay
            walls_dict[idx]['overlay_side'] = self.overlay_side(wall.obj_bp)
            walls_dict[idx]['right_overlay'] = right_overlay

        if enable_intermediate is False:
            intermediate_qty = 0
        walls_data['settings'] = {}
        walls_data['settings']['break_width'] = break_width
        walls_data['settings']['intermediate_qty'] = intermediate_qty
        return walls_data

    def main_accordion_scene(self, context):
        walls_length = 0
        walls_heights = []
        bpy.context.window.scene = bpy.data.scenes["_Main"]
        new_walls = []
        bpy.ops.scene.new("INVOKE_DEFAULT", type="FULL_COPY")
        new_scene = context.scene
        # Get the new scene walls
        for obj in new_scene.objects:
            if obj.get("IS_BP_WALL"):
                wall = sn_types.Wall(obj_bp=obj)
                new_walls.append(wall)
        for obj in new_walls:
            obj.obj_bp.rotation_euler.z = 0
            wall_assy = sn_types.Assembly(obj.obj_bp)
            walls_length += wall_assy.obj_x.location.x
            walls_heights.append(wall_assy.obj_z.location.z)
            if obj.obj_bp.hide_viewport:
                obj.obj_bp.hide_viewport = False
                for child in obj.obj_bp.children:
                    if child.type == 'EMPTY':
                        continue
                    child.hide_viewport = False
            # Removing all wall heights and building heights here too
            for wall_ch in obj.obj_bp.children:
                for wall_g_ch in wall_ch.children:
                    if wall_g_ch.type == 'FONT':
                        bpy.data.objects.remove(wall_g_ch, do_unlink=True)
                if wall_ch.get("IS_VISDIM_A"):
                    bpy.data.objects.remove(wall_ch, do_unlink=True)
                elif wall_ch.type == 'FONT':
                    bpy.data.objects.remove(wall_ch, do_unlink=True)
        new_scene.name = "Z_Main Accordion"
        new_scene.snap.name_scene = "Z_Main Accordion"
        new_scene.snap.elevation_img_name = "Z_Main Accordion"
        new_scene.snap.scene_type = 'VIRTUAL'
        self.create_linesets(new_scene)
        camera = self.create_camera(new_scene)
        camera.rotation_euler.x = math.radians(90.0)
        camera.rotation_euler.z = 0
        new_scene.snap.opengl_dim.gl_font_size = 18
        new_scene.render.pixel_aspect_x = 1.0
        new_scene.render.pixel_aspect_y = 1.0
        new_scene.render.resolution_x = 1800
        new_scene.render.resolution_y = 900
        new_scene.render.resolution_percentage = 100
        self.remove_accordion_scene_material_pointers(new_scene)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.view3d.camera_to_view_selected()
        camera.data.type = 'ORTHO'
        max_height = max(walls_heights)
        proportion = round((walls_length / max_height), 2)
        camera.data.ortho_scale += proportion
        bpy.ops.object.select_all(action='DESELECT')
        result = (new_scene, new_walls)
        return result

    def accordion_cross_section_slot(self, current_wall, previous_wall, 
                                     next_wall, assemblies_dict):
        offset = 6 # 6 inches
        slots = {}
        slots["left"] = False
        slots["right"] = False
        left_space, right_space = 0.0, 0.0
        curr_wall_width = sn_types.Assembly(current_wall).obj_x.location.x
        curr_wall_width_inches = self.to_inch(curr_wall_width)
        prvs_wall_width = sn_types.Assembly(previous_wall).obj_x.location.x
        prvs_wall_width_inches = self.to_inch(prvs_wall_width)
        depth_prvs, start_curr, end_curr = (None, None, None)
        end_prvs, depth_next = (None, None)
        curr_min = assemblies_dict[current_wall].get("min_loc_data")
        curr_max = assemblies_dict[current_wall].get("max_loc_data")
        prvs_max = assemblies_dict[previous_wall].get("max_loc_data")
        next_min = assemblies_dict[next_wall].get("min_loc_data")
        if prvs_max is not None:
            depth_prvs = prvs_max.get("depth")
            end_prvs = prvs_max.get("end")
        if curr_min is not None:
            start_curr = curr_min.get("start")
        if curr_max is not None:
            end_curr = curr_max.get("end")
        if next_min is not None:
            depth_next = next_min.get("depth")
            start_next = next_min.get("start") 
        # LEFT check
        if start_curr is not None and depth_prvs is not None:
            end_situation = (curr_wall_width_inches - end_curr) <= offset
            start_situation = (prvs_wall_width_inches - end_prvs) <= offset
            if depth_prvs <= start_curr and (start_situation or end_situation):
                # NOTE Issue #1197 - start_curr is the value we want!
                #      when a left slot is True
                slots["left"] = True
                left_space = start_curr
            elif depth_prvs > start_curr:
                slots["left"] = False
        elif start_curr is None and depth_prvs is not None:
            slots["left"] = True
        elif start_curr is None and depth_prvs is None:
            slots["left"] = False
        # RIGHT check
        if end_curr is not None and depth_next is not None:
            remaining_space = curr_wall_width_inches - end_curr
            if remaining_space >= depth_next and start_next <= offset:
                # NOTE Issue #1197 - remaining_space is the value we want!
                #      when a right slot is True
                slots["right"] = True
                right_space = remaining_space
            elif remaining_space < depth_next:
                slots["right"] = False
        elif end_curr is None and depth_next is not None:
            slots["right"] = True
        elif end_curr is None and depth_next is None:
            slots["right"] = False
        spaces = round(left_space, 2), round(right_space, 2)
        section_slots = (slots, spaces)
        return section_slots

    def accordion_instances_arragement(self, walls, accordions, 
                                       assemblies_dict, extra_dims):
        targets = {}
        walls_rem_spaces = {}
        walls_sum = 0
        for wall in walls:
            walls_sum += wall.obj_x.location.x
        walls = [wall.obj_bp for wall in walls]
        # NOTE Fetch parts and create the new inserts getting at the previous
        # wall max_loc_data and at the next min_loc_data
        for key in assemblies_dict.keys():
            left_instance, right_instance = None, None
            prvs_wall_key = walls[walls.index(key) - 1]
            curr_wall_key = walls[walls.index(key)]
            next_wall_key = walls[walls.index(key) - (len(walls) - 1)]
            slots, spaces = self.accordion_cross_section_slot(curr_wall_key,
                                                      prvs_wall_key,
                                                      next_wall_key,
                                                      assemblies_dict)
            extra_dims[curr_wall_key] = []
            walls_rem_spaces[curr_wall_key] = spaces
            left_slot = slots.get("left") 
            right_slot = slots.get("right")
            curr_wall_ch = curr_wall_key.children
            wall_mesh = [m for m in curr_wall_ch if m.type == 'MESH' and 'wall' in m.name.lower()][0]
            curr_wall_glb = self.get_object_global_location(wall_mesh)
            curr_wall_glb_x_pos = curr_wall_glb[0]
            left_parts_data = assemblies_dict[prvs_wall_key]["max_loc_data"]
            right_parts_data = assemblies_dict[next_wall_key]["min_loc_data"]
            curr_wall_name = curr_wall_key.name
            curr_wall_width = sn_types.Assembly(curr_wall_key).obj_x.location.x
            if left_slot and left_parts_data is not None:
                prvs_wall_width = self.to_inch(sn_types.Assembly(prvs_wall_key).obj_x.location.x)
                prvs_parts_max = assemblies_dict[prvs_wall_key]['max_loc_data']
                prvs_assy_end = None
                if prvs_parts_max:
                    prvs_assy_end = prvs_parts_max['end']
                    if (prvs_wall_width - prvs_assy_end) > left_parts_data['depth']:
                        continue
                offset = curr_wall_glb_x_pos
                left_name = f'{curr_wall_name}_left'
                left_grp = bpy.data.collections.new(f'{left_name}_grp')
                self.add_ch_accordion_parts(extra_dims, curr_wall_key, 
                                            left_parts_data, left_grp)
                self.add_accordion_virtual_parts(left_parts_data, left_grp)
                left_instance = bpy.data.objects.new(
                    f'{left_name}_ins', None)
                left_instance.instance_type = 'COLLECTION'
                left_instance.instance_collection = left_grp
                if offset == 0:
                    left_instance.location = (offset, (walls_sum * -1), 0)
                elif offset != 0:
                    left_instance.location = (offset, (offset * -1), 0)
                left_instance.rotation_euler = (0, 0, math.radians(90))
            if right_slot and right_parts_data is not None:
                next_wall_width = self.to_inch(sn_types.Assembly(next_wall_key).obj_x.location.x)
                next_parts_min = assemblies_dict[next_wall_key]['min_loc_data']
                next_assy_start = None
                if next_parts_min:
                    next_assy_start = next_parts_min['start']
                    if next_assy_start > right_parts_data['depth']:
                        continue
                offset = curr_wall_glb_x_pos + curr_wall_width
                right_name = f'{curr_wall_name}_right'
                right_grp = bpy.data.collections.new(f'{right_name}_grp')
                self.add_ch_accordion_parts(extra_dims, curr_wall_key, 
                                            right_parts_data, right_grp)
                self.add_accordion_virtual_parts(right_parts_data, right_grp)
                right_instance = bpy.data.objects.new(
                    f'{right_name}_ins', None)
                right_instance.instance_type = 'COLLECTION'
                right_instance.instance_collection = right_grp
                if offset == 0:
                    right_instance.location = (offset, (walls_sum * -1), 0)
                elif offset != 0:
                    right_instance.location = (offset, (offset * -1), 0)
                right_instance.rotation_euler = (0, 0, math.radians(-90))
            targets[curr_wall_key] = (left_instance, right_instance)
        # NOTE to work properly, the cross-sections for L-shelves/Corner Shelves
        #      for accordions are added after the ones for sections
        for wall in walls:
            corner_result = self.get_lsh_csh_assemblies(wall)
            if corner_result:
                previous_wall = walls[walls.index(wall) - 1]
                previous_wall_name = previous_wall.name
                right_name = f'{previous_wall_name}_right_grp'
                all_collections = bpy.data.collections
                present_collections = [col.name for col in all_collections]
                existing_grp = right_name in present_collections
                prvs_wall_width = sn_types.Assembly(
                    previous_wall).obj_x.location.x
                target = targets.get(previous_wall)
                # NOTE if the group already exists, just add the objects there
                #      and if it doesn't, create the group and instance
                if existing_grp:
                    grp = bpy.data.collections[right_name]
                    for corner in corner_result:
                        self.group_children(grp, corner)
                elif not existing_grp:
                    grp = bpy.data.collections.new(f'{right_name}')
                    for corner in corner_result:
                        self.group_children(grp, corner)
                    wall_ch = previous_wall.children
                    wall_mesh = [m for m in wall_ch \
                        if m.type == 'MESH' and 'wall' in m.name.lower()][0]
                    curr_wall_glb = self.get_object_global_location(wall_mesh)
                    curr_wall_glb_x_pos = curr_wall_glb[0]
                    offset = curr_wall_glb_x_pos + prvs_wall_width
                    right_instance = bpy.data.objects.new(
                        f'{previous_wall_name}_right_ins', None)
                    right_instance.location = (offset, (offset * -1), 0)
                    right_instance.rotation_euler = (0, 0, math.radians(-90))
                    right_instance.instance_type = 'COLLECTION'
                    right_instance.instance_collection = grp
                    if target:
                        left_instance, _ = target
                        targets[previous_wall] = left_instance, right_instance
                    elif not target:
                        targets[previous_wall] = None, right_instance
        return (targets, walls_rem_spaces)

    def add_ch_accordion_parts(self, extra_dims, curr_wall_key,
                               parts_data, grp):
        for part in parts_data["parts"]:
            if 'corner shelves' in part.name.lower():
                csh_dim = self.get_strict_corner_dim_height(part)
                extra_dims[curr_wall_key].append(csh_dim)
                for tk in part.children:
                    if 'toe kick' in tk.name.lower():
                        tk_assy = sn_types.Assembly(tk)
                        toe_kick_height = tk_assy.obj_z.location.z
                        extra_dims[curr_wall_key].append(toe_kick_height)
            if 'l shelves' in part.name.lower():
                lsh_dim = self.get_strict_corner_dim_height(part)
                extra_dims[curr_wall_key].append(lsh_dim)
                for tk in part.children:
                    if 'toe kick' in tk.name.lower():
                        tk_assy = sn_types.Assembly(tk)
                        toe_kick_height = tk_assy.obj_z.location.z
                        extra_dims[curr_wall_key].append(toe_kick_height)
            if part.name not in grp.objects:
                self.group_every_children_on_acc(grp, part)

    def add_accordion_virtual_parts(self, parts_data, group):
        v_parts = parts_data.get("virtual_parts")
        if v_parts is not None:
            for part in v_parts:
                mesh = part.get("mesh")
                original_part = part.get('original')
                original_part_obj = bpy.data.objects[original_part]
                current_wall = original_part_obj.parent.parent
                partition = part.get('partition')
                dimension = part.get('dimension')
                x_offset = part.get('x_offset')
                location = (0, 0, original_part_obj.location[2])
                oclusion = utils.create_cube_mesh(
                                f'{partition}_occl', dimension)
                utils.copy_world_loc(mesh, oclusion)
                utils.copy_world_rot(mesh, oclusion)
                oclusion.location[0] -= x_offset
                oclusion.location[2] = location[2]
                oclusion.rotation_euler[2] = math.radians(180)
                group.objects.link(oclusion)

    def apply_build_height_label(self, wall_bp, position, multiplier, ovrly_x_offset):
        position_metric = position * unit.inch(1)
        wall_mesh = [m for m in wall_bp.children if m.type == 'MESH' and 'wall' in m.name.lower()][0]
        curr_wall_glb_x = self.get_object_global_location(wall_mesh)[0]
        offset = unit.inch(-7) + (unit.inch(-4) * multiplier) + ovrly_x_offset
        dim = sn_types.Dimension()
        dim.parent = wall_bp
        dim.start_x(value=offset + curr_wall_glb_x)
        dim.start_y(value=0)
        dim.start_z(value=0)
        dim.end_z(value=position_metric)
        dim.set_label(str(position) + "\"")

    def apply_toe_kick_label(self, wall_bp, position, multiplier, 
                                ovrly_x_offset):
        position_metric = position * unit.inch(1)
        wall_mesh = [m for m in wall_bp.children \
            if m.type == 'MESH' and 'wall' in m.name.lower()][0]
        curr_wall_glb_x = self.get_object_global_location(wall_mesh)[0]
        offset = unit.inch(-6) + (unit.inch(-2) * multiplier) + ovrly_x_offset
        dim = sn_types.Dimension()
        dim.parent = wall_bp
        dim.start_x(value=offset + curr_wall_glb_x)
        dim.start_y(value=0)
        dim.start_z(value=0)
        dim.end_z(value=position_metric)
        dim.set_label(" ")
        text = sn_types.Dimension()
        text.parent(dim.anchor)
        text.start_x(value=unit.inch(-3))
        text.start_z(value=position_metric / 2)
        text.set_label(str(position) + "\"")
    
    def ceiling_height_dimension(self, item, bheight_offset):
        wall_mesh = [m for m in item.children \
            if m.type == 'MESH' and 'wall' in m.name.lower()][0]
        curr_wall_glb_x = self.get_object_global_location(wall_mesh)[0]
        assy = sn_types.Assembly(item)
        height = assy.obj_z.location.z
        dim = sn_types.Dimension()
        dim.parent = item.parent
        dim.start_x(value=unit.inch(-1) + bheight_offset + curr_wall_glb_x)
        dim.start_y(value=0)
        dim.start_z(value=0)
        dim.end_z(value=height)
        wall_height = self.to_inch_lbl(height)
        dim.set_label(wall_height)

    def overlay_label(self, wall_bp, x_loc, z_loc, side):
        dim = sn_types.Dimension()
        dim.parent(wall_bp)
        dim.start_x(value=x_loc / 2)
        dim.start_z(value=z_loc + unit.inch(6))
        dim.set_label("Positive|Overlay")

    def accordion_build_hight_n_ceiling_dimensions(self, context, 
                                                   accordion, existing_dims,
                                                   extra_dims):
        bh_dims = []
        first_wall = None
        # If a dimension is less than 10 inches it's text will be horizontal
        small_dim_height_value = 10 
        for i, wall_bp in enumerate(accordion):
            curr_wall_extra_dims = extra_dims.get(wall_bp)
            if curr_wall_extra_dims is not None:
                for dim in curr_wall_extra_dims:
                    bh_dims.append(dim)
            if i == 0:
                first_wall = wall_bp
            for item in wall_bp.children:
                if "IS_BP_CABINET" in item:
                    assy = sn_types.Assembly(item)
                    ctop_thickness = 0
                    toe_kick_height = 0
                    for sub_item in item.children:
                        if "IS_BP_CABINET_COUNTERTOP" in sub_item:
                            sub_assy = sn_types.Assembly(sub_item)
                            ctop_thickness_ppt = sub_assy.get_prompt("Deck Thickness")
                            if ctop_thickness_ppt:
                                ctop_thickness = ctop_thickness_ppt.get_value()
                        elif "IS_BP_CARCASS" in sub_item:
                            sub_assy = sn_types.Assembly(sub_item)
                            toe_kick_ppt = sub_assy.get_prompt("Toe Kick Height")
                            if toe_kick_ppt:
                                if toe_kick_ppt.get_value() > toe_kick_height:
                                    toe_kick_height = toe_kick_ppt.get_value()
                    
                    if 'IS_MIRROR' in assy.obj_z:
                        bh_dims.append(assy.obj_bp.location.z + ctop_thickness)
                    else:
                        bh_dims.append(assy.obj_z.location.z + ctop_thickness)

                    if toe_kick_height > 0: 
                        bh_dims.append(toe_kick_height)
                    continue
                if 'corner shelves' in item.name.lower():
                    self.strict_corner_bh(bh_dims, item)
                if 'l shelves' in item.name.lower():
                    self.strict_corner_bh(bh_dims, item)
                if 'section' in item.name.lower():
                    self.section_bh(bh_dims, item)
                if 'IS_TOPSHELF_SUPPORT_CORBELS' in item:
                    self.ts_support_corbel_bh(bh_dims, item)
                if 'IS_BP_WALL_BED' in item:
                    assy = sn_types.Assembly(item)
                    bh_dims.append(assy.obj_z.location.z)
        first_wall = self.get_first_acc_wall(accordion)
        last_wall = accordion[-1]
        bh_dims = [self.to_inch(bh) for bh in bh_dims]
        bh_dims = list(set(bh_dims)) 
        bh_dims = sorted(bh_dims)
        for bh in list(bh_dims):
            if isinstance(existing_dims, List) and bh in existing_dims:
                bh_dims.remove(bh)
        existing_dims += bh_dims
        if len(bh_dims) > 0:
            overlay_x_offset = 0
            overlay_z_offset = 0
            first_overlay = self.wall_assys_has_positive_overlay(first_wall)
            last_overlay = self.wall_assys_has_positive_overlay(last_wall)
            ov_side_first_wall = self.overlay_side(first_wall)
            ov_side_last_wall = self.overlay_side(last_wall)
            if first_overlay and ov_side_first_wall == "start":
                overlay_result = self.positive_overlay(first_wall)
                overlay_x_offset, overlay_z_offset = overlay_result
                self.overlay_label(
                    first_wall, overlay_x_offset, overlay_z_offset, "")
            if last_overlay and ov_side_last_wall == "end":
                overlay_result = self.positive_overlay(last_wall)
                x_offset, z_offset = overlay_result
                wall_length = sn_types.Assembly(last_wall).obj_x.location.x
                x_offset = (x_offset + wall_length) * 2
                x_offset += unit.inch(6)
                self.overlay_label(
                    last_wall, x_offset, z_offset, "")
                overlay_x_offset = 0
            for i, value in enumerate(bh_dims):
                if value > small_dim_height_value:
                    self.apply_build_height_label(
                        first_wall, value, i, overlay_x_offset)
                elif value <= small_dim_height_value:
                    self.apply_toe_kick_label(
                        first_wall, value, i, overlay_x_offset)
            dims_offset = (unit.inch(-4) * len(bh_dims))
            max_offset = unit.inch(-7) + dims_offset + overlay_x_offset
            if first_wall is not None:
                self.ceiling_height_dimension(first_wall, max_offset)
            return max_offset
        return None

    def get_first_acc_wall(self, accordion):
        first_wall = None
        # NOTE toggle to stop looking after other walls once you've skipped
        #      the ones considered empty
        found = False
        walls = [wall.name for wall in accordion]
        for wall in accordion:
            has_csh_lsh = self.next_wall_has_lsh_csh(walls, wall)
            empty = self.empty_wall(wall)
            just_door = self.is_just_door_wall(wall)
            std_walls = not empty and not just_door and not found
            just_csh_lsh_cross_sections = has_csh_lsh and not found
            if std_walls or just_csh_lsh_cross_sections:
                first_wall = wall
                found = True
        return first_wall

    def ts_support_corbel_bh(self, bh_dims, item):
        product = sn_types.Assembly(item)
        bh_dims.append(product.obj_bp.location.z)

    def section_bh(self, bh_dims, item):
        build_height_dim = 0
        countertop_height = 0
        ctop_thickness = 0
        topshelf_thickness = 0
        hanging_assy = sn_types.Assembly(item)
        hanging_height = 0
        if hasattr(hanging_assy.obj_z, 'location'):
            hanging_height = hanging_assy.obj_z.location.z
            for n_item in item.children:
                if 'counter top' in n_item.name.lower():
                    countertop_height = n_item.location[2]
                    for k_item in n_item.children:
                        for x_item in k_item.children:
                            if not x_item.hide_viewport:
                                z_loc = x_item.dimensions[2]
                                ctop_thickness = abs(z_loc)

                if 'top shelf' in n_item.name.lower():
                    for k_item in n_item.children:
                        if 'topshelf' in k_item.name.lower():
                            for f_item in k_item.children:
                                if f_item.type == "MESH":
                                    assy = sn_types.Assembly(
                                                    k_item)
                                    topshelf_thickness = abs(
                                                    assy.obj_z.location.z)

        # Get world location z from each partition obj_x
        obj_bp = hanging_assy.obj_bp
        partitions = [sn_types.Assembly(obj) for obj in obj_bp.children if obj.sn_closets.is_panel_bp]
        partition_world_heights = [p.obj_x.matrix_world.translation.z for p in partitions]
        tallest_partition_height = max(partition_world_heights)

        hanging = hanging_height > 0
        ctop = ctop_thickness == 0
        tshelf = topshelf_thickness == 0
        if hanging and ctop and tshelf:
            build_height_dim = tallest_partition_height
        elif ctop_thickness > 0:
            build_height_dim = (countertop_height + ctop_thickness)
        elif topshelf_thickness > 0:
            build_height_dim = (tallest_partition_height + topshelf_thickness)
        # NOTE the TK on sections are optional and do not impact directly on
        #      build height, so they are added apart.
        for tk in item.children:
            if 'toe kick' in tk.name.lower():
                tk_assy = sn_types.Assembly(tk)
                tk_height_pmpt = tk_assy.get_prompt("Toe Kick Height")
                tk_height_metric = tk_height_pmpt.get_value()
                bh_dims.append(tk_height_metric)
        bh_dims.append(build_height_dim)

    def strict_corner_bh(self, bh_dims, item):
        tk_height, tsh_height = 0, 0
        is_hanging, tsh = False, False
        lsh_assy = sn_types.Assembly(item)
        tk_height_pmpt = lsh_assy.get_prompt("Toe Kick Height")
        is_hanging_pmpt = lsh_assy.get_prompt("Is Hanging")
        tsh_pmpt = lsh_assy.get_prompt("Add Top Shelf")
        if tk_height_pmpt and is_hanging_pmpt and tsh_pmpt:
            tk_height = tk_height_pmpt.get_value()
            is_hanging = is_hanging_pmpt.get_value()
            tsh = tsh_pmpt.get_value()
        lsh_height = lsh_assy.obj_z.location.z + tk_height
        if is_hanging:
            lsh_height = lsh_assy.obj_z.location.z
        if tsh:
            tsh_height += unit.inch(0.75)
        bh_dims.append(lsh_height + tsh_height)
               
    
    def wall_width(self, walls_list, wall):
        assembly = sn_types.Assembly(wall)
        x_offset = assembly.obj_x.location.x / 2
        text_loc = (x_offset, 0, -unit.inch(10))
        just_wall = self.is_just_door_wall(wall)
        has_lsh_csh = self.next_wall_has_lsh_csh(walls_list, wall)
        empty = self.empty_wall(wall)
        if (not just_wall and not empty) or has_lsh_csh:
            self.elv_wall_labels(assembly, text_loc)
        has_entry = any('Door Frame' in e.name for c in wall.children
                        for e in c.children)
        if (not has_entry and not just_wall and not empty) or has_lsh_csh:
            dim = sn_types.Dimension()
            label = self.to_inch_lbl(assembly.obj_x.location.x)
            dim.parent(wall)
            dim.start_y(value=assembly.obj_y.location.y)
            dim.start_z(value=assembly.obj_z.location.z + unit.inch(4))
            dim.end_x(value=assembly.obj_x.location.x)
            dim.set_label(label)
    
    def accordion_building_height_ceiling_height(self, context, 
                                                 accordion, walls_list,
                                                 extra_dims, wall_rem_spaces):
        offsets = []
        exstg_dims = []
        for wall in accordion:
            left_space, right_space = wall_rem_spaces.get(wall, (0, 0))
            if left_space > 0:
                self.add_remaining_space_lbl(wall, left_space, "left")
            elif right_space > 0:
                self.add_remaining_space_lbl(wall, right_space, "right")
            self.wall_width(walls_list, wall)
            offset = self.accordion_build_hight_n_ceiling_dimensions(context, 
                                                                     accordion,
                                                                     exstg_dims, 
                                                                     extra_dims)
            if offset:
                offsets.append(offset)
        if offsets:
            return max(offsets)
        else:
            return 0

    def make_flat_crown_label(self, labels, item):
        flat_crown_layers = 0
        for ch in item.children:
            is_layered = ch.get('IS_BP_LAYERED_CROWN')
            snap_attr = hasattr(ch, 'snap')
            not_ext_left = 'left' not in ch.name.lower()
            not_ext_right = 'right' not in ch.name.lower()
            if is_layered and snap_attr and not_ext_left and not_ext_right:
                hidden = sn_types.Assembly(ch).get_prompt('Hide').get_value()
                if not hidden:
                    flat_crown_layers += 1
        lay_crown = flat_crown_layers > 0
        tkh_str = ''
        parent_assy = sn_types.Assembly(item.parent)
        assy = sn_types.Assembly(item)
        hang_h = parent_assy.obj_z.location.z
        fc_h = 0
        fc_prod = sn_types.Assembly(item)
        ext_ceil = fc_prod.get_prompt('Extend To Ceiling')
        tkh = fc_prod.get_prompt('Top KD Holes Down')
        if ext_ceil and ext_ceil.get_value() and tkh and not lay_crown:
            if tkh.get_value() == 1:
                tkh_str = 'Top KD|Down 1 Hole'
            elif tkh.get_value() == 2:
                tkh_str = 'Top KD|Down 2 Holes'
        for a in item.children:
            if a.get("IS_BP_ASSEMBLY") and 'Flat Crown' in a.name and not lay_crown:
                fc_assy = sn_types.Assembly(a)
                fc_h = fc_assy.obj_y.location.y
                fc_str = f'Flat Crown {self.to_inch_lbl(fc_h)}'
                labels.append((fc_str, hang_h + fc_assy.obj_y.location.y))
            elif a.get("IS_BP_ASSEMBLY") and 'Flat Crown' in a.name and lay_crown:
                fc_assy = sn_types.Assembly(a)
                fc_h = fc_assy.obj_y.location.y
                fc_str = f'Layered Crown'
                if flat_crown_layers == 1:
                    fc_str += ' (1 layer)'
                elif flat_crown_layers == 2:
                    fc_str += ' (2 layers)'
                labels.append((fc_str, hang_h + fc_assy.obj_y.location.y))
        labels.append(
            (tkh_str, (hang_h + fc_assy.obj_y.location.y) + unit.inch(-6)))
        labels = list(dict.fromkeys(labels))


    def add_flat_crowns(self, context, accordion, offset):
        offset = ((abs(offset) * -1) - unit.inch(15))
        flat_crowns_labels = []
        drawn_labels = []
        first_wall = self.get_first_acc_wall(accordion)
        for wall in accordion:
            for child in wall.children:
                if child.get('IS_BP_ASSEMBLY'):
                    for gchild in child.children:
                        if 'flat crown' in gchild.name.lower():
                            self.make_flat_crown_label(flat_crowns_labels, 
                                                       gchild)
        if first_wall:
            meshes = []
            for mesh in first_wall.children:
                if mesh.type == 'MESH' and 'wall mesh' in mesh.name.lower():
                    meshes.append(mesh)
            wall_offset_x = self.get_object_global_location(meshes[0])[0]
            wall_offset_x += offset
            for label, height in flat_crowns_labels:
                if label not in drawn_labels:
                    x_offset = unit.inch(-20)
                    if 'layered' in label.lower():
                        x_offset = unit.inch(-28)
                    lbl_offset = height + (len(drawn_labels) * unit.inch(2))
                    dim = sn_types.Dimension()
                    dim.parent = first_wall
                    dim.start_x(value=wall_offset_x)
                    dim.start_z(value=lbl_offset)
                    dim.set_label(label)
                    drawn_labels.append(label)


    def shift_dims_nearby_partitions(self, at_position):
        for each in bpy.context.scene.objects:
            if 'parthgt' in each.name.lower() and each.parent.type == "MESH":
                each_gl_pos = self.get_object_global_location(each.parent)
                each_x_pos = self.to_inch(each_gl_pos[0])
                each_x_pos_start = each_x_pos - 5
                each_x_pos_end = each_x_pos + 5
                if each_x_pos_start <= at_position <= each_x_pos_end:
                    each.location[2] += unit.inch(3)

    def get_strict_corner_dim_height(self, strict_corner_shelves):
        toe_kick_height = 0
        sc_assy = sn_types.Assembly(strict_corner_shelves)
        csh_dim = sc_assy.obj_z.location.z
        tsh = sc_assy.get_prompt("Add Top Shelf").get_value()
        if tsh:
            csh_dim += unit.inch(0.75)
        for tk in strict_corner_shelves.children:
            if 'toe kick' in tk.name.lower():
                tk_assy = sn_types.Assembly(tk)
                toe_kick_height = tk_assy.obj_z.location.z
        csh_dim += toe_kick_height
        return csh_dim

    def add_csh_lsh_accordion_dims(self, insert):
        csh_lsh_objects = []
        for obj in insert.instance_collection.all_objects:
            if hasattr(obj, 'name') and hasattr(obj.parent, 'name'):
                rot_z = obj.rotation_euler.z
                stringer = obj.sn_closets.is_panel_bp
                left = math.isclose(rot_z, math.radians(-90), abs_tol=1e-3)
                c_shelves = 'corner shelves' in obj.parent.name.lower()
                l_shelves = 'l shelves' in obj.parent.name.lower()
                if stringer and left and (c_shelves or l_shelves):
                    csh_lsh_objects.append(obj)
        for item in csh_lsh_objects:
            csh = 'corner shelves' in item.parent.name.lower()
            lsh = 'l shelves' in item.parent.name.lower()
            assy = sn_types.Assembly(item.parent)
            panel_height = item.location[2]
            width = abs(assy.obj_y.location.y)
            left_depth_pmpt = assy.get_prompt("Left Depth")
            has_top_kd = assy.get_prompt("Add Top KD").get_value()
            left_depth = left_depth_pmpt.distance_value
            left_depth_lbl = self.to_inch_lbl(left_depth)
            if has_top_kd:
                self.csh_lsh_top_kd_lbl(insert, assy, item.parent)
            self.csh_lsh_bottom_kd_lbl(insert, assy, item.parent)
            self.lsh_csh_toe_kick_lbl(assy)
            self.lsh_csh_width(insert, assy, width)
            self.lsh_csh_left_partition(insert, assy)
            self.csh_lsh_pdt_name(insert, csh, lsh, assy)
            self.csh_lsh_depth(insert, panel_height, width, left_depth_lbl)

    def csh_lsh_depth(self, insert, stringer_heigth, width, left_depth_lbl):
        hashmark = sn_types.Line(unit.inch(6), (-45, 0, 90))
        utils.copy_world_loc(insert, hashmark.anchor)
        hashmark.anchor.location[0] -= (width - unit.inch(0.75))
        hashmark.anchor.location[2] += (stringer_heigth + unit.inch(0.75))
        hashmark.anchor.rotation_euler[1] = math.radians(45)
        depth_dim = sn_types.Dimension()
        depth_dim.parent(hashmark.end_point)
        depth_dim.start_z(value=unit.inch(2))
        depth_dim.set_label(left_depth_lbl)

    def csh_lsh_pdt_name(self, insert, c_shelves, l_shelves, assy):
        pdt_label = ""
        panel_height, tk_height = 0, 0
        is_hanging = False
        panel_height_pmpt = assy.get_prompt("Panel Height")
        tk_height_pmpt = assy.get_prompt("Toe Kick Height")
        is_hanging_pmpt = assy.get_prompt("Is Hanging")
        if panel_height_pmpt and tk_height_pmpt and is_hanging_pmpt:
            panel_height = panel_height_pmpt.get_value()
            tk_height = tk_height_pmpt.get_value()
            is_hanging = is_hanging_pmpt.get_value()
        elif not panel_height_pmpt or tk_height_pmpt or is_hanging_pmpt:
            return
        if c_shelves:
            pdt_label = "Corner Shelves"
        elif l_shelves:
            pdt_label = "L-Shaped Shelves" 
        height = (assy.obj_z.location.z / 2) + tk_height
        if is_hanging:
            height =  assy.obj_z.location.z - panel_height / 2
        pdt_dim = sn_types.Dimension()
        pdt_dim.set_label(pdt_label)
        utils.copy_world_loc(insert, pdt_dim.anchor, (0, 0, height))
        utils.copy_world_rot(insert, pdt_dim.anchor, (0, -45, 0))

    def csh_lsh_top_kd_lbl(self, insert, assy, item):
        tk_height, panel_height, tk_height = 0, 0, 0
        is_hanging = False
        panel_height_pmpt = assy.get_prompt("Panel Height")
        tk_height_pmpt = assy.get_prompt("Toe Kick Height")
        is_hanging_pmpt = assy.get_prompt("Is Hanging")
        if panel_height_pmpt and tk_height_pmpt and is_hanging_pmpt:
            panel_height = panel_height_pmpt.get_value()
            tk_height = tk_height_pmpt.get_value()
            is_hanging = is_hanging_pmpt.get_value()
        elif not panel_height_pmpt or tk_height_pmpt or is_hanging_pmpt:
            return
        height = assy.obj_z.location.z + tk_height - unit.inch(1.5)
        if is_hanging:
            height = assy.obj_z.location.z - unit.inch(1.5)
        width = assy.obj_x.location.x
        kd_dim = sn_types.Dimension()
        kd_dim.set_label("KD")
        utils.copy_world_loc(insert, kd_dim.anchor)
        utils.copy_world_rot(insert, kd_dim.anchor)
        kd_dim.anchor.location[0] -= width / 2
        kd_dim.anchor.location[2] = height


    def csh_lsh_bottom_kd_lbl(self, insert, assy, item):
        tk_height, panel_height = 0, 0
        is_hanging = False
        panel_height_pmpt = assy.get_prompt("Panel Height")
        tk_height_pmpt = assy.get_prompt("Toe Kick Height")
        is_hanging_pmpt = assy.get_prompt("Is Hanging")
        if panel_height_pmpt and tk_height_pmpt and is_hanging_pmpt:
            panel_height = panel_height_pmpt.get_value()
            tk_height = tk_height_pmpt.get_value()
            is_hanging = is_hanging_pmpt.get_value()
        elif not panel_height_pmpt or tk_height_pmpt or is_hanging_pmpt:
            return
        height = tk_height
        if is_hanging:
            height = assy.obj_z.location.z - panel_height + unit.inch(1.5)
        width = assy.obj_x.location.x
        kd_dim = sn_types.Dimension()
        kd_dim.set_label("KD")
        utils.copy_world_loc(insert, kd_dim.anchor)
        utils.copy_world_rot(insert, kd_dim.anchor)
        kd_dim.anchor.location[0] -= width / 2
        kd_dim.anchor.location[2] = height

    def lsh_csh_toe_kick_lbl(self, assy):
        tk_fronts = [obj for obj in utils.get_child_objects(assy.obj_bp) if
                     obj.sn_closets.is_toe_kick_bp and
                     'front' in obj.name.lower() and
                     closet_props.part_is_not_hidden(sn_types.Assembly(obj))]

        for tk in tk_fronts:
            has_lbl = any([c.get('IS_VISDIM_A') for c in tk.children])
            if not has_lbl:
                tk_ins_assy = sn_types.Assembly(tk.parent)
                tk_skin = tk_ins_assy.get_prompt('Add TK Skin')
                lbl_txt = 'TK'
                if tk_skin and tk_skin.get_value():
                    lbl_txt += ' + 1/4" Skin'
                tk_assy = sn_types.Assembly(tk)
                tk_w = tk_assy.obj_x.location.x
                tk_h = tk_assy.obj_y.location.y
                lbl_loc = (0, tk_h/2, tk_w + unit.inch(3))
                tk_lbl = sn_types.Dimension()
                tk_lbl.set_label(lbl_txt)
                utils.copy_world_loc(tk, tk_lbl.anchor, lbl_loc)
                utils.copy_world_rot(tk, tk_lbl.anchor)

    def lsh_csh_width(self, insert, assy, width):
        wall_height = 0
        is_hanging = False
        height = unit.inch(-3)
        is_hanging_pmpt = assy.get_prompt("Is Hanging")
        wall_bp = sn_utils.get_wall_bp(assy.obj_bp)
        wall_assy = sn_types.Assembly(wall_bp)
        if wall_assy:
            wall_height = wall_assy.obj_z.location.z
        if is_hanging_pmpt:
            is_hanging = is_hanging_pmpt.get_value()
        if is_hanging:
            height = assy.obj_z.location.z + unit.inch(10)
        if abs(wall_height - height) < unit.inch(2):
            height -= unit.inch(3)
        discount = unit.inch(0.75)
        label = self.to_inch_lbl(width - discount)
        width_dim = sn_types.Dimension()
        width_dim.set_label(label)
        utils.copy_world_loc(insert, width_dim.anchor)
        utils.copy_world_rot(insert, width_dim.anchor)
        width_dim.anchor.location[0] -= width / 2
        width_dim.anchor.location[2] = height
    
    def lsh_csh_left_partition(self, insert, assy):
        panel_height, tk_height = 0, 0
        is_hanging = False
        panel_height_pmpt = assy.get_prompt("Panel Height")
        tk_height_pmpt = assy.get_prompt("Toe Kick Height")
        is_hanging_pmpt = assy.get_prompt("Is Hanging")
        if panel_height_pmpt and tk_height_pmpt and is_hanging_pmpt:
            panel_height = panel_height_pmpt.get_value()
            tk_height = tk_height_pmpt.get_value()
            is_hanging = is_hanging_pmpt.get_value()
        elif not panel_height_pmpt or tk_height_pmpt or is_hanging_pmpt:
            return
        height = panel_height
        depth = assy.obj_y.location.y
        label = self.to_inch_str(height)
        dim = sn_types.Dimension()
        dim.set_label(label)
        lbl_x = depth + unit.inch(2)
        lbl_z = (panel_height / 2) + tk_height 
        lbl_loc = (0, lbl_x, lbl_z)
        if is_hanging:
            lbl_z = assy.obj_z.location.z - (panel_height / 2)
            lbl_loc = (0, lbl_x, lbl_z)
        lbl_rot = (0, -90, 0)
        utils.copy_world_loc(insert, dim.anchor, lbl_loc)
        utils.copy_world_rot(insert, dim.anchor, lbl_rot)
        dim_x_loc = self.to_inch(dim.anchor.location[0])
        self.shift_dims_nearby_partitions(dim_x_loc)
    
    def next_wall_has_lsh_csh(self, walls_list, wall):
        if wall.name in walls_list:
            csh_lsh_count = 0
            curr_idx = walls_list.index(wall.name)
            next_wall_name = None
            if curr_idx == len(walls_list) - 1:
                next_wall_name = walls_list[0]
            elif curr_idx < len(walls_list) - 1:
                next_wall_name = walls_list[curr_idx + 1]
            next_wall_obj = bpy.data.objects[next_wall_name]
            for obj in next_wall_obj.children:
                lsh = 'l shelves' in obj.name.lower()
                csh = 'corner shelves' in obj.name.lower()
                if lsh or csh:
                    csh_lsh_count += 1
            if csh_lsh_count > 0:
                return True
        return False

    def accordion_orthoscale_ratio(self, width):
        # NOTE don't touch those numbers unless you do an ab-exponential
        #      regression X-> walls width sum / Y -> good ortho scale
        #      still you see I added a padding while using it.
        a = 7.84889826
        b = 1.04456527
        result = (a * math.pow(b, width)) + self.ac_pad
        return result

    def planview_orthoscale_ratio(self, width):
        # NOTE don't touch those numbers unless you do an ab-exponential
        #      regression X-> walls width sum / Y -> good ortho scale
        #      still you see I added a padding while using it.
        a = 3.78424377
        b = 1.099096036
        result = (a * math.pow(b, width)) + 2
        return result

    def adjust_accordion_dims(self, insert):
        insert_objs = insert.instance_collection.all_objects
        dims = [obj for obj in insert_objs if obj.get('IS_VISDIM_A')]
        for d in dims:
            dim_loc_x = d.location.x
            dim_loc_y = d.location.y
            dim_loc_z = d.matrix_world.translation.z

            parent_part = d.parent
            part_rot_z = parent_part.rotation_euler.z
            parent_insert = parent_part.parent

            in_top_shelf_l = ('topshelf' in parent_part.name.lower() and
                              math.isclose(part_rot_z, math.radians(90), abs_tol=1e-3))
            in_filler = parent_part.sn_closets.is_filler_bp

            if in_top_shelf_l:
                loc_off = (0, -dim_loc_x * 2, dim_loc_z)
                utils.copy_world_loc(insert, d, loc_off)
                d.rotation_euler.z = math.radians(-90)

            if in_filler:
                in_l_shelf = 'l shelves' in parent_insert.name.lower()
                left = 'left' in parent_part.name.lower()
                if in_l_shelf and left:
                    prod_assy = sn_types.Assembly(parent_insert)
                    depth = prod_assy.obj_y.location.y
                    loc_off = (0, depth, dim_loc_z)
                    utils.copy_world_loc(insert, d, loc_off)

    def add_remaining_space_lbl(self, wall, value, position):
        x_loc = 0
        wall_length = self.to_inch(sn_types.Assembly(wall).obj_x.location.x)
        if position == "left":
            x_loc = unit.inch(value / 2)
        elif position == "right":
            x_loc = unit.inch(wall_length - (value / 2))
        label = str(value) + "\""
        spdim = sn_types.Dimension()
        spdim.parent(wall)
        spdim.start_x(value=x_loc)
        spdim.start_y(value=0)
        spdim.start_z(value=unit.inch(-3))
        spdim.set_label(label)
        self.ignore_obj_list.append(spdim)
        return spdim

    def cross_sect_lshcsh_elvs_kds(self, shelf_assy, wall_assy, floor_obj):
        tk_height = 0
        is_hanging = False
        discount = unit.inch(0.75)
        shelf_depth = abs(shelf_assy.obj_y.location.y)
        shelf_height = shelf_assy.obj_z.location.z
        wall_length = wall_assy.obj_x.location.x
        is_hanging_pmpt = shelf_assy.get_prompt("Is Hanging")
        tk_height_pmpt = shelf_assy.get_prompt("Toe Kick Height")
        panel_height_pmpt = shelf_assy.get_prompt("Panel Height")
        if panel_height_pmpt and tk_height_pmpt and is_hanging_pmpt:
            panel_height = panel_height_pmpt.get_value()
            tk_height = tk_height_pmpt.get_value()
            is_hanging = is_hanging_pmpt.get_value()
        bottom_kd_height = tk_height
        top_kd_height = shelf_height + tk_height - unit.inch(1.5)
        if is_hanging_pmpt:
            is_hanging = is_hanging_pmpt.get_value()
        if is_hanging:
            bottom_kd_height = shelf_height - panel_height + unit.inch(1.5)
            top_kd_height = shelf_height - unit.inch(1.5)
        bottom_kd_dim = sn_types.Dimension()
        bottom_kd_dim.parent(floor_obj)
        bottom_kd_dim.set_label("KD")
        offset = (wall_length - (shelf_depth / 2), 0, bottom_kd_height)
        utils.copy_world_loc(floor_obj, bottom_kd_dim.anchor, offset)
        utils.copy_world_rot(floor_obj, bottom_kd_dim.anchor)
        top_kd_dim = sn_types.Dimension()
        top_kd_dim.parent(floor_obj)
        top_kd_dim.set_label("KD")
        offset = (wall_length - (shelf_depth / 2), 0, top_kd_height)
        utils.copy_world_loc(floor_obj, top_kd_dim.anchor, offset)
        utils.copy_world_rot(floor_obj, top_kd_dim.anchor)
    
    def cross_sect_lshcsh_elvs_panel(self, shelf_assy, wall_assy, floor_obj):
        tk_height = 0
        is_hanging = False
        wall_length = wall_assy.obj_x.location.x
        is_hanging_pmpt = shelf_assy.get_prompt("Is Hanging")
        tk_height_pmpt = shelf_assy.get_prompt("Toe Kick Height")
        panel_height_pmpt = shelf_assy.get_prompt("Panel Height")
        if panel_height_pmpt and tk_height_pmpt and is_hanging_pmpt:
            panel_height = panel_height_pmpt.get_value()
            tk_height = tk_height_pmpt.get_value()
            is_hanging = is_hanging_pmpt.get_value()
        panel_z_height = (panel_height / 2) + tk_height
        panel_height_lbl = self.to_inch_str(panel_height)
        if is_hanging_pmpt:
            is_hanging = is_hanging_pmpt.get_value()
        if is_hanging:
            panel_z_height = shelf_assy.obj_z.location.z - panel_height / 2
        panel_height_dim = sn_types.Dimension()
        panel_height_dim.parent(floor_obj)
        panel_height_dim.set_label(panel_height_lbl)
        offset = (wall_length - unit.inch(4), 0, panel_z_height)
        lbl_rot = (0, -90, 0)
        utils.copy_world_loc(floor_obj,  panel_height_dim.anchor, offset)
        utils.copy_world_rot(floor_obj,  panel_height_dim.anchor, lbl_rot)
    
    def cross_sect_lshcsh_elvs_width(self, shelf_assy, wall_assy, floor_obj):
        is_hanging = False
        discount = unit.inch(0.75)
        width_height = unit.inch(-3)
        shelf_depth = abs(shelf_assy.obj_y.location.y)
        wall_length = wall_assy.obj_x.location.x
        width_lbl = self.to_inch_lbl(shelf_depth - discount)
        is_hanging_pmpt = shelf_assy.get_prompt("Is Hanging")
        if is_hanging_pmpt:
            is_hanging = is_hanging_pmpt.get_value()
        if is_hanging:
            width_height = shelf_assy.obj_z.location.z + unit.inch(10)
        width_dim = sn_types.Dimension()
        width_dim.parent(floor_obj)
        width_dim.set_label(width_lbl)
        offset = (wall_length - (shelf_depth / 2), 0, width_height)
        utils.copy_world_loc(floor_obj, width_dim.anchor, offset)
        utils.copy_world_rot(floor_obj, width_dim.anchor)

    def add_corner_cross_sections_dims(self, walls, wall_groups):
        for wall_name, wall_grp in wall_groups.items():
            wall_bp = bpy.data.objects[f"{wall_name}"]
            right_wall = sn_types.Wall(wall_bp).get_connected_wall("RIGHT")
            right_wall_bp = right_wall.obj_bp
            right_wall_name = right_wall.obj_bp.name
            if not right_wall:
                return
            corners_shlvs = self.get_lsh_csh_assemblies(right_wall_bp)
            if not corners_shlvs:
                return
            for shelf in corners_shlvs:
                scene_name = f'{wall_grp.name}'
                floor_name = f'{wall_grp.name} Floor'
                bpy.context.window.scene = bpy.data.scenes[scene_name]
                floor_obj = bpy.data.objects[floor_name]
                floor = floor_obj
                shelf_assy = sn_types.Assembly(shelf)
                sh_assy = shelf_assy
                wall_assy = sn_types.Assembly(wall_bp)
                if not wall_assy or not shelf_assy:
                    return
                self.cross_sect_lshcsh_elvs_width(sh_assy, wall_assy, floor)
                self.cross_sect_lshcsh_elvs_kds(sh_assy, wall_assy, floor)
                self.cross_sect_lshcsh_elvs_panel(sh_assy, wall_assy, floor)

    def accordion_obstacles(self, grp, walls_list, wall):
        for item in grp.objects:
            is_obstacle = item.get('IS_OBSTACLE')
            hidden_on_accordions = item.get('SHOW_ON_ACCORDIONS', True) == False
            if is_obstacle and not hidden_on_accordions:
                self.pick_n_place_obstacles_cross_sections(
                    walls_list, wall, item)
                for child in item.children:
                    if child.name in grp.objects:
                        grp.objects.unlink(child)
                if sn_utils.get_wall_bp(item) == wall:
                    self.place_wall_obstacle_mesh(wall, item)
            if is_obstacle and hidden_on_accordions:
            # NOTE Seems odd, but if the obstacle isn't explicitely hidden
            # it will be shown, also dealing with older projects
                for child in item.children:
                    grp.objects.unlink(child)
                grp.objects.unlink(item)

    def obstacles_shading(self, accordion_scene):
        shading = self.get_shading_material()
        if shading:
            obstacle_to_shade = [o for o in accordion_scene.objects \
                if o.get("OBSTACLE_SHADING_MESH") or o.get("GLASS_SHADING_MESH")]
            for obj in obstacle_to_shade:
                obj.data.materials.append(shading)

    def get_shading_material(self):
        CLASSY_CLOSETS_RGBA = (0.275,0.056,0.087,1)
        shading = None
        has_material = [m for m in bpy.data.materials \
            if m.name == "ShadingColor"]
        if len(has_material) == 0:
            bpy.data.materials.new(name="ShadingColor")
        shading = bpy.data.materials["ShadingColor"]
        shading.use_nodes = True
        node = shading.node_tree.nodes['Principled BSDF']
        color = node.inputs['Base Color'].default_value = CLASSY_CLOSETS_RGBA
        return shading

    def place_wall_obstacle_mesh(self, wall, item):
        obs_assy = sn_types.Assembly(item)
        dim_x = obs_assy.obj_x.location.x
        dim_z = obs_assy.obj_z.location.z
        loc_x, _, loc_z = item.location
        [wall_mesh] = [m for m in wall.children if m.type == "MESH"]
        obs_mesh = utils.create_cube_mesh(
                        "obstacle_mesh", (dim_x, unit.inch(2), dim_z))
        obs_mesh.parent = wall_mesh
        obs_mesh.location = (loc_x, unit.inch(-2), loc_z)
        obs_mesh["OBSTACLE_SHADING_MESH"] = True
        label = re.sub(r'\d{3}', '', item.name)
        label = re.sub(r'\w*.\d{1,3}.', '', label)
        label = label.replace(".", "")
        obs_dim = sn_types.Dimension()
        obs_dim.parent(obs_mesh)
        obs_dim.set_label(label)
        obs_dim.start_x(value=dim_x / 2)
        obs_dim.start_z(value=dim_z / 2)

    def sqrooms_obstacl_neighbor_walls(self, walls_list, wall):
        curr_idx = walls_list.index(wall.name)
        prvs_wall, next_wall = None, None
        if curr_idx == 0:
            prvs_wall = bpy.data.objects[walls_list[-1]]
            next_wall = bpy.data.objects[walls_list[1]]
        elif curr_idx in [1, 2]:
            prvs_wall = bpy.data.objects[walls_list[curr_idx - 1]]
            next_wall = bpy.data.objects[walls_list[curr_idx + 1]]
        elif curr_idx == 3:
            prvs_wall = bpy.data.objects[walls_list[curr_idx - 1]]
            next_wall = bpy.data.objects[walls_list[0]]
        return (prvs_wall, next_wall)

    def open_end_obstacl_neighbor_walls(self, walls_list, wall):
        curr_idx = walls_list.index(wall.name)
        walls_qty = len(walls_list) - 1
        prvs_wall, next_wall = None, None
        if curr_idx == 0:
            next_wall = bpy.data.objects[walls_list[curr_idx + 1]]
        elif curr_idx == walls_qty:
            prvs_wall = bpy.data.objects[walls_list[curr_idx - 1]]
        elif curr_idx < walls_qty:
            if curr_idx != 0:
                prvs_wall = bpy.data.objects[walls_list[curr_idx - 1]]
            if curr_idx != len(walls_list) - 1:
                next_wall = bpy.data.objects[walls_list[curr_idx + 1]]
        return (prvs_wall, next_wall)
    
    # TODO change function signature to be more intuitive for later use
    def place_obstacl_cs_mesh(self, parent, dim_y, dim_z, loc_z, position):
        if self.empty_wall(parent):
            return
        wall_length = sn_types.Assembly(parent).obj_x.location.x
        [wall_mesh] = [m for m in parent.children if m.type == "MESH"]
        x, y, z = dim_y, unit.inch(2), dim_z
        x_pos, z_pos = 0, loc_z
        if position == "left":
            x_pos = wall_length - x
        elif position == "right":
            pass
        cs_mesh = utils.create_cube_mesh(
            "obstcl_cross_section", (x, y, z))
        cs_mesh["OBSTACLE_SHADING_MESH"] = True
        utils.copy_world_loc(wall_mesh, cs_mesh, (x_pos, unit.inch(-2), z_pos))

    def place_obstacl_cross_sections(self, obstacle, walls):
        CS_THRESHOLD = unit.inch(6)
        assy = sn_types.Assembly(obstacle)
        obstacle_wall = utils.get_wall_bp(obstacle)
        dim_x = abs(assy.obj_x.location.x)
        dim_y = abs(assy.obj_y.location.y)
        dim_z = abs(assy.obj_z.location.z)
        wall_length = sn_types.Assembly(obstacle_wall).obj_x.location.x
        left, right = walls
        loc_x, loc_y, loc_z = obstacle.location
        left_cs = left and loc_x < CS_THRESHOLD
        right_cs = right and (wall_length - (loc_x + dim_x)) < CS_THRESHOLD 
        if left_cs:
            self.place_obstacl_cs_mesh(left, dim_y, dim_z, loc_z, "left")
        if right_cs:
            self.place_obstacl_cs_mesh(right, dim_y, dim_z, loc_z, "right")

    def pick_n_place_obstacles_cross_sections(self, walls_list, wall, obstacle):
        type = bpy.context.scene.sn_roombuilder.room_type
        scene_name = bpy.context.scene.name.lower()
        accordion_sc = "accordion" in scene_name
        elevation_sc = "cswall-wall" in scene_name
        obstacle_same_wall = wall == utils.get_wall_bp(obstacle)
        acc_rule = accordion_sc and obstacle_same_wall and type != 'SINGLE'
        elv_rule = elevation_sc
        if acc_rule or elv_rule:
            walls = None, None
            if type == 'SQUARE':
                walls = self.sqrooms_obstacl_neighbor_walls(walls_list, wall)
            if type == 'LSHAPE' or type == 'CUSTOM' or type == 'USHAPE':
                walls = self.open_end_obstacl_neighbor_walls(walls_list, wall)
            if accordion_sc:
                self.place_obstacl_cross_sections(obstacle, walls)
            elif elevation_sc:
                return walls

    def add_obstacles_cs_on_elvs(self, context, main_sc_objs, wall_groups):
        CS_THRESHOLD = unit.inch(6)
        walls_list = [w.name for w in main_sc_objs if w.get("IS_BP_WALL")]
        obstacles = [o for o in main_sc_objs if o.get("IS_OBSTACLE")]
        for obstacle in obstacles:
            obst_ch = obstacle.children
            obstacle_meshes = [m for m in obst_ch if m.type == "MESH"]
            left_elv_coll, right_elv_coll = None, None
            wall = utils.get_wall_bp(obstacle)
            wall_length = sn_types.Assembly(wall).obj_x.location.x
            left, right = self.pick_n_place_obstacles_cross_sections(
                walls_list, wall, obstacle)
            assy = sn_types.Assembly(obstacle)
            dim_x = abs(assy.obj_x.location.x)
            loc_x = obstacle.location[0]
            left_cs = left and loc_x < CS_THRESHOLD
            right_cs = right and (wall_length - (loc_x + dim_x)) < CS_THRESHOLD
            if left_cs and left.name in wall_groups.keys():
                left_elv_coll = wall_groups[left.name]
                for mesh in obstacle_meshes:
                    left_elv_coll.objects.link(mesh)
            if right_cs and left.name in wall_groups.keys():
                right_elv_coll = wall_groups[right.name]
                for mesh in obstacle_meshes:
                    right_elv_coll.objects.link(mesh)

    def add_remaining_space_lbl_elv(self, wall_grp, wall, value, position):
        x_loc = 0
        scene_name = f'{wall_grp.name}'
        floor_name = f'{wall_grp.name} Floor'
        floor_obj = bpy.data.objects[floor_name]
        bpy.context.window.scene = bpy.data.scenes[scene_name]
        wall_length = self.to_inch(sn_types.Assembly(wall).obj_x.location.x)
        if position == "left":
            x_loc = unit.inch(value / 2)
        elif position == "right":
            x_loc = unit.inch(wall_length - (value / 2))
        label = str(round(value, 2)) + "\""
        spdim = sn_types.Dimension()
        spdim.parent(floor_obj)
        utils.copy_world_loc(
            floor_obj, spdim.anchor, (x_loc, 0, unit.inch(-3)))
        utils.copy_world_rot(floor_obj, spdim.anchor)
        spdim.set_label(label)
        self.ignore_obj_list.append(spdim)
        return spdim

    def remove_accordion_scene_material_pointers(self, accordion_scene):
        to_avoid = []
        for obj in accordion_scene.objects:
            skippable_meshes = [c for c in obj.children \
                if c.type == 'MESH' and not c.hide_viewport]
            shown = len(skippable_meshes) > 0
            is_door = obj.sn_closets.is_door_bp
            is_hamper_door = obj.sn_closets.is_hamper_front_bp
            is_drawer_door = obj.sn_closets.is_drawer_front_bp
            skippable = (is_door or is_hamper_door or is_drawer_door) and shown
            if skippable:
                to_avoid += skippable_meshes
        for obj in accordion_scene.objects:
            if obj not in to_avoid:
                not_hidden = not obj.hide_render and not obj.hide_viewport
                for mat_slot in obj.snap.material_slots:
                    obj.snap.material_slots.remove(0)
                obj.snap.type_mesh = 'NONE'
                if obj.type == 'MESH' and not_hidden:
                    obj.data.materials.clear()

    def add_accordion_views(self, context):        
        main_sc_objs = bpy.data.scenes["_Main"].objects
        dimprops = get_dimension_props()
        any_csh_lsh = [o for o in bpy.data.objects if 'cshlsh' in o.name.lower()]
        has_csh_lsh = len(any_csh_lsh) > 0
        show_csh_lsh = dimprops.corner_shelves_l_shelves
        wall_groups = {}
        extra_dims = {}
        main_scene, new_walls = self.main_accordion_scene(context)
        data_dict = self.fetch_accordions_walls_data(main_scene, new_walls)
        accordions = self.divide_walls_to_acordions(main_scene, data_dict)
        main_sc_objs = [o for o in bpy.data.scenes["Z_Main Accordion"].objects]
        for wall in new_walls:
            wall_name = wall.obj_bp.name
            wall_obj = context.view_layer.objects[wall.obj_bp.name]
            wall_groups[wall_name] = None
        walls_list = list(wall_groups.keys())
        assemblies_dict = self.get_walls_assys_arrangement(wall_groups)
        # Getting the accordion cross-sections displacement
        targets, walls_rem_spaces = self.accordion_instances_arragement(new_walls,
                                                      accordions,
                                                      assemblies_dict,
                                                      extra_dims)
        # Create Accordion Scenes
        for i, accordion in enumerate(accordions):   
            empty_acc_check = []
            for j, wall in enumerate(accordion):
                empty = self.empty_wall(wall)
                just_door = self.is_just_door_wall(wall)
                if empty or just_door:
                    empty_acc_check.append(True)
                elif not empty and not just_door:
                    empty_acc_check.append(False)
            empty_acc_check = list(set(empty_acc_check))
            if len(empty_acc_check) == 1 and empty_acc_check[0] == True:
                continue
            walls_length_sum = 0
            walls_heights = []
            grp_name = "Accordion " + str(i + 1)
            grp = bpy.data.collections.new(grp_name)
            new_scene = self.create_acordion_scene(context, grp)
            for j, wall in enumerate(accordion):
                wall_assy = sn_types.Assembly(wall)
                just_door = self.is_just_door_wall(wall)
                empty = self.empty_wall(wall)
                has_lsh_csh = self.next_wall_has_lsh_csh(walls_list, wall)
                current_wall_width = sn_types.Assembly(wall).obj_x.location.x
                walls_length_sum += current_wall_width
                walls_heights.append(sn_types.Assembly(wall).obj_z.location.z)
                # Making copies of existing annotations
                if (just_door or empty) and not has_lsh_csh:
                    continue
                self.group_every_children_on_acc(grp, wall)
                # NOTE wall height / building height need to be added just 
                # at the first wall of each accordion. So we 
                # remove the existing ones and apply as desired
                for obj in wall.children:
                    if obj.get("IS_VISDIM_A"):
                        bpy.data.objects.remove(obj, do_unlink=True)
                    if obj.snap.is_wall_mesh:
                        wall_mesh = self.create_elevation_wall(wall_assy, 'Acc')
                        grp.objects.link(wall_mesh)
                        grp.objects.unlink(obj)
                    if obj.get('IS_OBSTACLE'):
                        on_accordions = obj.get('SHOW_ON_ACCORDIONS', True)
                        if on_accordions:
                            self.add_obstacle_height_width_dim(obj)
                            # NOTE check if it will be delete or re-included
                            # for child in obj.children:
                            #     new_scene.collection.objects.link(child)
                            #     child.hide_render = False

                new_scene.collection.objects.link(wall)
                # left_space, right_space = walls_rem_spaces.get(wall, (0, 0))
                self.link_tagged_dims_to_scene(new_scene, wall)
                self.accordion_obstacles(grp, walls_list, wall)
                target = targets.get(wall)
                has_target = target is not None
                if has_target:
                    left_insert, right_insert = target
                    has_left_insert = left_insert is not None
                    has_right_insert = right_insert is not None
                    if has_left_insert:
                        new_scene.collection.objects.link(left_insert)
                        if show_csh_lsh and has_csh_lsh:
                            self.add_csh_lsh_accordion_dims(left_insert)
                        
                    if has_right_insert:
                        new_scene.collection.objects.link(right_insert)
                        if show_csh_lsh and has_csh_lsh:
                            self.add_csh_lsh_accordion_dims(right_insert)
                            self.adjust_accordion_dims(right_insert)
                wall_assy = sn_types.Assembly(wall) 
                acc_floor = self.create_elevation_floor(new_scene, wall_assy)
                wall_obj = sn_types.Wall(obj_bp=wall)
                wall_groups_list = wall_obj.get_wall_groups()
                for item in wall_groups_list:
                    if 'door' in item.name.lower():
                        for door in item.children:
                            if 'door frame' in door.name.lower():
                                self.return_wall_labels(wall,
                                                        door, 
                                                        False, 
                                                        True)
            offset = self.accordion_building_height_ceiling_height(context, 
                                                                   accordion,
                                                                   walls_list,
                                                                   extra_dims,
                                                                   walls_rem_spaces)
            self.add_flat_crowns(context, accordion, offset)
            proportion = round((walls_length_sum / max(walls_heights)), 2)
            instance_name = "Accordion Instance " + str(i + 1)
            instance = bpy.data.objects.new(instance_name, None)
            instance.instance_type = 'COLLECTION'
            instance.instance_collection = grp
            new_scene.name = grp_name
            new_scene.collection.objects.link(instance)
            self.obstacles_shading(new_scene)
            new_scene.render.resolution_x = 3600
            new_scene.render.resolution_y = 1800
            new_scene.snap.scene_type = 'ACCORDION'
            camera = self.create_camera(new_scene)
            camera.rotation_euler.x = math.radians(90.0)
            camera.rotation_euler.z = 0
            self.hide_cross_sections_for_camera(new_scene)
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.view3d.camera_to_view_selected()
            camera.data.type = 'ORTHO'
            # Ratio done by ab-exponential regression 
            # Walls length X good ortho prop.
            ratio = self.accordion_orthoscale_ratio(walls_length_sum)
            camera.data.ortho_scale = ratio
            instance.hide_select = True
            bpy.ops.object.select_all(action='DESELECT')
            self.show_cross_sections_for_camera(new_scene)
            

    def hide_cross_sections_for_camera(self, new_scene):
        for o in new_scene.objects: 
            left_insert = 'left_ins' in o.name.lower()
            right_insert = 'right_ins' in o.name.lower()
            if left_insert or right_insert:
                o.hide_viewport = True
    
    def show_cross_sections_for_camera(self, new_scene):
        for o in new_scene.objects: 
            left_insert = 'left_ins' in o.name.lower()
            right_insert = 'right_ins' in o.name.lower()
            if left_insert or right_insert:
                o.hide_viewport = False

    def key_with_max_value(self, d):
        v = list(d.values())
        k = list(d.keys())
        return k[v.index(max(v))]

    def key_with_min_value(self, d):
        v = list(d.values())
        k = list(d.keys())
        return k[v.index(min(v))]

    def create_elevation_floor(self, scene, wall):
        wall_parts = wall.obj_bp.children
        [wall_mesh] = [obj for obj in wall_parts if obj.snap.is_wall_mesh]

        panels = [sn_types.Assembly(part) for obj in wall_parts
                  if obj.get('IS_BP_CLOSET') for part in obj.children
                  if part.sn_closets.is_panel_bp]

        depths = [p.obj_y.location.y for p in panels
                  if closet_props.part_is_not_hidden(p)]

        elv_floor_width = wall.obj_x.location.x

        if len(depths) > 0:
            elv_floor_depth = min(depths)
        else:
            elv_floor_depth = -wall_mesh.dimensions.y

        elv_floor_size = (elv_floor_width, elv_floor_depth)
        elv_floor_name = f'{scene.name} Floor'
        elv_top_name = f'{scene.name} Top'
        elv_floor = utils.create_floor_mesh(elv_floor_name, elv_floor_size)
        elv_top = utils.create_floor_mesh(elv_top_name,elv_floor_size)
        utils.copy_world_loc(wall.obj_bp, elv_floor)
        utils.copy_world_rot(wall.obj_bp, elv_floor)
        utils.copy_world_loc(wall.obj_bp, elv_top, (0, 0, wall_mesh.dimensions.z))
        utils.copy_world_rot(wall.obj_bp, elv_top)
        return elv_floor

    def create_elevation_wall(self, wall_assy, prefix):
        wall_bp = wall_assy.obj_bp
        wall_mesh_name = f'{prefix} {wall_bp.snap.name_object}'
        wall_mesh_off = unit.inch(0.002)

        elv_wall_size = (wall_assy.obj_x.location.x + wall_mesh_off,
                        wall_assy.obj_z.location.z)

        elv_wall = utils.create_floor_mesh(wall_mesh_name, elv_wall_size)

        utils.copy_world_loc(wall_bp, elv_wall, (-0.5 * wall_mesh_off, 0, 0))
        utils.copy_world_rot(wall_bp, elv_wall, (90, 0, 0))

        has_entry = any('Door Frame' in e.name for c in wall_bp.children
                        for e in c.children)
        if has_entry:
            for child in wall_bp.children:
                if child.snap.is_wall_mesh:
                    bool_mesh = bpy.data.objects['MESH.Door Frame.Bool Obj']
                    entry_mod = elv_wall.modifiers.new('Elv_Entry', 'BOOLEAN')
                    entry_mod.object = bool_mesh

        return elv_wall
    
    def add_annotation_label(self, wall, annotation):
        annotation_assy = sn_types.Assembly(annotation)
        annotation_label = annotation_assy.get_prompt("Label").get_value()
        an_x, an_y, an_z = annotation.location
        an_dim = sn_types.Dimension()
        utils.copy_world_loc(annotation, an_dim.anchor)
        utils.copy_world_rot(annotation, an_dim.anchor)
        an_dim.set_label(annotation_label)
        self.ignore_obj_list.append(an_dim)

    def add_obstacle_height_width_dim(self, obstacle):
        wall_bp = sn_utils.get_wall_bp(obstacle)
        if wall_bp:
            assy = sn_types.Assembly(obstacle)
            loc_x, loc_y, loc_z = obstacle.location
            dim_x = abs(assy.obj_x.location.x)
            dim_y = abs(assy.obj_y.location.y) * -1
            dim_z = abs(assy.obj_z.location.z)
            # Height 
            height_lbl = self.to_inch_lbl(loc_z)
            height_dim = sn_types.Dimension()
            height_dim.set_label(height_lbl)
            utils.copy_world_loc(wall_bp, height_dim.anchor, (loc_x, 0, 0))
            utils.copy_world_rot(wall_bp, height_dim.anchor)
            height_dim.end_point.location.z = loc_z
            # Width
            width_lbl = self.to_inch_lbl(loc_x)
            width_dim = sn_types.Dimension()
            width_dim.set_label(width_lbl)
            utils.copy_world_loc(wall_bp, width_dim.anchor, (0, 0, loc_z))
            utils.copy_world_rot(wall_bp, width_dim.anchor)
            width_dim.end_point.location.x = loc_x


    def create_elv_view_scene(self, context, assembly, grp):
        if assembly.obj_bp and assembly.obj_x and assembly.obj_y and assembly.obj_z:
            new_scene = self.create_new_scene(context, grp, assembly.obj_bp)

            self.create_elevation_floor(new_scene, assembly)
            self.group_children(grp, assembly.obj_bp)
            wall_mesh = self.create_elevation_wall(assembly, 'Elv')
            grp.objects.link(wall_mesh)

            instance = bpy.data.objects.new(
                assembly.obj_bp.snap.name_object + " " + "Instance", None)
            new_scene.collection.objects.link(instance)
            instance.instance_type = 'COLLECTION'
            instance.instance_collection = grp
            # Add partitions to the dimension ignore list so
            # it won't be linked to the scene "automatically"
            #
            # It also get rid of the hang height dimension
            self.ignore_obj_list.append(assembly.obj_bp)
            for item in assembly.obj_bp.children:
                if item.get("IS_BP_ASSEMBLY"):
                    for n_item in item.children:
                        if n_item.sn_closets.is_panel_bp: 
                            self.ignore_obj_list.append(n_item)

                if any('Door Frame' in c.name for c in item.children):
                    self.return_wall_labels(assembly.obj_bp, item, True)

                if item.get("IS_VISDIM_A"):
                    self.ignore_obj_list.append(item)

                if item.get('IS_OBSTACLE') and item.get('SHOW_ON_ELEVATIONS', True):
                    self.add_obstacle_height_width_dim(item)
                    for child in item.children:
                        new_scene.collection.objects.link(child)
                        child.hide_render = False


            x_offset = assembly.obj_x.location.x / 2
            text_loc = (x_offset, 0, -unit.inch(10))
            self.elv_wall_labels(assembly, text_loc)
            self.link_tagged_dims_to_scene(new_scene, assembly.obj_bp)
            self.link_custom_entities_to_scene(new_scene, assembly.obj_bp)

            camera = self.create_camera(new_scene)
            camera.rotation_euler.x = math.radians(90.0)
            camera.rotation_euler.z = assembly.obj_bp.rotation_euler.z
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.view3d.camera_to_view_selected()
            camera.data.type = 'ORTHO'
            camera.data.ortho_scale += self.pv_pad
            instance.hide_select = True
            bpy.ops.object.select_all(action='DESELECT')


    def create_single_elv_view(self, context):
        grp = bpy.data.collections.new(self.single_scene_name)

        bpy.ops.scene.new('INVOKE_DEFAULT', type='EMPTY')
        new_scene = context.scene
        new_scene.name = grp.name
        new_scene.snap.name_scene = self.single_scene_name
        new_scene.snap.elevation_img_name = self.single_scene_name
        new_scene.snap.plan_view_scene = False
        new_scene.snap.elevation_scene = True
        self.create_linesets(new_scene)

        for item in self.single_scene_objs:
            obj = bpy.data.objects[item.name]
            self.group_children(grp, obj)
            self.link_dims_to_scene(new_scene, obj)

        instance = bpy.data.objects.new(
            self.single_scene_name + " " + "Instance", None)
        new_scene.collection.objects.link(instance)
        instance.instance_type = 'COLLECTION'
        instance.instance_collection = grp

        new_scene.world = self.main_scene.world
        # ----------------------------------------------------------------------------------------

        # self.link_dims_to_scene(new_scene, assembly.obj_bp)

        # Skip for now
        # self.add_text(context, assembly)

        camera = self.create_camera(new_scene)
        camera.rotation_euler.x = math.radians(90.0)
        # camera.rotation_euler.z = assembly.obj_bp.rotation_euler.z
        
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.view3d.camera_to_view_selected()
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale += self.pv_pad
        #bpy.data.objects[grp.name + ' Instance'].hide_select = True

    def shelf_is_kd(self, shelf_obj):
        """
        Find top and bottom KD shelves by looking for expression in drivers.
        Used to remove top or bottom shelves from Freestyle linesets
        """
        if shelf_obj.sn_closets.is_shelf_bp:
            shelf_part = sn_types.Part(shelf_obj)
            parent_obj = shelf_obj.parent
            lock_shelf_pmt = shelf_part.get_prompt('Is Locked Shelf')
            lock_shelf = ''
            if lock_shelf_pmt:
                lock_shelf = lock_shelf_pmt.get_value()
            top_bot_kd = False

            # Check parent assembly
            in_drawer = parent_obj.sn_closets.is_drawer_stack_bp

            if shelf_obj.animation_data:

                for d in shelf_obj.animation_data.drivers:
                    exp = d.driver.expression
                    rem_top_str = 'Remove_Top_Shelf'
                    rem_bot_str = 'Remove_Bottom_Shelf'
                    rem_bot_hang_str = 'Remove_Bottom_Hanging_Shelf'
                    top_kd_str = 'Top_KD'
                    bot_kd_str = 'Bottom_KD'
                    if (rem_top_str in exp or rem_bot_str in exp or
                    top_kd_str in exp or bot_kd_str in exp or rem_bot_hang_str):
                        top_bot_kd = True

                return lock_shelf and (top_bot_kd or in_drawer)
            else:
                return False
        else:
            return False

    def parts_for_freestyle(self):
        """
        Generator that returns the List of all (FS) Freestyle qualified parts
        It skips lots of items that doesn't need to be evaluated by FS
        """
        for obj in bpy.data.objects:
            not_hidden = closet_props.part_is_not_hidden(sn_types.Part(obj))
            is_skip = any(re.findall('|'.join(fet.FS_SKIPS), obj.name))
            if not_hidden and not is_skip:
                yield obj

    def add_meshes_to_freestyle_collections(self):
        for item in self.parts_for_freestyle():
            exc_objs = []
            in_vis = (eval(f'{repr(item)}{prop}') for prop in fet.VIS_TYPES)
            include_vix_override = (eval(f'{repr(item)}{prop}') for prop in fet.VIS_INCLUDE_OVERRIDE)
            in_hide = (eval(f'{repr(item)}{prop}') for prop in fet.HIDE_TYPES)
            include_hide_override = (eval(f'{repr(item)}{prop}') for prop in fet.HIDE_INCLUDE_OVERRIDE)
            is_kd = self.shelf_is_kd(item)
            is_pv_dim_mesh = "pv_wallbreak_msh" in item.name

            exclude_vis = any(in_vis) and not any(include_vix_override)
            exclude_hide = (any(in_hide) or is_kd) and not any(include_hide_override)

            if exclude_vis or exclude_hide or is_pv_dim_mesh:
                if item.type == 'MESH':
                    exc_objs.append(item)
                else:
                    part = sn_types.Part(item)
                    cutpart = part.get_cutparts()
                    if cutpart:
                        exc_objs.extend(cutpart)
                    else:
                        parts = [c for c in item.children if c.type == 'MESH']
                        exc_objs.extend(parts)

            for obj in exc_objs:
                if exclude_vis or is_pv_dim_mesh:
                    if obj.name not in self.FS_VIS_EXCLUSION_COLL.objects:
                        self.FS_VIS_EXCLUSION_COLL.objects.link(obj)

                if exclude_hide:
                    if obj.name not in self.FS_HIDE_EXCLUSION_COLL.objects:
                        self.FS_HIDE_EXCLUSION_COLL.objects.link(obj)

        pv_icons = [obj for obj in bpy.data.objects if 'ICON.' in obj.name]

        for obj in pv_icons:
            if obj.name not in self.ICONS_COLL:
                self.ICONS_COLL.objects.link(obj)
        
        for obj in bpy.data.objects:
            entry_door = utils.get_entry_door_bp(obj)
            no_obj_x = 'obj_x' not in obj.name.lower()
            no_obj_y = 'obj_y' not in obj.name.lower()
            no_obj_z = 'obj_z' not in obj.name.lower()
            no_pmpt  = 'obj_prompts' not in obj.name.lower()
            if entry_door and no_obj_x and no_obj_y and no_obj_z and no_pmpt:
                if obj.name not in self.FS_HIDE_EXCLUSION_COLL.objects:
                    self.FS_HIDE_EXCLUSION_COLL.objects.link(obj)

    def write_island_height(self, island, x_loc):
        island_assembly = sn_types.Assembly(obj_bp=island)
        height_label = sn_types.Dimension()
        dim_x = abs(island_assembly.obj_x.location.x)
        dim_z = abs(island_assembly.obj_z.location.z)
        x_0 = x_loc-unit.inch(8)-dim_x/2
        height_label.start_x(value=x_0)
        height_label.start_z(value=unit.inch(0))
        tk_height = island_assembly.get_prompt("Toe Kick Height").get_value()
        top_thickness = island_assembly.get_prompt("Top Thickness").get_value()
        height = tk_height + dim_z + 2*top_thickness
        height_label.end_point.location = (0, 0, height)
        label = self.to_inch_lbl(height)
        height_label.set_label(label)

    def write_island_tk_height(self, island, x_loc):
        island_assembly = sn_types.Assembly(obj_bp=island)
        height_label = sn_types.Dimension()
        dim_x = abs(island_assembly.obj_x.location.x)
        x_0 = x_loc-unit.inch(4)-dim_x/2
        height_label.start_x(value=x_0)
        height_label.start_z(value=unit.inch(0))
        tk_height = island_assembly.get_prompt("Toe Kick Height").get_value()
        height_label.end_point.location = (0, 0, tk_height)
        label = self.to_inch_lbl(tk_height)
        height_label.set_label(label)

    def write_island_opening_width(self, island, x_loc):
        island_assembly = sn_types.Assembly(obj_bp=island)
        dim_x = abs(island_assembly.obj_x.location.x)
        panel_thk =\
            abs(island_assembly.get_prompt("Panel Thickness").distance_value)
        prev_value = x_loc + panel_thk - dim_x/2
        for i in range(1, 9):
            width = island_assembly.get_prompt("Opening " + str(i) + " Width")
            if width:
                width_value = width.distance_value
                x_pos = width_value/2 + prev_value
                width_label = sn_types.Dimension()
                width_label.start_x(value=x_pos)
                width_label.start_z(value=unit.inch(-4))
                label = self.to_inch_lbl(width_value)
                width_label.set_label(label)
                prev_value = prev_value + width_value + panel_thk

    def get_mat_color(self, island):
        children = island.children
        for child in children:
            name = child.name
            if "Backing" in name:
                obj = child
                break
        children = obj.children
        for child in children:
            name = child.name
            if "Part Mesh" in name:
                obj = child
                break
        material = obj.active_material
        if material is not None:
            return obj.active_material.name
        else:
            return ""

    def get_countertop_dim(self, island):
        children = island.children
        for child in children:
            name = child.name
            if "Countertop" in name:
                obj = child
                break
        obj_assembly = sn_types.Assembly(obj_bp=obj)
        obj_x = abs(obj_assembly.obj_x.location.x)
        obj_y = abs(obj_assembly.obj_y.location.y)
        return obj_x, obj_y

    def write_island_countertop(self, island, x_loc):
        island_assembly = sn_types.Assembly(obj_bp=island)
        tk_height = island_assembly.get_prompt("Toe Kick Height").get_value()
        top_thickness = island_assembly.get_prompt("Top Thickness").get_value()
        dim_z = abs(island_assembly.obj_z.location.z)
        # height = tk_height + dim_z + 2*top_thickness
        height = tk_height + dim_z
        CT_label = sn_types.Dimension()
        CT_label.start_x(value=x_loc)
        CT_label.start_z(value=height + unit.inch(6))
        no_CT =\
            island_assembly.get_prompt("No Countertop").get_value()
        if no_CT:
            label = "No Countertop"
        else:
            CT_types =\
                island_assembly.get_prompt("Countertop Type").combobox_items
            CT_value =\
                island_assembly.get_prompt("Countertop Type").get_value()
            CT_type = CT_types[CT_value].name
            CT_color = self.get_mat_color(island)
            CT_x, CT_y = self.get_countertop_dim(island)
            CT_info = CT_type + " " + CT_color
            CT_dim = self.to_inch_lbl(CT_x) + "x" + self.to_inch_lbl(CT_y)
            label = CT_info + " CT - " + CT_dim
        CT_label.set_label(label)
        hsh_len = unit.inch(6)
        hashmark = sn_types.Line(length=hsh_len, axis='X')
        hashmark.anchor.name = 'Hashmark_Overhang'
        hashmark.anchor.location.x = x_loc
        hashmark.anchor.location.z = height + unit.inch(0.3)
        hashmark.anchor.rotation_euler.y = -np.deg2rad(135)

    def write_island_pards(self, island, x_loc):
        island_assembly = sn_types.Assembly(obj_bp=island)
        dim_x = island_assembly.obj_x.location.x
        dim_z = abs(island_assembly.obj_z.location.z)
        tk_height = island_assembly.get_prompt("Toe Kick Height").get_value()
        top_thickness = island_assembly.get_prompt("Top Thickness").get_value()
        height = tk_height + dim_z + 2*top_thickness
        x_0 = x_loc - dim_x/2 - unit.inch(4)
        children = island.children
        for child in children:
            name = child.name
            if "Partition" in name:
                obj = child
                obj_x = obj.location.x
                x_pos = x_0 + obj_x
                z_pos = height - unit.inch(8)
                pard_size = sn_types.Dimension()
                pard_size.start_x(value=x_pos)
                pard_size.start_z(value=z_pos)
                pard_size.anchor.rotation_euler = (0, -np.pi/2, 0)
                obj_assembly = sn_types.Assembly(obj_bp=obj)
                dim_x = abs(obj_assembly.obj_x.location.x)
                label = self.to_inch_lbl(dim_z)
                pard_size.set_label(label)

    def write_shelf(self, obj, loc_x, loc_z, shelf_rot):
        obj_assembly = sn_types.Assembly(obj_bp=obj)
        is_locked_shelf = obj_assembly.get_prompt("Is Locked Shelf")
        is_hide = obj_assembly.get_prompt("Hide")
        obj_x = obj.location.x
        obj_z = obj.location.z
        parent_z_0 = "Shelf" in obj.parent.name and obj_z == 0
        if is_locked_shelf and is_locked_shelf.get_value() and not parent_z_0 and not is_hide.get_value():
            shelf_label = sn_types.Dimension()
            obj_dim_x = abs(obj_assembly.obj_x.location.x)
            obj_dim_z = abs(obj_assembly.obj_x.location.z)
            if shelf_rot == 0:
                x_pos = loc_x + obj_x + obj_dim_x/2
            else:
                x_pos = loc_x - obj_x + obj_dim_x/2
            z_pos = loc_z + obj_z + obj_dim_z/2
            shelf_label.start_x(value=x_pos)
            shelf_label.start_z(value=z_pos)
            shelf_label.set_label("KD")
        else:
            children = obj.children
            for child in children:
                name = child.name
                child_assembly = sn_types.Assembly(obj_bp=child)
                hide = child_assembly.get_prompt("Hide")
                if "Shelf" in name and hide is not None:
                    if shelf_rot == 0:
                        self.write_shelf(
                            child, loc_x + obj_x, loc_z + obj_z, shelf_rot)
                    else:
                        self.write_shelf(
                            child, loc_x - obj_x, loc_z + obj_z, shelf_rot)

    def write_island_shelfs(self, island, x_loc, z_loc, shelf_rot):
        island_assembly = sn_types.Assembly(obj_bp=island)
        dim_x = island_assembly.obj_x.location.x
        if shelf_rot == 0:
            x_0 = x_loc - dim_x/2
        else:
            x_0 = x_loc + dim_x/2
        children = island.children
        for child in children:
            name = child.name
            is_front =\
                round(child.rotation_euler.z, 2) == round(shelf_rot, 2)
            if ("Shelf" in name or "Drawer" in name) and is_front:
                self.write_shelf(child, x_0, z_loc, shelf_rot)

    def get_height_code(self, height):
        HAMPER_HEIGHTS = [
            ('589.280', '19H-23.78"', '19H-23.78"'),
            ('621.284', '20H-25.04"', '20H-25.04"'),
            ('653.288', '21H-26.30"', '21H-26.30"'),
            ('685.292', '22H-27.56"', '22H-27.56"')
        ]
        front_heights = common_lists.FRONT_HEIGHTS
        for item in HAMPER_HEIGHTS:
            front_heights.append(item)
        height_inch = round(unit.meter_to_inch(height), 2)
        for item in front_heights:
            item_inch = item[1].split("-")[-1:][0]
            num_inch = round(float(item_inch.split("\"")[0]), 2)
            if num_inch == height_inch:
                return item[1].split("-")[0]
        return 0

    def write_drawer(self, obj, x_loc, z_loc):
        obj_assembly = sn_types.Assembly(obj_bp=obj)
        obj_z = obj.location.z
        width = obj_assembly.obj_x.location.x
        drawer_quantity = obj_assembly.get_prompt("Drawer Quantity")
        for child in obj.children:
            if "OBJ_PROMPTS_Drawer_Fronts" in child.name:
                drawer_front_ppt_obj = child
        if drawer_quantity:
            z_loc = z_loc + obj_z
            for i in range(drawer_quantity.get_value()-1, 0, -1):
                drawer_height =\
                    drawer_front_ppt_obj.snap.get_prompt(
                        "Drawer " + str(i) + " Height").get_value()
                x_pos = x_loc + 0.8*width
                z_pos = z_loc + 0.5*drawer_height
                drawer_label = sn_types.Dimension()
                drawer_label.start_x(value=x_pos)
                drawer_label.start_z(value=z_pos)
                label = self.get_height_code(drawer_height)
                drawer_label.set_label(label)
                z_loc += drawer_height

    def query_velvet_liner(self, drawer_stack, drawer_num):
        width_in = round(unit.meter_to_inch(drawer_stack.obj_x.location.x))
        insert_width = 0
        vl18 = [3,4,5]
        vl21 = [4,5,6]
        vl24 = [4,5,6]
        if 18 <= width_in < 21:
            insert_width = 18
        elif 21 <= width_in < 24:
            insert_width = 21
        elif 24 <= width_in:
            insert_width = 24

        insert_type_ppt = drawer_stack.get_prompt(f'Jewelry Insert Type {drawer_num}')

        if insert_type_ppt and insert_width > 0:
            insert_type = insert_type_ppt.get_value()
            # Double Jewelry
            if insert_type == 0:
                upper = f'Upper Jewelry Insert Velvet Liner {insert_width}in {drawer_num}'
                lower = f'Lower Jewelry Insert Velvet Liner {insert_width}in {drawer_num}'
                u_choice = drawer_stack.get_prompt(upper).get_value()
                l_choice = drawer_stack.get_prompt(lower).get_value()
                if insert_width == 18 and (u_choice in vl18 or l_choice in vl18):
                    return True
                elif insert_width == 21 and (u_choice in vl21 or l_choice in vl21):
                    return True
                elif insert_width == 24 and (u_choice in vl24 or l_choice in vl24):
                    return True
            # STD Insert
            elif insert_type == 1:
                jwl_ins = f'Jewelry Insert {insert_width}in {drawer_num}'
                sld_ins = f'Sliding Insert {insert_width}in {drawer_num}'
                j_choice = drawer_stack.get_prompt(jwl_ins).get_value()
                s_choice = drawer_stack.get_prompt(sld_ins).get_value()
                drawer_stack.get_prompt(sld_ins)
                if insert_width == 18 and (j_choice in vl18 or s_choice in vl18):
                    return True
                elif insert_width == 21 and (j_choice in vl21 or s_choice in vl21):
                    return True
                elif insert_width == 24 and (j_choice in vl24 or s_choice in vl24):
                    return True
            # Non-STD Insert GT 16
            elif insert_type == 2:
                lower = f'Lower Jewelry Insert Velvet Liner {insert_width}in {drawer_num}'
                l_choice = drawer_stack.get_prompt(lower).get_value()
                if insert_width == 18 and l_choice in vl18:
                    return True
                elif insert_width == 21 and l_choice in vl21:
                    return True
                elif insert_width == 24 and l_choice in vl24:
                    return True
            # Non-STD Insert LT 16
            elif insert_type == 3:
                return True
        return False
    
    def get_jewelry_insert_info(self, drw_stack, drw_idx):
        drawer_stack = data_drawers.Drawer_Stack(drw_stack)

        has_velvet_liner = False
        use_dbl_drawer = drawer_stack.get_prompt("Use Double Drawer " + str(drw_idx))
        is_dbl_drawer = use_dbl_drawer.get_value()
        has_jwl_insert_pmpt = drawer_stack.get_prompt(f"Has Jewelry Insert {drw_idx}")
        has_sld_insert_pmpt = drawer_stack.get_prompt(f"Has Sliding Insert {drw_idx}")
        has_velvet_liner = self.query_velvet_liner(drawer_stack, drw_idx)

        if has_jwl_insert_pmpt and has_sld_insert_pmpt:
            has_jwl_insert = has_jwl_insert_pmpt.get_value()
            has_sld_insert = has_sld_insert_pmpt.get_value()
            if is_dbl_drawer and not has_velvet_liner:
                return "Db Jwlry"
            elif not is_dbl_drawer and not has_velvet_liner:
                if has_jwl_insert and not has_sld_insert:
                    return "Jwlry"
                elif not has_jwl_insert and has_sld_insert:
                    return "SLD"
                elif has_jwl_insert and has_sld_insert:
                    return "Jwlry + SLD"
            elif has_velvet_liner:
                return "VL"
        return ""
    
    def write_jewelry_insert(self, obj, x_loc, z_loc):
        hsh_len = unit.inch(6)
        obj_assembly = sn_types.Assembly(obj_bp=obj)
        obj_z = obj.location.z
        width = obj_assembly.obj_x.location.x
        drawer_quantity = obj_assembly.get_prompt("Drawer Quantity")
        for child in obj.children:
            if "OBJ_PROMPTS_Drawer_Fronts" in child.name:
                drawer_front_ppt_obj = child
        if drawer_quantity:
            z_loc = z_loc + obj_z
            for i in range(drawer_quantity.get_value()-1, 0, -1):
                drawer_height =\
                    drawer_front_ppt_obj.snap.get_prompt(
                        "Drawer " + str(i) + " Height").get_value()
                label = self.get_jewelry_insert_info(obj, i)
                if label != "":
                    z_offset = (drawer_height / 2) + unit.inch(0.3)
                    hashmark = sn_types.Line(length=hsh_len, axis='X')
                    hashmark.anchor.name = 'Hashmark_JewelryInsert'
                    hashmark.anchor.location.x = x_loc + width
                    hashmark.anchor.location.z = z_loc + z_offset
                    hashmark.anchor.rotation_euler.y = np.deg2rad(45)
                    drawer_label = sn_types.Dimension()
                    drawer_label.start_x(
                        value=x_loc + width + unit.inch(5.25))
                    drawer_label.start_z(
                        value=z_loc + (0.5 * drawer_height) - unit.inch(5.25))
                    drawer_label.set_label(label)
                z_loc += drawer_height

    def write_hamper(self, obj, x_loc, z_loc):
        obj_assembly = sn_types.Assembly(obj_bp=obj)
        obj_z = obj.location.z
        width = obj_assembly.obj_x.location.x
        hamper_height = obj_assembly.get_prompt("Hamper Height")
        if hamper_height:
            top_overlay =\
                obj_assembly.get_prompt("Top Overlay").get_value()
            bottom_overlay =\
                obj_assembly.get_prompt("Bottom Overlay").get_value()
            z_loc = z_loc + obj_z
            height = hamper_height.get_value()
            x_pos = x_loc + 0.8*width
            z_pos = z_loc + 0.5*height
            drawer_label = sn_types.Dimension()
            drawer_label.start_x(value=x_pos)
            drawer_label.start_z(value=z_pos)
            label = self.get_height_code(height + top_overlay + bottom_overlay)
            drawer_label.set_label(label)

    def write_obj_drawers(self, obj, x_0, z_loc, obj_rot, drawer_rot):
        children = obj.children
        for child in children:
            name = child.name
            child_assembly = sn_types.Assembly(obj_bp=child)
            child_x = child_assembly.obj_x
            rot_z = child.rotation_euler.z
            is_front =\
                round(obj_rot + rot_z, 2) == round(drawer_rot, 2)
            child_x_loc = child.location.x
            factor = 1 if round(child.rotation_euler.z, 2) == 0 else -1
            if is_front and child_x is not None:
                x_child = x_0 + factor*child_x_loc
                if "Drawer" in name:
                    self.write_drawer(child, x_child, z_loc)
                child_z_loc = child.location.z
                self.write_obj_drawers(
                    child, x_child, z_loc + child_z_loc,
                    obj_rot + rot_z, drawer_rot)
    
    def write_obj_jewelry_inserts(self, obj, x_0, z_loc, obj_rot, drawer_rot):
        children = obj.children
        for child in children:
            name = child.name
            child_assembly = sn_types.Assembly(obj_bp=child)
            child_x = child_assembly.obj_x
            rot_z = child.rotation_euler.z
            is_front =\
                round(obj_rot + rot_z, 2) == round(drawer_rot, 2)
            child_x_loc = child.location.x
            factor = 1 if round(child.rotation_euler.z, 2) == 0 else -1
            if is_front and child_x is not None:
                x_child = x_0 + factor*child_x_loc
                if "Drawer" in name:
                    self.write_jewelry_insert(child, x_child, z_loc)
                child_z_loc = child.location.z
                self.write_obj_jewelry_inserts(
                    child, x_child, z_loc + child_z_loc,
                    obj_rot + rot_z, drawer_rot)
    
    def write_obj_hampers(self, obj, x_0, z_loc, obj_rot, drawer_rot):
        children = obj.children
        for child in children:
            name = child.name
            child_assembly = sn_types.Assembly(obj_bp=child)
            child_x = child_assembly.obj_x
            rot_z = child.rotation_euler.z
            is_front =\
                round(obj_rot + rot_z, 2) == round(drawer_rot, 2)
            child_x_loc = child.location.x
            factor = 1 if round(child.rotation_euler.z, 2) == 0 else -1
            if is_front and child_x is not None:
                x_child = x_0 + factor*child_x_loc
                if "Hamper" in name:
                    self.write_hamper(child, x_child, z_loc)
                child_z_loc = child.location.z
                self.write_obj_hampers(
                    child, x_child, z_loc + child_z_loc,
                    obj_rot + rot_z, drawer_rot)

    def write_island_depths(self, island, x_loc, side):
        island_assembly = sn_types.Assembly(obj_bp=island)
        dim_y = abs(island_assembly.obj_y.location.y)
        panel_thk =\
            abs(island_assembly.get_prompt("Panel Thickness").distance_value)
        prev_value = x_loc + panel_thk - dim_y/2
        is_dbl = False
        index_0 = {"B": 1, "D": 2}
        depth_order = {"B": 1, "D": -1}
        k = index_0[side]
        delta_k = depth_order[side]
        for i in range(1, 3):
            depth = island_assembly.get_prompt("Depth " + str(k))
            if depth:
                is_dbl = True
                depth_value = depth.distance_value
                x_pos = depth_value/2 + prev_value
                depth_label = sn_types.Dimension()
                depth_label.start_x(value=x_pos)
                depth_label.start_z(value=unit.inch(-4))
                label = self.to_inch_lbl(depth_value)
                depth_label.set_label(label)
                prev_value = prev_value + depth_value + panel_thk
            k = k + delta_k
        if not is_dbl:
            depth_value = abs(island_assembly.obj_y.location.y)
            depth_label = sn_types.Dimension()
            x_pos = depth_value/2 + prev_value
            depth_label.start_x(value=x_pos)
            depth_label.start_z(value=unit.inch(-4))
            label = self.to_inch_lbl(depth_value)
            depth_label.set_label(label)

    def write_island_overhang(self, island, x_loc, z_off, type, width_rot):
        left = ["Back Overhang", "Right Overhang"]
        right = ["Front Overhang", "Left Overhang"]
        valid = left + right
        if type not in valid:
            return
        island_assembly = sn_types.Assembly(obj_bp=island)
        tk_height = island_assembly.get_prompt("Toe Kick Height").get_value()
        top_thickness = island_assembly.get_prompt("Top Thickness").get_value()
        deck_overhang =\
            island_assembly.get_prompt(type).get_value()
        overhang_val = self.to_inch_lbl(deck_overhang)
        label = f"{overhang_val}|overhang"
        dim_z = abs(island_assembly.obj_z.location.z)
        dim_y = abs(island_assembly.obj_y.location.y)
        dim_x = abs(island_assembly.obj_x.location.x)
        x_dims = {"x": dim_x, "y": dim_y}
        hsh_lens = {"x": 0.19, "y": 0.1}
        hsh_rots = {"x": 60, "y": 30}
        hsh_len = hsh_lens[width_rot]
        width = x_dims[width_rot]
        height = tk_height + dim_z
        z_0 = height + z_off
        if type in left:
            hsh_x = (x_loc - width/2) + deck_overhang
            x_0 = x_loc - unit.inch(6) - width/2
            hsh_start = hsh_x + (deck_overhang * -2)
            hsh_rot = math.radians(180 - hsh_rots[width_rot])
        elif type in right:
            hsh_x = (x_loc - width/2)
            x_0 = hsh_x + width + deck_overhang
            hsh_start = x_0
            hsh_rot = math.radians(hsh_rots[width_rot])
        hashmark = sn_types.Line(length=hsh_len, axis='X')
        hashmark.anchor.location.x = hsh_start
        hashmark.anchor.name = 'Hashmark_Overhang'
        hashmark.anchor.location.z = height
        hashmark.anchor.rotation_euler.y = hsh_rot
        ovhg_dim = sn_types.Dimension()
        ovhg_dim.start_y(value=unit.inch(4))
        ovhg_dim.parent(hashmark.end_point)
        ovhg_dim.set_label(label)

    def write_front_back_depth(self, island, x_loc, view):
        depth_index = {"Front": 1, "Back": 2}
        island_assembly = sn_types.Assembly(obj_bp=island)
        index = depth_index[view]
        depth_prompt = island_assembly.get_prompt("Depth " + str(index))
        tk_height = island_assembly.get_prompt("Toe Kick Height").get_value()
        left_thk = island_assembly.get_prompt(
            "Left Side Thickness").get_value()
        right_thk = island_assembly.get_prompt(
            "Right Side Thickness").get_value()
        panel_thk = island_assembly.get_prompt("Panel Thickness").get_value()
        shelf_thk = island_assembly.get_prompt("Shelf Thickness").get_value()
        overhang = island_assembly.get_prompt("Side Deck Overhang").get_value()
        dim_x = abs(island_assembly.obj_x.location.x)
        init_sides = {"Front": left_thk, "Back": right_thk}
        side_thk = init_sides[view]
        z_loc = tk_height + shelf_thk + 0.12
        x_label = x_loc + side_thk + overhang/2 + 0.14 - dim_x/2
        hsh_len = 0.11
        hsh_rot = math.radians(-45)
        if depth_prompt is None:
            depth = abs(island_assembly.obj_y.location.y)
        else:
            depth = depth_prompt.get_value()
        for i in range(1, 5):
            width = island_assembly.get_prompt("Opening " + str(i) + " Width")
            if width:
                depth_label = sn_types.Dimension()
                depth_label.start_x(value=x_label)
                depth_label.start_z(value=z_loc)
                label = self.to_inch_lbl(depth)
                depth_label.set_label(label)
                hashmark = sn_types.Line(length=hsh_len, axis='X')
                hashmark.anchor.name = 'Hashmark_Depth'
                hashmark.anchor.location.x = x_label - 0.14
                hashmark.anchor.location.z = z_loc - 0.12
                hashmark.anchor.rotation_euler.y = hsh_rot
                x_label += width.get_value() + panel_thk
            else:
                return

    def write_elv_label(self, txt, x_loc, z_loc):
        label = sn_types.Dimension()
        label.start_x(value=x_loc)
        label.start_z(value=z_loc)
        label.set_label(txt)

    def write_view_A(self, island, dimprops):
        island_index = island.get("ISLAND_INDEX")
        label = "I-1"
        if island_index:
            label = f"I-{str(((int(island_index) * 4) + 1) - 4)}"        
        x_loc = -self.get_island_view_x_loc(island)
        island_assembly = sn_types.Assembly(obj_bp=island)
        dim_x = island_assembly.obj_x.location.x
        if dimprops.framing_height:
            self.write_island_height(island, x_loc)
        if dimprops.toe_kicks:
            self.write_island_tk_height(island, x_loc)
        if dimprops.section_widths:
            self.write_island_opening_width(island, x_loc)
        if dimprops.countertop:
            self.write_island_countertop(island, x_loc)
        if dimprops.partition_height:
            self.write_island_pards(island, x_loc)
        if dimprops.kds:
            self.write_island_shelfs(island, x_loc, 0, 0)
        if dimprops.label_drawer_front_height:
            self.write_obj_drawers(island, x_loc - dim_x/2, 0, 0, 0)
        if dimprops.double_jewelry:
            self.write_obj_jewelry_inserts(island, x_loc - dim_x/2, 0, 0, 0)
        if dimprops.label_hamper_type:
            self.write_obj_hampers(island, x_loc - dim_x/2, 0, 0, 0)
        if dimprops.section_depths:
            self.write_front_back_depth(island, x_loc, "Front")
        self.write_elv_label(label, x_loc, -unit.inch(8))

    def write_view_B(self, island, dimprops):
        island_index = island.get("ISLAND_INDEX")
        label = "I-2"
        if island_index:
            label = f"I-{str(((int(island_index) * 4) + 2) - 4)}"        
        x_loc = -self.get_island_view_x_loc(island)/3
        if dimprops.section_depths:
            self.write_island_depths(island, x_loc, "B")
        if dimprops.ct_overhang:
            self.write_island_overhang(
                island, x_loc, -unit.inch(1), "Back Overhang", "y")
            self.write_island_overhang(
                island, x_loc, -unit.inch(1), "Front Overhang", "y")
        self.write_elv_label(label, x_loc, -unit.inch(8))

    def write_view_C(self, island, dimprops):
        island_index = island.get("ISLAND_INDEX")
        label = "I-3"
        if island_index:
            label = f"I-{str(((int(island_index) * 4) + 3) - 4)}"        
        x_loc = self.get_island_view_x_loc(island)/3
        island_assembly = sn_types.Assembly(obj_bp=island)
        dim_x = island_assembly.obj_x.location.x
        if dimprops.section_widths:
            self.write_island_opening_width(island, x_loc)
        if dimprops.ct_overhang: 
            self.write_island_overhang(
                island, x_loc, -unit.inch(8), "Right Overhang", "x")
            self.write_island_overhang(
                island, x_loc, -unit.inch(8), "Left Overhang", "x")
        if dimprops.label_drawer_front_height:
            self.write_obj_drawers(island, x_loc + dim_x/2, 0, 0, np.pi)
        if dimprops.double_jewelry:
            self.write_obj_jewelry_inserts(island, x_loc + dim_x/2, 0, 0, np.pi)
        if dimprops.label_hamper_type:
            self.write_obj_hampers(island, x_loc + dim_x/2, 0, 0, np.pi)
        if dimprops.kds:
            self.write_island_shelfs(island, x_loc, 0, np.pi)
        if dimprops.section_depths:
            self.write_front_back_depth(island, x_loc, "Back")
        self.write_elv_label(label, x_loc, -unit.inch(8))

    def write_view_D(self, island, dimprops):
        island_index = island.get("ISLAND_INDEX")
        label = "I-4"
        if island_index:
            label = f"I-{str(((int(island_index) * 4) + 4) - 4)}"        
        x_loc = self.get_island_view_x_loc(island)
        if dimprops.section_depths:
            self.write_island_depths(island, x_loc, "D")
        self.write_elv_label(label, x_loc, -unit.inch(8))

    def get_island_type(self, island):
        name = island.name
        name_split = name.split(" ")
        return name_split[0]

    def add_camera_to_island_scene(self, scene,
                            rotation=(0, 0, 0),
                            location=(0, 0, 0)):
        camera = self.create_camera(scene)
        camera.rotation_euler = rotation
        camera.location = location
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.view3d.camera_to_view_selected()
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale += self.isl_pad
        bpy.ops.object.select_all(action='DESELECT')

    def get_island_view_x_loc(self, island):
        island_assembly = sn_types.Assembly(obj_bp=island)
        x_dim = abs(island_assembly.obj_x.location.x)
        y_dim = abs(island_assembly.obj_y.location.y)
        space = unit.inch(35)
        return (3*space/2 + y_dim + x_dim/2)

    def get_instance_location(self, obj, view):
        obj_assembly = sn_types.Assembly(obj_bp=obj)
        dim_x = abs(obj_assembly.obj_x.location.x)
        dim_y = abs(obj_assembly.obj_y.location.y)
        obj_rot_z = obj.rotation_euler.z
        views_rotation = {
            "A": 0,
            "B": np.pi/2,
            "C": np.pi,
            "D": -np.pi/2}
        z_rot = views_rotation[view]
        x_loc = self.get_island_view_x_loc(obj)
        y_loc = unit.inch(60)
        location = [0, 0]
        theta = round(obj_rot_z + z_rot, 2) % round(2*np.pi, 2)
        if theta == 0 or round(theta, 2) == round(3*np.pi/2, 2):
            dir = -1 if theta == 0 else 1
            is_0 = theta == 0
            location[0] = dir*x_loc - is_0*dim_x/2 + (not is_0)*dim_y/2
            location[1] = y_loc + is_0*dim_y/2 + (not is_0)*dim_x/2
        elif round(theta, 2) == round(np.pi/2, 2) or round(theta, 2) == round(np.pi, 2):  # noqa E501
            dir = -1 if round(theta, 2) == round(np.pi/2, 2) else 1
            is_90d = round(theta, 2) == round(np.pi/2, 2)
            location[0] = dir*x_loc/3 - is_90d*dim_y/2 + (not is_90d)*dim_x/2
            location[1] = unit.inch(60) - is_90d*dim_x/2 - (not is_90d)*dim_y/2
        return z_rot, location

    def create_obj_instance(self, name, grp, obj, z_rot, location):
        instance = bpy.data.objects.new(
            name + " " + "Instance", None)
        instance.instance_type = 'COLLECTION'
        instance.instance_collection = grp
        instance.hide_select = True
        instance.location = obj.location
        instance.rotation_euler.z = z_rot
        rot_z = np.matrix(
            [[np.cos(z_rot), -np.sin(z_rot)], [np.sin(z_rot), np.cos(z_rot)]])
        pos = np.matrix([[instance.location.x], [instance.location.y]])
        loc = np.matrix([[location[0]], [location[1]]])
        new_pos = -rot_z@pos + loc
        instance.location = (new_pos[0, 0], new_pos[1, 0], 0)
        return instance

    def create_island_elv_view_scene(self, context, island):
        dimprops = get_dimension_props()
        scene_name = "View - " + island.name
        grp = bpy.data.collections.new(scene_name)
        new_scene =\
            self.create_island_new_scene(context, grp, scene_name, island)
        # NOTE As the Islands are rotated instances of the original islands
        #      the code that replaces door/drawer/hamper meshes won't work
        #      properly.
        self.group_children_island(grp, island)
        view = 'A'
        for i in range(4):
            instance_name = scene_name + "Instance " + view
            z_rot, location = self.get_instance_location(island, view)
            instance =\
                self.create_obj_instance(
                    instance_name, grp, island, z_rot, location)
            new_scene.collection.objects.link(instance)
            view = chr(ord(view) + 1)
        self.write_view_A(island, dimprops)
        self.write_view_B(island, dimprops)
        self.write_view_C(island, dimprops)
        self.write_view_D(island, dimprops)
        self.add_camera_to_island_scene(new_scene, (np.pi/2, 0, 0))
        return grp

    def hide_annotation_objects(self):
        for o in bpy.data.scenes["_Main"].objects:
            if o.get("IS_BP_ANNOTATION"):
                lbl = sn_types.Assembly(o).get_prompt("Label").get_value()
                anno_dim = sn_types.Dimension()
                anno_dim.parent(o)
                anno_dim.start_x(value=0)
                anno_dim.start_y(value=0)
                anno_dim.start_z(value=0)
                anno_dim.set_label(lbl)
                for m in o.children:
                    if m.type == 'MESH':
                        m.hide_viewport = True
                        m.hide_render = True

    def unhide_wall(self, obj):
        wall_bp = utils.get_wall_bp(obj)
        if bpy.context.view_layer.objects.get(wall_bp.name):
            bpy.ops.sn_roombuilder.hide_show_wall(
                wall_bp_name=f"{wall_bp.name}", hide=False)

    def enable_all_elvs(self):
        all_scenes = bpy.data.scenes
        desired = ('PLAN_VIEW', 'ELEVATION', 'ACCORDION', 'ISLAND')
        scenes = [sc for sc in all_scenes if sc.snap.scene_type in desired]
        for sc in scenes:
            sc.snap.elevation_selected = True

    def switch_off_kds(self):
        locked_shelves_prompts = []
        for scene in bpy.data.scenes:
            for obj in scene.objects:
                is_stack = obj.get("IS_STACK_SHELF")
                unseen = obj not in locked_shelves_prompts
                if is_stack:
                    shelf_assy = sn_types.Assembly(obj)
                    shelf_bp = shelf_assy.obj_bp
                    is_shelf_bp = shelf_bp.sn_closets.is_shelf_bp
                    if shelf_assy and is_shelf_bp:
                        is_locked_pmpt = shelf_assy.get_prompt(
                            "Is Locked Shelf")
                        locked = is_locked_pmpt.get_value()
                        if locked and is_stack and unseen:
                            is_locked_pmpt.set_value(0)
                            locked_shelves_prompts.append(obj)
        return locked_shelves_prompts
    
    def switch_on_kds(self, switched_off):
        for obj in switched_off:
            assy = sn_types.Assembly(obj)
            if assy:
                is_locked_pmpt = assy.get_prompt("Is Locked Shelf")
                is_locked_pmpt.set_value(1)

    def invoke(self, context, event):
        main_sc_objects = []
        existing_scenes = [sc.name for sc in bpy.data.scenes]
        if "_Main" in existing_scenes:
            main_sc_objects = [o for o in bpy.data.scenes["_Main"].objects\
                if o.get("IS_BP_ISLAND")]
        main_islands = [o for o in main_sc_objects if o.get("IS_BP_ISLAND")]
        if len(main_islands) > 4:
            message = f"SNaP projects are limited to 4 (four) islands"
            return bpy.ops.snap.message_box('INVOKE_DEFAULT', message=message)
        bpy.ops.snap_closet_dimensions.auto_dimension()
        return self.execute(context)

    def unhide_cabinet_drawer_boxes(self, boxes):
        for box in boxes:
            hide = box.get_prompt("Hide")
            hide.set_value(False)

    def execute(self, context):
        self.current_ctx = context
        self.pre_2d_cleanup(context)
        dimprops = get_dimension_props()
        room_type = context.scene.sn_roombuilder.room_type
        views_props = context.window_manager.views_2d
        accordions_only = views_props.views_option == 'ACCORDIONS'
        elevations_only = views_props.views_option == 'ELEVATIONS'
        wall_qty = context.window_manager.snap.main_scene_wall_qty
        if room_type == 'SINGLE' or wall_qty == 1:
            accordions_only = False
            elevations_only = True
        context.window_manager.snap.use_opengl_dimensions = True
        self.font = opengl_dim.get_custom_font()
        self.font_bold = opengl_dim.get_custom_font_bold()
        self.create_freestyle_collections()
        self.create_linestyles()
        self.main_scene = context.scene
        context.scene.name = "_Main"
        mesh_data_dict = {}
        joint_parts = None
        self.hide_annotation_objects()
        cabinet_drawer_boxes = []

        if self.use_single_scene:
            self.create_single_elv_view(context)
        else:
            for obj in bpy.data.objects:
                if obj.type == 'CURVE' and 'hashmark' in obj.name.lower():
                    bpy.data.objects.remove(obj, do_unlink=True)
            for obj in bpy.data.objects:
                no_users = obj.users == 0
                parent = obj.parent
                ctop = 'countertop' in obj.name.lower()
                cutpart = 'cutpart' in obj.name.lower()
                try:
                    partition = parent.sn_closets.is_panel_bp
                except AttributeError:
                    partition = False
                try:
                    wall = 'wall' in parent.name.lower()
                except AttributeError:
                    wall = False
                font = obj.type == 'FONT'
                if no_users and cutpart and ctop:
                    bpy.data.objects.remove(obj, do_unlink=True)
                if no_users and font and partition:
                    obj.hide = True
                    obj.hide_render = True
                if no_users and font and wall:
                    obj.hide = True
                    obj.hide_render = True

                if "CABINET_DRAWER_BOX" in obj:
                    drawer_box = sn_types.Assembly(obj)
                    cabinet_drawer_boxes.append(drawer_box)
                    drawer_box.get_prompt("Hide").set_value(True)

            walls = []
            wall_groups = {}
            bpy.ops.sn_scene.clear_2d_views()
            # NOTE this is a bit uggly, but is the safest way of removing
            #      these collections before generating them again
            for col in bpy.data.collections:
                if 'cswall' in col.name.lower():
                    bpy.data.collections.remove(col)
            for col in bpy.data.collections:
                if 'sn-cs-joint' in col.name.lower():
                    bpy.data.collections.remove(col)
            for col in bpy.data.collections:
                if 'accordion' in col.name.lower():
                    bpy.data.collections.remove(col)
            for col in bpy.data.collections:
                if 'left_grp' in col.name.lower():
                    bpy.data.collections.remove(col)
            for col in bpy.data.collections:
                if 'right_grp' in col.name.lower():
                    bpy.data.collections.remove(col)
            for col in bpy.data.collections:
                if 'plan view' in col.name.lower():
                    bpy.data.collections.remove(col)


            # Get mesh data so it can be used to make the relationship
            # between the Original _Main scene and it's copy that 
            # forms the accordion view. It's important doing it before
            # generating 
            for obj in bpy.data.objects:
                if obj.data is not None:
                    mesh_data = obj.data.name
                    mesh_data_dict[obj.name] = mesh_data
            # [[o for o in s.objects] for s in bpy.data.scenes if s.name == "_Main" or "Scene"]
            scene_objects = []
            for sc in bpy.data.scenes:
                if sc.name == "_Main" or "Scene":
                    for obj in sc.objects:
                        scene_objects.append(obj)
            for obj in scene_objects:
                if obj.get("IS_BP_WALL"):
                    self.unhide_wall(obj)
                    wall = sn_types.Wall(obj_bp=obj)
                    wall_groups_list = wall.get_wall_groups()
                    wall_door_only = False
                    door_toggle = False
                    door_only = len(wall_groups_list) == 1
                    right_wall = wall.get_connected_wall('RIGHT')
                    corner_items = None
                    if right_wall:
                        corner_items = self.get_lsh_csh_assemblies(
                            right_wall.obj_bp)
                    has_assys = len(wall_groups_list) > 0
                    for item in wall_groups_list:
                        if 'BPASSEMBLY.' in item.name:
                            for door in item.children:
                                if 'door frame' in door.name.lower():
                                    door_toggle = True
                    if door_toggle and door_only:
                        wall_door_only = True
                    if (has_assys and not wall_door_only) or corner_items:
                        grp_name = f"CSwall-{wall.obj_bp.snap.name_object}"
                        grp = bpy.data.collections.new(grp_name)
                        if elevations_only:
                            self.create_elv_view_scene(context, wall, grp)
                        left_wall = wall.get_connected_wall('LEFT')
                        walls.append((wall, left_wall))
                        wall_groups[wall.obj_bp.name] = grp

                name = obj.name
                if "Island" in name and obj.parent is None:
                    island = obj

                    self.create_island_elv_view_scene(context, island)
            self.create_plan_view_scene(context)

            virtual = self.create_virtual_scene()
            if len(walls) > 0:
                if elevations_only and room_type != 'SINGLE' and wall_qty > 1:
                    main_sc_objs = [o for o in self.main_scene.objects]
                    assy_dict = self.add_cross_sections(walls, wall_groups)
                    self.add_remaining_space_dims(assy_dict, wall_groups)
                    self.add_corner_cross_sections_dims(walls, wall_groups)
                    self.add_obstacles_cs_on_elvs(context, main_sc_objs, wall_groups)
                elif accordions_only:
                    self.add_accordion_views(context)

        self.clear_unused_linestyles()
        bpy.context.window.scene = self.main_scene
        wm = context.window_manager.snap
        wm.elevation_scene_index = 0
        bpy.ops.object.select_all(action='DESELECT')

        switched_off_kds = self.switch_off_kds()
        self.add_meshes_to_freestyle_collections()
        self.switch_on_kds(switched_off_kds)
        self.unhide_cabinet_drawer_boxes(cabinet_drawer_boxes)
        hide_dim_handles()
        self.enable_all_elvs()
        return {'FINISHED'}

    def pre_2d_cleanup(self, context):
        all_scenes = bpy.data.scenes
        for scene in all_scenes:
            if scene.name not in ["_Main", "Scene"]:
                bpy.data.scenes.remove(scene)
        for view in context.window_manager.snap.image_views:
            context.window_manager.snap.image_views.remove(0)
        for obj in bpy.data.objects:
            # Profiles have no users, but most be preserved
            if obj.get('IS_MOLDING_PROFILE') is not None:
                continue
            if len(obj.users_scene) == 0:
                # first, remove mesh data, if its sole user is the object
                mesh = obj.data
                if obj.name in bpy.data.objects:
                    bpy.data.objects.remove(obj)
                if isinstance(mesh, bpy.types.Mesh) and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)

    


class VIEW_OT_render_2d_views(Operator):
    bl_idname = "2dviews.render_2d_views"
    bl_label = "Render 2D Views"
    bl_description = "Renders 2d Scenes"

    r = 0
    g = 0
    b = 0
    a = 0

    PDF_TEMP_XML = "pdf_temp.xml"

    def check_file(self, path):

        while not os.path.exists(path + ".jpg"):
            time.sleep(0.1)

        p = psutil.Process()
        open_files = []

        for p in p.open_files():
            open_files.append(p.path)

        if path in open_files:
            print(path, "is in", open_files)
            print("File is still open!")

            self.check_file(path)

        else:
            return True

    def save_dim_color(self, color):
        self.r = color[0]
        self.g = color[1]
        self.b = color[2]
        self.a = color[3]

    def reset_dim_color(self, context):
        context.scene.snap.opengl_dim.gl_default_color[0] = self.r
        context.scene.snap.opengl_dim.gl_default_color[1] = self.g
        context.scene.snap.opengl_dim.gl_default_color[2] = self.b
        context.scene.snap.opengl_dim.gl_default_color[3] = self.a

    def swap_colors(self, context, revert=False):
        scene = context.window.scene
        if revert:
            print(f"Reverted Colors back - Scene :{scene.name}")
        elif not revert:
            print(f"Changing to Oxford White (Frost) for Rendering - Scene: {scene.name}")
        return True

    def render_scene(self, context, scene):
        swaped_colors = False
        shaded_sc_types = ['ELEVATION', 'ACCORDION']
        valid_shaded_sc_type = scene.snap.scene_type in shaded_sc_types
        is_elevation = scene.snap.scene_type == 'ELEVATION'
        scene_setup_props = scene.snap_closet_dimensions
        shading_kill_switch = scene_setup_props.disable_2dviews_shading
        is_shaded_scene = valid_shaded_sc_type
        context.window.scene = scene

        self.save_dim_color(scene.snap.opengl_dim.gl_default_color)

        scene.snap.opengl_dim.gl_default_color = (0.1, 0.1, 0.1, 1.0)
        rd = scene.render
        rl = scene.view_layers[0]
        rd.filepath = bpy.app.tempdir
        fixed_scene_name = scene.name.replace("CSwall-", "")
        rd.filepath += fixed_scene_name

        freestyle_settings = rl.freestyle_settings
        rd.use_freestyle = True
        rd.image_settings.file_format = 'JPEG'
        rd.line_thickness = 0.75
        rd.resolution_percentage = 100
        rl.use_solid = False
        rl.use_pass_combined = True
        rl.use_pass_z = False
        freestyle_settings.crease_angle = 2.617994
        freestyle_settings.as_render_pass = True
        if "Island" in scene.name:
            freestyle_settings.linesets["Hidden Lines"].show_render = False

        if rd.engine != 'BLENDER_EEVEE':
            # I am checking because if this code runs, the viewport goes black until interacted with
            rd.engine = 'BLENDER_EEVEE'
        # bpy.context.scene.cycles.samples = 1
        # by default, view_transform is filmic, which makes the whites grey
        bpy.context.scene.view_settings.view_transform = 'Standard'
    
        for rl in context.scene.view_layers:
            for child in rl.layer_collection.children:
                child.exclude = False
        # as we just changed to use EEVEE instead of CYCLES, a node setup is required
        # as I can't find a way to not render the material
        scene.use_nodes = True
        tree = scene.node_tree

        for node in tree.nodes:
            tree.nodes.remove(node)

        if shading_kill_switch or not is_shaded_scene:
            view2d_rl_node = tree.nodes.new(type='CompositorNodeRLayers')
            a_over_node = tree.nodes.new(type='CompositorNodeAlphaOver')
            comp_node = tree.nodes.new(type='CompositorNodeComposite')

            tree.links.new(view2d_rl_node.outputs['Freestyle'], a_over_node.inputs[2])
            tree.links.new(a_over_node.outputs[0], comp_node.inputs[0])

        elif not shading_kill_switch and is_shaded_scene:
            if is_elevation:
                swaped_colors = self.swap_colors(context)
            # View layer just for the coloring
            color_layer_name = "shading"
            shading_layer = scene.view_layers.new(color_layer_name)
            shading_layer.use_freestyle = False

            # Nodes for coloring the desired materials
            shading_layer = tree.nodes.new(type='CompositorNodeRLayers')
            shading_layer.layer = color_layer_name
            color_node = tree.nodes.new(type='CompositorNodeMixRGB')
            color_node.blend_type = "COLOR"
            color_dial = 0.8
            color_node.inputs[0].default_value = color_dial
            # Nodes for Freestyle edge lines rendering
            view2d_rl_node = tree.nodes.new(type='CompositorNodeRLayers')
            a_over_node = tree.nodes.new(type='CompositorNodeAlphaOver')
            comp_node = tree.nodes.new(type='CompositorNodeComposite')

            tree.links.new(view2d_rl_node.outputs['Freestyle'], a_over_node.inputs[2])
            tree.links.new(shading_layer.outputs['Image'], color_node.inputs[2])
            tree.links.new(color_node.outputs[0], a_over_node.inputs[1])
            tree.links.new(a_over_node.outputs[0], comp_node.inputs[0])


        # Prevent Main Accordion from being rendered
        if "Z_Main Accordion" in bpy.data.scenes:
            bpy.data.scenes["Z_Main Accordion"].snap.elevation_selected = False
        if "z_virtual" in bpy.data.scenes:
            bpy.data.scenes["z_virtual"].snap.elevation_selected = False

        # Render composite
        bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)

        img_path = bpy.path.abspath(scene.render.filepath)
        self.check_file(img_path)

        img_result = opengl_dim.render_opengl(self, context)

        image_view = context.window_manager.snap.image_views.add()
        image_view.name = img_result.name
        image_view.image_name = img_result.name

        image_view.is_plan_view = False
        image_view.is_elv_view = False
        image_view.is_acc_view = False
        image_view.is_island_view = False
        image_view.is_virtual_view = False
        if scene.snap.scene_type == 'PLAN_VIEW':
            image_view.is_plan_view = True
        elif scene.snap.scene_type == 'ELEVATION':
            image_view.is_elv_view = True
        elif scene.snap.scene_type == 'ACCORDION':
            image_view.is_acc_view = True
        elif scene.snap.scene_type == 'ISLAND':
            image_view.is_island_view = True
            image_view.island_index = scene.snap.island_index
        elif scene.snap.scene_type == 'VIRTUAL':
            image_view.is_virtual_view = True

        # Clear and deactivate nodes to prevent conflicts with other rendering methods
        for node in tree.nodes:
            tree.nodes.remove(node)
        scene.use_nodes = False
        self.reset_dim_color(context)
        if swaped_colors:
            self.swap_colors(context, True)

    def get_project_xml(self):
        props = bpy.context.window_manager.sn_project
        proj = props.get_project()
        cleaned_name = proj.get_clean_name(proj.name)
        project_dir = bpy.context.preferences.addons['snap'].preferences.project_dir
        selected_project = os.path.join(project_dir, cleaned_name)
        xml_file = os.path.join(selected_project, self.PDF_TEMP_XML)
        global PROJECT_NAME
        PROJECT_NAME = cleaned_name

        if not os.path.exists(project_dir):
            print("Projects Directory does not exist")
        if not os.path.exists(xml_file):
            print("The 'snap_job.xml' file is not found. Please select desired rooms and perform an export.")   
        else:
            return xml_file

    def create_prep_script(self):
        tmp_filename = "export_temp.py"
        proj_props = bpy.context.window_manager.sn_project
        proj_name = proj_props.projects[proj_props.project_index].name
        proj_dir = os.path.join(sn_xml.get_project_dir(), proj_name)
        proj_dir = proj_dir.replace("\\", "/")
        self.remove_pdf_xml_file()
        file = open(os.path.join(bpy.app.tempdir, tmp_filename), 'w')
        file.write("import bpy\n")
        file.write("from snap import sn_xml\n")
        file.write(f"sn_xml.Snap_XML.filename = \"{self.PDF_TEMP_XML}\"\n")
        file.write(f"bpy.ops.sn_export.export_xml('INVOKE_DEFAULT', xml_path='{proj_dir}')\n")
        file.close()
        return os.path.join(bpy.app.tempdir, tmp_filename)

    def remove_pdf_xml_file(self):
        proj_props = bpy.context.window_manager.sn_project
        proj_name = proj_props.projects[proj_props.project_index].name
        proj_dir = os.path.join(sn_xml.get_project_dir(), proj_name)
        proj_dir = proj_dir.replace("\\", "/")
        xml_4_pdf = f"{proj_dir}/{self.PDF_TEMP_XML}"
        if os.path.exists(xml_4_pdf):
            os.remove(xml_4_pdf)

    def create_pdf_xml(self, context):
        room_file = None
        # Save main file to run XML generation
        bpy.ops.wm.save_mainfile()
        pm_props = context.window_manager.sn_project
        proj = pm_props.projects[pm_props.project_index]
        for room in proj.rooms:
            if room.name == pm_props.current_file_room:
                room_file = room.file_path
        if room_file:
            script_path = self.create_prep_script()
            subprocess.call(bpy.app.binary_path + ' "' + room_file + '" -b --python "' + script_path + '"')
            xml_file = self.get_project_xml()
            return xml_file
        return None

    def execute(self, context):
        add_on_save_switched_on = []
        for scene in bpy.data.scenes:
            if scene.snap_closet_dimensions.auto_add_on_save:
                add_on_save_switched_on.append(scene) 
                scene.snap_closet_dimensions.auto_add_on_save = False
        self.create_pdf_xml(context)
        # file_path = bpy.app.tempdir if bpy.data.filepath == "" else os.path.dirname(
        #     bpy.data.filepath)
        for item in context.window_manager.snap.image_views:
            context.window_manager.snap.image_views.remove(0)

        # HACK: YOU HAVE TO SET THE CURRENT SCENE TO RENDER JPEG BECAUSE
        # OF REPORTS LAB AND BLENDER LIMITATIONS. :(
        rd = context.scene.render
        rd.image_settings.file_format = 'JPEG'

        current_scene = context.window.scene

        for scene in bpy.data.scenes:
            # We need to explicitly set lock to false
            scene.render.use_lock_interface = False
            if scene.snap.elevation_selected:
                self.render_scene(context, scene)

        # we need to force a redraw or the screen will be black
        

        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
                screen.update_tag()

        bpy.context.window.scene = current_scene
        
        win = bpy.context.window
        scr = win.screen
        areas3d = [area for area in scr.areas if area.type == 'VIEW_3D']
        if areas3d:
            region = [region for region in areas3d[0].regions if region.type == 'WINDOW']

            override = {'window':win,
                        'screen':scr,
                        'area'  :areas3d[0],
                        'region':region[0],
                        'scene' :current_scene,
                        }
            bpy.ops.view3d.dolly(override, mx=1, my=1, delta=0, use_cursor_init=False)
        for scene in add_on_save_switched_on:
            scene.snap_closet_dimensions.auto_add_on_save = True
        return {'FINISHED'}

class VIEW_OT_accordion_interface(Operator):
    bl_idname = "sn_2d_views.accordion_interface"
    bl_label = "Accordion 2D View Options"

    info = {}

    @classmethod
    def poll(cls, context):
        return True

    def check(self, context):
        return True

    def execute(self, context):
        pass
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(320))

    def draw(self, context):
        # wm = context.window_manager.snap
        scene = context.scene
        acc_props = scene.snap.accordion_view
        layout = self.layout
        box = layout.box()

        row = box.row()
        row.label(text="Accordion Break Width:")
        row.prop(acc_props, 'break_width', text="")
        # row = box.row()
        # row.label(text="Enable Intermediate Walls")
        # row.prop(acc_props, 'enable_intermediate_walls', text="")
        if acc_props.enable_intermediate_walls:
            row = box.row()
            row.label(text="Intermediate Wall Space")
            row.prop(acc_props, 'intermediate_space', text="")
            row = box.row()
            row.label(text="Intermediate Walls Quantity")
            row.prop(acc_props, 'intermediate_qty', text="")


class VIEW_OT_view_image(Operator):
    bl_idname = "2dviews.view_image"
    bl_label = "View Image"
    bl_description = "Opens the image editor to view the 2D view."

    image_name: StringProperty(name="Object Name",
                               description="This is the readable name of the object")

    def execute(self, context):
        bpy.ops.sn_general.open_new_window(space_type='IMAGE_EDITOR')
        image_view = context.window_manager.snap.image_views[self.image_name]

        override = context.copy()
        areas = context.screen.areas

        for area in areas:
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    override['space'] = space
                    for image in bpy.data.images:
                        if image.name == image_view.image_name:
                            space.image = image

            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region

        override['window'] = context.window
        override['area'] = context.area
        bpy.ops.image.view_all(override, fit_view=True)

        return {'FINISHED'}


class VIEW_OT_delete_image(Operator):
    bl_idname = "2dviews.delete_image"
    bl_label = "View Image"
    bl_description = "Delete the Image"

    image_name: StringProperty(name="Object Name",
                               description="This is the readable name of the object")

    def execute(self, context):
        for index, iv in enumerate(context.window_manager.snap.image_views):
            if iv.name == self.image_name:
                context.window_manager.snap.image_views.remove(index)

        for image in bpy.data.images:
            if image.name == self.image_name:
                bpy.data.images.remove(image)
                break

        return {'FINISHED'}


class VIEW_OT_create_snap_shot(Operator):
    bl_idname = "2dviews.create_snap_shot"
    bl_label = "Create New View"
    bl_description = "Renders 2d Scenes"

    def execute(self, context):
        bpy.ops.view3d.toolshelf()
        context.area.header_text_set(
            text="Position view then LEFT CLICK to take screen shot. ESC to Cancel.")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def get_file_path(self):
        counter = 1
        while os.path.exists(os.path.join(bpy.app.tempdir, "View " + str(counter) + ".png")):
            counter += 1
        return os.path.join(bpy.app.tempdir, "View " + str(counter) + ".png")

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type in {'ESC', 'RIGHTMOUSE'}:
            context.area.header_text_set()
            bpy.ops.view3d.toolshelf()
            return {'FINISHED'}

        if event.type in {'LEFTMOUSE'}:
            context.area.header_text_set(" ")
            file_path = self.get_file_path()
            # The PDF writter can only use JPEG images
            context.scene.render.image_settings.file_format = 'JPEG'
            bpy.ops.screen.screenshot(filepath=file_path, full=False)
            bpy.ops.view3d.toolshelf()
            context.area.header_text_set()
            image = bpy.data.images.load(file_path)
            image_view = context.window_manager.snap.image_views.add()
            image_view.name = os.path.splitext(image.name)[0]
            image_view.image_name = image.name

            return {'FINISHED'}

        return {'RUNNING_MODAL'}


class VIEW_OT_add_annotation(Operator):
    bl_idname = "sn_2d_views.add_annotation"
    bl_label = "Add Annotation"

    header_text = "Place Annotation"

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(550))

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text="Annotations were moved as a drop object to: Products - Basic")

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        return {'FINISHED'}

    def modal(self, context, event):
        context.area.tag_redraw()
        context.area.header_text_set(text=self.header_text)

        if event.type in {'ESC'}:
            return {'FINISHED'}

        return {'FINISHED'}


class VIEW_OT_add_dimension(Operator):
    bl_description = "Add Dimension to Selected Assembly"
    bl_idname = "sn_2d_views.add_dimension"
    bl_label = "Add Dimension"
    bl_options = {'UNDO'}

    label: StringProperty(name="Dimension Label",
                          default="")

    offset: FloatProperty(name="Offset", subtype='DISTANCE')

    above_assembly_draw_to: EnumProperty(name="Draw to Above Assembly Top or Bottom",
                                         items=[('Top', "Top", "Top"),
                                                ('BOTTOM', "Bottom", "Bottom")],
                                         default='BOTTOM')

    configuration: EnumProperty(name="configuration",
                                items=[('WIDTH', "Width", 'Width of Assembly'),
                                       ('HEIGHT', "Height", 'Height of Assembly'),
                                       ('DEPTH', "Depth", 'Depth of Assembly'),
                                       ('WALL_TOP', "Wall Top", 'Top of Wall'),
                                       ('WALL_BOTTOM', "Wall Bottom", 'Bottom of Wall'),
                                       ('WALL_LEFT', "Wall Left", 'Left Wall End'),
                                       ('WALL_RIGHT', "Wall Right", 'Right Wall End'),
                                       ('AVAILABLE_SPACE_ABOVE', "Available Space Above", 'Available Space Above'),
                                       ('AVAILABLE_SPACE_BELOW', "Available Space Below", 'Available Space Below'),
                                       ('AVAILABLE_SPACE_LEFT', "Available Space Left", 'Available Space Left'),
                                       ('AVAILABLE_SPACE_RIGHT', "Available Space Right", 'Available Space Right')],
                                default='WIDTH')

    dimension = None
    assembly = None
    wall = None
    del_dim = True
    neg_z_dim = False

    @classmethod
    def poll(cls, context):
        if utils.get_bp(context.object, 'PRODUCT'):
            return True
        else:
            return False

    def check(self, context):
        self.dimension.anchor.location = (0, 0, 0)
        self.dimension.end_point.location = (0, 0, 0)

        self.dimension.set_label(self.label)

        if self.configuration in ['HEIGHT', 'WALL_TOP', 'WALL_BOTTOM',
                                  'AVAILABLE_SPACE_ABOVE', 'AVAILABLE_SPACE_BELOW']:
            self.dimension.anchor.location.x += self.offset
        else:
            self.dimension.anchor.location.z += self.offset

        if self.configuration == 'WIDTH':
            self.dimension.end_point.location.x = self.assembly.obj_x.location.x

        if self.configuration == 'HEIGHT':
            self.dimension.end_point.location.z = self.assembly.obj_z.location.z

        if self.configuration == 'DEPTH':
            self.dimension.end_point.location.y = self.assembly.obj_y.location.y

        if self.configuration == 'WALL_TOP':
            if not self.neg_z_dim:
                self.dimension.anchor.location.z = self.assembly.obj_z.location.z
                self.dimension.end_point.location.z = self.wall.obj_z.location.z -\
                                                      self.assembly.obj_bp.location.z -\
                                                      self.assembly.obj_z.location.z
            else:
                self.dimension.end_point.location.z = self.wall.obj_z.location.z -\
                                                      self.assembly.obj_bp.location.z

        if self.configuration == 'WALL_BOTTOM':
            if not self.neg_z_dim:
                self.dimension.end_point.location.z = -self.assembly.obj_bp.location.z
            else:
                self.dimension.anchor.location.z = self.assembly.obj_z.location.z
                self.dimension.end_point.location.z = -self.assembly.obj_bp.location.z -\
                                                      self.assembly.obj_z.location.z

        if self.configuration == 'WALL_LEFT':
            self.dimension.end_point.location.x = -self.assembly.obj_bp.location.x

        if self.configuration == 'WALL_RIGHT':
            self.dimension.anchor.location.x = self.assembly.obj_x.location.x
            self.dimension.end_point.location.x = self.wall.obj_x.location.x -\
                                                  self.assembly.obj_bp.location.x -\
                                                  self.assembly.obj_x.location.x

        if self.configuration == 'AVAILABLE_SPACE_ABOVE':
            if not self.neg_z_dim:
                self.dimension.anchor.location.z = self.assembly.obj_z.location.z
                assembly_dim_z = self.assembly.obj_z.location.z
            else:
                assembly_dim_z = 0.0

            assembly_a = self.assembly.get_adjacent_assembly(direction='ABOVE')

            if assembly_a:
                above_assembly_loc_z = assembly_a.obj_bp.location.z

                if self.above_assembly_draw_to == 'BOTTOM':
                    above_assembly_dim_z = assembly_a.obj_z.location.z
                    self.dimension.end_point.location.z = above_assembly_loc_z +\
                                                          above_assembly_dim_z -\
                                                          self.assembly.obj_bp.location.z -\
                                                          assembly_dim_z

                else:
                    self.dimension.end_point.location.z = above_assembly_loc_z -\
                                                          self.assembly.obj_bp.location.z -\
                                                          assembly_dim_z

            else:
                self.dimension.end_point.location.z = self.wall.obj_z.location.z -\
                                                      self.assembly.obj_bp.location.z -\
                                                      assembly_dim_z

        if self.configuration == 'AVAILABLE_SPACE_BELOW':
            if self.assembly.obj_z.location.z < 0:
                self.dimension.anchor.location.z = self.assembly.obj_z.location.z

            assembly_b = self.assembly.get_adjacent_assembly(direction='BELOW')
            if assembly_b:
                if not self.neg_z_dim:
                    self.dimension.end_point.location.z = -self.assembly.obj_bp.location.z +\
                                                          assembly_b.obj_bp.location.z +\
                                                          assembly_b.obj_z.location.z
                else:
                    self.dimension.end_point.location.z = -self.assembly.obj_bp.location.z -\
                                                          self.assembly.obj_z.location.z +\
                                                          assembly_b.obj_bp.location.z +\
                                                          assembly_b.obj_z.location.z
            else:
                self.dimension.end_point.location.z = -self.assembly.obj_bp.location.z

        if self.configuration == 'AVAILABLE_SPACE_LEFT':
            if self.assembly.get_adjacent_assembly(direction='LEFT'):
                self.dimension.end_point.location.x = -self.assembly.obj_bp.location.x +\
                                                      self.assembly.get_adjacent_assembly(direction='LEFT').obj_bp.location.x +\
                                                      self.assembly.get_adjacent_assembly(direction='LEFT').obj_x.location.x
            else:
                self.dimension.end_point.location.x = -self.assembly.obj_bp.location.x

        if self.configuration == 'AVAILABLE_SPACE_RIGHT':
            self.dimension.anchor.location.x = self.assembly.obj_x.location.x
            if self.assembly.get_adjacent_assembly(direction='RIGHT'):
                self.dimension.end_point.location.x = self.assembly.get_adjacent_assembly(direction='RIGHT').obj_bp.location.x -\
                                                      self.assembly.obj_bp.location.x -\
                                                      self.assembly.obj_x.location.x
            else:
                self.dimension.end_point.location.x = self.wall.obj_x.location.x -\
                                                      self.assembly.obj_bp.location.x -\
                                                      self.assembly.obj_x.location.x

        return True

    def __del__(self):
        if not self.del_dim:
            obj_del = []
            obj_del.append(self.dimension.anchor)
            obj_del.append(self.dimension.end_point)
            utils.delete_obj_list(obj_del)

    def invoke(self, context, event):
        wm = context.window_manager

        if not wm.snap.use_opengl_dimensions:
            wm.snap.use_opengl_dimensions = True

        if context.object:
            obj_wall_bp = utils.get_wall_bp(context.object)
            if obj_wall_bp:
                self.wall = sn_types.Wall(obj_bp=obj_wall_bp)

            obj_assembly_bp = utils.get_parent_assembly_bp(context.object)
            obj_assembly_bp = utils.get_bp(context.object, 'PRODUCT')
            if obj_assembly_bp:
                self.assembly = sn_types.Assembly(obj_assembly_bp)
                wall_bp = utils.get_wall_bp(obj_assembly_bp)
                self.wall = sn_types.Wall(obj_bp=wall_bp)

        self.dimension = sn_types.Dimension()
        self.dimension.set_color(value=7)
        self.dimension.parent(obj_assembly_bp)
        self.dimension.end_point.location.x = self.assembly.obj_x.location.x

        if self.assembly.obj_z.location.z < 0:
            self.neg_z_dim = True
        else:
            self.neg_z_dim = False

        self.configuration = 'WIDTH'
        self.label = ""

        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(550))

    def execute(self, context):
        self.del_dim = False
        self.dimension.set_color(value=0)
        self.dimension.anchor.hide_set(False)
        self.dimension.end_point.hide_set(False)

        if self.label != "":
            self.dimension.set_label(self.label)

        wall_dim_x = self.wall.get_var("dim_x", "wall_dim_x")
        wall_dim_z = self.wall.get_var("dim_z", "wall_dim_z")

        assembly_loc_x = self.assembly.get_var("loc_x", "assembly_loc_x")
        assembly_loc_z = self.assembly.get_var("loc_z", "assembly_loc_z")
        assembly_dim_x = self.assembly.get_var("dim_x", "assembly_dim_x")
        assembly_dim_z = self.assembly.get_var("dim_z", "assembly_dim_z")

        assembly_l = self.assembly.get_adjacent_assembly(direction='LEFT')
        if assembly_l:
            assembly_l_loc_x = assembly_l.get_var("loc_x", "assembly_l_loc_x")
            assembly_l_dim_x = assembly_l.get_var("dim_x", "assembly_l_dim_x")

        assembly_r = self.assembly.get_adjacent_assembly(direction='RIGHT')
        if assembly_r:
            assembly_r_loc_x = assembly_r.get_var("loc_x", "assembly_r_loc_x")

        assembly_a = self.assembly.get_adjacent_assembly(direction='ABOVE')
        if assembly_a:
            assembly_a_loc_z = assembly_a.get_var("loc_z", "assembly_a_loc_z")
            assembly_a_dim_z = assembly_a.get_var("dim_z", "assembly_a_dim_z")

        assembly_b = self.assembly.get_adjacent_assembly(direction="BELOW")
        if assembly_b:
            assembly_b_loc_z = assembly_b.get_var("loc_z", "assembly_b_loc_z")
            assembly_b_dim_z = assembly_b.get_var("dim_z", "assembly_b_dim_z")

        if self.configuration == 'WIDTH':
            self.dimension.end_x(expression="dim_x", driver_vars=[self.assembly.get_var("dim_x")])

        if self.configuration == 'HEIGHT':
            self.dimension.end_z(expression="dim_z", driver_vars=[self.assembly.get_var("dim_z")])

        if self.configuration == 'DEPTH':
            self.dimension.end_y(expression="dim_y", driver_vars=[self.assembly.get_var("dim_y")])

        if self.configuration == 'WALL_TOP':
            if not self.neg_z_dim:
                self.dimension.start_z(expression="assembly_dim_z",
                                       driver_vars=[assembly_dim_z])

                self.dimension.end_z(expression="wall_dim_z-assembly_loc_z-assembly_dim_z",
                                     driver_vars=[wall_dim_z, assembly_loc_z, assembly_dim_z])
            else:
                self.dimension.end_z(expression="wall_dim_z-assembly_loc_z",
                                     driver_vars=[wall_dim_z, assembly_loc_z])

        if self.configuration == 'WALL_BOTTOM':
            if not self.neg_z_dim:
                self.dimension.end_z(expression="-assembly_loc_z", driver_vars=[assembly_loc_z])
            else:
                self.dimension.start_z(expression="assembly_dim_z", driver_vars=[assembly_dim_z])
                self.dimension.end_z(expression="-assembly_loc_z-assembly_dim_z",
                                     driver_vars=[assembly_loc_z, assembly_dim_z])

        if self.configuration == 'WALL_LEFT':
            self.dimension.end_x(expression="-assembly_loc_x", driver_vars=[assembly_loc_x])

        if self.configuration == 'WALL_RIGHT':
            self.dimension.start_x(expression="dim_x", driver_vars=[self.assembly.get_var("dim_x")])
            self.dimension.end_x(expression="wall_dim_x-assembly_dim_x-assembly_loc_x",
                                 driver_vars=[wall_dim_x, assembly_dim_x, assembly_loc_x])

        if self.configuration == 'AVAILABLE_SPACE_ABOVE':
            if assembly_a:
                self.dimension.start_z(expression="dim_z", driver_vars=[self.assembly.get_var("dim_z")])

                if self.above_assembly_draw_to == 'BOTTOM':
                    self.dimension.end_z(expression="assembly_a_loc_z+assembly_a_dim_z-assembly_loc_z-assembly_dim_z",
                                         driver_vars=[assembly_a_loc_z,
                                                      assembly_a_dim_z,
                                                      assembly_loc_z,
                                                      assembly_dim_z])
                else:
                    self.dimension.end_z(expression="assembly_a_loc_z-assembly_loc_z-assembly_dim_z",
                                         driver_vars=[assembly_a_loc_z,
                                                      assembly_loc_z,
                                                      assembly_dim_z])
            else:
                if not self.neg_z_dim:
                    self.dimension.end_z(expression="wall_dim_z-assembly_loc_z-assembly_dim_z",
                                         driver_vars=[wall_dim_z,
                                                      assembly_loc_z,
                                                      assembly_dim_z])
                else:
                    self.dimension.end_z(expression="wall_dim_z-assembly_loc_z",
                                         driver_vars=[wall_dim_z,
                                                      assembly_loc_z])
        if self.configuration == 'AVAILABLE_SPACE_BELOW':
            if assembly_b:
                if not self.neg_z_dim:
                    self.dimension.end_z(expression="-assembly_loc_z+assembly_b_loc_z+assembly_b_dim_z",
                                         driver_vars=[assembly_loc_z,
                                                      assembly_b_loc_z,
                                                      assembly_b_dim_z])
                else:
                    self.dimension.start_z(expression="assembly_dim_z", driver_vars=[assembly_dim_z])
                    self.dimension.end_z(expression="-assembly_loc_z-assembly_dim_z+assembly_b_loc_z+assembly_b_dim_z",
                                         driver_vars=[assembly_loc_z,
                                                      assembly_dim_z,
                                                      assembly_b_loc_z,
                                                      assembly_b_dim_z])
            else:
                self.dimension.end_z(expression="-loc_z",
                                     driver_vars=[self.assembly.get_var("loc_z")])

        if self.configuration == 'AVAILABLE_SPACE_LEFT':
            if assembly_l:
                self.dimension.end_x(expression="-assembly_loc_x+assembly_l_loc_x+assembly_l_dim_x",
                                     driver_vars=[assembly_l_loc_x,
                                                  assembly_loc_x,
                                                  assembly_l_dim_x])
            else:
                self.dimension.end_x(expression="-assembly_loc_x", driver_vars=[assembly_loc_x])

        if self.configuration == 'AVAILABLE_SPACE_RIGHT':
            self.dimension.start_x(expression="dim_x", driver_vars=[self.assembly.get_var("dim_x")])
            if assembly_r:
                self.dimension.end_x(expression="assembly_r_loc_x-assembly_loc_x-assembly_dim_x",
                                     driver_vars=[assembly_r_loc_x,
                                                  assembly_loc_x,
                                                  assembly_dim_x])

            else:
                self.dimension.end_x(expression="wall_dim_x-assembly_loc_x-assembly_dim_x",
                                     driver_vars=[wall_dim_x,
                                                  assembly_loc_x,
                                                  assembly_dim_x])

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        config_box = layout.box()
        config_box.label(text="Configuration")

        row = config_box.row()
        split1 = row.split(align=True)
        split1.label(text="Assembly Dimension: ")
        split1.prop_enum(self, "configuration", 'WIDTH')
        split1.prop_enum(self, "configuration", 'HEIGHT')
        split1.prop_enum(self, "configuration", 'DEPTH')

        row = config_box.row()
        split2 = row.split(align=True)
        split2.label(text="To Wall: ")
        split2.prop_enum(self, "configuration", 'WALL_LEFT', text="Left")
        split2.prop_enum(self, "configuration", 'WALL_RIGHT', text="Right")
        split2.prop_enum(self, "configuration", 'WALL_TOP', text="Top")
        split2.prop_enum(self, "configuration", 'WALL_BOTTOM', text="Bottom")

        row = config_box.row()
        split3 = row.split(align=True)
        split3.label(text="Available Space: ")
        split3.prop_enum(self, "configuration", 'AVAILABLE_SPACE_LEFT', text="Left")
        split3.prop_enum(self, "configuration", 'AVAILABLE_SPACE_RIGHT', text="Right")
        split3.prop_enum(self, "configuration", 'AVAILABLE_SPACE_ABOVE', text="Above")
        split3.prop_enum(self, "configuration", 'AVAILABLE_SPACE_BELOW', text="Below")

        if self.configuration == 'AVAILABLE_SPACE_ABOVE' and self.assembly.get_adjacent_assembly(direction='ABOVE'):
            row = config_box.row()
            row.prop(self, "above_assembly_draw_to", text="Draw to Above Assembly")

        box2 = layout.box()
        col = box2.column()
        col.prop(self, "label", text="Label")
        col.prop(self, "offset", text="Offset")


class VIEW_OT_dimension_options(Operator):
    bl_idname = "sn_2d_views.dimension_options"
    bl_label = "Dimension Global Options"

    info = {}

    @classmethod
    def poll(cls, context):
        return True

    def check(self, context):
        return True

    def execute(self, context):
        pass
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(320))

    def draw(self, context):
        # wm = context.window_manager.snap
        scene = context.scene
        dim_props = scene.snap.opengl_dim
        sys_units = scene.unit_settings.system
        layout = self.layout
        box = layout.box()

        row = box.row()

        if dim_props.gl_dim_units == 'AUTO':
            row.label(text="Units:" + "                    (" + sys_units.title() + ")")
        else:
            row.label(text="Units:")

        row.prop(dim_props, 'gl_dim_units', text="")

        row = box.row()
        row.label(text="Arrow Type:")
        row.prop(dim_props, 'gl_arrow_type', text="")
        row = box.row()
        row.label(text="Color:")
        row.prop(dim_props, 'gl_default_color', text="")
        row = box.row()

        if dim_props.gl_dim_units in ('INCH', 'FEET') or dim_props.gl_dim_units == 'AUTO' and sys_units == 'IMPERIAL':
            row.label(text="Round to the nearest:")
            row.prop(dim_props, 'gl_imperial_rd_factor', text="")
            row = box.row()
            row.label(text="Number format:")
            row.prop(dim_props, 'gl_number_format', text="")

        else:
            row.label(text="Precision:")
            row.prop(dim_props, 'gl_precision', text="")

        row = box.row()
        row.label(text="Text Size:")
        row.prop(dim_props, 'gl_font_size', text="")
        row = box.row()
        row.label(text="Arrow Size:")
        row.prop(dim_props, 'gl_arrow_size', text="")


class VIEW_OT_create_single_dimension(Operator):
    bl_idname = "sn_2d_views.create_single_dimension"
    bl_label = "Create Single Dimension"

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        dim = sn_types.Dimension()
        dim.end_x(value=unit.inch(0))
        dim.anchor.select_set(True)
        context.view_layer.objects.active = dim.anchor
        bpy.ops.sn_2d_views.toggle_dimension_handles(turn_on=True)
        context.window_manager.snap.use_opengl_dimensions = True
        return {'FINISHED'}


class VIEW_OT_toggle_dimension_handles(Operator):
    bl_idname = "sn_2d_views.toggle_dimension_handles"
    bl_label = "Toggle Dimension Handles"

    turn_on: BoolProperty(name="Turn On", default=False)

    def execute(self, context):
        space_data = context.space_data

        if not space_data.overlay.show_extras:
            space_data.overlay.show_extras = True

        if context.scene.name == '_Main' or context.scene.name == 'Scene':
            collection_objs = bpy.data.collections['Collection'].objects
        else:
            collection_objs = context.scene.collection.objects
        for obj in collection_objs:
            if obj.get("IS_VISDIM_A") or obj.get("IS_VISDIM_B"):
                # obj.hide_set(not self.turn_on)
                obj.hide_viewport = not self.turn_on
        return {'FINISHED'}


class VIEW_OT_dimension_interface(Operator):
    bl_idname = "sn_2d_views.dimension_interface"
    bl_label = "Dimension Global Options"

    info = {}

    @classmethod
    def poll(cls, context):
        return True

    def check(self, context):
        return True

    def execute(self, context):
        pass
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(320))

    def draw(self, context):
        # wm = context.window_manager.snap
        scene = context.scene
        dim_props = scene.snap.opengl_dim
        sys_units = scene.unit_settings.system
        layout = self.layout
        box = layout.box()

        row = box.row()

        if dim_props.gl_dim_units == 'AUTO':
            row.label(text="Units:" + "                    (" + sys_units.title() + ")")
        else:
            row.label(text="Units:")

        row.prop(dim_props, 'gl_dim_units', text="")

        row = box.row()
        row.label(text="Arrow Type:")
        row.prop(dim_props, 'gl_arrow_type', text="")
        row = box.row()
        row.label(text="Color:")
        row.prop(dim_props, 'gl_default_color', text="")
        row = box.row()

        if dim_props.gl_dim_units == 'FEET' or dim_props.gl_dim_units == 'AUTO' and sys_units == 'IMPERIAL':
            row.label(text="Round to the nearest:")
            row.prop(dim_props, 'gl_imperial_rd_factor', text="")
            row = box.row()
            row.label(text="Number format:")
            row.prop(dim_props, 'gl_number_format', text="")
        elif dim_props.gl_dim_units == 'INCH' and sys_units == 'IMPERIAL':
            row.label(text="Precision:")
            row.prop(dim_props, 'gl_precision', text="")
            row = box.row()
            row.label(text="Number format:")
            row.prop(dim_props, 'gl_number_format', text="")
        else:
            row.label(text="Precision:")
            row.prop(dim_props, 'gl_precision', text="")

        row = box.row()
        row.label(text="Text Size:")
        row.prop(dim_props, 'gl_font_size', text="")
        row = box.row()
        row.label(text="Arrow Size:")
        row.prop(dim_props, 'gl_arrow_size', text="")


class VIEW_OT_walk_space_dimension(Operator):
    bl_idname = "sn_2d_views.draw_walk_space"
    bl_label = "Draw Walk Space"

    info = {}

    def execute(self, context):
        walls, islands = self.get_walls_islands(context)
        walls_coords = self.get_walls_coordinates(walls)
        self.write_space_to_walk(islands, walls, walls_coords)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

    def get_walls_islands(self, context):
        walls = []
        islands = []
        scene = context.scene
        for obj in scene.objects:
            if obj.get("IS_BP_WALL"):
                wall = sn_types.Wall(obj_bp=obj)
                walls.append(wall)
            name = obj.name
            if "Island" in name:
                wall_bp = sn_utils.get_wall_bp(obj)
                if not wall_bp:
                    islands.append(obj)
        islands = sorted(islands, 
                key=lambda i: i.location[0])
        for idx, island in enumerate(islands):
            island["ISLAND_INDEX"] = str(idx + 1)
        return walls, islands

    def get_walls_coordinates(self, walls):
        walls_coordinates = []
        prev_x = 0
        prev_y = 0
        for wall in walls:
            wall_len = wall.obj_x.location.x
            theta = wall.obj_bp.rotation_euler.z
            if walls.index(wall) == 0:
                x_0 = wall.obj_bp.location.x
                y_0 = wall.obj_bp.location.y
            else:
                x_0 = prev_x
                y_0 = prev_y
            x_f = x_0 + wall_len*np.cos(theta)
            y_f = y_0 + wall_len*np.sin(theta)
            wall_coord = [[x_0, y_0], [x_f, y_f]]
            prev_x = x_f
            prev_y = y_f
            walls_coordinates.append(wall_coord)
        return walls_coordinates

    def write_space_to_walk(self, islands, walls, walls_coords):
        sides = ["left", "right", "top", "bottom"]
        for island in islands:
            for side in sides:
                target_wall =\
                    self.get_target_wall(island, walls, walls_coords, side)
                if target_wall is not None:
                    self.write_space_dim(island, target_wall, side)
            self.write_island_label(island, walls[0])

    def write_island_label(self, island, wall):
        corners = self.get_island_corners(island)
        z_loc = wall.obj_z.location.z
        island_assembly = sn_types.Assembly(obj_bp=island)
        dim_x = abs(island_assembly.obj_x.location.x)
        dim_y = abs(island_assembly.obj_y.location.y)
        theta = island.rotation_euler.z
        delta = 0.15
        off_factor = 0.2
        label_locations = {
            1: [
                corners[0][0] +
                off_factor*dim_x*np.cos(theta) + delta*np.sin(theta),
                corners[0][1] +
                off_factor*dim_x*np.sin(theta) - delta*np.cos(theta),
                z_loc],
            2: [
                corners[3][0] +
                off_factor*dim_y*np.sin(theta) - delta*np.cos(theta),
                corners[3][1] -
                off_factor*dim_y*np.cos(theta) - delta*np.sin(theta),
                z_loc],
            3: [
                corners[2][0] -
                off_factor*np.cos(theta) - delta*np.sin(theta),
                corners[2][1] -
                off_factor*dim_x*np.sin(theta) + delta*np.cos(theta),
                z_loc],
            4: [
                corners[1][0] -
                off_factor*dim_y*np.sin(theta) + delta*np.cos(theta),
                corners[1][1] +
                off_factor*dim_y*np.cos(theta) + delta*np.sin(theta),
                z_loc]
        }
        for i in range(4):
            label_location = label_locations[i+1]
            island_index = island.get("ISLAND_INDEX")
            if island_index:
                counter = f"{str(((int(island_index) * 4) + (i + 1)) - 4)}"
                self.label_island_side("I-" + counter, label_location)
            elif not island_index:
                self.label_island_side("I-" + str(i+1), label_location)

    def write_space_dim(self, island, target_wall, side):
        side_vector = self.get_side_vector(island, side)
        wall_vector = target_wall[1]
        p0_x = max(
            min(side_vector[0][0], side_vector[1][0]),
            min(wall_vector[0][0], wall_vector[1][0]))
        pf_x = min(
            max(side_vector[0][0], side_vector[1][0]),
            max(wall_vector[0][0], wall_vector[1][0]))
        p0_y = max(
            min(side_vector[0][1], side_vector[1][1]),
            min(wall_vector[0][1], wall_vector[1][1]))
        pf_y = min(
            max(side_vector[0][1], side_vector[1][1]),
            max(wall_vector[0][1], wall_vector[1][1]))
        wall = target_wall[0]
        center_points = {
            "left": (p0_y + pf_y)/2,
            "right": (p0_y + pf_y)/2,
            "top": (p0_x + pf_x)/2,
            "bottom": (p0_x + pf_x)/2
        }
        center_point = center_points[side]
        depth = self.get_max_depth_wall(target_wall, center_point)
        wall_z_loc = wall.obj_z.location.z  # noqa F841
        start_points = {
            "left": (wall_vector[0][0] + depth, center_point, wall_z_loc),
            "right": (side_vector[0][0], center_point, wall_z_loc),
            "top": (center_point, side_vector[0][1], wall_z_loc),
            "bottom": (center_point, side_vector[0][1], wall_z_loc)
        }
        end_points_dir_index = {
            "left": [1, 0],
            "right": [1, 0],
            "top": [1, 1],
            "bottom": [-1, 1]
        }
        distance = target_wall[2] - depth
        start_point = start_points[side]
        end_point_dir = end_points_dir_index[side][0]
        index = end_points_dir_index[side][1]
        end_point = [0, 0, 0]
        end_point[index] = end_point_dir*distance
        self.draw_island_dim(start_point, end_point, distance)

    def get_target_wall(self, island, walls, walls_coords, side):
        side_vector = self.get_side_vector(island, side)
        origin_side_vector =\
            np.array(side_vector[1]) - np.array(side_vector[0])
        wall_candidates = []
        for wall in walls:
            wall_index = walls.index(wall)
            wall_vector = walls_coords[wall_index]
            wall_origin_vector =\
                np.array(wall_vector[1]) - np.array(wall_vector[0])
            dot_prod = np.dot(
                (1/np.linalg.norm(wall_origin_vector))*wall_origin_vector,
                (1/np.linalg.norm(origin_side_vector))*origin_side_vector)
            is_parallel = abs(round(dot_prod, 1)) == 1
            location_conditions = {
                "left": wall_vector[0][0] < side_vector[0][0],
                "right": wall_vector[0][0] > side_vector[0][0],
                "top": wall_vector[0][1] > side_vector[0][1],
                "bottom": wall_vector[0][1] < side_vector[0][1]
            }
            location_condition = location_conditions[side]
            if is_parallel and location_condition:
                is_candidate =\
                    self.is_contained_segment(wall_vector, side_vector)
                if is_candidate:
                    wall_candidates.append([wall, wall_vector])
        if len(wall_candidates) == 0:
            return None
        target_wall =\
            self.get_wall_from_candidates(side_vector, wall_candidates, side)
        return target_wall

    def get_wall_from_candidates(self, side_vector, wall_candidates, side):
        side_distance = {
                "left": "abs(side_vector[0][0] - wall_vector[0][0])",
                "right": "abs(wall_vector[0][0] - side_vector[0][0])",
                "top": "abs(wall_vector[0][1] - side_vector[0][1])",
                "bottom": "abs(side_vector[0][1] - wall_vector[0][1])"
        }
        distances = []
        for wall, wall_vector in wall_candidates:
            distance = eval(side_distance[side])
            distances.append(distance)
        min_distance = min(distances)
        index = distances.index(min_distance)
        target_wall = wall_candidates[index]
        return [target_wall[0], target_wall[1], min_distance]

    def is_contained_segment(self, segment_wall, segment_side):
        i_vector = np.array([1, 0])
        j_vector = np.array([0, 1])
        is_x_contained =\
            self.is_contained_segment_axis(
                segment_wall, segment_side, i_vector)
        is_y_contained =\
            self.is_contained_segment_axis(
                segment_wall, segment_side, j_vector)
        return is_x_contained or is_y_contained

    def is_contained_segment_axis(self, segment_wall, segment_side, axis):
        wall_a_proj = np.dot(segment_wall[0], axis)
        wall_b_proj = np.dot(segment_wall[1], axis)
        wall_0_proj = min(wall_a_proj, wall_b_proj)
        wall_f_proj = max(wall_a_proj, wall_b_proj)
        side_a_proj = np.dot(segment_side[0], axis)
        side_b_proj = np.dot(segment_side[1], axis)
        side_0_proj = min(side_a_proj, side_b_proj)
        side_f_proj = max(side_a_proj, side_b_proj)
        is_contained =\
            not (side_0_proj > wall_f_proj or wall_0_proj > side_f_proj)
        return is_contained

    def get_side_vector(self, island, side):
        island_corners = self.get_island_corners(island)
        left_point = self.get_external_point(island_corners, "left")
        right_point = self.get_external_point(island_corners, "right")
        top_point = self.get_external_point(island_corners, "top")
        bottom_point = self.get_external_point(island_corners, "bottom")
        coords = {
            "left": [
                [left_point[0], bottom_point[1]],
                [left_point[0], top_point[1]]],
            "right": [
                [right_point[0], top_point[1]],
                [right_point[0], bottom_point[1]]],
            "top": [
                [right_point[0], top_point[1]],
                [left_point[0], top_point[1]]],
            "bottom": [
                [left_point[0], bottom_point[1]],
                [right_point[0], bottom_point[1]]],
        }
        return coords[side]

    def get_external_point(self, points, position):
        indices = {
            "left": 0,
            "right": 0,
            "top": 1,
            "bottom": 1
        }
        functions = {
            "left": min,
            "right": max,
            "top": max,
            "bottom": min
        }
        coords = []
        axis = indices[position]
        function = functions[position]
        for point in points:
            coords.append(point[axis])
        external_coord = function(coords)
        index = coords.index(external_coord)
        return points[index]

    def get_island_corners(self, island):
        island_assembly = sn_types.Assembly(obj_bp=island)
        dim_x = abs(island_assembly.obj_x.location.x)
        dim_y = abs(island_assembly.obj_y.location.y)
        loc_x = island.location.x
        loc_y = island.location.y
        theta = island.rotation_euler.z
        p1_x = loc_x + dim_y*np.sin(theta)
        p1_y = loc_y - dim_y*np.cos(theta)
        p2_x = loc_x + dim_y*np.sin(theta) + dim_x*np.cos(theta)
        p2_y = p1_y + dim_x*np.sin(theta)
        p3_x = loc_x + dim_x*np.cos(theta)
        p3_y = loc_y + dim_x*np.sin(theta)
        p4_x = loc_x
        p4_y = loc_y
        return [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y), (p4_x, p4_y)]

    def get_hang_conditions(self, element, closet_loc_x, center_point, factor):
        children = element.children
        element_assembly = sn_types.Assembly(obj_bp=element)
        panel_thk = element_assembly.get_prompt("Panel Thickness")
        if not panel_thk:
            return False
        panel_thk_val = panel_thk.get_value()
        for child in children:
            if "Hang" in child.name:
                child_assembly = sn_types.Assembly(obj_bp=child)
                child_width = abs(child_assembly.obj_x.location.x)
                hang_loc_x =\
                    closet_loc_x + factor*(child.location.x - panel_thk_val)
                hang_final = hang_loc_x + factor*(child_width + panel_thk_val)
                hang_0 = min(hang_loc_x, hang_final)
                hang_f = max(hang_loc_x, hang_final)
                is_hang_front_island =\
                    hang_0 <= center_point and hang_f > center_point  # noqa E501
                if is_hang_front_island:
                    return True
        return False

    def get_max_depth_wall(self, target_wall, center_point):
        wall = target_wall[0]
        wall_vector = target_wall[1]
        theta = wall.obj_bp.rotation_euler.z
        wall_point_0 = wall_vector[0]
        if round(theta, 2) == 0 or abs(round(theta, 2)) == round(np.pi, 2):  # noqa E501
            wall_location = wall_point_0[0]
            factor = 1 if np.cos(theta) >= 0 else -1
        elif abs(round(theta, 2)) == round(np.pi/2, 2):
            wall_location = wall_point_0[1]
            factor = 1 if np.sin(theta) >= 0 else -1
        children = wall.obj_bp.children
        for child in children:
            child_assembly = sn_types.Assembly(obj_bp=child)
            opening_qty = child_assembly.get_prompt("Opening Quantity")
            child_dim_y = child_assembly.obj_y
            if opening_qty:
                is_in_front_island =\
                    self.is_obj_in_front_island(
                        wall_location, child_assembly, factor, center_point)
                if is_in_front_island:
                    return self.get_closet_op_depth(
                        child_assembly, wall_location,
                        center_point, factor)
            elif child_dim_y:
                is_in_front_island =\
                    self.is_obj_in_front_island(
                        wall_location, child_assembly, factor, center_point)
                child_loc_x = wall_location + factor*abs(child.location.x)
                draw_to_hang =\
                    self.get_hang_conditions(
                        child, child_loc_x, center_point, factor)
                if is_in_front_island and draw_to_hang:
                    return unit.inch(24)
                elif is_in_front_island and "Entry Door" in child.name:
                    return 0
                elif is_in_front_island:
                    return abs(child_assembly.obj_y.location.y)
        return 0

    def is_obj_in_front_island(self, wall_location, obj_assembly,
                               factor, center_point):
        obj = obj_assembly.obj_bp
        obj_width = abs(obj_assembly.obj_x.location.x)
        obj_loc_x = wall_location + factor*abs(obj.location.x)
        final_point = obj_loc_x + factor*obj_width
        loc_0 = min(obj_loc_x, final_point)
        loc_f = max(obj_loc_x, final_point)
        return loc_0 <= center_point and loc_f > center_point

    def get_closet_op_depth(self, closet_assembly, wall_location,
                            center_point, factor):
        opening_qty =\
            closet_assembly.get_prompt("Opening Quantity").get_value()
        closet = closet_assembly.obj_bp
        left_side_thk = closet_assembly.get_prompt(
            "Left Side Thickness").get_value()
        panel_thk = closet_assembly.get_prompt(
            "Panel Thickness").get_value()
        closet_loc_x = wall_location + factor*abs(closet.location.x)
        opening_loc_x = closet_loc_x
        draw_to_hang = self.get_hang_conditions(
            closet, closet_loc_x, center_point, factor)
        if draw_to_hang:
            return unit.inch(24)
        for i in range(opening_qty):
            opening_depth =\
                closet_assembly.get_prompt(
                    "Opening " + str(i+1) + " Depth").get_value()
            opening_width =\
                closet_assembly.get_prompt(
                    "Opening " + str(i+1) + " Width").get_value()
            left_panel_thk = left_side_thk if i == 0 else panel_thk
            opening_final_point =\
                opening_loc_x + factor*(opening_width + left_panel_thk)
            loc_0 = min(opening_loc_x, opening_final_point)
            loc_f = max(opening_loc_x, opening_final_point)
            is_in_front_island =\
                loc_0 <= center_point and loc_f > center_point
            if is_in_front_island:
                return opening_depth
            opening_loc_x = opening_final_point
        return 0

    def label_island_side(self, text, location):
        label = sn_types.Dimension()
        label.start_x(value=location[0])
        label.start_y(value=location[1])
        label.start_z(value=location[2])
        label.set_label(text)
        label.anchor.snap.comment = "render_plan"
        label.end_point.snap.comment = "render_plan"

    def draw_island_dim(self, start_point, end_point, distance):
        dim = sn_types.Dimension()
        dim.anchor.snap.comment = "render_plan"
        dim.end_point.snap.comment = "render_plan"
        dim.start_x(value=start_point[0])
        dim.start_y(value=start_point[1])
        dim.start_z(value=start_point[2])
        dim.end_point.location = (end_point[0], end_point[1], end_point[2])
        lbl = self.to_inch_lbl(distance)
        dim.set_label(lbl)

    def to_inch_lbl(self, measure):
        return self.to_inch_str(measure) + "\""

    def to_inch(self, measure):
        return round(measure / unit.inch(1), 2)

    def to_inch_str(self, measure):
        return str(self.to_inch(measure))


classes = (
    VIEW_OT_move_image_list_item,
    VIEW_OT_create_new_view,
    VIEW_OT_append_to_view,
    VIEW_OT_generate_2d_views,
    VIEW_OT_render_2d_views,
    VIEW_OT_view_image,
    VIEW_OT_delete_image,
    VIEW_OT_create_snap_shot,
    VIEW_OT_add_annotation,
    VIEW_OT_add_dimension,
    VIEW_OT_dimension_options,
    VIEW_OT_create_single_dimension,
    VIEW_OT_toggle_dimension_handles,
    VIEW_OT_dimension_interface,
    VIEW_OT_walk_space_dimension,
    VIEW_OT_accordion_interface,
)

register, unregister = bpy.utils.register_classes_factory(classes)
