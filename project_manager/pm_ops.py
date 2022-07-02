import bpy
import os
import re
import shutil
from snap import sn_utils
import pathlib
from distutils.dir_util import copy_tree
import xml.etree.ElementTree as ET
from copy import deepcopy
import subprocess
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty)
from shutil import copyfile

from . import pm_utils, pm_props


class SNAP_OT_Copy_Room(Operator):
    bl_idname = "product_manager.copy_room"
    bl_label = "Copies the selected Room"
    bl_description = "Copies selected Room"

    file_path: StringProperty(name="File Path", description="Room File Path", subtype="FILE_PATH")
    new_room_name: StringProperty(name="Room Name", description="Room Name", default="")
    src_room = None
    new_room = None

    def register_room_in_xml(self):
        project_root, room_file = os.path.split(self.file_path)
        project_name = os.path.split(project_root)[1]
        room_relative_path = os.path.join(project_name, room_file)
        xml_path = os.path.join(project_root, '.snap', project_name + '.ccp')

        xml = ET.parse(xml_path)
        room_node = None

        rooms_node = xml.findall('.//Rooms')[0]
        for i, room in enumerate(rooms_node):
            if room.attrib['path'] == room_relative_path:
                room_node = room
                index = i
                break

        new_attrib = deepcopy(room_node.attrib)
        new_attrib['name'] = self.new_room.file_name
        new_attrib['path'] = os.path.join(project_name, self.new_room.file_name + '.blend')
        new_element = ET.Element('Room', attrib=new_attrib)
        new_element.text = new_attrib['name']
        rooms_node.insert(index + 1, new_element)
        xml.write(xml_path)

    def invoke(self, context, event):
        wm = context.window_manager

        proj_wm = wm.sn_project
        project = proj_wm.projects[proj_wm.project_index]
        self.src_room = project.rooms[project.room_index]
        self.new_room_name = self.src_room.name + " - Copy"
        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(400))

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="'{}'".format(self.src_room.name))
        col.separator()
        col.label(text="New Room Name:")
        col.prop(self, "new_room_name", text="")

    def execute(self, context):
        props = context.window_manager.sn_project

        # only really necessary when the user copies the current room
        if len(bpy.data.filepath) > 0:
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)

        clean_room_name = pm_props.CollectionMixIn().get_clean_name(self.new_room_name)
        new_filepath = os.path.join(os.path.dirname(self.file_path), clean_room_name) + ".blend"

        if len(props.projects) > 0:
            project = props.projects[props.project_index]
            self.new_room = project.add_room_from_file(self.new_room_name, new_filepath)
            project.main_tabs = 'ROOMS'

        new_path = os.path.join(os.path.dirname(self.new_room.file_path), self.new_room.file_name + ".blend")
        copyfile(self.file_path, new_path)
        self.register_room_in_xml()
        bpy.ops.wm.open_mainfile(filepath=new_path)
        return {'FINISHED'}


class SNAP_OT_Create_Project(Operator):
    """ This will create a project.
    """
    bl_idname = "project_manager.create_project"
    bl_label = "Create New Project"
    bl_description = "Creates a project"

    project_name: StringProperty(name="Project Name", description="Project Name", default="New Project")

    def listdir(self, path):
        return [d for d in os.listdir(path) if os.path.isdir(d)]

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(400))

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        row = col.row()
        row.label(text="Project Name:")
        row.prop(self, "project_name", text="")

    def execute(self, context):
        wm = context.window_manager.sn_project
        pm_props.create_project_flag = True

        if self.project_name == "":
            return {'FINISHED'}

        if re.compile("[@_!#$'%^&*()<>?/\|}{~:]").search(self.project_name) == None:
            proj = wm.projects.add()
            proj.init(self.project_name.strip())

            for index, project in enumerate(wm.projects):
                if project.name == self.project_name:
                    wm.project_index = index
            pm_props.create_project_flag = False
            return {'FINISHED'}
        else:
            bpy.ops.snap.log_window(
                "INVOKE_DEFAULT",
                message="Project Name Error",
                message2="Project Name CANNOT contain: [@_!#$'%^&*()<>?/\|}{~:]",
                icon="ERROR",
                width=400)
            return {'FINISHED'}


class SNAP_OT_Copy_Project(Operator):
    """ This will copy a project.
    """
    bl_idname = "project_manager.copy_project"
    bl_label = "Copy Project"
    bl_description = "Copies a project"

    project_name: StringProperty(name="Project Name", description="Project Name", default="New Project")
    index: IntProperty(name="Project Index")
    source_project = None

    @classmethod
    def poll(cls, context):
        wm = context.window_manager.sn_project
        return len(wm.projects) > 0

    def invoke(self, context, event):
        wm = context.window_manager
        proj_wm = wm.sn_project
        self.source_project = proj_wm.projects[proj_wm.project_index]
        self.project_name = self.source_project.name + " - Copy"
        return wm.invoke_props_dialog(self, width=sn_utils.get_prop_dialog_width(400))

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="'{}'".format(self.source_project.name))
        col.separator()
        col.label(text="New Project Name:")
        col.prop(self, "project_name", text="")

    def update_project_file(self, project_path):
        """Update .ccp"""
        ccp_path = os.path.join(project_path, ".snap", self.source_project.name + ".ccp")
        new_ccp_path = os.path.join(project_path, ".snap", self.project_name + ".ccp")

        # Rename copied .ccp
        if os.path.exists(ccp_path):
            os.rename(ccp_path, new_ccp_path)

        # Update name in .ccp
        if os.path.exists(new_ccp_path):
            tree = ET.parse(new_ccp_path)
            root = tree.getroot()

            for elm in root.findall("ProjectInfo"):
                items = list(elm)

                for item in items:
                    if item.tag == 'name':
                        item.text = self.project_name

            # Update room filepaths
            for elm in root.findall("Rooms"):
                items = list(elm)

                for item in items:
                    bfile_path = pathlib.Path(item.attrib['path'])
                    new_path = os.path.join(self.project_name, bfile_path.parts[-1])
                    item.attrib['path'] = new_path

            tree.write(new_ccp_path)

    def execute(self, context):
        wm = context.window_manager.sn_project

        if not self.project_name:
            return {'FINISHED'}

        # Check if project name exists
        existing_project = wm.projects.get(self.project_name)
        if existing_project:
            bpy.ops.snap.message_box(
                'INVOKE_DEFAULT',
                message="Cannot create project that already exists: '{}'".format(existing_project.name))
            return {'FINISHED'}

        # Copy project
        dst_path = os.path.join(self.source_project.dir_path, "..", self.project_name)
        shutil.copytree(self.source_project.dir_path, dst_path)
        self.update_project_file(dst_path)
        hidden_dir = os.path.join(dst_path, ".snap")
        if os.path.exists(hidden_dir):
            pm_utils.set_file_attr_hidden(hidden_dir)

        # Reload projects and set index to copied project
        pm_utils.reload_projects()

        for index, project in enumerate(wm.projects):
            if project.name == self.project_name:
                wm.project_index = index

        return {'FINISHED'}


class SNAP_OT_Import_Project(Operator):
    """ This will import a project.
    """
    bl_idname = "project_manager.import_project"
    bl_label = "Import Project"
    bl_description = "Imports a project"

    filename: StringProperty(name="Project File Name", description="Project file name to import")
    filepath: StringProperty(name="Project Path", description="Project path to import", subtype="FILE_PATH")
    directory: StringProperty(name="Project File Directory Name", description="Project file directory name")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if pathlib.Path(self.filename).suffix == ".ccp":
            copy_tree(self.directory, os.path.join(pm_utils.get_project_dir(), self.filename.split('.')[0]))
            pm_utils.reload_projects()

        return {'FINISHED'}


class SNAP_OT_Unarchive_Project(Operator):
    """ This will unarchive a project.
    """
    bl_idname = "project_manager.unarchive_project"
    bl_label = "Unarchive Project"
    bl_description = "Unarchives a project"

    filename: StringProperty(name="Project File Name", description="Project file name to import")
    filepath: StringProperty(name="Project Path", description="Project path to import", subtype="FILE_PATH")
    directory: StringProperty(name="Project File Directory Name", description="Project file directory name")

    def invoke(self, context, event):
        self.filepath = os.path.join(os.path.expanduser("~"), "Documents", "SNaP Archived Projects", "")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        import zipfile
        if pathlib.Path(self.filename).suffix == ".zip":
            with zipfile.ZipFile(os.path.join(pm_utils.get_archive_dir(), self.filename), "r") as zip_ref:
                zip_ref.extractall(os.path.join(pm_utils.get_project_dir(), self.filename.split('.')[0]))
                pm_utils.reload_projects()

        if os.path.exists(os.path.join(pm_utils.get_project_dir(), self.filename.split('.')[0])):
            os.remove(os.path.join(pm_utils.get_archive_dir(), self.filename))
        return {'FINISHED'}


class SNAP_OT_Delete_Project(Operator):
    bl_idname = "project_manager.delete_project"
    bl_label = "Delete Project"
    bl_options = {'UNDO'}

    index: IntProperty(name="Project Index")

    archive_project: BoolProperty(name="No, send to an archived folder",
                                          default=False,
                                          description="Archive project to zipped folder")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column()

        props = context.window_manager.sn_project
        proj = props.projects[self.index]

        col.label(text="'{}'".format(proj.name))
        col.label(text="Are you sure you want to delete this project?")
        col.prop(self,'archive_project',text="Archive Project upon removal")

    def execute(self, context):
        props = context.window_manager.sn_project
        proj = props.projects[self.index]
        cleaned_name = proj.get_clean_name(proj.name)
        proj.proj_dir = os.path.join(pm_utils.get_project_dir(), cleaned_name)
        rbin_path = os.path.join(os.path.expanduser("~"), "Documents", "SNaP Projects Recycle Bin")
        rbin_proj_path = os.path.join(rbin_path, cleaned_name)
        archive_path = os.path.join(os.path.expanduser("~"), "Documents", "SNaP Archived Projects")
        props.projects.remove(self.index)
        props.project_index = 0

        if os.path.exists(rbin_proj_path):
            shutil.rmtree(rbin_proj_path)

        if not os.path.exists(rbin_path):
            os.mkdir(rbin_path)

        if self.archive_project:
            # import zipfile
            if os.path.isfile(os.path.join(archive_path, cleaned_name + ".zip")):
                os.remove(os.path.join(archive_path, cleaned_name + ".zip"))
            if not os.path.exists(archive_path):
                os.mkdir(archive_path)
            shutil.move(shutil.make_archive(proj.proj_dir, 'zip', proj.proj_dir), archive_path)

        shutil.move(proj.proj_dir, rbin_path)

        return {'FINISHED'}


class SNAP_OT_Add_Room(Operator):
    """ This will add a room to the active project.
    """
    bl_idname = "project_manager.add_room"
    bl_label = "Add Room"
    bl_description = "Adds a room to the active project"

    room_name: StringProperty(name="Room Name", description="Room Name")
    room_category: EnumProperty(name="Room Category",
                                description="Select the Category of the Room",
                                items=[
                                    ("Please Select", "REQUIRED Please Select a Category",
                                    "Please Select a Category"),
                                    ("FG-CLST", "Closet", "Closet"),
                                    ("FG-ENTC", "Entertainment Center", "Entertainment Center"),
                                    ("FG-GARG", "Garage", "Garage"),
                                    ("FG-HMOF", "Home Office", "Home Office"),
                                    ("FG-LNDY", "Laundry", "Laundry"),
                                    ("FG-MDRM", "Mud Room", "Mud Room"),
                                    ("FG-PNTY", "Pantry", "Pantry"),
                                    ("FG-KITN", "Kitchen", "Kitchen"),
                                    ("FG-BATH", "Bathroom", "Bathroom"),
                                    ("FG-RFCE", "Reface", "Reface"),
                                    ("FG-RMDL", "Remodel", "Remodel"),
                                    ("FG-STNE", "Stone", "Stone"),
                                    ("FG-SPEC", "Specialty", "Specialty"),
                                    ("FG-COMM", "Commercial", "Commercial"),
                                    ("FG-CMSS", "Commercial Solid Surface", "Commercial Solid Surface"),
                                    ("FG-CMST", "Commercial Stone", "Commercial Stone")])

    def execute(self, context):
        props = context.window_manager.sn_project

        if re.compile("[@_!#$'%^&*()<>?/\|}{~:]").search(self.room_name) == None:
            if len(props.projects) > 0:
                project = props.projects[props.project_index]
                project.add_room(self.room_name)
                project.main_tabs = 'ROOMS'
            return {'FINISHED'}
        else:
            bpy.ops.snap.log_window(
                "INVOKE_DEFAULT",
                message="Room Name Error",
                message2="Room Name CANNOT contain: [@_!#$'%^&*()<>?/\|}{~:]",
                icon="ERROR",
                width=400)
            return {'FINISHED'}


class SNAP_OT_Open_Room(Operator):
    """ This will open room .blend file.
    """
    bl_idname = "project_manager.open_room"
    bl_label = "Open Room"
    bl_description = "Opens a room file"

    file_path: StringProperty(name="File Path", description="Room File Path", subtype="FILE_PATH")

    def execute(self, context):
        props = context.window_manager.sn_project

        if len(props.projects) > 0:
            project = props.projects[props.project_index]

        room_path = os.path.join(project.dir_path, os.path.basename(self.file_path))
        bpy.ops.wm.open_mainfile(filepath=room_path)
        sn_utils.update_accordions_prompt()
        sn_utils.fetch_mainscene_walls()

        return {'FINISHED'}


class SNAP_OT_Delete_Room(Operator):
    bl_idname = "project_manager.delete_room"
    bl_label = "Delete Room"
    bl_options = {'UNDO'}

    room_name: StringProperty(name="Room Name", description="Room Name")
    index: IntProperty(name="Project Index")
    invoke_default: BoolProperty(name="Invoke Default", default=False)

    def invoke(self, context, event):
        wm = context.window_manager
        self.invoke_default = True
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column()

        props = context.window_manager.sn_project
        proj = props.projects[props.project_index]
        room = proj.rooms[self.index]

        col.label(text="'{}'".format(room.name))
        col.label(text="Are you sure you want to delete this room?")

    def execute(self, context):
        props = context.window_manager.sn_project
        # if there is no project active, skip
        if len(props.projects) == 0:
            return {'FINISHED'}

        if not self.invoke_default:
            proj = props.projects[props.current_file_project]
            room = proj.rooms[props.current_file_room]
            self.room_name = room.name
            for i, room in enumerate(proj.rooms):
                if room.name == self.room_name:
                    proj.rooms.remove(i)
        else:
            proj = props.projects[props.project_index]
            room = proj.rooms[self.index]
            self.room_name = room.name
            proj.rooms.remove(self.index)

        tree = ET.parse(proj.file_path)
        root = tree.getroot()

        for elm in root.findall("Rooms"):
            items = list(elm)

            for item in items:
                if item.get("name") == self.room_name:
                    rel_path = os.path.join(*item.get("path").split(os.sep)[-2:])
                    proj_dir = pm_utils.get_project_dir()
                    room_filepath = os.path.join(proj_dir, rel_path)
                    elm.remove(item)

        tree.write(proj.file_path)

        # ToDo: install send2trash to interpreter to use here instead
        os.remove(room_filepath)
        proj.room_index = 0

        if proj.name == props.current_file_project:
            if self.room_name == props.current_file_room:
                bpy.ops.wm.read_homefile()

        return {'FINISHED'}


class SNAP_OT_Import_Room(Operator, ImportHelper):
    """ This will import a room into the currently selected project.
    """
    bl_idname = "project_manager.import_room"
    bl_label = "Import Room"
    bl_description = "Imports a room into the currently selected project"

    filename: StringProperty(name="Project File Name", description="Project file name to import")
    filepath: StringProperty(name="Project Path", description="Project path to import", subtype="FILE_PATH")
    directory: StringProperty(name="Project File Directory Name", description="Project file directory name")
    # ImportHelper mixin class uses this
    filename_ext = ".blend"
    filter_glob: StringProperty(default="*.blend", options={'HIDDEN'}, maxlen=255)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        wm = context.window_manager
        proj_wm = wm.sn_project
        self.project = proj_wm.projects[proj_wm.project_index]

        if pathlib.Path(self.filename).suffix == ".blend":
            room = self.project.add_room(self.filename.replace(".blend", ""))
            new_filepath = os.path.join(self.project.dir_path, room.name + ".blend")
            copyfile(self.filepath, new_filepath)

        else:
            message = "This is not a valid file!: {}".format(self.filename)
            bpy.ops.snap.message_box('INVOKE_DEFAULT', message=message, icon='ERROR')

        return {'FINISHED'}


class SNAP_OT_Select_All_Rooms(Operator):
    bl_idname = "project_manager.select_all_rooms"
    bl_label = "Select All Rooms"
    bl_description = "This will select all of the rooms in the project"


    select_all: BoolProperty(name="Select All", default=True)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        props = context.window_manager.sn_project
        proj = props.projects[props.project_index]

        for room in proj.rooms:
            room.selected = self.select_all

        return{'FINISHED'}


class SNAP_OT_Prepare_Project_XML(Operator):
    """ Create Project XML"""
    bl_idname = "project_manager.prepare_proj_xml"
    bl_label = "Create Project XML"
    bl_options = {'UNDO'}

    tmp_filename = "export_temp.py"
    xml_filename = "snap_job.xml"
    proj_dir: StringProperty(name="Project Directory", subtype='DIR_PATH')

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=256)

    def draw(self, context):
        layout = self.layout
        props = context.window_manager.sn_project
        proj = props.get_project()
        layout.label(text="Project: {}".format(proj.name))
        box = layout.box()

        for room in proj.rooms:
            col = box.column(align=True)
            row = col.row()
            row.prop(room, "selected", text="")
            row.label(text=room.name)

        row = layout.row()
        row.operator(
            "project_manager.select_all_rooms", text="Select All", icon='CHECKBOX_HLT').select_all = True
        row.operator(
            "project_manager.select_all_rooms", text="Deselect All", icon='CHECKBOX_DEHLT').select_all = False

    def create_prep_script(self):
        nrm_dir = self.proj_dir.replace("\\", "/")
        file = open(os.path.join(bpy.app.tempdir, self.tmp_filename), 'w')
        file.write("import bpy\n")
        file.write("bpy.ops.sn_export.export_xml('INVOKE_DEFAULT', xml_path='{}')\n".format(nrm_dir))
        file.close()

        return os.path.join(bpy.app.tempdir, self.tmp_filename)

    def execute(self, context):
        debug_mode = context.preferences.addons["snap"].preferences.debug_mode
        debug_mac = context.preferences.addons["snap"].preferences.debug_mac
        proj_props = bpy.context.window_manager.sn_project
        proj_name = proj_props.projects[proj_props.project_index].name
        path = os.path.join(pm_utils.get_project_dir(), proj_name, self.xml_filename)
        proj = proj_props.projects[proj_props.project_index]

        if os.path.exists(path):
            os.remove(path)

        self.proj_dir = os.path.join(pm_utils.get_project_dir(), proj_name)
        script_path = self.create_prep_script()

        # Call blender in background and run XML export on each room file in project
        for room in proj.rooms:
            if room.selected:
                subprocess.call(bpy.app.binary_path + ' "' + room.file_path + '" -b --python "' + script_path + '"')

        if debug_mode and debug_mac:
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
            if "Machining" in bpy.data.collections:
                for obj in bpy.data.collections["Machining"].objects:
                    obj.display_type = 'WIRE'

        return{'FINISHED'}


class SNAP_OT_Load_Projects(Operator):
    bl_idname = "project_manager.load_projects"
    bl_label = "Load Projects"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        pm_utils.load_projects()

        return{'FINISHED'}


classes = (
    SNAP_OT_Create_Project,
    SNAP_OT_Copy_Project,
    SNAP_OT_Import_Project,
    SNAP_OT_Delete_Project,
    SNAP_OT_Add_Room,
    SNAP_OT_Open_Room,
    SNAP_OT_Delete_Room,
    SNAP_OT_Import_Room,
    SNAP_OT_Select_All_Rooms,
    SNAP_OT_Prepare_Project_XML,
    SNAP_OT_Copy_Room,
    SNAP_OT_Load_Projects,
    SNAP_OT_Unarchive_Project
)


register, unregister = bpy.utils.register_classes_factory(classes)
