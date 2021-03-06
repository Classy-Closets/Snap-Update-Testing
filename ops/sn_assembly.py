import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from snap import sn_types
from snap import sn_utils
from snap import sn_unit
import bmesh
import math


class SN_ASSY_OT_create_new_assembly(Operator):
    bl_idname = "sn_assembly.create_new_assembly"
    bl_label = "Create New Assembly"
    bl_description = "This will create a new assembly"
    bl_options = {'UNDO'}

    assembly_name: StringProperty(name="Assembly Name", default="New Assembly")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        assembly = sn_types.Assembly()
        assembly.create_assembly(self.assembly_name)
        assembly.obj_x.location.x = 1
        assembly.obj_y.location.y = 1
        assembly.obj_z.location.z = 1
        assembly.obj_bp.select_set(True)
        assembly.obj_bp["ID_PROMPT"] = "sn_assembly.show_properties"
        context.view_layer.objects.active = assembly.obj_bp
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Enter the name of the assembly to add.")
        layout.prop(self, 'assembly_name')


class SN_ASSY_OT_delete_assembly(Operator):
    bl_idname = "sn_assembly.delete_assembly"
    bl_label = "Delete Assembly"
    bl_description = "This will delete the assembly"
    bl_options = {'UNDO'}

    assembly_name: StringProperty(name="Assembly Name", default="New Assembly")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        assembly = sn_types.Assembly()
        assembly.create_assembly()
        assembly.obj_x.location.x = 1
        assembly.obj_y.location.y = 1
        assembly.obj_z.location.z = 1
        assembly.obj_bp.select_set(True)
        context.view_layer.objects.active = assembly.obj_bp
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Are you sure you want to delete the assembly?")
        layout.label(text=self.assembly_name)


class SN_ASSY_OT_add_object(Operator):
    bl_idname = "sn_assembly.add_object"
    bl_label = "Add Object to Assembly"
    bl_description = "This will add a new object to the assembly"
    bl_options = {'UNDO'}

    assembly_name: StringProperty(name="Assembly Name", default="New Assembly")

    object_name: StringProperty(name="Object Name", default="New Object")
    object_type: bpy.props.EnumProperty(name="Object Type",
                                        items=[('MESH', "Mesh", "Add an Mesh Object"),
                                               ('EMPTY', "Empty", "Add an Empty Object"),
                                               ('CURVE', "Curve", "Add an Curve Object"),
                                               ('LIGHT', "Light", "Add an Light Object")],
                                        default='MESH')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj_bp = sn_utils.get_assembly_bp(context.object)
        assembly = sn_types.Assembly(obj_bp=obj_bp)
        if self.object_type == 'EMPTY':
            assembly.add_empty(self.object_name)

        if self.object_type == 'MESH':
            obj_mesh = sn_utils.create_cube_mesh(self.object_name, (assembly.obj_x.location.x,
                                                                    assembly.obj_y.location.y,
                                                                    assembly.obj_z.location.z))

            if 'ID_PROMPT' in assembly.obj_bp:
                obj_mesh['ID_PROMPT'] = assembly.obj_bp['ID_PROMPT']

            assembly.add_object(obj_mesh)

            # MAKE NORMALS CONSISTENT
            context.view_layer.objects.active = obj_mesh
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.editmode_toggle()

        if self.object_type == 'CURVE':
            curve = bpy.data.curves.new(self.object_name, 'CURVE')
            obj_curve = bpy.data.objects.new(self.object_name, curve)
            spline = obj_curve.data.splines.new('BEZIER')
            spline.bezier_points.add(count=1)
            obj_curve.data.splines[0].bezier_points[0].co = (0, 0, 0)
            obj_curve.data.splines[0].bezier_points[1].co = (assembly.obj_x.location.x, 0, 0)
            assembly.add_object(obj_curve)
        if self.object_type == 'LIGHT':
            pass  # TODO:
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'object_type', expand=True)
        layout.prop(self, 'object_name')


class SN_ASSY_OT_connect_mesh_to_hooks_in_assembly(Operator):
    bl_idname = "sn_assembly.connect_meshes_to_hooks_in_assembly"
    bl_label = "Connect Mesh to Hooks In Assembly"
    bl_description = "This connects all mesh hooks to a mesh"
    bl_options = {'UNDO'}

    obj_name: StringProperty(name="Object Name")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = bpy.data.objects[self.obj_name]
        obj_bp = sn_utils.get_assembly_bp(obj)
        if obj_bp:
            hooklist = []

            for child in obj_bp.children:
                if child.type == 'EMPTY' and 'obj_prompts' not in child:
                    hooklist.append(child)

            if obj.mode == 'EDIT':
                bpy.ops.object.editmode_toggle()

            sn_utils.apply_hook_modifiers(context, obj)
            for vgroup in obj.vertex_groups:
                for hook in hooklist:
                    if vgroup.name == hook.name:
                        sn_utils.hook_vertex_group_to_object(obj, vgroup.name, hook)

            obj.lock_location = (True, True, True)

        return {'FINISHED'}


class SN_ASSY_OT_create_assembly_script(Operator):
    bl_idname = "sn_assembly.create_assembly_script"
    bl_label = "Create Assembly Script"
    bl_description = "This will create a script of the selected assembly. This is in development."
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = context.object
        coll = sn_utils.get_assembly_collection(obj)
        assembly = sn_types.Assembly(obj_bp=coll)

        # Create New Script
        text = bpy.data.texts.new(coll.name)

        # Add Imports
        text.write('import bpy\n')
        # Figure out how to import bp_types

        # Add Class Def
        text.write('class ' + coll.name + '(bp_types.Assembly):\n')
        text.write('    def draw(self):\n')
        text.write('    self.create_assembly()\n')

        # Add Prompts
        for prompt in assembly.obj_prompts.prompt_page.prompts:
            pass

        # Add Empty Objects Except Built-in Assembly Objects
        # for obj in assembly.empty_objs:
        for obj in assembly.obj_bp.children:
            if obj.type == 'EMPTY':
                pass  # Assign Drivers and Constraints

        # Add Mesh Objects This needs to be done after empties for hooks
        # for obj in assembly.mesh_objs:
        for obj in assembly.obj_bp.children:
            pass
        return {'FINISHED'}


class SN_ASSY_OT_select_parent_assembly(bpy.types.Operator):
    bl_idname = "sn_assembly.select_parent"
    bl_label = "Select Parent Assembly"
    bl_description = "This selects the parent assembly"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj_bp = sn_utils.get_assembly_bp(context.object)
        if obj_bp and obj_bp.parent:
            return True
        else:
            return False

    def select_children(self, obj):
        obj.select_set(True)
        for child in obj.children:
            child.select_set(True)
            self.select_children(child)

    def execute(self, context):
        obj_bp = sn_utils.get_assembly_bp(context.object)
        assembly = sn_types.Assembly(obj_bp=obj_bp)

        if assembly:
            if assembly.obj_bp.parent:
                assembly.obj_bp.parent.select_set(True)
                context.view_layer.objects.active = assembly.obj_bp.parent

                self.select_children(assembly.obj_bp.parent)

        return {'FINISHED'}


classes = (
    SN_ASSY_OT_create_new_assembly,
    SN_ASSY_OT_delete_assembly,
    SN_ASSY_OT_add_object,
    SN_ASSY_OT_connect_mesh_to_hooks_in_assembly,
    SN_ASSY_OT_create_assembly_script,
    SN_ASSY_OT_select_parent_assembly,
)

register, unregister = bpy.utils.register_classes_factory(classes)
