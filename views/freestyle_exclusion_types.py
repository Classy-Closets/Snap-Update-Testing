"""
Contains lists of closet properties to check whether to exclude certain
assemblies from Freestyle linesets

HIDE_TYPES are objects that need to be excluded from the Hidden Line lineset
VIS_TYPES are objects that need to be excluded from the Visible Line lineset
HIDE_INCLUDE_OVERRIDE prevents HIDE from affecting an object that conforms to it
VIS_INCLUDE_OVERRIDE prevents VIS from affecting an object that conforms to it


Currently only Cleats are required to be excluded from visible rendering, but
a list was created in case more assemblies are required to be excluded from
visible rendering in the future.
"""

HIDE_TYPES = ['.sn_closets.is_panel_bp',
              '.sn_closets.is_blind_corner_panel_bp',
              '.sn_closets.is_drawer_box_bp',
              '.sn_closets.is_drawer_side_bp',
              '.sn_closets.is_drawer_back_bp',
              '.sn_closets.is_drawer_sub_front_bp',
              '.sn_closets.is_drawer_bottom_bp',
              '.sn_closets.is_file_rail_bp',
              '.sn_closets.is_toe_kick_bp',
              '.sn_closets.is_toe_kick_end_cap_bp',
              '.sn_closets.is_toe_kick_stringer_bp',
              '.sn_closets.is_toe_kick_skin_bp',
              '.sn_closets.is_back_bp',
              '.sn_closets.is_top_back_bp',
              '.sn_closets.is_bottom_back_bp',
              '.sn_closets.is_hutch_back_bp',
              '.sn_closets.is_drawer_back_bp',
              '.sn_closets.is_door_bp',
              '.sn_closets.is_slanted_shelf_bp',
              '.sn_closets.is_cleat_bp',
              '.sn_closets.is_hamper_bp',
              '.snap.is_wall_mesh',
              '.get("IS_BP_WALL_BED_VALANCE")',
              '.snap.type_mesh == "MACHINING"']

VIS_TYPES = ['.sn_closets.is_cleat_bp',
             '.sn_closets.is_toe_kick_stringer_bp']

FS_SKIPS = ['Anchor', 
            'End Point', 
            'CAGE', 
            'Dog Ear Height', 
            'OBJ_PROMPTS', 
            'OBJ_X', 
            'OBJ_Y', 
            'OBJ_Z', 
            'PARTHGT', 
            'Y1', 
            'Y2']

HIDE_INCLUDE_OVERRIDE = [
    '.get("IS_WALL_CLEAT")',
    '.get("IS_CABINET_SHELF")'
]

VIS_INCLUDE_OVERRIDE = [
    '.get("IS_WALL_CLEAT")'
]




