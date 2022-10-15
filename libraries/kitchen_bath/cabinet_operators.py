
import bpy
import math
from os import path
from snap import sn_types, sn_unit, sn_utils
from bpy.app.handlers import persistent
from . import cabinet_properties

def get_carcass_insert(product):
    new_list = []
    inserts = sn_utils.get_insert_bp_list(product.obj_bp,new_list)
    for insert in inserts:
        if insert.get("IS_BP_CARCASS"):
            carcass = sn_types.Assembly(insert)
            return carcass
    # pass

def get_product_components(product):

    lbl_text = ""
    count_door = 0
    count_drawer = 0
    count_shelf = 0
    count_false = 0
    components = sn_utils.get_assembly_bp_list(product.obj_bp, [])
    
    for component in components:
        if "IS_DOOR" in component:
            door = sn_types.Assembly(component)
            hide_ppt = door.get_prompt("Hide")
            if hide_ppt:
                if door.get_prompt("Hide").get_value() == False:
                    count_door += 1
        elif "IS_BP_DRAWER_FRONT" in component:
            if "IS_BP_FALSE_FRONT" in component:
                count_false += 1
            else:
                count_drawer += 1
        elif "IS_BP_SHELVES" in component:
            shelves = sn_types.Assembly(component)
            shelf_ppt = shelves.get_prompt("Shelf Qty")
            if shelf_ppt:
                count_shelf += shelves.get_prompt("Shelf Qty").get_value()
    
    if count_door > 1:
        lbl_text += str(count_door) + " Doors|"
    elif count_door == 1:
        lbl_text += "1 Door|"
    
    if count_drawer > 1:
        lbl_text += str(count_drawer) + " Drws|"
    elif count_drawer == 1:
        lbl_text += "1 Drw|"

    if count_shelf > 1:
        lbl_text += str(count_shelf) + " Shlvs|"
    elif count_shelf == 1:
        lbl_text += "1 Shelf|"

    if lbl_text.endswith("|"):
        lbl_text = lbl_text[:-1]

    return lbl_text

def get_product_profile_mesh(carcass_shape, name, size):
    x = size[0]
    y = size[1]
    z = size[2]
    l = size[3]
    r = -size[4]
    verts = []
    faces = {}

   
    if carcass_shape == 'DIAGONAL':
        print("diagonal")
        verts = [(0.0, 0.0, 0.0),
             (0.0, y, 0.0),
             (l, y, 0.0),
             (x, r, 0.0),
             (x, 0.0, 0.0),
             (0.0, 0.0, z),
             (0.0, y, z),
             (l, y, z),
             (x, r, z),
             (x, 0.0, z),
             ]

        faces = [(0, 1, 2, 3, 4),
                 (5, 6, 7, 8, 9),
                 (0, 1, 6, 5),
                 (1, 2, 7, 6),
                 (2, 3, 8, 7),
                 (3, 4, 9, 8),
                 (4, 0, 9, 8),
                ]

    elif carcass_shape == 'NOTCHED':
        print("notched")
        verts = [(0.0, 0.0, 0.0),
             (0.0, y, 0.0),
             (l, y, 0.0),
             (l, r, 0.0),
             (x, r, 0.0),
             (x, 0.0, 0.0),
            
             (0.0, 0.0, z),
             (0.0, y, z),
             (l, y, z),
             (l, r, z),
             (x, r, z),
             (x, 0.0, z),
             ]

        faces = [(0, 1, 2, 3, 4, 5),
                 (6, 7, 8, 9, 10, 11),
                 (0, 1, 7, 6),
                 (1, 2, 8, 7),
                 (2, 3, 9, 8),
                 (3, 4, 10, 9),
                 (4, 5, 11, 10),
                 (5, 0, 6, 11),
                ]
    else:
        print("rectangle")
        verts = [(0.0, 0.0, 0.0),
             (0.0, y, 0.0),
             (x, y, 0.0),
             (x, 0.0, 0.0),
             (0.0, 0.0, z),
             (0.0, y, z),
             (x, y, z),
             (x, 0.0, z),
             ]

        faces = [(0, 1, 2, 3),
                (4, 7, 6, 5),
                (0, 4, 5, 1),
                (1, 5, 6, 2),
                (2, 6, 7, 3),
                (4, 0, 3, 7),
                ]


    return sn_utils.create_object_from_verts_and_faces(verts, faces, name)

def add_rectangle_molding(product,is_crown=True):
    carcass = get_carcass_insert(product)
    if carcass:
        width = product.obj_x.location.x
        depth = product.obj_y.location.y
        toe_kick_setback = carcass.get_prompt("Toe Kick Setback")
        left_fin_end = carcass.get_prompt("Left Fin End")
        right_fin_end = carcass.get_prompt("Right Fin End")
        left_side_wall_filler = carcass.get_prompt("Left Side Wall Filler")
        right_side_wall_filler = carcass.get_prompt("Right Side Wall Filler")
        setback = 0
        if toe_kick_setback and is_crown == False:
            setback = toe_kick_setback.get_value()
        
        points = []
        
        #LEFT
        if left_side_wall_filler.get_value() > 0:
            points.append((-left_side_wall_filler.get_value(),depth+setback,0))
        
        elif left_fin_end.get_value() == True:
            points.append((0,0,0))
            points.append((0,depth+setback,0))
        else:
            points.append((0,depth+setback,0))
            
        #RIGHT
        if right_side_wall_filler.get_value() > 0:
            points.append((width + right_side_wall_filler.get_value(),depth+setback,0))
        
        elif right_fin_end.get_value() == True:
            points.append((width,depth+setback,0))
            points.append((width,0,0))
        else:
            points.append((width,depth+setback,0))
        
        return points
      
def add_inside_molding(product,is_crown=True,is_notched=True):
    carcass = get_carcass_insert(product)
    width = product.obj_x.location.x
    depth = product.obj_y.location.y
    toe_kick_setback = carcass.get_prompt("Toe Kick Setback")
    left_fin_end = carcass.get_prompt("Left Fin End")
    right_fin_end = carcass.get_prompt("Right Fin End")
    left_side_wall_filler = carcass.get_prompt("Left Side Wall Filler")
    right_side_wall_filler = carcass.get_prompt("Right Side Wall Filler")
    cabinet_depth_left = carcass.get_prompt("Cabinet Depth Left")
    cabinet_depth_right = carcass.get_prompt("Cabinet Depth Right")

    setback = 0
    if toe_kick_setback and is_crown == False:
        setback = toe_kick_setback.get_value()
    
    points = []
    
    #LEFT
    if left_side_wall_filler.get_value() > 0:
        points.append((cabinet_depth_left.get_value()-setback,depth-left_side_wall_filler.get_value(),0))
    
    elif left_fin_end.get_value() == True:
        points.append((0,depth,0))
        points.append((cabinet_depth_left.get_value()-setback,depth,0))
    else:
        points.append((cabinet_depth_left.get_value()-setback,depth,0))
        
    #CENTER
    if is_notched:
        points.append((cabinet_depth_left.get_value()-setback,-cabinet_depth_right.get_value()+setback,0))
        
    #RIGHT
    if right_side_wall_filler.get_value() > 0:
        points.append((width + right_side_wall_filler.get_value(),-cabinet_depth_right.get_value()+setback,0))
    
    elif right_fin_end.get_value() == True:
        points.append((width,-cabinet_depth_right.get_value()+setback,0))
        points.append((width,0,0))
    else:
        points.append((width,-cabinet_depth_right.get_value()+setback,0))
    
    return points
  
def add_transition_molding(product,is_crown=True):
    carcass = get_carcass_insert(product)
    if carcass:
        width = product.obj_x.location.x
        toe_kick_setback = carcass.get_prompt("Toe Kick Setback")
        left_fin_end = carcass.get_prompt("Left Fin End")
        right_fin_end = carcass.get_prompt("Right Fin End")
        left_side_wall_filler = carcass.get_prompt("Left Side Wall Filler")
        right_side_wall_filler = carcass.get_prompt("Right Side Wall Filler")
        cabinet_depth_left = carcass.get_prompt("Cabinet Depth Left")
        cabinet_depth_right = carcass.get_prompt("Cabinet Depth Right")
        left_side_thickness = carcass.get_prompt("Left Side Thickness")
        right_side_thickness = carcass.get_prompt("Right Side Thickness")
        
        setback = 0
        if toe_kick_setback and is_crown == False:
            setback = toe_kick_setback.get_value()
        
        points = []
        
        #LEFT
        if left_side_wall_filler.get_value() > 0:
            points.append((-left_side_wall_filler.get_value(),-cabinet_depth_left.get_value()+setback,0))
            points.append((left_side_thickness.get_value(),-cabinet_depth_left.get_value()+setback,0))
            
        elif left_fin_end.get_value() == True:
            points.append((0,0,0))
            points.append((0,-cabinet_depth_left.get_value()+setback,0))
            points.append((left_side_thickness.get_value(),-cabinet_depth_left.get_value()+setback,0))
        else:
            points.append((0,-cabinet_depth_left.get_value()+setback,0))
            points.append((left_side_thickness.get_value(),-cabinet_depth_left.get_value()+setback,0))
            
        #RIGHT
        if right_side_wall_filler.get_value() > 0:
            points.append((width - right_side_thickness.get_value() + right_side_wall_filler.get_value(),-cabinet_depth_right.get_value()+setback,0))
            points.append((width + right_side_wall_filler.get_value(),-cabinet_depth_right.get_value()+setback,0))
        
        elif right_fin_end.get_value() == True:
            points.append((width - right_side_thickness.get_value() + right_side_wall_filler.get_value(),-cabinet_depth_right.get_value()+setback,0))
            points.append((width,-cabinet_depth_right.get_value()+setback,0))
            points.append((width,0,0))
        else:
            points.append((width - right_side_thickness.get_value() + right_side_wall_filler.get_value(),-cabinet_depth_right.get_value()+setback,0))
            points.append((width,-cabinet_depth_right.get_value()+setback,0))
        
        return points

class OPERATOR_Frameless_Standard_Draw_Plan(bpy.types.Operator):
    bl_idname = "sn_cabinets.draw_plan"
    bl_label = "Draw Cabinet Plan View"
    bl_description = "Creates the plan view for cabinets"
    
    object_name: bpy.props.StringProperty(name="Object Name",default="")
    
    product = None

    left_filler_amount = 0
    right_filler_amount = 0
    cabinet_depth_left = 0
    cabinet_depth_right = 0
    carcass_shape = "RECTANGLE"
    
    def get_prompts(self):
        inserts = sn_utils.get_insert_bp_list(self.product.obj_bp,[])
        carcass_shape = ""
        for insert in inserts:
            carcass = sn_types.Assembly(insert)

            if "PROFILE_SHAPE_NOTCHED" in carcass.obj_bp:
                carcass_shape = "NOTCHED"
            elif "PROFILE_SHAPE_DIAGONAL" in carcass.obj_bp:
                carcass_shape = "DIAGONAL"
            elif "PROFILE_SHAPE_RECTANGLE" in carcass.obj_bp:
                carcass_shape = "RECTANGLE"

            left_wall_filler = carcass.get_prompt("Left Side Wall Filler")
            right_wall_filler = carcass.get_prompt("Right Side Wall Filler")
            cabinet_depth_left = carcass.get_prompt("Cabinet Depth Left")
            cabinet_depth_right = carcass.get_prompt("Cabinet Depth Right")

            if carcass_shape != "":
                self.carcass_shape = carcass_shape

            if left_wall_filler:
                self.left_filler_amount = left_wall_filler.get_value()
            if right_wall_filler:
                self.right_filler_amount = right_wall_filler.get_value()
            if cabinet_depth_left:
                self.cabinet_depth_left = cabinet_depth_left.get_value()
            if cabinet_depth_right:
                self.cabinet_depth_right = cabinet_depth_right.get_value()

                
    def execute(self, context):
        obj_bp = bpy.data.objects[self.object_name]
        
        self.product = sn_types.Assembly(obj_bp)
        self.get_prompts()
        
        assembly_mesh = get_product_profile_mesh(self.carcass_shape, self.product.obj_bp.snap.name_object,
                                            (self.product.obj_x.location.x,
                                             self.product.obj_y.location.y,
                                            self.product.obj_z.location.z,
                                             self.cabinet_depth_left,
                                             self.cabinet_depth_right))

        assembly_mesh.matrix_world = self.product.obj_bp.matrix_world
        assembly_mesh.snap.type = 'CAGE'
        
        if self.left_filler_amount > 0:
            l_filler_mesh = sn_utils.create_cube_mesh(self.product.obj_bp.snap.name_object,
                                                (-self.left_filler_amount,
                                                 sn_unit.inch(.75),
                                                 self.product.obj_z.location.z))
            l_filler_mesh.parent = assembly_mesh
            l_filler_mesh.location.y = self.product.obj_y.location.y
            
        if self.right_filler_amount > 0:
            r_filler_mesh = sn_utils.create_cube_mesh(self.product.obj_bp.snap.name_object,
                                                (self.right_filler_amount,
                                                 sn_unit.inch(.75),
                                                 self.product.obj_z.location.z))
            r_filler_mesh.parent = assembly_mesh   
            r_filler_mesh.location.x = self.product.obj_x.location.x
            r_filler_mesh.location.y = self.product.obj_y.location.y
            

        wall_bp = sn_utils.get_wall_bp(self.product.obj_bp)
        parent_rot = wall_bp.rotation_euler.z
        
        dim_lbl = sn_types.Dimension()
        dim_lbl.parent(assembly_mesh)
        scene = bpy.context.scene
        scene.snap.opengl_dim.gl_font_size = 15.5

        dim_lbl.anchor.rotation_euler = (0, -parent_rot, 0)
        dim_lbl.start_x(value=assembly_mesh.dimensions.x/2)

        assembly_above = self.product.get_adjacent_assembly(direction='ABOVE')
        if self.product.obj_bp.location.z > 1:  # if this is an upper...
            y_offset = 0.45
        elif not assembly_above:
            y_offset = 0.5
        else:
            y_offset = 0.73
        dim_lbl.start_y(value=-assembly_mesh.dimensions.y*y_offset)
        dim_lbl.start_z(value=math.fabs(assembly_mesh.dimensions.z))

        product_label = get_product_components(self.product)
        dim_lbl.set_label(product_label)


        return {'FINISHED'}

#region Old OPERATOR_Cabinet_Update
# class OPERATOR_Cabinet_Update(bpy.types.Operator):
#     bl_idname = cabinet_properties.LIBRARY_NAME_SPACE + ".update"
#     bl_label = "Cabinet Update"
#     bl_description = "Update Cabinets after being drawn"
    
#     object_name: bpy.props.StringProperty(name="Object Name",default="")
    
#     product = None
    
#     def execute(self, context):
#         print("enetring Operator_Cabinet_Update...")
#         obj_bp = bpy.data.objects[self.object_name]
        
#         self.product = sn_types.Assembly(obj_bp)
        
#         carcass = get_carcass_insert(self.product)
    

#         props = cabinet_properties.get_scene_props()
#         if self.product.obj_bp.lm_cabinets.product_sub_type == 'Base':
#             self.product.obj_y.location.y = -props.size_defaults.base_cabinet_depth
#             self.product.obj_z.location.z = props.size_defaults.base_cabinet_height
            
#         if self.product.obj_bp.lm_cabinets.product_sub_type == 'Sink':
#             self.product.obj_y.location.y = -props.size_defaults.sink_cabinet_depth
#             self.product.obj_z.location.z = props.size_defaults.sink_cabinet_height
            
#         if self.product.obj_bp.lm_cabinets.product_sub_type == 'Tall':
#             self.product.obj_y.location.y = -props.size_defaults.tall_cabinet_depth
#             self.product.obj_z.location.z = props.size_defaults.tall_cabinet_height
        
#         if self.product.obj_bp.lm_cabinets.product_sub_type == 'Upper':
#             self.product.obj_y.location.y = -props.size_defaults.upper_cabinet_depth
#             self.product.obj_z.location.z = -props.size_defaults.upper_cabinet_height
            
#             self.product.obj_bp.location.z = props.size_defaults.height_above_floor
        
#         if self.product.obj_bp.lm_cabinets.product_sub_type == 'Suspended':
#             self.product.obj_y.location.y = -props.size_defaults.suspended_cabinet_depth
#             self.product.obj_z.location.z = -props.size_defaults.suspended_cabinet_height
            
#             self.product.obj_bp.location.z = props.size_defaults.base_cabinet_height
            
#         if carcass:
#             carcass_defaults = props.carcass_defaults
#             toe_kick_height = carcass.get_prompt("Toe Kick Height")
#             toe_kick_setback = carcass.get_prompt("Toe Kick Setback")
            
#             if toe_kick_height:
#                 toe_kick_height.set_value(carcass_defaults.toe_kick_height)

#             if toe_kick_setback:
#                 toe_kick_setback.set_value(carcass_defaults.toe_kick_setback)
                
#         sn_utils.run_calculators(self.product.obj_bp)
#         return {'FINISHED'}
#endregion Old OPERATOR_Cabinet_Update

class OPERATOR_Auto_Add_Molding(bpy.types.Operator):
    bl_idname = cabinet_properties.LIBRARY_NAME_SPACE + ".auto_add_molding"
    bl_label = "Add Molding" 
    bl_options = {'UNDO'}

    molding_type: bpy.props.StringProperty(name="Molding Type")

    crown_profile = None
    base_profile = None
    
    is_base = False
    is_crown = False
    is_light_rail = False
    
    tall_cabinet_switch = sn_unit.inch(60)
    
    def get_profile(self):
        props = cabinet_properties.get_scene_props()
        if self.molding_type == 'Base':
            self.profile = sn_utils.get_object(path.join(path.dirname(__file__),
                                                      cabinet_properties.MOLDING_FOLDER_NAME,
                                                      cabinet_properties.BASE_MOLDING_FOLDER_NAME,
                                                      props.base_molding_category,
                                                      props.base_molding+".blend"))
        elif self.molding_type == 'Light':
            self.profile = sn_utils.get_object(path.join(path.dirname(__file__),
                                                      cabinet_properties.MOLDING_FOLDER_NAME,
                                                      cabinet_properties.LIGHT_MOLDING_FOLDER_NAME,
                                                      props.light_rail_molding_category,
                                                      props.light_rail_molding+".blend"))
        else:
            self.profile = sn_utils.get_object(path.join(path.dirname(__file__),
                                                      cabinet_properties.MOLDING_FOLDER_NAME,
                                                      cabinet_properties.CROWN_MOLDING_FOLDER_NAME,
                                                      props.crown_molding_category,
                                                      props.crown_molding+".blend"))

        self.profile['IS_MOLDING_PROFILE'] = True
        bpy.context.scene.collection.objects.link(self.profile)

    def get_products(self):
        products = []
        for obj in bpy.context.scene.objects:
            if obj.get("IS_BP_CABINET"):
                product = sn_types.Assembly(obj)
                products.append(product)
        return products
        
    def create_extrusion(self,points,is_crown=True,is_light_rail=False,product=None):
        if self.profile is None:
            self.get_profile()
        
        bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=False)
        obj_curve = bpy.context.active_object
        obj_curve.modifiers.new("Edge Split",type='EDGE_SPLIT')
        obj_props = cabinet_properties.get_object_props(obj_curve)
        if is_crown:
            obj_props.is_crown_molding = True
        elif is_light_rail:
            obj_props.is_light_rail_molding = True
        else:
            obj_props.is_base_molding = True
        obj_curve.data.splines.clear()
        spline = obj_curve.data.splines.new('BEZIER')
        spline.bezier_points.add(count=len(points) - 1)        
        # obj_curve.data.show_handles = False
        obj_curve.data.bevel_object = self.profile
        obj_curve.data.bevel_mode = 'OBJECT'
        obj_curve.snap.type_mesh = 'SOLIDSTOCK'
        obj_curve.snap.solid_stock = self.profile.name
        obj_curve.snap.name_object = self.molding_type + " Molding"
        obj_curve.name = self.molding_type + " Molding"
        
        bpy.ops.sn_object.add_material_slot(object_name=obj_curve.name)
        bpy.ops.sn_material.sync_material_slots(object_name=obj_curve.name)
        obj_curve.snap.material_slots[0].pointer_name = "Molding"
        
        obj_curve.location = (0,0,0)
        
        for i, point in enumerate(points):
            obj_curve.data.splines[0].bezier_points[i].co = point
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.handle_type_set(type='VECTOR')
        bpy.ops.object.editmode_toggle()
        obj_curve.data.dimensions = '2D'
        sn_utils.assign_materials_from_pointers(obj_curve)
        return obj_curve
        
    def clean_up_room(self):
        """ Removes all of the Dimensions and other objects
            That were added to the scene from this command
            We dont want multiple objects added on top of each other
            So we must clean up the scene before running this command 
        """
        objs = []
        for obj in bpy.data.objects:
            obj_props = cabinet_properties.get_object_props(obj)
            if self.is_crown:
                if obj_props.is_crown_molding == True:
                    objs.append(obj)
            elif self.is_light_rail:
                if obj_props.is_light_rail_molding == True:
                    objs.append(obj)
            else:
                if obj_props.is_base_molding == True:
                    objs.append(obj)
        sn_utils.delete_obj_list(objs)

    def set_curve_location(self,product,curve,is_crown):
        curve.parent = product.obj_bp
        if self.is_base:
            curve.location.z = 0
        elif self.is_crown:
            if product.obj_z.location.z < 0:
                curve.location.z = 0
            else:
                curve.location.z = product.obj_z.location.z
        else:
            curve.location.z = product.obj_z.location.z

        empty_assembly = sn_types.Assembly()
        empty_assembly.create_assembly()
        empty_assembly.obj_bp.snap.type_mesh = 'CUTPART'
        empty_assembly.obj_x.hide_set(True)
        empty_assembly.obj_y.hide_set(True)
        empty_assembly.obj_z.hide_set(True)
        empty_assembly.obj_bp.parent = product.obj_bp
        
        curve.parent = empty_assembly.obj_bp
        
        wall_bp = sn_utils.get_wall_bp(empty_assembly.obj_bp)
        if wall_bp:
            wall_coll = bpy.data.collections[wall_bp.snap.name_object]
            scene_coll = bpy.context.scene.collection
            sn_utils.add_assembly_to_collection(empty_assembly.obj_bp, wall_coll, recursive=True)
            sn_utils.remove_assembly_from_collection(empty_assembly.obj_bp, scene_coll, recursive=True)
            if "Collection" in bpy.data.collections:
                default_coll = bpy.data.collections["Collection"]
                sn_utils.remove_assembly_from_collection(empty_assembly.obj_bp, default_coll, recursive=True)


    def execute(self, context):
        self.is_base = True if self.molding_type == 'Base' else False
        self.is_crown = True if self.molding_type == 'Crown' else False
        self.is_light_rail = True if self.molding_type == 'Light' else False        
        
        self.clean_up_room()
        self.profile = None
        products = self.get_products()
        for product in products:
            shape = product.obj_bp.lm_cabinets.product_shape

            if (self.is_crown or self.is_light_rail) and product.obj_bp.lm_cabinets.product_sub_type == 'Base':
                continue # DONT ADD CROWN OR LIGHT RAIL MOLDING TO BASE
            
            if (self.is_crown or self.is_light_rail) and product.obj_bp.lm_cabinets.product_sub_type == 'Sink':
                continue # DONT ADD CROWN OR LIGHT RAIL MOLDING TO SINK            
            
            if self.is_light_rail and product.obj_bp.lm_cabinets.product_sub_type == 'Tall':
                continue # DONT ADD LIGHT RAIL MOLDING TO TALL            
            
            if product.obj_bp.lm_cabinets.product_sub_type == 'Suspended':
                continue # DONT ADD MOLDING TO SUSPENDED
            
            if self.is_base and product.obj_bp.lm_cabinets.product_sub_type == 'Upper':
                continue # DONT ADD BASE MOLDING TO UPPER        
            
            if shape == 'RECTANGLE':
                points = add_rectangle_molding(product,self.is_crown)
                if points:
                    curve = self.create_extrusion(points,self.is_crown,self.is_light_rail,product)
                    self.set_curve_location(product,curve,self.is_crown)
                    
            if shape == 'INSIDE_NOTCH':
                points = add_inside_molding(product,self.is_crown,True)
                if points:
                    curve = self.create_extrusion(points,self.is_crown,self.is_light_rail,product)
                    self.set_curve_location(product,curve,self.is_crown)
                
            if shape == 'INSIDE_DIAGONAL':
                points = add_inside_molding(product,self.is_crown,False)
                if points:
                    curve = self.create_extrusion(points,self.is_crown,self.is_light_rail,product)
                    self.set_curve_location(product,curve,self.is_crown)
                
            if shape == 'OUTSIDE_DIAGONAL':
                pass #TODO
            
            if shape == 'OUTSIDE_RADIUS':
                pass #TODO
            
            if shape == 'TRANSITION':
                points = add_transition_molding(product,self.is_crown)
                if points:
                    curve = self.create_extrusion(points,self.is_crown,self.is_light_rail,product)
                    self.set_curve_location(product,curve,self.is_crown)

        return {'FINISHED'}

class OPERATOR_Delete_Molding(bpy.types.Operator):
    bl_idname = cabinet_properties.LIBRARY_NAME_SPACE + ".delete_molding"
    bl_label = "Delete Molding" 
    bl_options = {'UNDO'}

    molding_type: bpy.props.StringProperty(name="Molding Type")

    def execute(self, context):
        is_crown = True if self.molding_type == 'Crown' else False
        objs = []
        for obj in context.scene.objects:
            obj_props = cabinet_properties.get_object_props(obj)
            if is_crown:
                if obj_props.is_crown_molding == True:
                    objs.append(obj)
            else:
                if obj_props.is_base_molding == True:
                    objs.append(obj)
        sn_utils.delete_obj_list(objs)
        return {'FINISHED'}
    
class OPERATOR_Update_Door_Selection(bpy.types.Operator):
    """ This will clear all the spec groups to save on file size.
    """
    bl_idname = cabinet_properties.LIBRARY_NAME_SPACE + ".update_door_selection"
    bl_label = "Update Door Selection"
    bl_description = "This will change the selected door with the active door"
    bl_options = {'UNDO'}
    
    cabinet_type: bpy.props.StringProperty(name = "Cabinet Type")
    
    #DOOR SELECTION
    current_selection = bpy.props.BoolProperty(name="Use Current Selection")
    base_doors = bpy.props.BoolProperty(name="Select all base doors")
    tall_doors = bpy.props.BoolProperty(name="Select all tall doors")
    upper_doors = bpy.props.BoolProperty(name="Select all upper doors")
    drawer_fronts = bpy.props.BoolProperty(name="Select all drawer doors")
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(400))      
    
    def draw(self, context):
        box = self.layout.box()
        split = box.split()
        
        col = split.column()
        sub = col.column()
        sub.prop(self, 'current_selection', text="Current Selection")
        sub.prop(self, 'base_doors', text="Base Doors")
        sub.prop(self, 'upper_doors', text="Upper Doors")
        
        col = split.column()
        sub = col.column()
        sub.prop(self, 'tall_doors', text="Tall Doors")
        sub.prop(self, 'drawer_fronts', text="Drawer Fronts")
        sub.prop(self, 'place_at_scene_origin')
        
    def get_door_selection(self):
        door_bps = []
        
        if self.current_selection:
            for obj in bpy.context.selected_objects:
                if obj.type == 'MESH' or 'CURVE':
                    obj_bp = sn_utils.get_assembly_bp(obj)
                    if obj_bp:
                        if obj_bp.snap.is_cabinet_door or obj_bp.snap.is_cabinet_drawer_front:
                            if obj_bp not in door_bps:
                                door_bps.append(obj_bp)
        
        if self.base_doors or self.tall_doors or self.upper_doors or self.drawer_fronts:
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH' or 'CURVE':
                    obj_bp = sn_utils.get_assembly_bp(obj)
                    if obj_bp:
                        if obj_bp.snap.is_cabinet_door:
                            product = sn_utils.get_parent_assembly_bp(obj_bp)
                            
                            if self.base_doors:
                                if product.lm_cabinets.product_sub_type in ('Base', 'Sink'):
                                    if obj_bp not in door_bps:
                                        door_bps.append(obj_bp)
                                    
                            if self.tall_doors:
                                if product.lm_cabinets.product_sub_type == 'Tall':
                                    if obj_bp not in door_bps:
                                        door_bps.append(obj_bp)    
                                    
                            if self.upper_doors:
                                if product.lm_cabinets.product_sub_type == 'Upper':
                                    if obj_bp not in door_bps:
                                        door_bps.append(obj_bp)
                                    
                        if obj_bp.snap.is_cabinet_drawer_front and self.drawer_fronts: 
                            if obj_bp not in door_bps:
                                door_bps.append(obj_bp) 
              
        return door_bps            
    
    def execute(self, context):
        props = cabinet_properties.get_scene_props()
        
        for obj_bp in self.get_door_selection():    
            door_assembly = sn_types.Assembly(obj_bp)
            
            group_bp = sn_utils.get_group(path.join(path.dirname(__file__),
                                                 cabinet_properties.DOOR_FOLDER_NAME,
                                                 props.door_category,
                                                 props.door_style+".blend"))
            new_door = sn_types.Assembly(group_bp)
            new_door.obj_bp.snap.name_object = door_assembly.obj_bp.snap.name_object
            new_door.obj_bp.parent = door_assembly.obj_bp.parent
            new_door.obj_bp.location = door_assembly.obj_bp.location
            new_door.obj_bp.rotation_euler = door_assembly.obj_bp.rotation_euler
            
            property_id = door_assembly.obj_bp.snap.property_id
            
            sn_utils.copy_drivers(door_assembly.obj_bp,new_door.obj_bp)
            sn_utils.copy_prompt_drivers(door_assembly.obj_bp,new_door.obj_bp)
            sn_utils.copy_drivers(door_assembly.obj_x,new_door.obj_x)
            sn_utils.copy_drivers(door_assembly.obj_y,new_door.obj_y)
            sn_utils.copy_drivers(door_assembly.obj_z,new_door.obj_z)
            obj_list = []
            obj_list.append(door_assembly.obj_bp)
            for child in door_assembly.obj_bp.children:
                obj_list.append(child)
            sn_utils.delete_obj_list(obj_list)
            
            new_door.obj_bp.snap.property_id = property_id
            new_door.obj_bp.snap.is_cabinet_door = True
            for child in new_door.obj_bp.children:
                child.snap.property_id = property_id
                if child.type == 'EMPTY':
                    child.hide
                if child.type == 'MESH':
                    child.draw_type = 'TEXTURED'
                    child.snap.comment = props.door_style
                    sn_utils.assign_materials_from_pointers(child)
                if child.snap.type == 'CAGE':
                    child.hide = True
                    
        return {'FINISHED'}

class OPERATOR_Update_Pull_Selection(bpy.types.Operator):
    bl_idname = cabinet_properties.LIBRARY_NAME_SPACE + ".update_pull_selection"
    bl_label = "Change Pulls"
    bl_description = "This will update all of the door pulls that are currently selected"
    bl_options = {'UNDO'}
    
    update_all = bpy.props.BoolProperty(name="Update All",default=False)
    
    def execute(self, context):
        props = cabinet_properties.get_scene_props()
        pulls = []
        
        if self.update_all:
            for obj in context.scene.objects:
                if obj.snap.is_cabinet_pull == True:
                    pulls.append(obj)
        else:
            for obj in context.selected_objects:
                if obj.snap.is_cabinet_pull == True:
                    pulls.append(obj)
                
        for pull in pulls:
            pull_assembly = sn_types.Assembly(pull.parent)
            pull_assembly.set_name(props.pull_name)
            pull_length = pull_assembly.get_prompt("Pull Length")
            new_pull = sn_utils.get_object(path.join(path.dirname(__file__),
                                                  cabinet_properties.PULL_FOLDER_NAME,
                                                  props.pull_category,
                                                  props.pull_name+".blend"))
            new_pull.snap.is_cabinet_pull = True
            new_pull.snap.name_object = pull.snap.name_object
            new_pull.snap.comment = props.pull_name
            new_pull.parent = pull.parent
            new_pull.location = pull.location
            new_pull.rotation_euler = pull.rotation_euler
            sn_utils.assign_materials_from_pointers(new_pull)
            pull_length.set_value(new_pull.dimensions.x)
            sn_utils.copy_drivers(pull,new_pull)
        sn_utils.delete_obj_list(pulls)
        return {'FINISHED'}

class OPERATOR_Update_Column_Selection(bpy.types.Operator):
    bl_idname = cabinet_properties.LIBRARY_NAME_SPACE + ".update_column_selection"
    bl_label = "Update Column"
    bl_description = "This will change the selected column style with the active column style"
    bl_options = {'UNDO'}
    
    column_type: bpy.props.StringProperty(name = "Column Type")
    
    def execute(self, context):
        props = cabinet_properties.get_scene_props()
        
        col_bps = []
        for obj in context.selected_objects:
            obj_bp = sn_utils.get_assembly_bp(obj)
            obj_props = cabinet_properties.get_object_props(obj_bp)
            if obj_props.is_column and obj_bp not in col_bps:
                col_bps.append(obj_bp)
        
        for obj_bp in col_bps:
            column_assembly = sn_types.Assembly(obj_bp)      
    
            new_column_bp = sn_utils.get_group(path.join(path.dirname(__file__),cabinet_properties.COLUMN_FOLDER_NAME,props.column_category,props.column_style+".blend"))
            new_column = sn_types.Assembly(new_column_bp)
            obj_props = cabinet_properties.get_object_props(new_column.obj_bp)
            obj_props.is_column = True
            new_column.obj_bp.snap.name_object = column_assembly.obj_bp.snap.name_object
            new_column.obj_bp.parent = column_assembly.obj_bp.parent
            new_column.obj_bp.location = column_assembly.obj_bp.location
            new_column.obj_bp.rotation_euler = column_assembly.obj_bp.rotation_euler
            
            property_id = column_assembly.obj_bp.snap.property_id
            
            sn_utils.copy_drivers(column_assembly.obj_bp,new_column.obj_bp)
            sn_utils.copy_prompt_drivers(column_assembly.obj_bp,new_column.obj_bp)
            sn_utils.copy_drivers(column_assembly.obj_x,new_column.obj_x)
            sn_utils.copy_drivers(column_assembly.obj_y,new_column.obj_y)
            sn_utils.copy_drivers(column_assembly.obj_z,new_column.obj_z)
            obj_list = []
            obj_list.append(column_assembly.obj_bp)
            for child in column_assembly.obj_bp.children:
                obj_list.append(child)
            sn_utils.delete_obj_list(obj_list)
    
            new_column.obj_bp.snap.property_id = property_id
            for child in new_column.obj_bp.children:
                child.snap.property_id = property_id
                if child.type == 'EMPTY':
                    child.hide
                if child.type == 'MESH':
                    child.draw_type = 'TEXTURED'
                    sn_utils.assign_materials_from_pointers(child)
                if child.snap.type == 'CAGE':
                    child.hide = True

        return {'FINISHED'}
        
class OPERATOR_Place_Applied_Panel(bpy.types.Operator):
    bl_idname = cabinet_properties.LIBRARY_NAME_SPACE + ".place_applied_panel"
    bl_label = "Place Applied Panel"
    bl_description = "This will allow you to place the active panel on cabinets and closets for an applied panel"
    bl_options = {'UNDO'}
    
    #READONLY
    filepath: bpy.props.StringProperty(name="Material Name")
    type_insert: bpy.props.StringProperty(name="Type Insert")
    
    item_name = None
    dir_name = ""
    
    assembly = None
    
    cages = []
    
    def get_panel(self,context):
        props = cabinet_properties.get_scene_props()
        bp = sn_utils.get_group(path.join(path.dirname(__file__),
                                       cabinet_properties.DOOR_FOLDER_NAME,
                                       props.door_category,
                                       props.door_style+".blend"))
        self.assembly = sn_types.Assembly(bp)
        
    def set_xray(self,turn_on=True):
        cages = []
        for child in self.assembly.obj_bp.children:
            child.show_x_ray = turn_on
            if turn_on:
                child.draw_type = 'WIRE'
            else:
                if child.snap.type == 'CAGE':
                    cages.append(child)
                child.draw_type = 'TEXTURED'
                sn_utils.assign_materials_from_pointers(child)
        sn_utils.delete_obj_list(cages)

    def invoke(self, context, event):
        self.get_panel(context)
        context.window.cursor_set('PAINT_BRUSH')
        context.scene.update() # THE SCENE MUST BE UPDATED FOR RAY CAST TO WORK
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel_drop(self,context,event):
        if self.assembly:
            sn_utils.delete_object_and_children(self.assembly.obj_bp)
        bpy.context.window.cursor_set('DEFAULT')
        sn_utils.delete_obj_list(self.cages)
        return {'FINISHED'}

    def add_to_left(self,part,product):
        self.assembly.obj_bp.parent = product.obj_bp
        
        toe_kick_height = 0
        if product.get_prompt('Toe Kick Height'):
            toe_kick_height = product.get_prompt('Toe Kick Height')
        
        if product.obj_z.location.z > 0:
            self.assembly.obj_bp.location = (0,0,toe_kick_height)
        else:
            self.assembly.obj_bp.location = (0,0,product.obj_z.location.z)
        
        self.assembly.obj_bp.rotation_euler = (0,math.radians(-90),0)
        self.assembly.obj_x.location.x = math.fabs(product.obj_z.location.z) - toe_kick_height
        self.assembly.obj_y.location.y = product.obj_y.location.y
    
    def add_to_right(self,part,product):
        self.assembly.obj_bp.parent = product.obj_bp
        
        toe_kick_height = 0
        if product.get_prompt('Toe Kick Height'):
            toe_kick_height = product.get_prompt('Toe Kick Height')
        
        if product.obj_z.location.z > 0:
            self.assembly.obj_bp.location = (product.obj_x.location.x,0,toe_kick_height)
        else:
            self.assembly.obj_bp.location = (product.obj_x.location.x,0,product.obj_z.location.z)
            
        self.assembly.obj_bp.rotation_euler = (0,math.radians(-90),math.radians(180))
        self.assembly.obj_x.location.x = math.fabs(product.obj_z.location.z) - toe_kick_height
        self.assembly.obj_y.location.y = math.fabs(product.obj_y.location.y)
        
    def add_to_back(self,part,product):
        self.assembly.obj_bp.parent = product.obj_bp
        
        toe_kick_height = 0
        if product.get_prompt('Toe Kick Height'):
            toe_kick_height = product.get_prompt('Toe Kick Height').get_value()
        
        if product.obj_z.location.z > 0:
            self.assembly.obj_bp.location = (0,0,toe_kick_height)
        else:
            self.assembly.obj_bp.location = (0,0,product.obj_z.location.z)
            
        self.assembly.obj_bp.rotation_euler = (0,math.radians(-90),math.radians(-90))
        self.assembly.obj_x.location.x = math.fabs(product.obj_z.location.z) - toe_kick_height
        self.assembly.obj_y.location.y = product.obj_x.location.x
    
    def door_panel_drop(self,context,event):
        selected_point, selected_obj = sn_utils.get_selection_point(context,event,objects=self.cages)
        bpy.ops.object.select_all(action='DESELECT')
        sel_product_bp = sn_utils.get_bp(selected_obj,'PRODUCT')
        sel_assembly_bp = sn_utils.get_assembly_bp(selected_obj)

        if sel_product_bp and sel_assembly_bp:
            product = sn_types.Assembly(sel_product_bp)
            assembly = sn_types.Assembly(sel_assembly_bp)
            if product and assembly and 'Door' not in assembly.obj_bp.snap.name_object:
                self.assembly.obj_bp.parent = None
                if product.placement_type == 'Corner':
                    pass
                    #TODO: IMPLEMENT CORNER PLACEMENT
                else:
                    if 'Left' in assembly.obj_bp.snap.name_object:
                        self.add_to_left(assembly,product)
                    if 'Right' in assembly.obj_bp.snap.name_object:
                        self.add_to_right(assembly,product)
                    if 'Back' in assembly.obj_bp.snap.name_object:
                        self.add_to_back(assembly,product)
        else:
            self.assembly.obj_bp.parent = None
            self.assembly.obj_bp.location = selected_point

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.set_xray(False)
            sn_utils.delete_obj_list(self.cages)
            bpy.context.window.cursor_set('DEFAULT')
            if event.shift:
                self.get_panel(context)
            else:
                bpy.ops.object.select_all(action='DESELECT')
                context.scene.objects.active = self.assembly.obj_bp
                self.assembly.obj_bp.select = True
                return {'FINISHED'}
        
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
        
        if event.type in {'ESC'}:
            self.cancel_drop(context,event)
            return {'FINISHED'}
        
        return self.door_panel_drop(context,event)

bpy.utils.register_class(OPERATOR_Frameless_Standard_Draw_Plan)
#bpy.utils.register_class(OPERATOR_Cabinet_Update)
bpy.utils.register_class(OPERATOR_Auto_Add_Molding)
bpy.utils.register_class(OPERATOR_Delete_Molding)
bpy.utils.register_class(OPERATOR_Update_Door_Selection)
bpy.utils.register_class(OPERATOR_Update_Pull_Selection)
bpy.utils.register_class(OPERATOR_Update_Column_Selection)
bpy.utils.register_class(OPERATOR_Place_Applied_Panel)