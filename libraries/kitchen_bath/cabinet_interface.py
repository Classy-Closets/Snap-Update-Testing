from ctypes.wintypes import tagMSG
import bpy
from bpy.props import (
    StringProperty,
    FloatProperty,
    EnumProperty
    )


import math
import snap
from snap import sn_types, sn_unit, sn_utils
from snap.libraries.kitchen_bath.carcass_simple import Inside_Corner_Carcass, Standard_Carcass
from . import cabinet_properties
from .frameless_exteriors import Doors, Vertical_Drawers, Horizontal_Drawers
from snap.libraries.closets.ui.closet_prompts_ui import get_panel_heights

def draw_carcass_options(carcass,layout):
    left_fin_end = carcass.get_prompt("Left Fin End")
    right_fin_end = carcass.get_prompt("Right Fin End")
    left_wall_filler = carcass.get_prompt("Left Side Wall Filler")
    right_wall_filler = carcass.get_prompt("Right Side Wall Filler")
    
    valance_height_top = carcass.get_prompt("Valance Height Top")
    toe_kick_height = carcass.get_prompt("Toe Kick Height")
    remove_bottom = carcass.get_prompt("Remove Bottom")
    remove_back = carcass.get_prompt("Remove Back")
    use_thick_back = carcass.get_prompt("Use Thick Back")
    use_nailers = carcass.get_prompt("Use Nailers")
    cabinet_depth_left = carcass.get_prompt("Cabinet Depth Left")
    cabinet_depth_right = carcass.get_prompt("Cabinet Depth Right")
    
    # SIDE OPTIONS:
    if left_wall_filler and right_wall_filler:
        col = layout.column(align=True)
        col.label(text="Side Options:")
        
        row = col.row()
        row.prop(left_wall_filler,'distance_value',text="Left Filler Amount")
        row.prop(right_wall_filler,'distance_value',text="Right Filler Amount")
    
    # CARCASS OPTIONS:
    col = layout.column(align=True)
    col.label(text="Carcass Options:")
    row = col.row()

    if use_thick_back:
        row.prop(use_thick_back,'checkbox_value',text="Use Thick Back")
    # if use_nailers:t
    #     row.prop(use_nailers,'checkbox_value',text="Use Nailers")
    if remove_bottom:
        row.prop(remove_bottom,'checkbox_value',text="Remove Bottom")
    if remove_back:
        row.prop(remove_back,'checkbox_value',text="Remove Back")
    if cabinet_depth_left:
        row = col.row()
        row.prop(cabinet_depth_left,'distance_value',text="Cabinet Depth Left")
        row.prop(cabinet_depth_right,'distance_value',text="Cabinet Depth Right")
    
    # TOE KICK OPTIONS
    if toe_kick_height:
        col = layout.column(align=True)
        toe_kick_setback = carcass.get_prompt("Toe Kick Setback")
        col.label(text="Toe Kick Options:")
        row = col.row()
        row.prop(toe_kick_height,'distance_value',text="Toe Kick Height")
        row.prop(toe_kick_setback,'distance_value',text="Toe Kick Setback")
        
    # VALANCE OPTIONS
    if valance_height_top:
        r_full_height = carcass.get_prompt("Right Side Full Height")
        l_full_height = carcass.get_prompt("Left Side Full Height")
        valance_each_unit = carcass.get_prompt("Valance Each Unit")
        
        col = layout.column(align=True)
        col.label(text="Valance Options:")
        door_valance_top = carcass.get_prompt("Door Valance Top")
        row = col.row()
        row.prop(valance_height_top,'distance_value',text="Valance Height Top")
        row.prop(door_valance_top,'checkbox_value',text="Door Valance Top")

        valance_height_bottom = carcass.get_prompt("Valance Height Bottom")
        
        if valance_height_bottom:
            door_valance_bottom = carcass.get_prompt("Door Valance Bottom")
            row = col.row()
            row.prop(valance_height_bottom,'distance_value',text="Valance Height Bottom")
            row.prop(door_valance_bottom,'checkbox_value',text="Door Valance Bottom")
        
        row = col.row()
        row.prop(l_full_height,'checkbox_value',text="Left Side Full Height")
        row.prop(r_full_height,'checkbox_value',text="Right Side Full Height")
        
        row = col.row()
        row.prop(valance_each_unit,'checkbox_value',text="Add Valance For Each Unit")

def draw_countertop_options(ctop,product,layout):
    Add_Backsplash = ctop.get_prompt("Add Backsplash")
    Add_Left_Backsplash = ctop.get_prompt("Add Left Backsplash")
    Add_Right_Backsplash = ctop.get_prompt("Add Right Backsplash")
    Countertop_Overhang_Front = product.get_prompt("Countertop Overhang Front")
    Countertop_Overhang_Right_Front = product.get_prompt("Countertop Overhang Right Front")
    Countertop_Overhang_Left_Front = product.get_prompt("Countertop Overhang Left Front")
    Countertop_Overhang_Back = product.get_prompt("Countertop Overhang Back")
    Countertop_Overhang_Right_Back = product.get_prompt("Countertop Overhang Right Back")
    Countertop_Overhang_Left_Back = product.get_prompt("Countertop Overhang Left Back")
    Countertop_Overhang_Left = product.get_prompt("Countertop Overhang Left")
    Countertop_Overhang_Right = product.get_prompt("Countertop Overhang Right")
    
    
    Countertop_Overhang = product.get_prompt("Countertop Overhang")
    Add_Left_Rear_Backsplash = ctop.get_prompt("Add Left Rear Backsplash")
    Add_Right_Rear_Backsplash = ctop.get_prompt("Add Right Rear Backsplash")

    box = layout.box()
    col = box.column(align=True)
    col.label(text="Countertop Options:")
    
    if Add_Left_Backsplash and Add_Right_Backsplash:

        if Add_Backsplash:
            row = col.row(align=True)
            row.prop(Add_Backsplash,'checkbox_value',text="")
            row.label(text="Add Back Splash")

        if Add_Left_Backsplash:
            row = col.row(align=True)
            row.prop(Add_Left_Backsplash,'checkbox_value',text="")            
            row.label(text="Add Left Splash")
            row.prop(Add_Right_Backsplash,'checkbox_value',text="")            
            row.label(text="Add Right Splash")
        
        if Add_Left_Rear_Backsplash:
            row = col.row(align=True)
            row.prop(Add_Left_Rear_Backsplash,'checkbox_value',text="")            
            row.label(text="Add Left Rear Splash")
            row.prop(Add_Right_Rear_Backsplash,'checkbox_value',text="")   
            row.label(text="Add Right Rear Splash")
    
    if Countertop_Overhang_Left:
        col = box.column(align=False)
        col.label(text="Overhang:")

        if Countertop_Overhang_Front:
            row_1 = col.row(align=True)
            row_1.prop(Countertop_Overhang_Front,'distance_value',text="Front")
            row_1.prop(Countertop_Overhang_Back,'distance_value',text="Back")

        if Countertop_Overhang_Right_Front:
            row_1 = col.row(align=True)
            row_1.prop(Countertop_Overhang_Left_Front,'distance_value',text="Front Left")
            row_1.prop(Countertop_Overhang_Right_Front,'distance_value',text="Front Right")
            
            row_2 = col.row(align=True)
            row_2.prop(Countertop_Overhang_Left_Back,'distance_value',text="Back Left")
            row_2.prop(Countertop_Overhang_Right_Back,'distance_value',text="Back Right")
            

        row_3 = col.row(align=True)
        row_3.prop(Countertop_Overhang_Left,'distance_value',text="Left")
        row_3.prop(Countertop_Overhang_Right,'distance_value',text="Right")

    # if Countertop_Overhang:
    #     row = col.row(align=True)
    #     split = row.split(factor=0.50)
    #     row = split.row()
    #     row.label(text="Overhang:")
    #     row.prop(Countertop_Overhang,'distance_value',text="Front")


def draw_door_options(door,layout):
    box = layout.box()

    open_door = door.get_prompt('Open Door')
    door_swing = door.get_prompt('Door Swing')
    inset_front = door.get_prompt('Inset Front')
    
    half_overlay_top = door.get_prompt('Half Overlay Top')
    half_overlay_bottom = door.get_prompt('Half Overlay Bottom')
    half_overlay_left = door.get_prompt('Half Overlay Left')
    half_overlay_right = door.get_prompt('Half Overlay Right')
    
    row = box.row()
    row.label(text="Door Options:")
    
    if open_door:
        # inset_front.draw(row, alt_text="Inset Door", allow_edit=False)
        open_door.draw(row, allow_edit=False)
        
    if door_swing:
        row = box.row()
        door_swing.draw(row, allow_edit=False)
    
    if inset_front:
        if not inset_front.get_value():
            row = box.row()
            row.label(text="Half Overlays:")
            if half_overlay_top:
                half_overlay_top.draw(row, alt_text="Top",allow_edit=False)
            if half_overlay_bottom:
                half_overlay_bottom.draw(row, alt_text="Bottom",allow_edit=False)
            if half_overlay_left:
                half_overlay_left.draw(row, alt_text="Left",allow_edit=False)
            if half_overlay_right:
                half_overlay_right.draw(row, alt_text="Right",allow_edit=False)

def draw_drawer_options(drawers,layout):
    open_prompt = drawers.get_prompt("Open Drawers")
    inset_front = drawers.get_prompt("Inset Front")
    half_overlay_top = drawers.get_prompt("Half Overlay Top")
    half_overlay_bottom = drawers.get_prompt("Half Overlay Bottom")
    half_overlay_left = drawers.get_prompt("Half Overlay Left")
    half_overlay_right = drawers.get_prompt("Half Overlay Right")
    
    box = layout.box()
    row = box.row()
    row.label(text="Drawer Options:")

    # if inset_front:
    #     row.prop(inset_front,'checkbox_value',text="Inset Drawer Front")

    if open_prompt:
        open_prompt.draw(row,allow_edit=False)

    if inset_front:
        if not inset_front.get_value():
            if half_overlay_top:
                col = box.column(align=True)
                row = col.row()
                row.label(text="Half Overlays:")
                row.prop(half_overlay_top,'checkbox_value',text="Top")
                row.prop(half_overlay_bottom,'checkbox_value',text="Bottom")
                row.prop(half_overlay_left,'checkbox_value',text="Left")
                row.prop(half_overlay_right,'checkbox_value',text="Right")
    
    df_2_height = drawers.get_prompt("Drawer Front 2 Height")

    if df_2_height:
        for i in range(1,10):
            drawer_height = drawers.get_prompt("Drawer Front " + str(i) + " Height")
            if drawer_height:
                row = box.row()
                row.label(text="Drawer Front " + str(i) + " Height:")
                if drawer_height.equal:
                    row.label(text=str(sn_unit.meter_to_active_unit(drawer_height.get_value())))
                    row.prop(drawer_height,'equal',text="")
                else:
                    row.prop(drawer_height,'distance_value',text="")
                    row.prop(drawer_height,'equal',text="")
            else:
                break

def draw_interior_options(assembly,layout):
    box = layout.box()
    
    adj_shelf_qty = assembly.get_prompt("Adj Shelf Qty")
    fix_shelf_qty = assembly.get_prompt("Fixed Shelf Qty")
    shelf_qty = assembly.get_prompt("Shelf Qty")
    shelf_setback = assembly.get_prompt("Shelf Setback")
    adj_shelf_setback = assembly.get_prompt("Adj Shelf Setback")
    fix_shelf_setback = assembly.get_prompt("Fixed Shelf Setback")
    div_qty_per_row = assembly.get_prompt("Divider Qty Per Row")
    division_qty = assembly.get_prompt("Division Qty")
    adj_shelf_rows = assembly.get_prompt("Adj Shelf Rows")
    fixed_shelf_rows = assembly.get_prompt("Fixed Shelf Rows")
    
    if shelf_qty:
        row = box.row()
        shelf_qty.draw(row,allow_edit=False)    
    
    if shelf_setback:
        row.label(text="Shelf Setback:")
        row.prop(shelf_setback,'distance_value', text="")
    
    if adj_shelf_qty:
        row = box.row()
        adj_shelf_qty.draw(row,allow_edit=False)

    if adj_shelf_setback:
        adj_shelf_setback.draw(row,allow_edit=False)
        
    if fix_shelf_qty:
        row = box.row()
        fix_shelf_qty.draw(row,allow_edit=False)

    if fix_shelf_setback:
        fix_shelf_setback.draw(row,allow_edit=False)
        
    if div_qty_per_row:
        row = box.row()
        div_qty_per_row.draw(row,allow_edit=False)

    if division_qty:
        row = box.row()
        division_qty.draw(row,allow_edit=False)

    if adj_shelf_rows:
        row = box.row()
        adj_shelf_rows.draw(row,allow_edit=False)

    if fixed_shelf_rows:
        row = box.row()
        fixed_shelf_rows.draw(row,allow_edit=False)

def draw_splitter_options(assembly,layout):
    if assembly.get_prompt("Opening 1 Height"):
        name = "Height"
    else:
        name = "Width"
        
    box = layout.box()
    
    for i in range(1,10):
        opening = assembly.get_prompt("Opening " + str(i) + " " + name)
        if opening:
            row = box.row()
            row.label(text="Opening " + str(i) + " " + name  + ":")
            if opening.equal:
                row.label(text=str(sn_unit.meter_to_active_unit(opening.get_value())))
                row.prop(opening,'equal',text="")
            else:
                row.prop(opening,'distance_value',text="")
                row.prop(opening,'equal',text="")
        else:
            break
class SNAP_PT_Cabinet_Options(bpy.types.Panel):
    """Panel to Store all of the Cabinet Options"""
    bl_id = cabinet_properties.LIBRARY_NAME_SPACE + "_Advanced_Cabinet_Options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Advanced Cabinet Options"

    props = None

    @classmethod
    def poll(cls, context):
        prefs = context.preferences.addons["snap"].preferences
        return prefs.enable_kitchen_bath_lib

    def draw_header(self, context):
        layout = self.layout
        wm = context.window_manager.snap
        kb_icon = wm.libraries["Kitchen Bath Library"].icon
        layout.label(text='', icon_value=snap.snap_icons[kb_icon].icon_id)        

    def draw_molding_options(self,layout):
        molding_box = layout.box()
        row = molding_box.row(align=True)
        row.label(text="Moldings Options:")
        row = molding_box.row(align=True)
        row.prop(self.props,'expand_crown_molding',text="",icon='TRIA_DOWN' if self.props.expand_crown_molding else 'TRIA_RIGHT',emboss=False)
        row.label(text="Crown:")
        row.prop(self.props,'crown_molding_category',text="",icon='FILE_FOLDER')
        row.prop(self.props,'crown_molding',text="")
        row.operator(cabinet_properties.LIBRARY_NAME_SPACE + ".auto_add_molding",text="",icon='PLUS').molding_type = 'Crown'
        row.operator(cabinet_properties.LIBRARY_NAME_SPACE + '.delete_molding',text="",icon='X').molding_type = 'Crown'
        if self.props.expand_crown_molding:
            row = molding_box.row()
            row.label(text="",icon='BLANK1')
            row.template_icon_view(self.props,"crown_molding",show_labels=True)
            
        row = molding_box.row(align=True)
        row.prop(self.props,'expand_base_molding',text="",icon='TRIA_DOWN' if self.props.expand_base_molding else 'TRIA_RIGHT',emboss=False)
        row.label(text="Base:")
        row.prop(self.props,'base_molding_category',text="",icon='FILE_FOLDER')
        row.prop(self.props,'base_molding',text="")
        row.operator(cabinet_properties.LIBRARY_NAME_SPACE + ".auto_add_molding",text="",icon='PLUS').molding_type = 'Base'
        row.operator(cabinet_properties.LIBRARY_NAME_SPACE + '.delete_molding',text="",icon='X').molding_type = 'Base'
        if self.props.expand_base_molding:
            row = molding_box.row()
            row.label(text="",icon='BLANK1')
            row.template_icon_view(self.props,"base_molding",show_labels=True)
            
        row = molding_box.row(align=True)
        row.prop(self.props,'expand_light_rail_molding',text="",icon='TRIA_DOWN' if self.props.expand_light_rail_molding else 'TRIA_RIGHT',emboss=False)
        row.label(text="Light Rail:")
        row.prop(self.props,'light_rail_molding_category',text="",icon='FILE_FOLDER')
        # row.prop(self.props,'light_rail_molding',text="")
        row.operator(cabinet_properties.LIBRARY_NAME_SPACE + ".auto_add_molding",text="",icon='PLUS').molding_type = 'Light'
        row.operator(cabinet_properties.LIBRARY_NAME_SPACE + '.delete_molding',text="",icon='X').molding_type = 'Light'
        if self.props.expand_light_rail_molding:
            row = molding_box.row()
            row.label(text="",icon='BLANK1')
            row.template_icon_view(self.props,"light_rail_molding",show_labels=True)            
            
    def draw_hardware_options(self,layout):
        #IMPLEMENT CHANGING HINGES GLOBALLY
        #IMPLEMENT CHANGING DRAWER SLIDES GLOBALLY
        hardware_box = layout.box()
        hardware_box.label(text="Hardware Options:")
        
        row = hardware_box.row(align=True)
        row.prop(self.props,'expand_pull',text="",icon='TRIA_DOWN' if self.props.expand_pull else 'TRIA_RIGHT',emboss=False)
        row.label(text='Pulls:')
        row.prop(self.props,'pull_category',text="",icon='FILE_FOLDER')
        row.prop(self.props,'pull_name',text="")
        row.operator(cabinet_properties.LIBRARY_NAME_SPACE + '.update_pull_selection',text="",icon='FILE_REFRESH').update_all = True
        row.operator(cabinet_properties.LIBRARY_NAME_SPACE + '.update_pull_selection',text="",icon='MAN_TRANS').update_all = False
        if self.props.expand_pull:
            row = hardware_box.row()
            row.label(text="",icon='BLANK1')
            row.template_icon_view(self.props,"pull_name",show_labels=True)

    def draw_door_style_options(self,layout):
        door_style_box = layout.box()
        door_style_box.label(text="Door Options:")
        row = door_style_box.row(align=True)
        row.prop(self.props,'expand_door',text="",icon='TRIA_DOWN' if self.props.expand_door else 'TRIA_RIGHT',emboss=False)
        row.label(text="Doors:")
        row.prop(self.props,'door_category',text="",icon='FILE_FOLDER')
        row.prop(self.props,'door_style',text="")
        row.operator(cabinet_properties.LIBRARY_NAME_SPACE + '.update_door_selection',text="",icon='MAN_TRANS')
        if self.props.expand_door:
            row = door_style_box.row()
            row.label(text="",icon='BLANK1')
            row.template_icon_view(self.props,"door_style",show_labels=True)
        row = door_style_box.row(align=True)
        row.label(text="Applied Panel:")
        row.operator(cabinet_properties.LIBRARY_NAME_SPACE + '.place_applied_panel',text="Add Applied Panel",icon='MAN_TRANS')
            
    def draw_interior_defaults(self,layout):
        col = layout.column(align=True)
        
        box = col.box()
        
        box.label(text="Default Shelf Quantity:")
        row = box.row()
        row.label(text="Base Cabinets:")
        row.prop(self.props.interior_defaults,"base_adj_shelf_qty",text="Quantity")
        row = box.row()
        row.label(text="Tall Cabinets:")
        row.prop(self.props.interior_defaults,"tall_adj_shelf_qty",text="Quantity")
        row = box.row()
        row.label(text="Upper Cabinets:")
        row.prop(self.props.interior_defaults,"upper_adj_shelf_qty",text="Quantity")
        
        box = col.box()
        
        box.label(text="Default Shelf Setback:")
        row = box.row()
        row.label(text="Adjustable:")
        row.prop(self.props.interior_defaults,"adj_shelf_setback",text="Setback")
        row = box.row()
        row.label(text="Fixed:")
        row.prop(self.props.interior_defaults,"fixed_shelf_setback",text="Setback")
        
    def draw_exterior_defaults(self,layout):
        col = layout.column(align=True)
        
        box = col.box()
        box.label(text="Door & Drawer Defaults:")
        
        row = box.row(align=True)
        row.prop(self.props.exterior_defaults,"inset_door")
        row.prop(self.props.exterior_defaults,"no_pulls")
        
        row = box.row(align=True)
        row.prop(self.props.exterior_defaults,"use_buyout_drawer_boxes")
        row.prop(self.props.exterior_defaults,"horizontal_grain_on_drawer_fronts")        
        
        if not self.props.exterior_defaults.no_pulls:
            box = col.box()
            box.label(text="Pull Placement:")
            
            row = box.row(align=True)
            row.label(text="Base Doors:")
            row.prop(self.props.exterior_defaults,"base_pull_location",text="From Top of Door")
            
            row = box.row(align=True)
            row.label(text="Tall Doors:")
            row.prop(self.props.exterior_defaults,"tall_pull_location",text="From Bottom of Door")
            
            row = box.row(align=True)
            row.label(text="Upper Doors:")
            row.prop(self.props.exterior_defaults,"upper_pull_location",text="From Bottom of Door")
            
            row = box.row(align=True)
            row.label(text="Distance From Edge:")
            row.prop(self.props.exterior_defaults,"pull_from_edge",text="")
            
            row = box.row(align=True)
            row.prop(self.props.exterior_defaults,"center_pulls_on_drawers")
    
            if not self.props.exterior_defaults.center_pulls_on_drawers:
                row.prop(self.props.exterior_defaults,"drawer_pull_from_top",text="Distance From Top")
        
        box = col.box()
        box.label(text="Door & Drawer Reveals:")
        
        if self.props.exterior_defaults.inset_door:
            row = box.row(align=True)
            row.label(text="Inset Reveals:")
            row.prop(self.props.exterior_defaults,"inset_reveal",text="")
        else:
            row = box.row(align=True)
            row.label(text="Standard Reveals:")
            row.prop(self.props.exterior_defaults,"left_reveal",text="Left")
            row.prop(self.props.exterior_defaults,"right_reveal",text="Right")
            
            row = box.row(align=True)
            row.label(text="Base Door Reveals:")
            row.prop(self.props.exterior_defaults,"base_top_reveal",text="Top")
            row.prop(self.props.exterior_defaults,"base_bottom_reveal",text="Bottom")
            
            row = box.row(align=True)
            row.label(text="Tall Door Reveals:")
            row.prop(self.props.exterior_defaults,"tall_top_reveal",text="Top")
            row.prop(self.props.exterior_defaults,"tall_bottom_reveal",text="Bottom")
            
            row = box.row(align=True)
            row.label(text="Upper Door Reveals:")
            row.prop(self.props.exterior_defaults,"upper_top_reveal",text="Top")
            row.prop(self.props.exterior_defaults,"upper_bottom_reveal",text="Bottom")
            
        row = box.row(align=True)
        row.label(text="Vertical Gap:")
        row.prop(self.props.exterior_defaults,"vertical_gap",text="")
    
        row = box.row(align=True)
        row.label(text="Door To Cabinet Gap:")
        row.prop(self.props.exterior_defaults,"door_to_cabinet_gap",text="")
        
    def draw_carcass_defaults(self,layout):
        col = layout.column(align=True)

        box = col.box()
        row = box.row(align=True)
        row.label(text="Cabinet Back Options:")
        row = box.row(align=True)
        row.prop(self.props.carcass_defaults,"remove_back")
        row.prop(self.props.carcass_defaults,"use_nailers")
        row.prop(self.props.carcass_defaults,"use_thick_back")
        row = box.row(align=True)
        row.label(text="Nailer Width:")
        row.prop(self.props.carcass_defaults,"nailer_width",text="")
        row = box.row(align=True)
        row.label(text="Center Nailer Switch:")
        row.prop(self.props.carcass_defaults,"center_nailer_switch",text="")

        box = col.box()
        row = box.row(align=True)
        row.label(text="Cabinet Top Options:")
        row = box.row(align=True)
        row.prop(self.props.carcass_defaults,"use_full_tops")
        if not self.props.carcass_defaults.use_full_tops:
            row = box.row(align=True)
            row.label(text="Stretcher Width:")
            row.prop(self.props.carcass_defaults,"stretcher_width",text="")
        row = box.row(align=True)
        row.label(text="Sub Front Height:")
        row.prop(self.props.carcass_defaults,"sub_front_height",text="")
        
        box = col.box()
        row = box.row(align=True)
        row.label(text="Cabinet Side Options:")
        row = box.row(align=True)
        row.prop(self.props.carcass_defaults,"use_notched_sides")
        row.prop(self.props.carcass_defaults,"extend_sides_to_floor")
        
        box = col.box()
        row = box.row(align=True)
        row.label(text="Cabinet Valance Options:")
        row = box.row(align=True)
        row.label(text="Valance Height Top:")
        row.prop(self.props.carcass_defaults,"valance_height_top")
        row = box.row(align=True)
        row.label(text="Valance Height Bottom:")
        row.prop(self.props.carcass_defaults,"valance_height_bottom")
        row = box.row(align=True)
        row.prop(self.props.carcass_defaults,"door_valance_top")
        row.prop(self.props.carcass_defaults,"door_valance_bottom")
        row = box.row(align=True)
        row.prop(self.props.carcass_defaults,"valance_each_unit")
        
        box = col.box()
        row = box.row(align=True)
        row.label(text="Cabinet Base Assembly:")
        row = box.row(align=True)
        row.label(text="Toe Kick Height:")
        row.prop(self.props.carcass_defaults,"toe_kick_height")
        row = box.row(align=True)
        row.label(text="Toe Kick Setback:")
        row.prop(self.props.carcass_defaults,"toe_kick_setback")
        row = box.row(align=True)
        row.prop(self.props.carcass_defaults,"use_leg_levelers")
    
    def draw_cabinet_sizes(self,layout):

        col = layout.column(align=True)

        box = col.box()
        box.label(text="Standard Frameless Cabinet Sizes:")
        
        row = box.row(align=True)
        row.label(text="Base:")
        row.prop(self.props.size_defaults,"base_cabinet_height",text="")
        row.prop(self.props.size_defaults,"base_cabinet_depth",text="Depth")
        
        row = box.row(align=True)
        row.label(text="Tall:")
        row.prop(self.props.size_defaults,"tall_cabinet_height",text="")
        row.prop(self.props.size_defaults,"tall_cabinet_depth",text="Depth")
        
        row = box.row(align=True)
        row.label(text="Upper:")
        row.prop(self.props.size_defaults,"upper_cabinet_height",text="")
        row.prop(self.props.size_defaults,"upper_cabinet_depth",text="Depth")

        row = box.row(align=True)
        row.label(text="Sink:")
        row.prop(self.props.size_defaults,"sink_cabinet_height",text="")
        row.prop(self.props.size_defaults,"sink_cabinet_depth",text="Depth")
        
        row = box.row(align=True)
        row.label(text="Suspended:")
        row.prop(self.props.size_defaults,"suspended_cabinet_height",text="")
        row.prop(self.props.size_defaults,"suspended_cabinet_depth",text="Depth")
        
        row = box.row(align=True)
        row.label(text="1 Door Wide:")
        row.prop(self.props.size_defaults,"width_1_door",text="Width")
        
        row = box.row(align=True)
        row.label(text="2 Door Wide:")
        row.prop(self.props.size_defaults,"width_2_door",text="Width")
        
        row = box.row(align=True)
        row.label(text="Drawer Stack Width:")
        row.prop(self.props.size_defaults,"width_drawer",text="Width")
        
        box = col.box()
        box.label(text="Blind Cabinet Widths:")
        
        row = box.row(align=True)
        row.label(text='Base:')
        row.prop(self.props.size_defaults,"base_width_blind",text="Width")
        
        row = box.row(align=True)
        row.label(text='Tall:')
        row.prop(self.props.size_defaults,"tall_width_blind",text="Width")
        
        row = box.row(align=True)
        row.label(text='Upper:')
        row.prop(self.props.size_defaults,"upper_width_blind",text="Width")
        
        box = col.box()
        box.label(text="Inside Corner Cabinet Sizes:")
        row = box.row(align=True)
        row.label(text="Base:")
        row.prop(self.props.size_defaults,"base_inside_corner_size",text="")
        
        row = box.row(align=True)
        row.label(text="Upper:")
        row.prop(self.props.size_defaults,"upper_inside_corner_size",text="")
        
        box = col.box()
        box.label(text="Placement:")
        row = box.row(align=True)
        row.label(text="Height Above Floor:")
        row.prop(self.props.size_defaults,"height_above_floor",text="")
        
        box = col.box()
        box.label(text="Drawer Heights:")
        row = box.row(align=True)
        row.prop(self.props.size_defaults,"equal_drawer_stack_heights")
        if not self.props.size_defaults.equal_drawer_stack_heights:
            row = box.row(align=True)
            row.label(text="Top Drawer Front Height")
            row = box.row(align=True)
            row.prop(self.props.size_defaults,"top_drawer_front_height", text="")
    
    def draw(self, context):
        self.props = cabinet_properties.get_scene_props()
        layout = self.layout

        box = layout.box()
        row = box.row()
        row.prop(self.props,'main_tabs',expand=True)
        
        if self.props.main_tabs == 'DEFAULTS':
            col = box.column(align=True)
            box = col.box()
            row = box.row()
            row.prop(self.props,'defaults_tabs',expand=True)
            
            if self.props.defaults_tabs == 'SIZES':
                self.draw_cabinet_sizes(box)
            
            if self.props.defaults_tabs == 'CARCASS':
                self.draw_carcass_defaults(box)
            
            if self.props.defaults_tabs == 'EXTERIOR':
                self.draw_exterior_defaults(box)
                
            if self.props.defaults_tabs == 'INTERIOR':
                self.draw_interior_defaults(box)
            
        if self.props.main_tabs == 'OPTIONS':
            col = box.column(align=True)
            self.draw_molding_options(col)
            # self.draw_hardware_options(col)
            # self.draw_door_style_options(col)

#---------PRODUCT: EXTERIOR PROMPTS

class PROMPTS_Door_Prompts(bpy.types.Operator):
    bl_idname = cabinet_properties.LIBRARY_NAME_SPACE + ".door_prompts"
    bl_label = "Door Prompts" 
    bl_description = "This shows all of the available door options"
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")
    
    assembly = None
    
    @classmethod
    def poll(cls, context):
        return True
        
    def check(self, context):
        self.assembly.obj_bp.location = self.assembly.obj_bp.location # Redraw Viewport
        return True
        
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self,context,event):
        obj = bpy.data.objects[self.object_name]
        obj_insert_bp = sn_utils.get_bp(obj,'INSERT')
        self.assembly = sn_types.Assembly(obj_insert_bp)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(500))
        
    def draw(self, context):
        layout = self.layout
        if self.assembly.obj_bp:
            if self.assembly.obj_bp.name in context.scene.objects:
                draw_door_options(self.assembly,layout)

class PROMPTS_Frameless_Cabinet_Prompts(sn_types.Prompts_Interface):
    bl_idname = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    bl_label = "Frameless Cabinet Prompts" 
    bl_options = {'UNDO'}
    
    object_name: StringProperty(name="Object Name")
    
    width: FloatProperty(name="Width",unit='LENGTH',precision=4)
    height: EnumProperty(name="Default Hanging Panel Height", items=get_panel_heights)
    depth: FloatProperty(name="Depth",unit='LENGTH',precision=4)

    product_tabs: EnumProperty(name="Door Swing",items=[('CARCASS',"Carcass","Carcass Options"),
                                                                   ('EXTERIOR',"Exterior","Exterior Options"),
                                                                   ('INTERIOR',"Interior","Interior Options"),
                                                                   ('SPLITTER',"Openings","Openings Options")])

    door_rotation: FloatProperty(name="Door Rotation",subtype='ANGLE',min=0,max=math.radians(120))
    
    door_swing: EnumProperty(name="Door Swing",items=[('Left Swing',"Left Swing","Left Swing"),
                                                                 ('Right Swing',"Right Swing","Right Swing")])

    placement_on_wall: EnumProperty(
        name="Placement on Wall",items=[('SELECTED_POINT', "Selected Point", ""),
                                        ('FILL', "Fill", ""),
                                        ('LEFT', "Left", ""),
                                        ('CENTER', "Center", ""),
                                        ('RIGHT', "Right", "")],
                                        default='SELECTED_POINT')
    
    left_offset: FloatProperty(name="Left Offset", default=0, subtype='DISTANCE', precision=4)
    right_offset: FloatProperty(name="Right Offset", default=0, subtype='DISTANCE', precision=4)
    selected_location = 0
    last_placement = 'SELECTED_POINT'
    default_width = 0
    
    product = None
    
    open_door_prompts = []
    
    show_exterior_options = False
    show_interior_options = False
    show_splitter_options = False

    carcass = None
    exterior = None
    interior = None
    counter_top = None
    
    doors = []
    drawers = []
    splitters = []
    interiors = []
    inserts = []
    calculators = []

    def reset_variables(self):
        self.product_tabs = 'CARCASS'
        self.width = 0
        self.doors = []
        self.drawers = []
        self.splitters = []
        self.interiors = []
        self.calculators = []

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

    def update_door_dimensions(self):
        for door_insert_bp in self.doors:
            doors = Doors(door_insert_bp)
            doors.update_dimensions()

    def update_drawer_dimensions(self):
        for drawer_insert in self.drawers:
            if "VERTICAL_DRAWERS" in drawer_insert.obj_bp:
                drawer = Vertical_Drawers(drawer_insert.obj_bp)
            else:
                drawer = Horizontal_Drawers(drawer_insert.obj_bp)
            drawer.update_dimensions()

    def update_carcass_dimensions(self):
        if self.carcass:
            if "STANDARD_CARCASS" in self.carcass.obj_bp:
                carcass = Standard_Carcass(self.carcass.obj_bp)
            else:
                carcass = Inside_Corner_Carcass(self.carcass.obj_bp)
            carcass.update_dimensions()
                    
    def update_placement(self, context):
        product = self.get_product(context)
        left_x = product.get_collision_location('LEFT')
        right_x = product.get_collision_location('RIGHT')
        offsets = self.left_offset + self.right_offset
        
        if self.placement_on_wall == 'FILL':
            product.obj_bp.location.x = left_x + self.left_offset
            product.obj_x.location.x = right_x - left_x - offsets
        if self.placement_on_wall == 'LEFT':
            product.obj_bp.location.x = left_x + self.left_offset
        if self.placement_on_wall == 'CENTER':
            x_loc = left_x + (right_x - left_x) / 2 - (self.product.calc_width() / 2) 
            product.obj_bp.location.x = x_loc
        if self.placement_on_wall == 'RIGHT':
            if product.obj_bp.snap.placement_type == 'CORNER':
                product.obj_bp.rotation_euler.z = math.radians(-90)
            product.obj_bp.location.x = (right_x - product.calc_width()) - self.right_offset
        if self.placement_on_wall == 'SELECTED_POINT' and self.last_placement != 'SELECTED_POINT':
                product.obj_bp.location.x = self.selected_location
        elif self.placement_on_wall == 'SELECTED_POINT' and self.last_placement == 'SELECTED_POINT':
            self.selected_location = product.obj_bp.location.x

        self.last_placement = self.placement_on_wall


    def check(self, context):
        self.update_overall_width()
        self.update_product_size()
        self.update_placement(context)
        self.run_calculators(self.product.obj_bp)
        context.view_layer.update()
        self.update_door_dimensions()
        self.update_drawer_dimensions()
        self.update_carcass_dimensions()
        
        return True

    def execute(self, context):
        sn_utils.run_calculators(self.product.obj_bp)
        return {'FINISHED'}

    def get_product(self, context):
        obj = bpy.data.objects[bpy.context.object.name]
        obj_product_bp = sn_utils.get_bp(obj, 'PRODUCT')
        product = sn_types.Assembly(obj_product_bp)
        self.depth = math.fabs(product.obj_y.location.y)
        self.width = math.fabs(product.obj_x.location.x)
        return product

    def check_insert_tags(self, insert, tag_list):
        for tag in tag_list:
            if tag in insert and insert[tag]:
                return True
        return False

    def invoke(self,context,event):
        self.reset_variables()
        
        self.product = self.get_product(context)
        self.inserts = sn_utils.get_assembly_bp_list(self.product.obj_bp,[])

        self.selected_location = self.product.obj_bp.location.x
        self.default_width = math.fabs(self.product.obj_x.location.x)
        self.placement_on_wall = 'SELECTED_POINT'
        self.last_placement = 'SELECTED_POINT'
        self.left_offset = 0
        self.right_offset = 0

        for insert in self.inserts:
            if "IS_BP_CARCASS" in insert:
                self.carcass = sn_types.Assembly(insert)

                toe_kick_ppt = self.carcass.get_prompt("Toe Kick Height")
                if toe_kick_ppt:
                    self.height = str(round(math.fabs(sn_unit.meter_to_millimeter(self.product.obj_z.location.z-toe_kick_ppt.get_value()))))
                else:
                    self.height = str(round(math.fabs(sn_unit.meter_to_millimeter(self.product.obj_z.location.z))))

            if "IS_BP_CABINET_COUNTERTOP" in insert:
                self.counter_top = sn_types.Assembly(insert)

            if "IS_BP_DOOR_INSERT" in insert:
                self.show_exterior_options = True
                if insert not in self.doors:
                    self.doors.append(insert)

            if "IS_DRAWERS_BP" in insert:                
                self.show_exterior_options = True
                assy = sn_types.Assembly(insert)
                calculator = assy.get_calculator("Vertical Drawers Calculator")
                if assy:
                    self.drawers.append(assy)
                if calculator:
                    self.calculators.append(calculator)

            # if "IS_BP_SPLITTER" in insert and insert["IS_BP_SPLITTER"]:
            if self.check_insert_tags(insert, ["IS_BP_SPLITTER"]):
                self.show_splitter_options = True

                if insert not in self.splitters:
                    self.splitters.append(insert)                

                assy = sn_types.Assembly(insert)
                calculator = assy.get_calculator('Opening Heights Calculator')
                if assy and insert not in self.splitters:
                    self.splitters.append(assy)
                if calculator:
                    self.calculators.append(calculator)

            if self.check_insert_tags(insert, ["IS_BP_SHELVES","IS_BP_DIVIDER","IS_BP_DIVISION"]) :
                self.show_interior_options = True
                if insert not in self.interiors:
                    self.interiors.append(insert)

        self.run_calculators(self.product.obj_bp)
                
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=550)

    def draw_product_placment(self,layout):
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
                
    def draw_carcass_prompts(self,layout):
        if self.carcass:
            draw_carcass_options(self.carcass, layout)
            
        if self.counter_top:
            draw_countertop_options(self.counter_top, self.product, layout)
        
    def draw_door_prompts(self,layout):
        for door_bp in self.doors:
            door = sn_types.Assembly(door_bp)

            for child in door.obj_bp.children:
                if "DOOR_HOLE_LABEL" in child:
                    print("Update Door Height Label...")
                    # height_hole_count_dim = sn_types.Dimension(child)
                    # height_hole_count_dim.set_label()

            draw_door_options(door, layout)
        
    def draw_drawer_prompts(self,layout):
        for drawer in self.drawers:
            draw_drawer_options(drawer, layout)

    def draw_interior_prompts(self,layout):
        for interior_bp in self.interiors:
            interior = sn_types.Assembly(interior_bp)
            draw_interior_options(interior, layout)

    def draw_splitter_prompts(self,layout):
        for splitter_bp in self.splitters:
            splitter = sn_types.Assembly(splitter_bp)
            draw_splitter_options(splitter, layout)

    def draw(self, context):
        layout = self.layout

        if self.product.obj_bp:
            if self.product.obj_bp.name in context.scene.objects:
                box = layout.box()
                
                split = box.split(factor=.8)
                split.label(text=self.product.obj_bp.snap.name_object, icon='LATTICE_DATA')
                # split.menu('MENU_Current_Cabinet_Menu',text="Menu",icon='DOWNARROW_HLT')
                self.draw_product_size(box)
                
                prompt_box = box.box()
                row = prompt_box.row(align=True)
                row.prop_enum(self, "product_tabs", 'CARCASS') 
                if self.show_exterior_options:
                    row.prop_enum(self, "product_tabs", 'EXTERIOR') 
                if self.show_interior_options:
                    row.prop_enum(self, "product_tabs", 'INTERIOR') 
                if self.show_splitter_options:
                    row.prop_enum(self, "product_tabs", 'SPLITTER') 

                if self.product_tabs == 'CARCASS':
                    self.draw_carcass_prompts(prompt_box)
                    self.draw_product_placment(prompt_box)
                if self.product_tabs == 'EXTERIOR':
                    self.draw_door_prompts(prompt_box)
                    self.draw_drawer_prompts(prompt_box)
                if self.product_tabs == 'INTERIOR':
                    self.draw_interior_prompts(prompt_box)
                if self.product_tabs == 'SPLITTER':
                    self.draw_splitter_prompts(prompt_box)
      

bpy.utils.register_class(SNAP_PT_Cabinet_Options)
bpy.utils.register_class(PROMPTS_Door_Prompts)
bpy.utils.register_class(PROMPTS_Frameless_Cabinet_Prompts)
    