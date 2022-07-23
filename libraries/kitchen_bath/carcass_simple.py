from os import path
import math

from snap import sn_props, sn_types, sn_unit
from . import cabinet_properties
from snap.libraries.closets import closet_paths
from snap import sn_paths


PART_WITH_FRONT_EDGEBANDING = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")
PART_WITH_FRONT_AND_BOTTOM_EDGEBANDING = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")
PART_WITH_NO_EDGEBANDING = path.join(closet_paths.get_closet_assemblies_path(), "Part with Edgebanding.blend")
NOTCHED_SIDE = path.join(sn_paths.KITCHEN_BATH_ASSEMBLIES, "Notched Side.blend")
LEG_LEVELERS = path.join(sn_paths.KITCHEN_BATH_ASSEMBLIES, "Leg Levelers.blend")
CHAMFERED_PART = path.join(sn_paths.KITCHEN_BATH_ASSEMBLIES,"Chamfered Part.blend")
CORNER_NOTCH_PART = path.join(sn_paths.KITCHEN_BATH_ASSEMBLIES,"Corner Notch Part.blend")
USE_DADO_BOTTOM = True


# def add_toe_kick_notch(assembly):
#     Notch_X_Dimension = assembly.get_prompt("Notch X Dimension").get_var()
#     Notch_Y_Dimension = assembly.get_prompt("Notch Y Dimension").get_var()
#     dim_z = assembly.obj_z.snap.get_var("location.z")

#     obj, token = assembly.add_machine_token('Toe Kick Notch' ,'CORNERNOTCH','5','1')
#     token.add_driver(obj,'dim_in_x','Notch_X_Dimension',[Notch_X_Dimension])
#     token.add_driver(obj,'dim_in_y','Notch_Y_Dimension',[Notch_Y_Dimension])
#     token.add_driver(obj,'dim_in_z','fabs(dim_z)+INCH(.01)',[dim_z])
#     token.lead_in = sn_unit.inch(.25)
#     token.tool_number = DEFAULT_ROUTING_TOOL_CW

def add_side_height_dimension(part):
    Part_Height = part.obj_x.snap.get_var('location.x','Part_Height')
         
    dim = sn_types.Dimension()
    dim.anchor["SIDE_HEIGHT_LABEL"] = True
    dim.parent(part.obj_bp)
    
    dim.anchor.rotation_euler.y = math.radians(-90)
    if hasattr(part, "mirror_z") and part.mirror_z:
        dim.start_x('Part_Height/2',[part])
    else:
        dim.start_x('Part_Height/2',[Part_Height])
    dim.start_y(value=sn_unit.inch(-1.5))
    dim.start_z(value=sn_unit.inch(-1.5))
    dim.set_label("")

def update_dimensions(part):
    dimensions = []
    
    toe_kick_ppt = part.get_prompt('Toe Kick Height')
    toe_kick_height = 0
    if toe_kick_ppt:
        toe_kick_height = toe_kick_ppt.get_value()

    for child in part.obj_bp.children:
        for nchild in child.children:
            if 'SIDE_HEIGHT_LABEL' in nchild:
                dimensions.append(nchild)

    for anchor in dimensions:
        assembly = sn_types.Assembly(anchor.parent)
        abs_x_loc = math.fabs(sn_unit.meter_to_inch(assembly.obj_x.location.x - toe_kick_height))
        dim_x_label = str(round(abs_x_loc, 2)) + '\"'
        anchor.snap.opengl_dim.gl_label = dim_x_label

# ---------ASSEMBLY INSTRUCTIONS
def add_part(assembly, path):
    part_bp = assembly.add_assembly_from_file(path)
    part = sn_types.Assembly(part_bp)
    part.obj_bp.sn_closets.is_panel_bp = True
    return part  
    
class Standard_Carcass(sn_types.Assembly):

    type_assembly = "INSERT"
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    library_name = "Carcasses"
    placement_type = ""

    carcass_type = ""  # {Base, Tall, Upper, Sink, Suspended}
    open_name = ""

    remove_top = False  # Used to remove top for face frame sink cabinets

    def update_dimensions(self):
        update_dimensions(self)  # Call module level function to find and update door dim labels

    def update(self):
        super().update()
        self.obj_bp["IS_BP_CARCASS"] = True
        self.obj_bp["STANDARD_CARCASS"] = True

    def add_common_carcass_prompts(self):
        props = cabinet_properties.get_scene_props().carcass_defaults

        self.add_prompt("Left Fin End", 'CHECKBOX', False)
        self.add_prompt("Right Fin End", 'CHECKBOX', False)
        self.add_prompt("Left Side Wall Filler", 'DISTANCE', 0.0)
        self.add_prompt("Right Side Wall Filler", 'DISTANCE', 0.0)
        self.add_prompt("Use Nailers", 'CHECKBOX', props.use_nailers)
        self.add_prompt("Nailer Width", 'DISTANCE', props.nailer_width)
        self.add_prompt("Center Nailer Switch", 'DISTANCE', props.center_nailer_switch)
        self.add_prompt("Use Thick Back", 'CHECKBOX', props.use_thick_back)
        self.add_prompt("Remove Back", 'CHECKBOX', props.remove_back)
        self.add_prompt("Remove Bottom", 'CHECKBOX', False)

        if self.carcass_type in {'Base', 'Suspended'} and not props.use_full_tops:
            self.add_prompt("Stretcher Width", 'DISTANCE', props.stretcher_width)

        self.add_prompt("Left Side Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Right Side Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Top Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Bottom Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Back Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Thick Back Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Filler Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Nailer Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Edgebanding Thickness", 'DISTANCE', sn_unit.inch(.02))

        # Create separate prompts obj for insets
        ppt_obj_insets = self.add_prompt_obj("Backing_Config")
        self.add_prompt("Back Inset", 'DISTANCE', sn_unit.inch(0), prompt_obj=ppt_obj_insets)
        self.add_prompt("Top Inset", 'DISTANCE', sn_unit.inch(0), prompt_obj=ppt_obj_insets)
        self.add_prompt("Bottom Inset", 'DISTANCE', sn_unit.inch(0), prompt_obj=ppt_obj_insets)

    # Updated
    def add_base_assembly_prompts(self):
        props = cabinet_properties.get_scene_props().carcass_defaults
        self.add_prompt("Toe Kick Height",'DISTANCE', props.toe_kick_height)
        self.add_prompt("Toe Kick Setback",'DISTANCE', props.toe_kick_setback)
        self.add_prompt("Toe Kick Thickness", 'DISTANCE', sn_unit.inch(.75))

    def add_valance_prompts(self,add_bottom_valance):
        props = cabinet_properties.get_scene_props().carcass_defaults
        self.add_prompt("Valance Height Top",'DISTANCE',props.valance_height_top)
        self.add_prompt("Door Valance Top",'CHECKBOX',props.door_valance_top)
        if add_bottom_valance:
            self.add_prompt("Valance Height Bottom",'DISTANCE',props.valance_height_bottom)
            self.add_prompt("Door Valance Bottom",'CHECKBOX',props.door_valance_bottom)
        self.add_prompt("Left Side Full Height",'CHECKBOX',False)
        self.add_prompt("Right Side Full Height",'CHECKBOX',False)
        self.add_prompt("Valance Each Unit",'CHECKBOX',props.valance_each_unit)
        self.add_prompt("Valance Thickness",'DISTANCE',sn_unit.inch(.75))
    
    def add_sink_prompts(self):
        props = cabinet_properties.get_scene_props().carcass_defaults
        self.add_prompt("Sub Front Height",'DISTANCE', props.sub_front_height)
        self.add_prompt("Sub Front Thickness",'DISTANCE',sn_unit.inch(.75))
    
    def add_prompt_formulas(self):
        tt = self.get_prompt("Top Thickness").get_var('tt')
        bt = self.get_prompt("Bottom Thickness").get_var('bt')
        use_nailers = self.get_prompt("Use Nailers").get_var('use_nailers')
        nt = self.get_prompt("Nailer Thickness").get_var('nt')
        bkt = self.get_prompt("Back Thickness").get_var('bkt')
        tbkt = self.get_prompt("Thick Back Thickness").get_var('tbkt')
        use_thick_back = self.get_prompt("Use Thick Back").get_var('use_thick_back')
        remove_back = self.get_prompt("Remove Back").get_var('remove_back')
        Remove_Bottom = self.get_prompt('Remove Bottom').get_var('Remove_Bottom')
        if self.carcass_type in {'Base','Sink','Tall'}:
            kick_height = self.get_prompt("Toe Kick Height").get_var('kick_height')
        if self.carcass_type in {'Upper','Tall'}:
            vht = self.get_prompt("Valance Height Top").get_var('vht')
        if self.carcass_type == 'Upper':
            vhb = self.get_prompt("Valance Height Bottom").get_var('vhb')

        # Used to calculate the exterior opening for doors
        if self.carcass_type == 'Base':
            self.get_prompt('Top Inset').set_formula('tt',[tt])
            self.get_prompt('Bottom Inset').set_formula('kick_height+bt',[kick_height,bt])

        if self.carcass_type == 'Sink':
            Sub_Front_Height = self.get_prompt("Sub Front Height").get_var()
            self.get_prompt('Top Inset').set_formula('Sub_Front_Height',[Sub_Front_Height])
            self.get_prompt('Bottom Inset').set_formula('kick_height+bt',[kick_height,bt])

        if self.carcass_type == 'Tall':
            self.get_prompt('Top Inset').set_formula('vht+tt',[vht,tt])
            self.get_prompt('Bottom Inset').set_formula('kick_height+bt',[kick_height,bt])

        if self.carcass_type == 'Upper':
            self.get_prompt('Top Inset').set_formula('vht+tt',[vht,tt])
            self.get_prompt('Bottom Inset').set_formula('IF(Remove_Bottom,0,vhb+bt)',[vhb,bt,Remove_Bottom])

        if self.carcass_type == 'Suspended':
            self.get_prompt('Top Inset').set_formula('tt',[tt])
            self.get_prompt('Bottom Inset').set_formula('IF(Remove_Bottom,0,bt)',[bt,Remove_Bottom])

        self.get_prompt('Back Inset').set_formula('IF(use_nailers,nt,0)+IF(remove_back,0,IF(use_thick_back,tbkt,bkt))',[use_nailers,nt,bkt,tbkt,use_thick_back,remove_back])

        # region TODO XML Export

        # sgi = self.get_var('cabinetlib.spec_group_index','sgi')
        # lfe = self.get_var("Left Fin End",'lfe')
        # rfe = self.get_var("Right Fin End",'rfe')
        # Side_Pointer_Name = 'Cabinet_Unfinished_Side' + self.open_name
        # FE_Pointer_Name = 'Cabinet_Finished_Side' + self.open_name
        # Top_Pointer_Name = 'Cabinet_Top' + self.open_name
        # Bottom_Pointer_Name = 'Cabinet_Bottom' + self.open_name
        # Back_Pointer_Name = 'Cabinet_Back' + self.open_name
        # Thick_Back_Pointer_Name = 'Cabinet_Thick_Back' + self.open_name
        # Edgebanding_Pointer_Name = 'Cabinet_Body_Edges' + self.open_name

        # self.prompt('Left Side Thickness','IF(lfe,THICKNESS(sgi,"' + FE_Pointer_Name +'"),THICKNESS(sgi,"' + Side_Pointer_Name +'"))',[lfe,sgi])
        # self.prompt('Right Side Thickness','IF(rfe,THICKNESS(sgi,"' + FE_Pointer_Name +'"),THICKNESS(sgi,"' + Side_Pointer_Name +'"))',[rfe,sgi])
        # if self.carcass_type == "Sink" or self.remove_top:
        #     self.prompt('Top Thickness',value = 0)
        # else:
        #     self.prompt('Top Thickness','THICKNESS(sgi,"' + Top_Pointer_Name +'")',[sgi])
        # self.prompt('Bottom Thickness','THICKNESS(sgi,"' + Bottom_Pointer_Name +'")',[sgi])
        # if self.carcass_type in {'Base','Sink','Tall'}:
        #     self.prompt('Toe Kick Thickness','THICKNESS(sgi,"Cabinet_Toe_Kick")',[sgi])
        # if self.carcass_type == 'Sink':
        #     self.prompt('Sub Front Thickness','THICKNESS(sgi,"Cabinet_Sink_Sub_Front")',[sgi])
        # self.prompt('Back Thickness','IF(remove_back,0,IF(use_thick_back,THICKNESS(sgi,"' + Thick_Back_Pointer_Name +'"),THICKNESS(sgi,"' + Back_Pointer_Name +'")))',[sgi,use_thick_back,remove_back])
        # self.prompt('Thick Back Thickness','THICKNESS(sgi,"Cabinet_Thick_Back' + self.open_name +'")',[sgi])
        # self.prompt('Filler Thickness','THICKNESS(sgi,"Cabinet_Filler")',[sgi])
        # self.prompt('Nailer Thickness','THICKNESS(sgi,"Cabinet_Nailer")',[sgi])
        # if self.carcass_type in {'Tall','Upper'}:
        #     self.prompt('Valance Thickness','THICKNESS(sgi,"Cabinet_Valance")',[sgi])
        # self.prompt('Edgebanding Thickness','EDGE_THICKNESS(sgi,"' + Edgebanding_Pointer_Name + '")',[sgi])
        # endregion


    def add_base_sides(self):
        props = cabinet_properties.get_scene_props().carcass_defaults
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')

        Toe_Kick_Height = self.get_prompt('Toe Kick Height').get_var()
        Toe_Kick_Setback = self.get_prompt('Toe Kick Setback').get_var()
        Left_Fin_End = self.get_prompt('Left Fin End').get_var()
        Right_Fin_End = self.get_prompt('Right Fin End').get_var()
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()

        part_path = NOTCHED_SIDE if props.use_notched_sides else PART_WITH_FRONT_EDGEBANDING

        left_side = add_part(self, part_path)
        left_side.set_name(self.carcass_type + " Left Side")
        left_side.add_prompt("Is Cutpart",'CHECKBOX',True)
        if props.use_notched_sides:
            left_side.dim_x('Height',[Height])
            left_side.get_prompt('Notch X Dimension').set_formula('Toe_Kick_Height',[Toe_Kick_Height])
            left_side.get_prompt('Notch Y Dimension').set_formula('Toe_Kick_Setback',[Toe_Kick_Setback])
        else:
            left_side.loc_z('Toe_Kick_Height',[Toe_Kick_Height])
            left_side.dim_x('Height-Toe_Kick_Height',[Height,Toe_Kick_Height])
        left_side.rot_y(value=math.radians(-90))
        left_side.dim_y('Depth',[Depth])
        left_side.dim_z('-Left_Side_Thickness',[Left_Side_Thickness])
        left_side.get_prompt('Hide').set_formula('IF(Left_Fin_End,True,False)',[Left_Fin_End])
        add_side_height_dimension(left_side)
        # left_side.cutpart('Cabinet_Unfinished_Side' + self.open_name)
        # left_side.edgebanding('Cabinet_Body_Edges',l2=True)
        
        right_side = add_part(self, part_path)
        right_side.set_name(self.carcass_type + " Right Side")
        right_side.add_prompt("Is Cutpart",'CHECKBOX',True)
        right_side.loc_x('Width',[Width])
        if props.use_notched_sides:
            right_side.dim_x('Height',[Height])
            right_side.get_prompt('Notch X Dimension').set_formula('Toe_Kick_Height',[Toe_Kick_Height])
            right_side.get_prompt('Notch Y Dimension').set_formula('Toe_Kick_Setback',[Toe_Kick_Setback])
        else:
            right_side.loc_z('Toe_Kick_Height',[Toe_Kick_Height])
            right_side.dim_x('Height-Toe_Kick_Height',[Height,Toe_Kick_Height])
        right_side.rot_y(value=math.radians(-90))
        right_side.dim_y('Depth',[Depth])
        right_side.dim_z('Right_Side_Thickness',[Right_Side_Thickness])
        right_side.get_prompt('Hide').set_formula('IF(Right_Fin_End,True,False)',[Right_Fin_End])
        # right_side.cutpart('Cabinet_Unfinished_Side' + self.open_name)
        # right_side.edgebanding('Cabinet_Body_Edges',l2=True)
        
        left_fe = add_part(self, part_path)
        left_fe.set_name(self.carcass_type + " Left FE")
        left_fe.add_prompt("Is Cutpart",'CHECKBOX',True)

        if props.use_notched_sides:
            left_fe.dim_x('Height',[Height])
            left_fe.get_prompt('Notch X Dimension').set_formula('Toe_Kick_Height',[Toe_Kick_Height])
            left_fe.get_prompt('Notch Y Dimension').set_formula('Toe_Kick_Setback',[Toe_Kick_Setback])
        else:
            left_fe.loc_z('Toe_Kick_Height',[Toe_Kick_Height])
            left_fe.dim_x('Height-Toe_Kick_Height',[Height,Toe_Kick_Height])
        left_fe.rot_y(value=math.radians(-90))
        left_fe.dim_y('Depth',[Depth])
        left_fe.dim_z('-Left_Side_Thickness',[Left_Side_Thickness])
        left_fe.get_prompt('Hide').set_formula('IF(Left_Fin_End,False,True)',[Left_Fin_End])
        # left_fe.cutpart('Cabinet_Finished_Side' + self.open_name)
        # left_fe.edgebanding('Cabinet_Body_Edges',l2=True)
        
        right_fe = add_part(self, part_path)
        right_fe.set_name(self.carcass_type + " Right FE")
        right_fe.add_prompt("Is Cutpart",'CHECKBOX',True)
        right_fe.loc_x('Width',[Width])
        if props.use_notched_sides:
            right_fe.dim_x('Height',[Height])
            right_fe.get_prompt('Notch X Dimension').set_formula('Toe_Kick_Height',[Toe_Kick_Height])
            right_fe.get_prompt('Notch Y Dimension').set_formula('Toe_Kick_Setback',[Toe_Kick_Setback])
        else:
            right_fe.loc_z('Toe_Kick_Height',[Toe_Kick_Height])
            right_fe.dim_x('Height-Toe_Kick_Height',[Height,Toe_Kick_Height])
        right_fe.rot_y(value=math.radians(-90))
        right_fe.dim_y('Depth',[Depth])
        right_fe.dim_z('Right_Side_Thickness',[Right_Side_Thickness])
        right_fe.get_prompt('Hide').set_formula('IF(Right_Fin_End,False,True)',[Right_Fin_End])

        # region XML Export
        # right_fe.cutpart('Cabinet_Finished_Side' + self.open_name)
        # right_fe.edgebanding('Cabinet_Body_Edges',l2=True)
        # TODO XML Export
        # if props.use_notched_sides:
        #     add_toe_kick_notch(left_side)
        #     add_toe_kick_notch(right_side)
        #     add_toe_kick_notch(left_fe)
        #     add_toe_kick_notch(right_fe)
        # endregion
            
    def add_tall_sides(self):
        props = cabinet_properties.get_scene_props().carcass_defaults
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Toe_Kick_Height = self.get_prompt('Toe Kick Height').get_var()
        Toe_Kick_Setback = self.get_prompt('Toe Kick Setback').get_var()
        Left_Fin_End = self.get_prompt('Left Fin End').get_var()
        Right_Fin_End = self.get_prompt('Right Fin End').get_var()
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Left_Side_Full_Height = self.get_prompt('Left Side Full Height').get_var()
        Right_Side_Full_Height = self.get_prompt('Right Side Full Height').get_var()
        Top_Inset = self.get_prompt('Top Inset').get_var()
        Top_Thickness = self.get_prompt('Top Thickness').get_var()
    
        part_path = NOTCHED_SIDE if props.use_notched_sides else PART_WITH_FRONT_EDGEBANDING

        left_side = add_part(self, part_path)
        left_side.set_name(self.carcass_type + " Left Side")
        if props.use_notched_sides:
            left_side.dim_x('Height+IF(Left_Side_Full_Height,0,-Top_Inset+Top_Thickness)',[Height,Top_Inset,Top_Thickness,Left_Side_Full_Height])
            left_side.get_prompt('Notch X Dimension').set_formula('Toe_Kick_Height',[Toe_Kick_Height])
            left_side.get_prompt('Notch Y Dimension').set_formula('Toe_Kick_Setback',[Toe_Kick_Setback])
        else:
            left_side.loc_z('Toe_Kick_Height',[Toe_Kick_Height])
            left_side.dim_x('Height-Toe_Kick_Height+IF(Left_Side_Full_Height,0,-Top_Inset+Top_Thickness)',[Left_Side_Full_Height,Height,Toe_Kick_Height,Top_Thickness,Top_Inset])
        left_side.rot_y(value=math.radians(-90))
        left_side.dim_y('Depth',[Depth])
        left_side.dim_z('-Left_Side_Thickness',[Left_Side_Thickness])
        left_side.get_prompt('Hide').set_formula('IF(Left_Fin_End,True,False)',[Left_Fin_End])
        add_side_height_dimension(left_side)
        # left_side.cutpart('Cabinet_Unfinished_Side' + self.open_name)
        # left_side.edgebanding('Cabinet_Body_Edges',l2=True)
        
        right_side = add_part(self, part_path)
        right_side.set_name(self.carcass_type + " Right Side")
        right_side.loc_x('Width',[Width])
        if props.use_notched_sides:
            right_side.dim_x('Height+IF(Right_Side_Full_Height,0,-Top_Inset+Top_Thickness)',[Height,Top_Inset,Top_Thickness,Right_Side_Full_Height])
            right_side.get_prompt('Notch X Dimension').set_formula('Toe_Kick_Height',[Toe_Kick_Height])
            right_side.get_prompt('Notch Y Dimension').set_formula('Toe_Kick_Setback',[Toe_Kick_Setback])
        else:
            right_side.loc_z('Toe_Kick_Height',[Toe_Kick_Height])
            right_side.dim_x('Height-Toe_Kick_Height+IF(Right_Side_Full_Height,0,-Top_Inset+Top_Thickness)',[Right_Side_Full_Height,Top_Thickness,Top_Inset,Height,Toe_Kick_Height])
        right_side.rot_y(value=math.radians(-90))
        right_side.dim_y('Depth',[Depth])
        right_side.dim_z('Right_Side_Thickness',[Right_Side_Thickness])
        right_side.get_prompt('Hide').set_formula('IF(Right_Fin_End,True,False)',[Right_Fin_End])
        # right_side.cutpart('Cabinet_Unfinished_Side' + self.open_name)
        # right_side.edgebanding('Cabinet_Body_Edges',l2=True)
        
        left_fe = add_part(self, part_path)
        left_fe.set_name(self.carcass_type + " Left FE")
        if props.use_notched_sides:
            left_fe.dim_x('Height',[Height])
            left_fe.get_prompt('Notch X Dimension').set_formula('Toe_Kick_Height',[Toe_Kick_Height])
            left_fe.get_prompt('Notch Y Dimension').set_formula('Toe_Kick_Setback',[Toe_Kick_Setback])
        else:
            left_fe.loc_z('Toe_Kick_Height',[Toe_Kick_Height])
            left_fe.dim_x('Height-Toe_Kick_Height',[Height,Toe_Kick_Height])
        left_fe.rot_y(value=math.radians(-90))
        left_fe.dim_y('Depth',[Depth])
        left_fe.dim_z('-Left_Side_Thickness',[Left_Side_Thickness])
        left_fe.get_prompt('Hide').set_formula('IF(Left_Fin_End,False,True)',[Left_Fin_End])
        # left_fe.cutpart('Cabinet_Finished_Side' + self.open_name)
        # left_fe.edgebanding('Cabinet_Body_Edges',l2=True)
        
        right_fe = add_part(self, part_path)
        right_fe.set_name(self.carcass_type + " Right FE")
        right_fe.loc_x('Width',[Width])
        if props.use_notched_sides:
            right_fe.dim_x('Height',[Height])
            right_fe.get_prompt('Notch X Dimension').set_formula('Toe_Kick_Height',[Toe_Kick_Height])
            right_fe.get_prompt('Notch Y Dimension').set_formula('Toe_Kick_Setback',[Toe_Kick_Setback])
        else:
            right_fe.loc_z('Toe_Kick_Height',[Toe_Kick_Height])
            right_fe.dim_x('Height-Toe_Kick_Height',[Height,Toe_Kick_Height])
        right_fe.rot_y(value = -90)
        right_fe.dim_y('Depth',[Depth])
        right_fe.dim_z('Right_Side_Thickness',[Right_Side_Thickness])
        right_fe.get_prompt('Hide').set_formula('IF(Right_Fin_End,False,True)',[Right_Fin_End])
        # right_fe.cutpart('Cabinet_Finished_Side' + self.open_name)
        # right_fe.edgebanding('Cabinet_Body_Edges',l2=True)
        
         # TODO XML Export
        # if props.use_notched_sides:
        #     add_toe_kick_notch(left_side)
        #     add_toe_kick_notch(right_side)
        #     add_toe_kick_notch(left_fe)
        #     add_toe_kick_notch(right_fe)        
        
    def add_upper_sides(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        # Width = self.obj_bp.snap.get_var('dim_x', 'Width')
        # Height = self.obj_bp.snap.get_var('dim_z', 'Height')
        # Depth = self.obj_bp.snap.get_var('dim_y', 'Depth')
        Left_Fin_End = self.get_prompt('Left Fin End').get_var()
        Right_Fin_End = self.get_prompt('Right Fin End').get_var()
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Left_Side_Full_Height = self.get_prompt('Left Side Full Height').get_var()
        Right_Side_Full_Height = self.get_prompt('Right Side Full Height').get_var()
        Valance_Height_Top = self.get_prompt('Valance Height Top').get_var()
        Valance_Height_Bottom = self.get_prompt('Valance Height Bottom').get_var()

        left_side = add_part(self, PART_WITH_FRONT_AND_BOTTOM_EDGEBANDING)
        left_side.set_name(self.carcass_type + " Left Side")
        left_side.loc_z('IF(Left_Side_Full_Height,0,-Valance_Height_Top)',[Left_Side_Full_Height,Valance_Height_Top])
        # left_side.loc_z('IF(Left_Side_Full_Height,0,Height)',[Left_Side_Full_Height,Valance_Height_Top, Height])
        # left_side.loc_z(value=sn_unit.inch(36))
        left_side.rot_y(value=math.radians(-90))
        left_side.dim_x('Height+IF(Left_Side_Full_Height,0,Valance_Height_Top+Valance_Height_Bottom)',[Height,Valance_Height_Bottom,Valance_Height_Top,Left_Side_Full_Height])
        left_side.dim_y('Depth',[Depth])
        left_side.dim_z('-Left_Side_Thickness',[Left_Side_Thickness])
        left_side.get_prompt('Hide').set_formula('IF(Left_Fin_End,True,False)',[Left_Fin_End])
        add_side_height_dimension(left_side)
        # left_side.cutpart('Cabinet_Unfinished_Side' + self.open_name)
        # left_side.edgebanding('Cabinet_Body_Edges',l2=True)
        
        right_side = add_part(self, PART_WITH_FRONT_AND_BOTTOM_EDGEBANDING)
        right_side.set_name(self.carcass_type + " Right Side")
        right_side.loc_x('Width',[Width])
        right_side.loc_z('IF(Right_Side_Full_Height,0,-Valance_Height_Top)',[Right_Side_Full_Height,Valance_Height_Top])
        # right_side.loc_z('IF(Right_Side_Full_Height,0,Height)',[Right_Side_Full_Height,Valance_Height_Top, Height])
        right_side.rot_y(value=math.radians(-90))
        right_side.dim_x('Height+IF(Right_Side_Full_Height,0,Valance_Height_Top+Valance_Height_Bottom)',[Height,Right_Side_Full_Height,Valance_Height_Top,Valance_Height_Bottom])
        right_side.dim_y('Depth',[Depth])
        right_side.dim_z('Right_Side_Thickness',[Right_Side_Thickness])
        right_side.get_prompt('Hide').set_formula('IF(Right_Fin_End,True,False)',[Right_Fin_End])
        # right_side.cutpart('Cabinet_Unfinished_Side' + self.open_name)
        # right_side.edgebanding('Cabinet_Body_Edges',l2=True)
        
        left_fe = add_part(self, PART_WITH_FRONT_AND_BOTTOM_EDGEBANDING)
        left_fe.set_name(self.carcass_type + " Left FE")
        left_fe.rot_y(value=math.radians(-90))
        left_fe.dim_x('Height',[Height])
        left_fe.dim_y('Depth',[Depth])
        left_fe.dim_z('-Left_Side_Thickness',[Left_Side_Thickness])
        left_fe.get_prompt('Hide').set_formula('IF(Left_Fin_End,False,True)',[Left_Fin_End])
        # left_fe.cutpart('Cabinet_Finished_Side' + self.open_name)
        # left_fe.edgebanding('Cabinet_Body_Edges',l2=True)
        
        right_fe = add_part(self, PART_WITH_FRONT_AND_BOTTOM_EDGEBANDING)
        right_fe.set_name(self.carcass_type + " Right FE")
        right_fe.loc_x('Width',[Width])
        right_fe.rot_y(value=math.radians(-90))
        right_fe.dim_x('Height',[Height])
        right_fe.dim_y('Depth',[Depth])
        right_fe.dim_z('Right_Side_Thickness',[Right_Side_Thickness])
        right_fe.get_prompt('Hide').set_formula('IF(Right_Fin_End,False,True)',[Right_Fin_End])
        # right_fe.cutpart('Cabinet_Finished_Side' + self.open_name)
        # right_fe.edgebanding('Cabinet_Body_Edges',l2=True)
        
    def add_suspended_sides(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Left_Fin_End = self.get_prompt('Left Fin End').get_var()
        Right_Fin_End = self.get_prompt('Right Fin End').get_var()
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()

        left_side = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        left_side.set_name(self.carcass_type + " Left Side")
        left_side.rot_y(value=math.radians(-90))
        left_side.dim_x('Height',[Height])
        left_side.dim_y('Depth',[Depth])
        left_side.dim_z('-Left_Side_Thickness',[Left_Side_Thickness])
        left_side.get_prompt('Hide').set_formula('IF(Left_Fin_End,True,False)',[Left_Fin_End])
        add_side_height_dimension(left_side)
        # left_side.cutpart('Cabinet_Unfinished_Side' + self.open_name)
        # left_side.edgebanding('Cabinet_Body_Edges',l2=True)
        
        right_side = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        right_side.set_name(self.carcass_type + " Right Side")
        right_side.loc_x('Width',[Width])
        right_side.rot_y(value=math.radians(-90))
        right_side.dim_x('Height',[Height])
        right_side.dim_y('Depth',[Depth])
        right_side.dim_z('Right_Side_Thickness',[Right_Side_Thickness])
        right_side.get_prompt('Hide').set_formula('IF(Right_Fin_End,True,False)',[Right_Fin_End])
        # right_side.cutpart('Cabinet_Unfinished_Side' + self.open_name)
        # right_side.edgebanding('Cabinet_Body_Edges',l2=True)
        
        left_fe = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        left_fe.set_name(self.carcass_type + " Left FE")
        left_fe.rot_y(value=math.radians(-90))
        left_fe.dim_x('Height',[Height])
        left_fe.dim_y('Depth',[Depth])
        left_fe.dim_z('-Left_Side_Thickness',[Left_Side_Thickness])
        left_fe.get_prompt('Hide').set_formula('IF(Left_Fin_End,False,True)',[Left_Fin_End])
        # left_fe.cutpart('Cabinet_Finished_Side' + self.open_name)
        # left_fe.edgebanding('Cabinet_Body_Edges',l2=True)
        
        right_fe = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        right_fe.set_name(self.carcass_type + " Right FE")
        right_fe.loc_x('Width',[Width])
        right_fe.rot_y(value=math.radians(-90))
        right_fe.dim_x('Height',[Height])
        right_fe.dim_y('Depth',[Depth])
        right_fe.dim_z('Right_Side_Thickness',[Right_Side_Thickness])
        right_fe.get_prompt('Hide').set_formula('IF(Right_Fin_End,False,True)',[Right_Fin_End])
        # right_fe.cutpart('Cabinet_Finished_Side' + self.open_name)
        # right_fe.edgebanding('Cabinet_Body_Edges',l2=True)
        
    def add_fillers(self):
        width = self.obj_x.snap.get_var('location.x', 'width')
        height = self.obj_z.snap.get_var('location.z', 'height')
        depth = self.obj_y.snap.get_var('location.y', 'depth')        

        l_filler = self.get_prompt("Left Side Wall Filler").get_var('l_filler')
        r_filler = self.get_prompt("Right Side Wall Filler").get_var('r_filler')
        ft = self.get_prompt("Filler Thickness").get_var('ft')
        if self.carcass_type in {'Base','Sink','Tall'}:
            kick_height = self.get_prompt("Toe Kick Height").get_var('kick_height')
            
        left_filler = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        left_filler.set_name("Left Filler")
        left_filler.loc_y('depth',[depth])
        left_filler.loc_z('height',[height])
        left_filler.rot_x(value=math.radians(90))
        left_filler.rot_y(value=math.radians(90))
        left_filler.rot_z(value=math.radians(180))
        left_filler.dim_y('l_filler',[l_filler])
        left_filler.dim_z('ft',[ft])
        left_filler.get_prompt('Hide').set_formula('IF(l_filler>0,False,True)',[l_filler])
        # left_filler.cutpart('Cabinet_Filler')
        
        right_filler = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        right_filler.set_name("Right Filler")
        right_filler.loc_x('width',[width])
        right_filler.loc_y('depth',[depth])
        right_filler.loc_z('height',[height])
        right_filler.rot_x(value=math.radians(90))
        right_filler.rot_y(value=math.radians(90))
        right_filler.dim_y('r_filler',[r_filler])
        right_filler.dim_z('-ft',[ft])
        right_filler.get_prompt('Hide').set_formula('IF(r_filler>0,False,True)',[r_filler])
        # right_filler.cutpart('Cabinet_Filler')
        
        if self.carcass_type in {'Base','Sink','Tall'}:
            left_filler.dim_x('height-kick_height',[height,kick_height])
            right_filler.dim_x('height-kick_height',[height,kick_height])
            
        if self.carcass_type in {'Upper','Suspended'}:
            left_filler.dim_x('height',[height])
            right_filler.dim_x('height',[height])
            
    def add_full_top(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Top_Thickness = self.get_prompt('Top Thickness').get_var()
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Top_Inset = self.get_prompt('Top Inset').get_var()
        
        top = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        top.set_name(self.carcass_type + " Top")
        top.dim_x('Width-(Left_Side_Thickness+Right_Side_Thickness)',[Width,Left_Side_Thickness,Right_Side_Thickness])
        top.dim_y('Depth',[Depth])
        top.dim_z('-Top_Thickness',[Top_Thickness])
        top.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
        # top.loc_z('IF(Height>0,Height-Top_Inset+Top_Thickness,-Top_Inset+Top_Thickness)',[Height,Top_Inset,Top_Thickness])
        if self.carcass_type == "Upper":
            top.loc_z('IF(Height>0,2*Height-Top_Inset+Top_Thickness,-Top_Inset+Top_Thickness)',[Height,Top_Inset,Top_Thickness])
        else: 
            top.loc_z('IF(Height>0,Height-Top_Inset+Top_Thickness,-Top_Inset+Top_Thickness)',[Height,Top_Inset,Top_Thickness])


        # region XML Export
        # TODO: XML Export
        # top.cutpart("Cabinet_Top" + self.open_name)
        # top.edgebanding('Cabinet_Body_Edges', l2 = True)
        
        # if USE_CONST_HOLES_TOP:
        #     add_drilling(top)

        # endregion
        
    def add_sink_top(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Sub_Front_Height = self.get_prompt('Sub Front Height').get_var()
        Sub_Front_Thickness = self.get_prompt('Sub Front Thickness').get_var()
        
        front_s = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        front_s.set_name(self.carcass_type + " Front Stretcher")
        front_s.dim_x('Width-(Left_Side_Thickness+Right_Side_Thickness)',[Width,Left_Side_Thickness,Right_Side_Thickness])
        front_s.dim_y('-Sub_Front_Height',[Sub_Front_Height])
        front_s.dim_z('-Sub_Front_Thickness',[Sub_Front_Thickness])
        front_s.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
        front_s.loc_y('Depth',[Depth])
        front_s.loc_z('IF(Height>0,Height,0)',[Height])
        front_s.rot_x(value=math.radians(90))

        # front_s.cutpart("Cabinet_Sink_Sub_Front")
        # front_s.edgebanding('Cabinet_Body_Edges', l1 = True)

        # if USE_CONST_HOLES_STRETCHERS:
        #     add_drilling(front_s)
        
    def add_bottom(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')

        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Bottom_Thickness = self.get_prompt('Bottom Thickness').get_var()
        Remove_Bottom = self.get_prompt('Remove Bottom').get_var()
                
        bottom = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        bottom.set_name(self.carcass_type + " Bottom")
        if USE_DADO_BOTTOM:
            bottom.loc_x('Left_Side_Thickness-INCH(.25)',[Left_Side_Thickness])
            bottom.dim_x('Width-(Left_Side_Thickness+Right_Side_Thickness)+INCH(.5)',[Width,Left_Side_Thickness,Right_Side_Thickness])
        else:
            bottom.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
            bottom.dim_x('Width-(Left_Side_Thickness+Right_Side_Thickness)',[Width,Left_Side_Thickness,Right_Side_Thickness])
        bottom.dim_y('Depth',[Depth])
        bottom.dim_z('Bottom_Thickness',[Bottom_Thickness])

        bottom.get_prompt('Hide').set_formula('Remove_Bottom',[Remove_Bottom])
        # bottom.cutpart("Cabinet_Bottom" + self.open_name)
        # bottom.edgebanding('Cabinet_Body_Edges', l2 = True)
        
        if self.carcass_type in {'Upper','Suspended'}:
            Bottom_Inset = self.get_prompt('Bottom Inset').get_var()
            bottom.loc_z('Height+Bottom_Inset-Bottom_Thickness',[Height,Bottom_Inset,Bottom_Thickness])
            
        if self.carcass_type in {'Base','Tall','Sink'}:
            Toe_Kick_Height = self.get_prompt('Toe Kick Height').get_var()
            bottom.loc_z('Toe_Kick_Height',[Toe_Kick_Height])

        # region TODO XML Export
        # if USE_CONST_HOLES_BOTTOM:
        #     add_drilling(bottom)
            
        # if USE_DADO_BOTTOM:
        #     add_dado(bottom)
        # endregion
            
    def add_toe_kick(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')

        Toe_Kick_Height = self.get_prompt('Toe Kick Height').get_var()
        Toe_Kick_Setback = self.get_prompt('Toe Kick Setback').get_var()
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Remove_Bottom = self.get_prompt('Remove Bottom').get_var()
        
        kick = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        kick.set_name("Toe Kick")
        kick.dim_x('Width-(Left_Side_Thickness+Right_Side_Thickness)',[Width,Left_Side_Thickness,Right_Side_Thickness])
        kick.dim_y('Toe_Kick_Height',[Toe_Kick_Height])
        kick.dim_z(value=sn_unit.inch(-0.75))
        kick.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
        kick.loc_y('Depth+Toe_Kick_Setback',[Depth,Toe_Kick_Setback])
        kick.rot_x(value=math.radians(90))
        kick.get_prompt('Hide').set_formula('Remove_Bottom', [Remove_Bottom])

        # kick.cutpart("Cabinet_Toe_Kick")
    
    def add_leg_levelers(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Toe_Kick_Height = self.get_prompt('Toe Kick Height').get_var()
        Toe_Kick_Setback = self.get_prompt('Toe Kick Setback').get_var()
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()

        legs = add_part(self, LEG_LEVELERS)
        legs.set_name("Leg Levelers")
        legs.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
        legs.dim_x('Width-(Left_Side_Thickness+Right_Side_Thickness)',[Width,Left_Side_Thickness,Right_Side_Thickness])
        legs.dim_y('Depth+Toe_Kick_Setback',[Depth,Toe_Kick_Setback])
        legs.dim_z('Toe_Kick_Height',[Toe_Kick_Height])
    
    def add_back(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Height = self.obj_z.snap.get_var('location.z', 'Height')

        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Top_Inset = self.get_prompt('Top Inset').get_var()
        Bottom_Inset = self.get_prompt('Bottom Inset').get_var()
        Back_Thickness = self.get_prompt('Back Thickness').get_var()
        Bottom_Thickness = self.get_prompt('Bottom Thickness').get_var()
        Top_Thickness = self.get_prompt('Top Thickness').get_var()
        Remove_Back = self.get_prompt('Remove Back').get_var()
        Remove_Bottom = self.get_prompt('Remove Bottom').get_var()
        if self.carcass_type in {'Base','Tall','Sink'}:
            Toe_Kick_Height = self.get_prompt('Toe Kick Height').get_var()
        
        back = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        back.set_name(self.carcass_type + " Back")
        back.loc_x('Left_Side_Thickness',[Left_Side_Thickness])
        back.rot_y(value=math.radians(-90))
        back.rot_z(value=math.radians(-90))
        
        if self.carcass_type in {'Base','Sink'}:
            back.dim_x('fabs(Height)-IF(Remove_Bottom,0,Toe_Kick_Height+Bottom_Thickness)-Top_Thickness',[Height,Toe_Kick_Height,Bottom_Thickness,Remove_Bottom,Top_Thickness])
        
        if self.carcass_type == 'Tall':
            back.dim_x('fabs(Height)-IF(Remove_Bottom,0,Toe_Kick_Height+Bottom_Thickness)-Top_Inset',[Height,Top_Inset,Toe_Kick_Height,Bottom_Thickness,Remove_Bottom])
        
        if self.carcass_type in {'Upper','Suspended'}:
            back.dim_x('fabs(Height)-(Top_Inset+Bottom_Inset)',[Height,Top_Inset,Bottom_Inset])
            
        back.dim_y('Width-(Left_Side_Thickness+Right_Side_Thickness)',[Width,Left_Side_Thickness,Right_Side_Thickness])
        back.dim_z('-Back_Thickness',[Back_Thickness])
        # back.cutpart("Cabinet_Back" + self.open_name)
        back.get_prompt('Hide').set_formula('IF(Remove_Back,True,False)',[Remove_Back])
        
        if self.carcass_type in {'Base','Tall','Sink'}:
            back.loc_z('IF(Remove_Bottom,0,Toe_Kick_Height+Bottom_Thickness)',[Remove_Bottom,Toe_Kick_Height,Bottom_Thickness])
        
        if self.carcass_type in {'Upper','Suspended'}:
            back.loc_z('Height+Bottom_Inset',[Height,Bottom_Inset])
    
    def add_valances(self):
        Width = self.obj_x.snap.get_var('location.x', 'Width')
        Depth = self.obj_y.snap.get_var('location.y', 'Depth')
        Height = self.obj_z.snap.get_var('location.z', 'Height')
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Top_Inset = self.get_prompt('Top Inset').get_var()
        Top_Thickness = self.get_prompt('Top Thickness').get_var()
        Left_Fin_End = self.get_prompt('Left Fin End').get_var()
        Right_Fin_End = self.get_prompt('Right Fin End').get_var()
        Left_Side_Full_Height = self.get_prompt('Left Side Full Height').get_var()
        Right_Side_Full_Height = self.get_prompt('Right Side Full Height').get_var()
        Valance_Thickness = self.get_prompt("Valance Thickness").get_var()
        Valance_Each_Unit = self.get_prompt("Valance Each Unit").get_var()
        Valance_Height_Top = self.get_prompt("Valance Height Top").get_var()
        Valance_Height_Bottom = self.get_prompt("Valance Height Bottom").get_var()
        
        top_val = add_part(self, PART_WITH_FRONT_EDGEBANDING)
        top_val.set_name("Top Valance")
        top_val.loc_x('IF(OR(Left_Fin_End,Left_Side_Full_Height),Left_Side_Thickness,0)',[Left_Fin_End,Left_Side_Full_Height,Left_Side_Thickness])
        top_val.loc_y('Depth',[Depth])
        top_val.loc_z('IF(Height>0,Height-Top_Inset+Top_Thickness,-Top_Inset+Top_Thickness)',[Height,Top_Thickness,Top_Inset])
        top_val.rot_x(value=math.radians(90))
        top_val.dim_x('Width-(IF(OR(Left_Fin_End,Left_Side_Full_Height),Left_Side_Thickness,0)+IF(OR(Right_Fin_End,Right_Side_Full_Height),Right_Side_Thickness,0))',[Width,Right_Fin_End,Left_Fin_End,Left_Side_Full_Height,Left_Side_Thickness,Right_Side_Full_Height,Right_Side_Thickness])
        top_val.dim_y('Valance_Height_Top',[Valance_Height_Top])
        top_val.dim_z('-Valance_Thickness',[Valance_Thickness])
        top_val.get_prompt('Hide').set_formula('IF(AND(Valance_Each_Unit,Valance_Height_Top>0),False,True)',[Valance_Each_Unit,Valance_Height_Top])
        # top_val.cutpart("Cabinet_Valance")
        # top_val.edgebanding('Cabinet_Body_Edges',l1=True)
        
        if self.carcass_type == 'Upper':
            bottom_val = add_part(self, PART_WITH_FRONT_EDGEBANDING)
            bottom_val.set_name("Bottom Valance")
            bottom_val.loc_x('IF(OR(Left_Fin_End,Left_Side_Full_Height),Left_Side_Thickness,0)',[Left_Fin_End,Left_Side_Full_Height,Left_Side_Thickness])
            bottom_val.loc_y('Depth',[Depth])
            bottom_val.loc_z('Height+Valance_Height_Bottom',[Height,Valance_Height_Bottom])
            bottom_val.rot_x(value=math.radians(90))
            bottom_val.dim_x('Width-(IF(OR(Left_Fin_End,Left_Side_Full_Height),Left_Side_Thickness,0)+IF(OR(Right_Fin_End,Right_Side_Full_Height),Right_Side_Thickness,0))',[Width,Right_Fin_End,Left_Fin_End,Left_Side_Full_Height,Left_Side_Thickness,Right_Side_Full_Height,Right_Side_Thickness])
            bottom_val.dim_y('-Valance_Height_Bottom',[Valance_Height_Bottom])
            bottom_val.dim_z('-Valance_Thickness',[Valance_Thickness])
            bottom_val.get_prompt('Hide').set_formula('IF(AND(Valance_Each_Unit,Valance_Height_Bottom>0),False,True)',[Valance_Each_Unit,Valance_Height_Bottom])
            # bottom_val.cutpart("Cabinet_Valance")
            # bottom_val.edgebanding('Cabinet_Body_Edges',l1=True)
            
    def draw(self):
        props = cabinet_properties.get_scene_props().carcass_defaults
        self.create_assembly()

        self.add_common_carcass_prompts()
        if self.carcass_type == "Base":
            self.add_base_assembly_prompts()
            if not self.remove_top:
                self.add_full_top()
            if props.use_notched_sides:
                self.add_toe_kick()
            self.add_base_sides()
            if props.use_leg_levelers:
                self.add_leg_levelers()

        if self.carcass_type == "Tall":
            self.add_base_assembly_prompts()
            self.add_full_top()
            self.add_valance_prompts(add_bottom_valance=False)
            if props.use_notched_sides:
                self.add_toe_kick()
            self.add_tall_sides()
            if props.use_leg_levelers:
                self.add_leg_levelers()
            # self.add_valances()
            
        if self.carcass_type == "Upper":
            self.flip_z = True
            self.add_full_top()
            self.add_valance_prompts(add_bottom_valance=True)
            self.add_valances()
            self.add_upper_sides()
            
        if self.carcass_type == "Sink":
            self.add_base_assembly_prompts()
            self.add_sink_prompts()
            self.add_sink_top()
            if props.use_notched_sides:
                self.add_toe_kick()
            self.add_base_sides()
            if props.use_leg_levelers:
                self.add_leg_levelers()
                
        if self.carcass_type == "Suspended":
            self.flip_z = True
            self.add_suspended_sides()
            if not self.remove_top:
                self.add_full_top()

        self.add_fillers()
        self.add_bottom()
        self.add_back()
        self.add_prompt_formulas()
        
        self.update()
   
class Inside_Corner_Carcass(sn_types.Assembly):
    type_assembly = "INSERT"
    id_prompt = cabinet_properties.LIBRARY_NAME_SPACE + ".frameless_cabinet_prompts"
    library_name = "Carcasses"
    placement_type = ""
    
    carcass_type = "" # {Base, Tall, Upper}
    open_name = ""
    
    carcass_shape = "" # {Notched, Diagonal}
    left_right_depth = sn_unit.inch(23)

    def update_dimensions(self):
        update_dimensions(self)  # Call module level function to find and update door dim labels

    def update(self):
        super().update()
        self.obj_bp["IS_BP_CARCASS"] = True   
        self.obj_bp["INSIDE_CORNER_CARCASS"] = True 
    
    def add_common_carcass_prompts(self):
        props = cabinet_properties.get_scene_props().size_defaults
        if self.carcass_type == 'Upper':
            self.left_right_depth = props.upper_cabinet_depth
        else:
            self.left_right_depth = props.base_cabinet_depth

        self.add_prompt("Left Fin End", 'CHECKBOX', False)
        self.add_prompt("Right Fin End", 'CHECKBOX', False)
        self.add_prompt("Left Side Wall Filler", 'DISTANCE', 0.0)
        self.add_prompt("Right Side Wall Filler", 'DISTANCE', 0.0)
        
        self.add_prompt("Cabinet Depth Left", 'DISTANCE', self.left_right_depth)
        self.add_prompt("Cabinet Depth Right", 'DISTANCE', self.left_right_depth)
        
        self.add_prompt("Left Side Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Right Side Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Top Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Bottom Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Back Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Thick Back Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Filler Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Nailer Thickness", 'DISTANCE', sn_unit.inch(.75))
        self.add_prompt("Edgebanding Thickness", 'DISTANCE', sn_unit.inch(.02))

        ppt_obj_insets = self.add_prompt_obj("Backing_Config")
        self.add_prompt("Back Inset", 'DISTANCE', sn_unit.inch(0), prompt_obj=ppt_obj_insets)
        self.add_prompt("Top Inset", 'DISTANCE', sn_unit.inch(0), prompt_obj=ppt_obj_insets)
        self.add_prompt("Bottom Inset", 'DISTANCE', sn_unit.inch(0), prompt_obj=ppt_obj_insets)
        
    def add_base_assembly_prompts(self):
        props = cabinet_properties.get_scene_props().carcass_defaults
        self.add_prompt("Toe Kick Height", 'DISTANCE', props.toe_kick_height)
        self.add_prompt("Toe Kick Setback", 'DISTANCE', props.toe_kick_setback)
        self.add_prompt("Toe Kick Thickness", 'DISTANCE', sn_unit.inch(.75))
    
    def add_valance_prompts(self,add_bottom_valance):
        props = cabinet_properties.get_scene_props().carcass_defaults
        self.add_prompt("Valance Height Top", 'DISTANCE', props.valance_height_top)
        self.add_prompt("Door Valance Top", 'CHECKBOX', props.door_valance_top)
        if add_bottom_valance:
            self.add_prompt("Valance Height Bottom", 'DISTANCE', props.valance_height_bottom)
            self.add_prompt("Door Valance Bottom", 'CHECKBOX', props.door_valance_bottom)
        self.add_prompt("Left Side Full Height", 'CHECKBOX', False)
        self.add_prompt("Right Side Full Height", 'CHECKBOX', False)
        self.add_prompt("Valance Each Unit", 'CHECKBOX', props.valance_each_unit)
        self.add_prompt("Valance Thickness", 'DISTANCE', sn_unit.inch(.75))
    
    def add_prompt_formuls(self):
        # sgi = self.get_var('cabinetlib.spec_group_index','sgi')
        tt = self.get_prompt("Top Thickness").get_var('tt')
        bt = self.get_prompt("Bottom Thickness").get_var('bt')
        bkt = self.get_prompt("Back Thickness").get_var('bkt')
        lfe = self.get_prompt("Left Fin End").get_var('lfe')
        rfe = self.get_prompt("Right Fin End").get_var('rfe')
        if self.carcass_type in {'Base','Sink','Tall'}:
            kick_height = self.get_prompt("Toe Kick Height").get_var('kick_height')
        if self.carcass_type in {'Upper','Tall'}:
            vht = self.get_prompt("Valance Height Top").get_var('vht')
        if self.carcass_type == 'Upper':
            vhb = self.get_prompt("Valance Height Bottom").get_var('vhb')
            
        Side_Pointer_Name = 'Cabinet_Unfinished_Side' + self.open_name
        FE_Pointer_Name = 'Cabinet_Finished_Side' + self.open_name
        Top_Pointer_Name = 'Cabinet_Top' + self.open_name
        Bottom_Pointer_Name = 'Cabinet_Bottom' + self.open_name
        Thick_Back_Pointer_Name = 'Cabinet_Thick_Back' + self.open_name
        Edgebanding_Pointer_Name = 'Cabinet_Body_Edges' + self.open_name            
            
        # self.get_prompt('Left Side Thickness').set_formula('IF(lfe,THICKNESS(sgi,"' + FE_Pointer_Name +'"),THICKNESS(sgi,"' + Side_Pointer_Name +'"))',[lfe,sgi])
        # self.get_prompt('Right Side Thickness').set_formula('IF(rfe,THICKNESS(sgi,"' + FE_Pointer_Name +'"),THICKNESS(sgi,"' + Side_Pointer_Name +'"))',[rfe,sgi])
        # self.get_prompt('Top Thickness').set_formula('THICKNESS(sgi,"' + Top_Pointer_Name +'")',[sgi])
        # self.get_prompt('Bottom Thickness').set_formula('THICKNESS(sgi,"' + Bottom_Pointer_Name +'")',[sgi])
        # if self.carcass_type in {'Base','Sink','Tall'}:
        #     self.get_prompt('Toe Kick Thickness').set_formula('THICKNESS(sgi,"Cabinet_Toe_Kick")',[sgi])
        # if self.carcass_type == 'Sink':
        #     self.get_prompt('Sub Front Thickness').set_formula('THICKNESS(sgi,"Sink_Sub_Front")',[sgi])
        # self.get_prompt('Back Thickness').set_formula('THICKNESS(sgi,"' + Thick_Back_Pointer_Name +'")',[sgi])
        # self.get_prompt('Thick Back Thickness').set_formula('THICKNESS(sgi,"Cabinet_Thick_Back' + self.open_name +'")',[sgi])
        # self.get_prompt('Filler Thickness').set_formula('THICKNESS(sgi,"Cabinet_Filler")',[sgi])
        # self.get_prompt('Nailer Thickness').set_formula('THICKNESS(sgi,"Cabinet_Nailer")',[sgi])
        # if self.carcass_type in {'Tall','Upper'}:
        #     self.get_prompt('Valance Thickness').set_formuula('THICKNESS(sgi,"Cabinet_Valance")',[sgi])
        # self.get_prompt('Edgebanding Thickness').set_formula('EDGE_THICKNESS(sgi,"' + Edgebanding_Pointer_Name + '")',[sgi])
        
        if self.carcass_type == 'Base':
            self.get_prompt('Top Inset').set_formula('tt',[tt])
            self.get_prompt('Bottom Inset').set_formula('kick_height+bt',[kick_height,bt])
        if self.carcass_type == 'Sink':
            self.get_prompt('Top Inset').set_formula(value = sn_unit.inch(.75))
            self.get_prompt('Bottom Inset').set_formula('kick_height+bt',[kick_height,bt])
        if self.carcass_type == 'Tall':
            self.get_prompt('Top Inset').set_formula('vht+tt',[vht,tt])
            self.get_prompt('Bottom Inset').set_formula('kick_height+bt',[kick_height,bt])
        if self.carcass_type == 'Upper':
            self.get_prompt('Top Inset').set_formula('vht+tt',[vht,tt])
            self.get_prompt('Bottom Inset').set_formula('vhb+bt',[vhb,bt])
        if self.carcass_type == 'Suspended':
            self.get_prompt('Top Inset').set_formula('tt',[tt])
            self.get_prompt('Bottom Inset').set_formula('bt',[bt])
        
        self.get_prompt('Back Inset').set_formula('bkt',[bkt])
    
    def add_sides(self):
        props = cabinet_properties.get_scene_props().carcass_defaults
        width = self.obj_x.snap.get_var('location.x','width')
        height = self.obj_z.snap.get_var('location.z','height')
        depth = self.obj_y.snap.get_var('location.y','depth')
        if self.carcass_type in {'Base','Tall'}:
            Toe_Kick_Height = self.get_prompt('Toe Kick Height').get_var()
            Toe_Kick_Setback = self.get_prompt('Toe Kick Setback').get_var()
        Left_Fin_End = self.get_prompt('Left Fin End').get_var()
        Right_Fin_End = self.get_prompt('Right Fin End').get_var()
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Cabinet_Depth_Left = self.get_prompt("Cabinet Depth Left").get_var()
        Cabinet_Depth_Right = self.get_prompt("Cabinet Depth Right").get_var()
        sides = []
    
        if self.carcass_type in {"Base","Tall","Sink"}:
            left_side = add_part(self, NOTCHED_SIDE if props.use_notched_sides else PART_WITH_FRONT_EDGEBANDING)
            left_side.set_name(self.carcass_type + " Left Side")
            left_side.loc_y('depth',[depth])
            left_side.dim_x('height',[height])
            left_side.dim_y('-Cabinet_Depth_Left',[Cabinet_Depth_Left])
            left_side.rot_z(value=math.radians(90))
            add_side_height_dimension(left_side)
            sides.append(left_side)
        
            right_side = add_part(self, NOTCHED_SIDE if props.use_notched_sides else PART_WITH_FRONT_EDGEBANDING)
            right_side.set_name(self.carcass_type + " Right Side")
            right_side.dim_x('height',[height])
            right_side.dim_y('-Cabinet_Depth_Right',[Cabinet_Depth_Right])
            sides.append(right_side)
            
            left_fe = add_part(self, NOTCHED_SIDE if props.use_notched_sides else PART_WITH_FRONT_EDGEBANDING)
            left_fe.set_name(self.carcass_type + " Left FE")
            left_fe.loc_y('depth',[depth])
            left_fe.dim_x('height',[height])
            left_fe.dim_y('-Cabinet_Depth_Left',[Cabinet_Depth_Left])
            left_fe.rot_z(value=math.radians(90))
            sides.append(left_fe)
            
            right_fe = add_part(self, NOTCHED_SIDE if props.use_notched_sides else PART_WITH_FRONT_EDGEBANDING)
            right_fe.set_name(self.carcass_type + " Right FE")
            right_fe.dim_x('height',[height])
            right_fe.dim_y('-Cabinet_Depth_Right',[Cabinet_Depth_Right])
            sides.append(right_fe)
        
        if self.carcass_type in {"Upper","Suspended"}:
            left_side = add_part(self, PART_WITH_FRONT_AND_BOTTOM_EDGEBANDING)
            left_side.set_name(self.carcass_type + " Left Side")
            left_side.loc_y('depth',[depth])
            left_side.dim_x('height',[height])
            left_side.dim_y('-Cabinet_Depth_Left',[Cabinet_Depth_Left])
            left_side.rot_z(value=math.radians(90))
            add_side_height_dimension(left_side)
            sides.append(left_side)
        
            right_side = add_part(self, PART_WITH_FRONT_AND_BOTTOM_EDGEBANDING)
            right_side.set_name(self.carcass_type + " Right Side")
            right_side.dim_x('height',[height])
            right_side.dim_y('-Cabinet_Depth_Right',[Cabinet_Depth_Right])
            sides.append(right_side)
            
            left_fe = add_part(self, PART_WITH_FRONT_AND_BOTTOM_EDGEBANDING)
            left_fe.set_name(self.carcass_type + " Left FE")
            left_fe.loc_y('depth',[depth])
            left_fe.dim_x('height',[height])
            left_fe.dim_y('-Cabinet_Depth_Left',[Cabinet_Depth_Left])
            left_fe.rot_z(value=math.radians(90))
            sides.append(left_fe)
            
            right_fe = add_part(self, PART_WITH_FRONT_AND_BOTTOM_EDGEBANDING)
            right_fe.set_name(self.carcass_type + " Right FE")
            right_fe.dim_x('height',[height])
            right_fe.dim_y('-Cabinet_Depth_Right',[Cabinet_Depth_Right])
            sides.append(right_fe)
    
        for side in sides:
            side.rot_y(value=math.radians(-90))
            # side.edgebanding('Cabinet_Body_Edges',l1=True)
            if self.carcass_type in {'Base','Tall'}:
                side.get_prompt('Notch X Dimension').set_formula('Toe_Kick_Height',[Toe_Kick_Height])
                side.get_prompt('Notch Y Dimension').set_formula('Toe_Kick_Setback',[Toe_Kick_Setback])
            if "Left Side" in side.obj_bp.snap.name_object:
                side.get_prompt('Hide').set_formula('IF(Left_Fin_End,True,False)',[Left_Fin_End])
                side.dim_z('-Left_Side_Thickness',[Left_Side_Thickness])
                # side.cutpart("Cabinet_Unfinished_Side"+self.open_name)
            if "Right Side" in side.obj_bp.snap.name_object:
                side.get_prompt('Hide').set_formula('IF(Right_Fin_End,True,False)',[Right_Fin_End])
                side.dim_z('Right_Side_Thickness',[Right_Side_Thickness])
                # side.cutpart("Cabinet_Unfinished_Side"+self.open_name)
                side.loc_x('width',[width])
            if "Left FE" in side.obj_bp.snap.name_object:
                side.get_prompt('Hide').set_formula('IF(Left_Fin_End,False,True)',[Left_Fin_End])
                side.dim_z('-Left_Side_Thickness',[Left_Side_Thickness])
                # side.cutpart("Cabinet_Finished_Side"+self.open_name)
            if "Right FE" in side.obj_bp.snap.name_object:
                side.get_prompt('Hide').set_formula('IF(Right_Fin_End,False,True)',[Right_Fin_End])
                side.dim_z('Right_Side_Thickness',[Right_Side_Thickness])
                # side.cutpart("Cabinet_Finished_Side"+self.open_name)
                side.loc_x('width',[width])
                
    def add_fillers(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Depth = self.obj_y.snap.get_var('location.y','Depth')
        Height = self.obj_z.snap.get_var('location.z','Height')
        Left_Side_Wall_Filler = self.get_prompt("Left Side Wall Filler").get_var()
        Right_Side_Wall_Filler = self.get_prompt("Right Side Wall Filler").get_var()
        Filler_Thickness = self.get_prompt("Filler Thickness").get_var()
        Cabinet_Depth_Left = self.get_prompt("Cabinet Depth Left").get_var()
        Cabinet_Depth_Right = self.get_prompt("Cabinet Depth Right").get_var()
        
        if self.carcass_type in {'Base','Sink','Tall'}:
            Toe_Kick_Height = self.get_prompt("Toe Kick Height").get_var()
            
        left_filler = add_part(self, PART_WITH_NO_EDGEBANDING)
        left_filler.set_name("Left Filler")
        left_filler.loc_x('Cabinet_Depth_Left',[Cabinet_Depth_Left])
        left_filler.loc_y('Depth',[Depth])
        left_filler.loc_z('Height',[Height])
        left_filler.rot_x(value=math.radians(90))
        left_filler.rot_y(value=math.radians(90))
        left_filler.rot_z(value=math.radians(-90))
        left_filler.dim_y('Left_Side_Wall_Filler',[Left_Side_Wall_Filler])
        left_filler.dim_z('Filler_Thickness',[Filler_Thickness])
        left_filler.get_prompt('Hide').set_formula('IF(Left_Side_Wall_Filler>0,False,True)',[Left_Side_Wall_Filler])
        # left_filler.cutpart('Cabinet_Filler')
        
        right_filler = add_part(self, PART_WITH_NO_EDGEBANDING)
        right_filler.set_name("Right Filler")
        right_filler.loc_x('Width',[Width])
        right_filler.loc_y('-Cabinet_Depth_Right',[Cabinet_Depth_Right])
        right_filler.loc_z('Height',[Height])
        right_filler.rot_x(value=math.radians(90))
        right_filler.rot_y(value=math.radians(90))
        right_filler.dim_y('Right_Side_Wall_Filler',[Right_Side_Wall_Filler])
        right_filler.dim_z('-Filler_Thickness',[Filler_Thickness])
        right_filler.get_prompt('Hide').set_formula('IF(Right_Side_Wall_Filler>0,False,True)',[Right_Side_Wall_Filler])
        # right_filler.cutpart('Cabinet_Filler')
        
        if self.carcass_type in {'Base','Sink','Tall'}:
            left_filler.dim_x('Height-Toe_Kick_Height',[Height,Toe_Kick_Height])
            right_filler.dim_x('Height-Toe_Kick_Height',[Height,Toe_Kick_Height])
            
        if self.carcass_type in {'Upper','Suspended'}:
            left_filler.dim_x('Height',[Height])
            right_filler.dim_x('Height',[Height])
            
    def add_full_top(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Depth = self.obj_y.snap.get_var('location.y','Depth')
        Height = self.obj_z.snap.get_var('location.z','Height')
        Top_Thickness = self.get_prompt('Top Thickness').get_var()
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Cabinet_Depth_Left = self.get_prompt("Cabinet Depth Left").get_var()
        Cabinet_Depth_Right = self.get_prompt("Cabinet Depth Right").get_var()
        
        if self.carcass_shape == 'Diagonal':
            top = add_part(self, CHAMFERED_PART)
        if self.carcass_shape == 'Notched':
            top = add_part(self, CORNER_NOTCH_PART)
        
        top.set_name(self.carcass_type + " Top")
        top.dim_x('Width-Right_Side_Thickness',[Width,Right_Side_Thickness])
        top.dim_y('Depth+Left_Side_Thickness',[Depth,Left_Side_Thickness])
        top.dim_z('-Top_Thickness',[Top_Thickness])
        top.loc_z('IF(Height>0,Height,0)',[Height])
        # top.cutpart("Cabinet_Top"+self.open_name)
        top.get_prompt('Left Depth').set_formula('Cabinet_Depth_Left',[Cabinet_Depth_Left])
        top.get_prompt('Right Depth').set_formula('Cabinet_Depth_Right',[Cabinet_Depth_Right])
        # top.edgebanding('Cabinet_Body_Edges', l1 = True)
        
    def add_bottom(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Depth = self.obj_y.snap.get_var('location.y','Depth')
        Height = self.obj_z.snap.get_var('location.z','Height')
        if self.carcass_type in {'Base','Tall','Sink'}:
            Toe_Kick_Height = self.get_prompt('Toe Kick Height').get_var()
            Toe_Kick_Setback = self.get_prompt('Toe Kick Setback').get_var()
            Toe_Kick_Thickness = self.get_prompt('Toe Kick Thickness').get_var()
        Left_Side_Thickness = self.get_prompt('Left Side Thickness').get_var()
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Bottom_Thickness = self.get_prompt('Bottom Thickness').get_var()
        Cabinet_Depth_Left = self.get_prompt("Cabinet Depth Left").get_var()
        Cabinet_Depth_Right = self.get_prompt("Cabinet Depth Right").get_var()
        
        if self.carcass_shape == 'Diagonal':
            bottom = add_part(self, CHAMFERED_PART)
        if self.carcass_shape == 'Notched':
            bottom = add_part(self, CORNER_NOTCH_PART)
            
        bottom.set_name(self.carcass_type + " Bottom")
        bottom.dim_x('Width-Right_Side_Thickness',[Width,Right_Side_Thickness])
        bottom.dim_y('Depth+Left_Side_Thickness',[Depth,Left_Side_Thickness])
        bottom.get_prompt('Left Depth').set_formula('Cabinet_Depth_Left',[Cabinet_Depth_Left])
        bottom.get_prompt('Right Depth').set_formula('Cabinet_Depth_Right',[Cabinet_Depth_Right])
        # bottom.cutpart("Cabinet_Bottom"+self.open_name)
        # bottom.edgebanding('Cabinet_Body_Edges', l1 = True)
        
        if self.carcass_type in {'Upper','Suspended'}:
            bottom.dim_z('Bottom_Thickness',[Bottom_Thickness])
            bottom.loc_z('Height',[Height])
            
        if self.carcass_type in {'Base','Tall','Sink'}:
            bottom.dim_z('Bottom_Thickness',[Bottom_Thickness])
            bottom.loc_z('Toe_Kick_Height',[Toe_Kick_Height])
            
            left_kick = add_part(self, PART_WITH_NO_EDGEBANDING)
            left_kick.set_name("Left Toe Kick")
            left_kick.dim_y('Toe_Kick_Height',[Toe_Kick_Height])
            left_kick.dim_z('-Toe_Kick_Thickness',[Toe_Kick_Thickness])
            left_kick.loc_x('Cabinet_Depth_Left-Toe_Kick_Setback',[Cabinet_Depth_Left,Toe_Kick_Setback])
            left_kick.loc_y('Depth+Left_Side_Thickness',[Depth,Left_Side_Thickness])
            left_kick.rot_x(value=math.radians(90))
            left_kick.rot_z(value=math.radians(90))
            # left_kick.cutpart("Toe_Kick")
    
            if self.carcass_shape == 'Notched':
                left_kick.dim_x('fabs(Depth)-Cabinet_Depth_Right+Toe_Kick_Setback',[Depth,Cabinet_Depth_Right,Toe_Kick_Setback])
                
                right_kick = add_part(self, PART_WITH_NO_EDGEBANDING)
                right_kick.set_name("Left Toe Kick")
                right_kick.dim_x('fabs(Width)-Cabinet_Depth_Left+Toe_Kick_Setback-Right_Side_Thickness',[Width,Cabinet_Depth_Left,Toe_Kick_Setback,Right_Side_Thickness])
                right_kick.dim_y('Toe_Kick_Height',[Toe_Kick_Height])
                right_kick.dim_z('-Toe_Kick_Thickness',[Toe_Kick_Thickness])
                right_kick.loc_x('Cabinet_Depth_Left-Toe_Kick_Setback',[Cabinet_Depth_Left,Toe_Kick_Setback,Toe_Kick_Thickness])
                right_kick.loc_y('-Cabinet_Depth_Right+Toe_Kick_Setback',[Cabinet_Depth_Right,Toe_Kick_Setback])
                right_kick.rot_x(value=math.radians(90))
                # right_kick.cutpart("Toe_Kick")
            
            else:
                left_kick.dim_x('sqrt(((fabs(Depth)-Left_Side_Thickness-Cabinet_Depth_Right+Toe_Kick_Setback)**2)+((fabs(Width)-Right_Side_Thickness-Cabinet_Depth_Left+Toe_Kick_Setback)**2))',
                                [Depth,Width,Cabinet_Depth_Right,Cabinet_Depth_Left,Left_Side_Thickness,Right_Side_Thickness,Toe_Kick_Setback])
                
                left_kick.rot_z('atan((fabs(Depth)-Left_Side_Thickness-Cabinet_Depth_Right+Toe_Kick_Setback)/(fabs(Width)-Right_Side_Thickness-Cabinet_Depth_Left+Toe_Kick_Setback))',
                                [Depth,Width,Left_Side_Thickness,Right_Side_Thickness,Cabinet_Depth_Left,Cabinet_Depth_Right,Toe_Kick_Setback])
    
    def add_backs(self):
        Width = self.obj_x.snap.get_var('location.x','Width')
        Depth = self.obj_y.snap.get_var('location.y','Depth')
        Height = self.obj_z.snap.get_var('location.z','Height')
        Right_Side_Thickness = self.get_prompt('Right Side Thickness').get_var()
        Top_Inset = self.get_prompt('Top Inset').get_var()
        Bottom_Inset = self.get_prompt('Bottom Inset').get_var()
        Back_Thickness = self.get_prompt('Back Thickness').get_var()

        r_back = add_part(self, PART_WITH_NO_EDGEBANDING)
        r_back.set_name(self.carcass_type + " Back")
        r_back.loc_x('Back_Thickness',[Back_Thickness])
        r_back.loc_z('IF(Height>0,Bottom_Inset,Height+Bottom_Inset)',[Bottom_Inset,Height])
        r_back.rot_y(value=math.radians(-90))
        r_back.rot_z(value=math.radians(-90))
        r_back.dim_x('fabs(Height)-(Top_Inset+Bottom_Inset)',[Height,Top_Inset,Bottom_Inset])
        r_back.dim_y('Width-(Back_Thickness+Right_Side_Thickness)',[Width,Back_Thickness,Right_Side_Thickness])
        r_back.dim_z('-Back_Thickness',[Back_Thickness])
        # r_back.cutpart("Cabinet_Thick_Back" + self.open_name)
        
        l_back = add_part(self, PART_WITH_NO_EDGEBANDING)
        l_back.set_name(self.carcass_type + " Back")
        l_back.loc_z('IF(Height>0,Bottom_Inset,Height+Bottom_Inset)',[Bottom_Inset,Height])
        l_back.rot_y(value=math.radians(-90))
        l_back.rot_z(value=math.radians(180))
        l_back.dim_x('fabs(Height)-(Top_Inset+Bottom_Inset)',[Height,Top_Inset,Bottom_Inset])
        l_back.dim_y('fabs(Depth)-Right_Side_Thickness',[Depth,Right_Side_Thickness])
        l_back.dim_z('Back_Thickness',[Back_Thickness])
        # l_back.cutpart("Cabinet_Thick_Back" + self.open_name)
        
    def add_valances(self):
        pass
    
    def draw(self):
        self.create_assembly()
        
        self.add_common_carcass_prompts()
        
        if self.carcass_type in {"Base","Tall"}:
            self.add_base_assembly_prompts()
        
        if self.carcass_type == "Tall":
            self.add_valance_prompts(add_bottom_valance=False)
        elif self.carcass_type == "Upper":
                self.add_valance_prompts(add_bottom_valance=True)

        self.add_prompt_formuls()
        self.add_sides()
        self.add_full_top()
        self.add_bottom()
        self.add_backs()
        self.add_fillers()

        self.update()

#---------Standard Carcasses
        
class INSERT_Base_Carcass(Standard_Carcass):
    
    def __init__(self):
        self.category_name = "Carcasses"
        self.assembly_name = "Base Carcass"
        self.carcass_type = "Base"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)

class INSERT_Tall_Carcass(Standard_Carcass):
    
    def __init__(self):
        self.category_name = "Carcasses"
        self.assembly_name = "Tall Carcass"
        self.carcass_type = "Tall"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(84)
        self.depth = sn_unit.inch(23)

class INSERT_Upper_Carcass(Standard_Carcass):
    
    def __init__(self):
        self.category_name = "Carcasses"
        self.assembly_name = "Upper Carcass"
        self.carcass_type = "Upper"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(12)
               
class INSERT_Sink_Carcass(Standard_Carcass):
    
    def __init__(self):
        self.category_name = "Carcasses"
        self.assembly_name = "Sink Carcass"
        self.carcass_type = "Sink"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(23)

                
class INSERT_Suspended_Carcass(Standard_Carcass):
    
    def __init__(self):
        self.category_name = "Carcasses"
        self.assembly_name = "Suspended Carcass"
        self.carcass_type = "Suspended"
        self.width = sn_unit.inch(18)
        self.height = sn_unit.inch(6)
        self.depth = sn_unit.inch(23)

#---------Inside Corner Carcasses

class INSERT_Base_Inside_Corner_Notched_Carcass(Inside_Corner_Carcass):
    
    def __init__(self):
        self.category_name = "Carcasses"
        self.assembly_name = "Base Inside Corner Notched Carcass"
        self.carcass_type = "Base"
        self.carcass_shape = "Notched"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(36)
        self.left_right_depth = sn_unit.inch(23)
        
class INSERT_Upper_Inside_Corner_Notched_Carcass(Inside_Corner_Carcass):
    
    def __init__(self):
        self.category_name = "Carcasses"
        self.assembly_name = "Upper Inside Corner Notched Carcass"
        self.carcass_type = "Upper"
        self.carcass_shape = "Notched"
        self.width = sn_unit.inch(12)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(12)
        self.left_right_depth = sn_unit.inch(12)

class INSERT_Base_Inside_Corner_Diagonal_Carcass(Inside_Corner_Carcass):
    
    def __init__(self):
        self.category_name = "Carcasses"
        self.assembly_name = "Base Inside Corner Diagonal Carcass"
        self.carcass_type = "Base"
        self.carcass_shape = "Diagonal"
        self.width = sn_unit.inch(36)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(36)
        self.left_right_depth = sn_unit.inch(23)
        
class INSERT_Upper_Inside_Corner_Diagonal_Carcass(Inside_Corner_Carcass):
    
    def __init__(self):
        self.category_name = "Carcasses"
        self.assembly_name = "Upper Inside Corner Diagonal Carcass"
        self.carcass_type = "Upper"
        self.carcass_shape = "Diagonal"
        self.width = sn_unit.inch(12)
        self.height = sn_unit.inch(34)
        self.depth = sn_unit.inch(12)
        self.left_right_depth = sn_unit.inch(12)