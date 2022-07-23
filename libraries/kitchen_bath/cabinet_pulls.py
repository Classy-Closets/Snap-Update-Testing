import bpy
import os
import math
from snap import sn_types, sn_utils, sn_unit
from . import cabinet_properties
from snap.libraries.closets import closet_paths, closet_props

class Standard_Pull(sn_types.Assembly):
    
    library_name = "Cabinet Doors"
    type_assembly = "INSERT"
    
    door_type = "" # Base, Tall, Upper, Sink, Suspended
    door_swing = "" # Left Swing, Right Swing, Double Door, Flip up

    pull_name = ""

    def draw(self):
        props = bpy.context.scene.sn_closets.closet_options
        self.create_assembly()

        self.pull_name = props.pull_name
        
        # TODO does kichen need separate pull selection?
        # pull = self.add_object(os.path.join(os.path.dirname(__file__),
        #                                     cabinet_properties.PULL_FOLDER_NAME,
        #                                     props.pull_category,
        #                                     self.pull_name+".blend"))

        pull = self.add_object_from_file(
            os.path.join(
                closet_paths.get_root_dir(),
                closet_props.PULL_FOLDER_NAME,
                props.pull_category,
                props.pull_name + ".blend"))
        
        ppt_obj_pull_z = self.add_prompt_obj("Pull_Z_Location")
        self.add_prompt("Hide",'CHECKBOX',False)
        self.add_prompt("Pull Length",'DISTANCE',pull.dimensions.x)
        self.add_prompt("Pull X Location",'DISTANCE',0)
        self.add_prompt("Pull Z Location", 'DISTANCE', 0, prompt_obj=ppt_obj_pull_z)
        self.add_prompt("Pull Rotation",'ANGLE',0)
        self.add_prompt("Pull Quantity",'QUANTITY',1)
        
        Width = self.obj_x.snap.get_var("location.x","Width")
        Height = self.obj_z.snap.get_var("location.z","Height")
        Depth = self.obj_y.snap.get_var("location.y","Depth")
        Pull_X_Location = self.get_prompt("Pull X Location").get_var()
        Pull_Z_Location = self.get_prompt("Pull Z Location").get_var()
        Hide = self.get_prompt("Hide").get_var()
        
        pull.name = props.pull_name
        pull.snap.name_object = props.pull_name
        pull.snap.type_mesh = "HARDWARE"
        pull.snap.is_cabinet_pull = True
        pull.snap.comment = self.pull_name

        pull.snap.loc_x('Width-Pull_Z_Location',[Width,Pull_Z_Location])
        pull.snap.loc_y('Depth+IF(Depth<0,Pull_X_Location,-Pull_X_Location)',[Depth,Pull_X_Location,Pull_Z_Location])
        pull.snap.loc_z('Height',[Height])
        pull.snap.rot_x(value=math.radians(-90))
        if self.door_swing == 'Left Swing':
            pull.snap.rot_z(value=math.radians(180))
        # pull.material("Cabinet_Pull_Finish")
        pull.snap.hide('Hide',[Hide])

        spec_group = bpy.context.scene.snap.spec_groups[pull.snap.spec_group_index]
        for mat_pointer in spec_group.materials:
            if mat_pointer.name == "Pull_Finish":
                mat_pointer.category_name = "Finished Metals"
                mat_pointer.item_name = props.pull_category
        self.set_material_pointers('Pull_Finish')

        # self.update()