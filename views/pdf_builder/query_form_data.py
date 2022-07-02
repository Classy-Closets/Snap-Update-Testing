import os
import re
import bpy
import xml.etree.ElementTree as ET
from snap import sn_types, sn_utils, sn_unit
from snap.project_manager import pm_utils
from collections import Counter

class Query_PDF_Form_Data:
    def __init__(self, context, etl_object, page_walls_dict):
        self.spotted_garage_legs = []
        self.context = context
        self.etl_object = etl_object
        self.data_dict = {}
        self.page_walls_dict = page_walls_dict
        self.main_sc_objs = bpy.data.scenes['_Main'].objects
        self.walls_basepoints = self.__get_walls_obj_bp(context)
        self.garage_legs = self.__get_garage_legs()
        self.ext_colors = self.__walls_ext_color(self.walls_basepoints)
        self.full_backs = self.__get_full_backs(self.walls_basepoints)
        self.job_info = self.__job_info()
        self.int_color = self.__write_int_color()
        self.trim_color = self.__write_trim_color()
        self.pulls = self.__get_pulls(page_walls_dict)
        self.hampers = self.__get_hampers(page_walls_dict)
        self.room_name = self.__get_room_name(context)
        self.__dict_from_pages(page_walls_dict)
        self.__fill_pulls()
        self.__fill_garage_legs()


    def __get_room_name(self, context):
        pm_props = context.window_manager.sn_project
        room_name = pm_props.current_file_room
        clean_room_name = pm_utils.clean_name(room_name)
        return clean_room_name

    def __get_garage_leg_qty(self, garage_leg):
        qty = 0
        for leg in garage_leg.children:
            if leg.get("IS_BP_GARAGE_LEG"):
                for item in leg.children:
                    is_mesh = item.type == "MESH"
                    not_hidden = item.hide_render == False
                    if is_mesh and not_hidden:
                        qty += 1
        return qty

    def __get_garage_legs(self):
        leg_type_dict = {
            0: "Plastic",
            1: "Metal"
        }
        metal_leg = {
            0: "Brushed Steel", 
            1: "Black Matte", 
            2: "Polished Chrome"
        }
        garage_legs = {}
        for item in self.main_sc_objs:
            is_garage_leg ="garage leg" in item.name.lower()
            is_mesh = item.type != "MESH"
            unseen = item not in self.spotted_garage_legs
            if is_garage_leg and is_mesh and unseen:
                leg_str = ''
                leg_assy = sn_types.Assembly(item)
                leg_type = leg_assy.get_prompt("Material Type").get_value()
                leg_wall = sn_utils.get_wall_bp(item)
                leg_wall_letter = leg_wall.snap.name_object.replace(
                    "Wall ", "")
                leg_qty = self.__get_garage_leg_qty(item)
                if leg_type == 0:
                    leg_str = f"{leg_type_dict[leg_type]}"
                if leg_type == 1:
                    mat_type = leg_assy.get_prompt("Material Type").get_value()
                    leg_str = f"{metal_leg[mat_type]}"
                leg_entry = garage_legs.get(leg_wall_letter)
                if leg_entry:
                    entry_type = garage_legs[leg_wall_letter].get(f"{leg_str}")
                    if entry_type:
                        garage_legs[leg_wall_letter][leg_str] += leg_qty
                    elif not entry_type:
                        garage_legs[leg_wall_letter] = {}
                        garage_legs[leg_wall_letter][f"{leg_str}"] = leg_qty
                if not leg_entry:
                    garage_legs[leg_wall_letter] = {}
                    garage_legs[leg_wall_letter][f"{leg_str}"] = leg_qty
                self.spotted_garage_legs.append(item)
        return garage_legs

    def __get_hampers(self, page_walls_dict):
        mat_props = bpy.context.scene.closet_materials
        basket_color = mat_props.wire_basket_colors
        hamper_types = {
            0 : "Wire", 1: "Canvas"
        }
        scene_hampers = []
        pages_hampers = {}
        hampers_walls = {}
        hampers = (o for o in self.main_sc_objs if o.sn_closets.is_hamper_bp)
        seen = []
        for hmp in hampers:
            really_canvas = 'canvas' in hmp.name.lower()
            really_basket = 'basket' in hmp.name.lower()
            hamper_assy = sn_types.Assembly(hmp)
            hamper_ins_assy = sn_types.Assembly(hmp.parent)
            hidden = hamper_assy.get_prompt("Hide").get_value()
            hamper_type_pmpt = hamper_ins_assy.get_prompt("Hamper Type")
            hamper_pmpt = None
            if hamper_type_pmpt:
                hamper_pmpt = hamper_type_pmpt.get_value()
            hamper_type = hamper_types.get(hamper_pmpt)
            wall = sn_utils.get_wall_bp(hmp)
            if not wall:
                continue
            wall_name = wall.snap.name_object
            wall_letter = wall_name.replace("Wall ", "")
            unseen = hmp.name not in seen
            if unseen and not hidden and hamper_type == "Wire" and really_basket:
                basket_width = sn_unit.meter_to_inch(
                    hamper_assy.obj_x.location.x)
                basket_depth = sn_unit.meter_to_inch(
                    hamper_assy.obj_y.location.y)
                color_id = 2 if basket_color == 'CHROME' else 7
                width_id = 1 if basket_width == 18.0 else 2
                depth_id = 3 if basket_depth == 14.0 else 4
                vendor_id = '547.42.{}{}{}'.format(color_id,depth_id,width_id)
                scene_hampers.append((wall_letter, vendor_id))
                seen.append(hmp.name)
            elif unseen and not hidden and hamper_type == "Canvas" and really_canvas:
                basket_width = round(
                    sn_unit.meter_to_inch(hamper_ins_assy.obj_x.location.x), 2)
                if 24.0 > basket_width >= 18.0:
                    # HAMPER TILT OUT 18" 20H 
                    vendor_id = '547.43.311'
                    scene_hampers.append((wall_letter, vendor_id))
                    seen.append(hmp.name)
                elif 30.0 > basket_width >= 18.0:
                    # HAMPER TILT OUT 24" 20H DOUBLE BAG
                    vendor_id = '547.43.313'
                    scene_hampers.append((wall_letter, vendor_id))
                    seen.append(hmp.name)
                elif basket_width >= 30.0:
                    # HAMPER TILT OUT 30" 20H DOUBLE BAG
                    vendor_id = '547.43.515'
                    scene_hampers.append((wall_letter, vendor_id))
                    seen.append(hmp.name)
        for hamper in scene_hampers:
            wall, vendor_id = hamper
            has_entry = hampers_walls.get(wall)
            if has_entry:
                hampers_walls[wall].append(vendor_id)
            elif not has_entry:
                hampers_walls[wall] = []
                hampers_walls[wall].append(vendor_id)
        for page, walls in page_walls_dict.items():
            for wall in walls:
                if wall == "Island":
                    continue
            for wall, part_numbers in hampers_walls.items():
                if wall in walls:
                    if not pages_hampers.get(page):
                        pages_hampers[page] = {}
                    for part in part_numbers:
                        if pages_hampers[page].get(part):
                            pages_hampers[page][part] += 1
                        elif not pages_hampers[page].get(part):
                            pages_hampers[page][part] = 1
        return pages_hampers

    def __get_pulls(self, page_walls_dict):
        pages_pulls = {}
        walls = {}
        pulls = []
        for obj in self.main_sc_objs:
            if not obj.get('IS_BP_ASSEMBLY'):
                assy = sn_types.Assembly(obj.parent)
                bp = assy.obj_bp
                if hasattr(bp, 'sn_closets'):
                    if assy.obj_bp.sn_closets.is_handle and obj.type == 'MESH':
                        pulls.append((bp, bp.name, bp.parent.name))

        # initialize walls dict to save each pull parent counting
        for obj in self.main_sc_objs:
            if "IS_BP_WALL" in obj:
                wall_name = obj.snap.name_object
                wall_letter = wall_name.replace("Wall ", "")
                walls[wall_letter] = {
                    "hamper": [], "door": [], "drawer": []
                }
            elif "IS_BP_ISLAND" in obj and not walls.get("Island"):
                walls["Island"] = {
                    "hamper": [], "door": [], "drawer": []
                }
        for item in pulls:
            pull_obj, pull_name, parent = item
            pullch = pull_obj.children
            realname = [o.snap.name_object for o in pullch\
                 if o.type == 'MESH'][0]
            pull_assy = sn_types.Assembly(pull_obj)

            hidden_pull = pull_assy.get_prompt("Hide").get_value()
            wall = sn_utils.get_wall_bp(pull_obj)
            island = sn_utils.get_island_bp(pull_obj)
            if not wall and not island:
                continue
            wall_letter = ""
            if wall and not island:
                wall_name = wall.snap.name_object
                wall_letter = wall_name.replace("Wall ", "")
            elif not wall and island:
                wall_letter = "Island"
            elif not wall_letter and wall:
                wall_name = wall.snap.name_object
                wall_letter = wall_name.replace("Wall ", "")
            daddy = parent.lower()
            dad_hamper = 'hamper' in daddy
            dad_drawer = 'drawer' in daddy
            dad_door = 'door' in daddy
            if dad_hamper and not hidden_pull:
                walls[wall_letter]["hamper"].append(realname)
            elif dad_drawer and not hidden_pull:
                walls[wall_letter]["drawer"].append(realname)
            elif dad_door and not hidden_pull:
                walls[wall_letter]["door"].append(realname)
        for page, pg_walls in page_walls_dict.items():
            pages_pulls[page] = {
                "hamper": [], "door": [], "drawer": []}
            for each in pg_walls:
                pages_pulls[page]["hamper"] += walls[each]["hamper"]
                pages_pulls[page]["door"] += walls[each]["door"]
                pages_pulls[page]["drawer"] += walls[each]["drawer"]
        for page in pages_pulls.keys():
            hamper_count = dict(Counter(pages_pulls[page]["hamper"]))
            door_count = dict(Counter(pages_pulls[page]["door"]))
            drawer_count = dict(Counter(pages_pulls[page]["drawer"]))
            pages_pulls[page]["hamper"] = hamper_count
            pages_pulls[page]["door"] = door_count
            pages_pulls[page]["drawer"] = drawer_count
        return pages_pulls
    
    def __fill_pulls(self):
        for page, val in self.pulls.items():
            doors, drawers, hampers = val["door"], val["drawer"], val["hamper"]
            for pull, qty in doors.items():
                if self.data_dict[page]["door_hardware_qty"] != '':
                    self.data_dict[page]["door_hardware_qty"] += ' / '
                    self.data_dict[page]["door_hardware"] += ' / '
                self.data_dict[page]["door_hardware_qty"] += str(qty)
                self.data_dict[page]["door_hardware"] += pull
            for pull, qty in hampers.items():
                if self.data_dict[page]["hamper_hardware_qty"] != '':
                    self.data_dict[page]["hamper_hardware_qty"] += ' / '
                    self.data_dict[page]["hamper_hardware"] += ' / '
                self.data_dict[page]["hamper_hardware_qty"] += str(qty)
                self.data_dict[page]["hamper_hardware"] += pull
            for pull, qty in drawers.items():
                if self.data_dict[page]["drawer_hardware_qty"] != '':
                    self.data_dict[page]["drawer_hardware_qty"] += ' / '
                    self.data_dict[page]["drawer_hardware"] += ' / '
                self.data_dict[page]["drawer_hardware_qty"] += str(qty)
                self.data_dict[page]["drawer_hardware"] += pull

    def __fill_garage_legs(self):
        for page, pg_data in self.page_walls_dict.items():
            for wall_letter, legs_data in self.garage_legs.items():
                if wall_letter in pg_data:
                    for leg_color, leg_qty in legs_data.items():
                        if self.data_dict[page]["legs_qty"] != '':
                            self.data_dict[page]["legs_qty"] += ' / '
                            self.data_dict[page]["legs"] += ' / '
                        self.data_dict[page]["legs"] += leg_color
                        self.data_dict[page]["legs_qty"] += str(leg_qty)

    def __walls_ext_color(self, walls):
        ext_colors = []
        for wall in walls:
            wall_colors = self.__get_ext_wall_color(
                self.context,wall)
            if wall_colors:
                ext_colors = ext_colors + wall_colors
        ext_colors = list(set(ext_colors))
        colors_str = ""
        for i, color in enumerate(ext_colors):
            last_item = len(ext_colors) - 1
            if i != last_item:
                colors_str += (color + " / ")
            elif i == last_item:
                colors_str += color
        return colors_str

    def __get_walls_obj_bp(self, context):
        walls = []
        scene = context.scene
        for obj in scene.objects:
            if obj.get("IS_BP_WALL"):
                wall = sn_types.Wall(obj_bp=obj)
                walls.append(wall)
        return walls
    
    def __get_obj_mesh(self, obj):
        children = obj.children
        for child in children:
            if "mesh" in child.name.lower():
                return child
    
    def __get_door_obj(self, obj):
        children = obj.children
        for child in children:
            name = child.name
            is_door = "door" in name.lower()
            is_hamper = "hamper" in name.lower()
            is_drawer = "drawer" in name.lower()
            if is_door or is_hamper or is_drawer:
                return child
            elements = child.children
            for element in elements:
                name = element.name
                is_door = "door" in name.lower()
                is_hamper = "hamper" in name.lower()
                is_drawer = "drawer" in name.lower()
                if is_door or is_hamper or is_drawer:
                    return element

    def __get_full_backs(self, walls):
        fullback_str = ""
        result = []
        closet_full_back = None
        full_backs_values = {
            0: '1/4"',
            1: '3/4"'}
        for wall in walls:
            children = wall.obj_bp.children
            for child in children:
                if "Section" in child.name:
                    closet = sn_types.Assembly(obj_bp=child)
                    op_qty = closet.get_prompt("Opening Quantity").get_value()
                    for i in range(1, op_qty + 1):
                        add_full_back =\
                            closet.get_prompt(
                                "Add Full Back " + str(i)).get_value()
                        if add_full_back:
                            for item in closet.obj_bp.children:
                                if item.sn_closets.is_back_bp:
                                    if item.sn_closets.opening_name == str(i):
                                        back_assembly = sn_types.Assembly(obj_bp=item)
                                        use_center =\
                                            back_assembly.get_prompt(
                                                "Center Section Backing")
                                        if use_center.get_value():
                                            closet_full_back = closet
                                            op_index = i
            if closet_full_back is not None:
                full_back_index =\
                    closet_full_back.get_prompt(
                        "Opening " + str(op_index) + " Center Backing Thickness")
                result.append(full_backs_values[full_back_index.get_value()])
        result = sorted(list(set(result)))
        for i, res in enumerate(result):
            last_item = len(result) - 1
            if i != last_item:
                fullback_str += (res + " / ")
            elif i == last_item:
                fullback_str += res
        return fullback_str

    def __get_door_type(self, obj):
        door = None
        children = obj.children
        for child in children:
            obj_props = child.sn_closets
            is_door = obj_props.is_door_bp
            is_hamper = obj_props.is_hamper_front_bp
            is_drawer = obj_props.is_drawer_front_bp
            if is_door or is_hamper or is_drawer:
                door = child
                break
        if not door:
            return
        door_mesh = self.__get_obj_mesh(door)
        for slot in door_mesh.snap.material_slots:
            if "Wood_Door_Surface" == slot.pointer_name:
                return "wood"
            elif "Five_Piece_Melamine_Door_Surface" == slot.pointer_name:
                return "slab"
            elif "Door_Surface" == slot.pointer_name:
                return "slab"
            elif "Moderno_Door" == slot.pointer_name:
                return "slab"

    def __get_ext_wall_color(self, context, wall):
        ext_colors = []
        wall_obj = wall.obj_bp
        door_panel = self.__get_door_obj(wall_obj)
        if not door_panel:
            return
        style =\
            self.__get_door_type(door_panel)
        scene_props = context.scene.closet_materials
        color = None
        if style == "slab":
            mat_types = scene_props.materials.mat_types
            type_index = scene_props.door_drawer_mat_type_index
            material_type = mat_types[type_index]
            colors = material_type.colors
            color_index = scene_props.door_drawer_mat_color_index
            color = colors[color_index]
            if material_type.name.lower() == "veneer":
                colors.append(color.name)
            ext_colors.append(color.name)
        elif style == "wood":
            colors = scene_props.stain_colors
            color_index = scene_props.stain_color_index
            color = colors[color_index]
            ext_colors.append(color.name)
        ext_colors = list(set(ext_colors))
        return ext_colors


    def __job_info(self):
        job_dict = {}
        dirname = os.path.dirname(bpy.data.filepath).split("\\")[-1]
        filname = "{}.ccp".format(dirname)
        tree =\
            ET.parse(
                os.path.join(os.path.dirname(bpy.data.filepath), ".snap" ,filname))
        root = tree.getroot()
        elm_pinfo = root.find("ProjectInfo")
        customer_name = elm_pinfo.find("customer_name").text
        lead_id = elm_pinfo.find("client_id").text
        job_dict["customer_name"] = customer_name
        job_dict["lead_id"] = lead_id
        cphone_1 = elm_pinfo.find("customer_phone_1").text
        cphone_2 = elm_pinfo.find("customer_phone_2").text
        if cphone_1 and cphone_2 and cphone_1 != "None" and cphone_2 != "None":
            job_dict["cphone"] = cphone_1 + " / " + cphone_2
        elif cphone_1 and cphone_1 != "None":
            job_dict["cphone"] = cphone_1
        elif cphone_2 and cphone_2 != "None":
            job_dict["cphone"] = cphone_2
        designer = elm_pinfo.find("designer").text
        job_dict["designer"] = designer
        proj_notes = elm_pinfo.find("project_notes").text
        job_dict["proj_notes"] = proj_notes
        design_date = elm_pinfo.find("design_date").text
        job_dict["design_date"] = design_date
        return job_dict

    def __write_int_color(self):
        data_dict = {}
        scene_props = self.context.scene.closet_materials
        mat_types = scene_props.materials.mat_types
        type_index = scene_props.mat_type_index
        material_type = mat_types[type_index]
        colors = material_type.colors
        color_index = scene_props.mat_color_index
        color = colors[color_index]
        if material_type.name.lower() == "veneer":
            data_dict["veneer"] = color.name
        data_dict["int_color"] = color.name
        if "white" in color.name.lower():
            data_dict["int_white"] = True
        elif "almond" in color.name.lower():
            data_dict["int_almond"] = True
        if material_type.name == 'Garage Material':
            data_dict["int_white"] = True
            data_dict["int_color"] = "Oxford White"
            self.ext_colors = color.name
        return data_dict

    def __write_trim_color(self):
        data_dict = {}
        scene_props = self.context.scene.closet_materials
        edge_types = scene_props.edges.edge_types
        type_index = scene_props.edge_type_index
        edge_type = edge_types[type_index]
        colors = edge_type.colors
        color_index = scene_props.edge_color_index
        color = colors[color_index]
        data_dict["trim_color"] = color.name
        if "white" in color.name.lower():
            data_dict["trim_white"] = True
        elif "almond" in color.name.lower():
            data_dict["trim_almond"] = True
        if "dolce" in edge_type.name.lower():
            data_dict["edge_dolce"] = True
        elif "pvc" in edge_type.name.lower():
            data_dict["edge_3m_pvc"] = True
        return data_dict
        
    def process(self):
        return self.data_dict

    def __dict_from_pages(self, page_walls_dict):
        for page, walls in page_walls_dict.items():
            paging = f'{str(page + 1)} of {str(len(page_walls_dict))}'
            self.data_dict[page] = {}
            # Job Info
            self.__write_job_info(page, paging, walls)
            # Materials 
            self.__write_material_info(page, walls)
            # Install Section
            self.__write_install_info(page, walls)
            # Part Queries (Door, Drawes, Options and Counter Sections)
            # -> Door Section
            self.__write_door_section_info(page, walls)
            # -> Drawer Section
            self.__write_drawer_section_info(page, walls)
            # -> Options Section
            self.__write_options_info(page, walls)
            # -> Countertop Section
            self.__write_countertop_info(page, walls)

    def __write_options_info(self, page, walls):
        ji_results = {}
        si_results = {}
        vl_results = {}
        hmp_baskets_results = {}
        hmp_bags_results = {}
        # NOTE this lookup table (inserts_lut) is to differentiate 
        # an insert from it's sliding alike as on Pandas queries
        inserts_lut = {
            'Jewelry 18in Black' : 'CLA5106-1513-01',
            'Jewelry 18In Black Sliding' : '',
            'Jewelry 18in Maroon' : 'CLA5136-1513-02',
            'Jewelry 18in Maroon Sliding' : 'CLAAT200-1506-04',
            'Jewelry 18in Sterling Grey' : 'CLA51706-1513-01',
            'Jewelry 18in Sterling Grey Sliding' : 'CLAAT200-1506-05',
            'Jewelry 21in Black': 'CLA5106181301', 
            'Jewelry 21in Black Sliding': 'CLAAT200-1806-02', 
            'Jewelry 21in Lucite': '0', 
            'Jewelry 21in Maroon': 'CLA5136181301', 
            'Jewelry 21in Maroon Sliding': 'CLAAT200-1806-01', 
            'Jewelry 21in Sterling Grey' : 'CLA51706-1813-01',
            'Jewelry 21in Sterling Grey Slider' : 'CLAAT200-1806-04',
            'Jewelry 21in Sterling Grey Sliding' : 'CLAAT200-1806-04',
            'Jewelry 24in Black': 'CLA5106211301', 
            'Jewelry 24in Black Sliding': 'CLAAT200210606', 
            'Jewelry 24in Lucite': '0',
            'Jewelry 24in Maroon' : 'CLA5136211301',
            'Jewelry 24in Maroon Sliding' : 'OCTAT200210605',
            'Jewelry 24in Sterling Grey' : 'CLA51706-2113-01',
            'Jewelry 24in Sterling Grey Slider' : 'OCTAT200-2106-21',
        }
        jewelry_inserts = [
            'Jewelry 18in Black',
            'Jewelry 18in Maroon',
            'Jewelry 18in Sterling Grey',
            'Jewelry 21in Black',
            'Jewelry 21in Lucite',
            'Jewelry 21in Maroon',
            'Jewelry 21in Sterling Grey',
            'Jewelry 24in Black',
            'Jewelry 24in Lucite',
            'Jewelry 24in Maroon',
            'Jewelry 24in Sterling Grey',
        ]
        sliding_inserts = [
            'Jewelry 18in Black Sliding',
            'Jewelry 18in Maroon Sliding',
            'Jewelry 18in Sterling Grey Sliding',
            'Jewelry 21in Black Sliding',
            'Jewelry 21in Maroon Sliding',
            'Jewelry 21in Sterling Grey Sliding',
            'Jewelry 24in Black Sliding',
            'Jewelry 24in Maroon Sliding',
            'Jewelry 24in Sterling Grey Sliding',
        ]
        velvet_liners = [
            'Velvet Liner - Black',
            'Velvet Liner - Maroon',
            'Velvet Liner - Burgandy',
            'Velvet Liner - Sterling Grey'
        ]
        hampers_bags = [
        ]
        for insert in jewelry_inserts:
            results = self.etl_object.part_walls_query(insert, walls)
            for k, v in results.items():
                if inserts_lut.get(insert) == k:
                    show_string = insert.replace("Jewelry ", "")
                    ji_results[k] = (show_string, v)
        for sliding in sliding_inserts:
            results = self.etl_object.part_walls_query(sliding, walls)
            for k, v in results.items():
                if inserts_lut.get(sliding) == k:
                    show_string = sliding.replace("Jewelry ", "")
                    si_results[k] = (show_string, v)
        for liner in velvet_liners:
            results = self.etl_object.part_walls_query(liner, walls)
            for k, v in results.items():
                show_string = liner.replace("Velvet Liner - ", "")
                vl_results[k] = (show_string, v)
        for a_hamper in hampers_bags:
            results = self.etl_object.part_walls_query(a_hamper, walls)
            for k, v in results.items():
                hmp_bags_results[k] = v
        rod_result = self.etl_object.part_walls_query("hanging rod", walls)
        vrod_result = self.etl_object.part_walls_query("valet rod", walls)
        tie_result = self.etl_object.part_walls_query("tie", walls)
        hook_result = self.etl_object.part_walls_query("hook", walls)
        belt_result = self.etl_object.part_walls_query("belt", walls)
        self.data_dict[page]["jewelry_qty"] = ''
        self.data_dict[page]["jewelry"] = ''
        self.data_dict[page]["sld_tray_qty"] = ''
        self.data_dict[page]["sld_tray"] = ''
        self.data_dict[page]["vel_bottom_qty"] = ''
        self.data_dict[page]["vel_bottom"] = ''
        self.data_dict[page]["hamper_qty"] = ''
        self.data_dict[page]["hamper"] = ''
        self.data_dict[page]["hamper_bag_qty"] = ''
        self.data_dict[page]["hamper_bag"] = ''
        self.data_dict[page]["rod_qty"] = ''
        self.data_dict[page]["rod_style"] = ''
        self.data_dict[page]["handiwall_qty"] = ''
        self.data_dict[page]["handiwall"] = ''
        self.data_dict[page]["reach_pole_qty"] = ''
        self.data_dict[page]["reach_pole"] = ''
        self.data_dict[page]["belt_rack_qty"] = ''
        self.data_dict[page]["belt_rack_style"] = ''
        self.data_dict[page]["tie_rack_qty"] = ''
        self.data_dict[page]["tie_rack_style"] = ''
        self.data_dict[page]["valet_qty"] = ''
        self.data_dict[page]["valet_style"] = ''
        self.data_dict[page]["legs_qty"] = ''
        self.data_dict[page]["legs"] = ''
        self.data_dict[page]["hooks_qty"] = ''
        self.data_dict[page]["hooks_style"] = ''
        self.data_dict[page]["misc_qty"] = ''
        self.data_dict[page]["misc_style"] = ''
        # Hamper basket / bags
        for key, value in hmp_baskets_results.items():
            form_hmp_qty = self.data_dict[page]["hamper_qty"]
            qty = str(value.get("qty", 0))
            one_basket_only = len(hmp_baskets_results) == 1
            same_basket = len(hmp_baskets_results) > 1 and form_hmp_qty == ''
            same_basket_with_hamper_filled = len(hmp_baskets_results) > 1 and form_hmp_qty != ''
            if one_basket_only or same_basket:
                self.data_dict[page]["hamper_qty"] = qty
                self.data_dict[page]["hamper"] = key
            elif same_basket_with_hamper_filled:
                if self.data_dict[page]["misc_qty"] != '':
                    self.data_dict[page]["misc_qty"] += ' / '
                    self.data_dict[page]["misc_style"] += ' / '
                self.data_dict[page]["misc_qty"] += qty
                self.data_dict[page]["misc_style"] += key
        for key, value in hmp_bags_results.items():
            form_hmp_qty = self.data_dict[page]["hamper_bag_qty"]
            qty = str(value.get("qty", 0))
            one_bag_only = len(hmp_bags_results) == 1
            same_bag = len(hmp_bags_results) > 1 and form_hmp_qty == ''
            same_bag_with_hamper_filled = len(hmp_bags_results) > 1 and form_hmp_qty != ''
            if one_bag_only or same_bag:
                self.data_dict[page]["hamper_bag_qty"] = qty
                self.data_dict[page]["hamper_bag"] = key
            elif same_bag_with_hamper_filled:
                if self.data_dict[page]["misc_qty"] != '':
                    self.data_dict[page]["misc_qty"] += ' / '
                    self.data_dict[page]["misc_style"] += ' / '
                self.data_dict[page]["misc_qty"] += qty
                self.data_dict[page]["misc_style"] += key
        for key, value in rod_result.items():
            qty = str(value.get("qty", 0))
            if self.data_dict[page]["rod_qty"] != '':
                self.data_dict[page]["rod_qty"] += ' / '
                self.data_dict[page]["rod_style"] += ' / '
            self.data_dict[page]["rod_qty"] += qty
            self.data_dict[page]["rod_style"] += key
        for key, value in vrod_result.items():
            qty = str(value.get("qty", 0))
            if self.data_dict[page]["valet_qty"] != '':
                self.data_dict[page]["valet_qty"] += ' / '
                self.data_dict[page]["valet_style"] += ' / '
            self.data_dict[page]["valet_qty"] += qty
            self.data_dict[page]["valet_style"] += key
        for key, value in tie_result.items():
            qty = str(value.get("qty", 0))
            self.data_dict[page]["tie_rack_qty"] = qty
            self.data_dict[page]["tie_rack_style"] = key
        for key, value in hook_result.items():
            qty = str(value.get("qty", 0))
            self.data_dict[page]["hooks_qty"] = qty
            self.data_dict[page]["hooks_style"] = key
        for key, value in belt_result.items():
            qty = str(value.get("qty", 0))
            self.data_dict[page]["belt_rack_qty"] = qty
            self.data_dict[page]["belt_rack_style"] = key
        for key, value in ji_results.items():
            item_str, item_data = value
            qty = str(item_data.get("qty", 0))
            if self.data_dict[page]["jewelry_qty"] != '':
                self.data_dict[page]["jewelry_qty"] += '/'
                self.data_dict[page]["jewelry"] += ' / '
            self.data_dict[page]["jewelry_qty"] += qty
            self.data_dict[page]["jewelry"] += item_str
        for key, value in si_results.items():
            item_str, item_data = value
            qty = str(item_data.get("qty", 0))
            if self.data_dict[page]["sld_tray_qty"] != '':
                self.data_dict[page]["sld_tray_qty"] += '/'
                self.data_dict[page]["sld_tray"] += ' / '
            self.data_dict[page]["sld_tray_qty"] += qty
            self.data_dict[page]["sld_tray"] += item_str
        for key, value in vl_results.items():
            item_str, item_data = value
            qty = str(item_data.get("qty", 0))
            if self.data_dict[page]["vel_bottom_qty"] != '':
                self.data_dict[page]["vel_bottom_qty"] += '/'
                self.data_dict[page]["vel_bottom"] += ' / '
            self.data_dict[page]["vel_bottom_qty"] += qty
            self.data_dict[page]["vel_bottom"] += item_str
        for hamper_page, part_numbers in self.hampers.items():
            for_hamper = list(part_numbers.keys())[:1]
            for_misc = list(part_numbers.keys())[1:]
            same_page = hamper_page == page
            if same_page:
                for item in for_hamper:
                    qty = str(part_numbers[item])
                    self.data_dict[page]["hamper_qty"] = qty
                    self.data_dict[page]["hamper"] = item
                for item in for_misc:
                    qty = str(part_numbers[item])
                    if self.data_dict[page]["misc_qty"] != '':
                        self.data_dict[page]["misc_qty"] += "/"
                        self.data_dict[page]["misc_style"] += " / "
                    self.data_dict[page]["misc_qty"] += qty
                    self.data_dict[page]["misc_style"] += item


    def __write_drawer_section_info(self, page, walls):
        dovetail = 0
        melamine = 0
        drawers_doors = self.__get_drawer_face_types(walls)
        drw_boxes_result = self.etl_object.part_walls_query("Drawer Bottom", walls)
        file_result = self.etl_object.part_walls_query("file rail", walls)
        # Sliders queries
        sliders_results = {}
        sliders_names = ["hafele bb",
                         "hr bb sc",
                         "hettich 4d 9in",
                         "hettich 4d 12in",
                         "hettich 4d 15in",
                         "hettich 4d 18in",
                         "hettich 4d 21in",
                         "hettich v6 9in",
                         "hettich v6 12in",
                         "hettich v6 15in",
                         "hettich v6 18in",
                         "hettich v6 21in",
                         "blumotion um 9in",
                         "blumotion um 12in",
                         "blumotion um 15in",
                         "blumotion um 18in",
                         "blumotion um 21in",
                         "king slide um sc 9in",
                         "king slide um sc 12in",
                         "king slide um sc 15in",
                         "king slide um sc 18in",
                         "king slide um sc 21in"]
        for slider in sliders_names:
            results = self.etl_object.part_walls_query(slider, walls)
            for result in results.items():
                sliders_results[result[0]] = result[1]
        self.data_dict[page]["drawer_boxes_qty"] = ''
        self.data_dict[page]["drawer_boxes"] = ''
        self.data_dict[page]["drawer_slides_qty"] = ''
        self.data_dict[page]["drawer_slides"] = ''
        self.data_dict[page]["drawer_mel_qty"] = drawers_doors["drawer_mel_qty"]
        self.data_dict[page]["drawer_mel"] = drawers_doors["drawer_mel"]
        self.data_dict[page]["wood_drawer_qty"] = drawers_doors["wood_drawer_qty"]
        self.data_dict[page]["wood_drawer"] = drawers_doors["wood_drawer"]
        self.data_dict[page]["file_rails_qty"] = ''
        self.data_dict[page]["file_rails"] = ''
        self.data_dict[page]["drawer_hardware_qty"] = ''
        self.data_dict[page]["drawer_hardware"] = ''
        for key, value in drw_boxes_result.items():
            quantities = ''
            description = ''
            qty = str(value.get("qty", 0))
            if 'birch' in key.lower():
                dovetail += int(qty)
            elif 'paper'in key.lower():
                melamine += int(qty)
            if dovetail > 0 and melamine > 0:
                quantities = f'{melamine}/{dovetail}'
                description = f'Melamine / Dovetail'
            elif dovetail == 0 and melamine > 0:
                quantities = f'{melamine}'
                description = f'Melamine'
            elif dovetail > 0 and melamine == 0:
                quantities = f'{dovetail}'
                description = f'Dovetail'
            self.data_dict[page]["drawer_boxes_qty"] = quantities
            self.data_dict[page]["drawer_boxes"] = description
        for key, value in sliders_results.items():
            qty = str(value.get("qty", 0))
            if self.data_dict[page]["drawer_slides_qty"] != '':
                self.data_dict[page]["drawer_slides_qty"] += '/'
                self.data_dict[page]["drawer_slides"] += ' / '
            self.data_dict[page]["drawer_slides_qty"] += qty
            self.data_dict[page]["drawer_slides"] += key
        for key, value in file_result.items():
            qty = str(value.get("qty", 0))
            self.data_dict[page]["file_rails_qty"] = qty
            self.data_dict[page]["file_rails"] = key

    def __get_obj_styling(self, walls, scene_objects):
        spotted = []
        doors = {
            'melamine': {},
            'glass': {},
            'wood': {}
        }
        for door in scene_objects:
            is_hidden = sn_types.Assembly(door).get_prompt("Hide").get_value()
            has_glass = False
            is_wood = False
            within_walls = False
            is_island = sn_utils.get_island_bp(door)
            obj_wall = sn_utils.get_wall_bp(door)
            if not obj_wall and not is_island:
                continue
            elif obj_wall:
                wall_str = obj_wall.snap.name_object
                wall_letter = wall_str.replace("Wall ", "")
                within_walls = wall_letter in walls
            in_spot = door.name in spotted
            if (within_walls and not in_spot) or (is_island and not in_spot):
                mat_type = None
                door_mesh = self.__get_obj_mesh(door)
                if door_mesh:
                    active_mat = door_mesh.active_material_index
                    mat_name = door_mesh.material_slots[active_mat].name
                    mesh_slots = door_mesh.snap.material_slots
                    for slot in mesh_slots:
                        if 'Glass' == slot.pointer_name:
                            has_glass = True
                            mat_name = [s.item_name for s in mesh_slots\
                                if s.item_name != 'Glass'][:1][0]
                        if "Wood_Door_Surface" == slot.pointer_name:
                            mat_type = "Wood"
                        elif "Five_Piece_Melamine_Door_Surface" == slot.pointer_name:
                            mat_type = "Five_Piece_Melamine"
                        elif "Door_Surface" == slot.pointer_name:
                            mat_type = "Slab"
                        elif "Moderno_Door" == slot.pointer_name:
                            mat_type = "Moderno"
                    spotted.append(door.name)
                    fillname = door.name
                    is_drawer = door.sn_closets.is_drawer_front_bp
                    if is_drawer and mat_type != "Moderno" and 'part' not in door_mesh.name.lower():
                        fillname = door_mesh.name
                    to_replace = [
                        "Door","Drawer","Face","Glass",
                        "Left","Right","Mesh","MESH..", " "]
                    for each in to_replace:
                        fillname = fillname.replace(each, "")
                    number_re = re.findall(r'\.\d{3}', fillname)
                    if number_re:
                        fillname = fillname.replace(number_re[0], "")
                    if not has_glass and mat_type == "Wood":
                        is_wood = True
                    # Setting Style name
                    if fillname == "":
                        mat_type = "Slab"
                    elif fillname != "":
                        mat_type = fillname
                    # Adding drawer name exceptions I couldn't deal other way
                    if mat_type == 'SanMarino':
                        mat_type = 'San Marino'
                    if mat_type == 'MolinoVecchio':
                        mat_type = 'Molino Vecchio'
                    # Adding to entries
                    if not has_glass and not is_wood and not is_hidden:
                        has_current_style = doors['melamine'].get(mat_type)
                        if has_current_style:
                            doors["melamine"][mat_type]["qty"] += 1
                        elif not has_current_style:
                            doors["melamine"][mat_type] = {}
                            doors["melamine"][mat_type]["qty"] = 1
                            doors["melamine"][mat_type]["color"] = mat_name
                    if has_glass and not is_wood and not is_hidden:
                        has_current_style = doors["glass"].get(mat_type)
                        if has_current_style:
                            doors["glass"][mat_type]["qty"] += 1
                        elif not has_current_style:
                            doors["glass"][mat_type] = {}
                            doors["glass"][mat_type]["qty"] = 1
                            doors["glass"][mat_type]["color"] = mat_name
                    if not has_glass and is_wood and not is_hidden:
                        has_current_style = doors["wood"].get(mat_type)
                        if has_current_style:
                            doors["wood"][mat_type]["qty"] += 1
                        elif not has_current_style:
                            doors["wood"][mat_type] = {}
                            doors["wood"][mat_type]["qty"] = 1
                            doors["wood"][mat_type]["color"] = mat_name
        return doors

    def __get_walls_doors_types(self, walls):
        result = {
            "glass_inset_qty": "",
            "glass_inset": "",
            "door_mel_qty": "",
            "door_mel": "",
            "wood_door_qty": "",
            "wood_door": "",
        }
        scene_doors = (o for o in self.main_sc_objs\
            if o.sn_closets.is_door_bp)
        door_styled_data = self.__get_obj_styling(
            walls, scene_doors)
        melamine = door_styled_data["melamine"]
        glass = door_styled_data["glass"]
        wood = door_styled_data["wood"]
        for k, v in melamine.items():
            if result["door_mel_qty"] == "":
                result["door_mel_qty"] = str(v["qty"])
                result["door_mel"] = k
            elif result["door_mel_qty"] != "":
                result["door_mel_qty"] += "/" + str(v["qty"])
                result["door_mel"] += " / " + k
        for k, v in glass.items():
            if result["glass_inset_qty"] == "":
                result["glass_inset_qty"] = str(v["qty"])
                result["glass_inset"] = k
            elif result["glass_inset_qty"] != "":
                result["glass_inset_qty"] += "/" + str(v["qty"])
                result["glass_inset"] += " / " + k
        for k, v in wood.items():
            if result["wood_door_qty"] == "":
                result["wood_door_qty"] = str(v["qty"])
                result["wood_door"] = k
            elif result["wood_door_qty"] != "":
                result["wood_door_qty"] += "/" + str(v["qty"])
                result["wood_door"] += " / " + k
        return result

    def __get_hamper_doors_types(self, walls):
        result = {
            "hamper_face_qty" : "",
            "hamper_face" : ""
        }
        scene_hamper_front = (o for o in self.main_sc_objs\
            if o.sn_closets.is_hamper_front_bp)
        hamper_door_styled_data = self.__get_obj_styling(
            walls, scene_hamper_front)
        for item in hamper_door_styled_data.values():
            for k, v in item.items():
                if result["hamper_face_qty"] == "":
                    result["hamper_face_qty"] = str(v["qty"])
                    result["hamper_face"] = k
                elif result["hamper_face_qty"] != "":
                    result["hamper_face_qty"] += "/" + str(v["qty"])
                    result["hamper_face"] += " / " + k
        return result

    def __get_drawer_face_types(self, walls):
        result = {
            "drawer_mel_qty" : "",
            "drawer_mel" : "",
            "wood_drawer_qty" : "",
            "wood_drawer" : "",
        }
        scene_drawer_doors = (o for o in self.main_sc_objs\
            if o.sn_closets.is_drawer_front_bp)
        drawer_styled_data = self.__get_obj_styling(
            walls, scene_drawer_doors)
        for drw_type, drawers in drawer_styled_data.items():
            if drw_type == "glass":
                continue
            elif drw_type == "melamine":
                for drw_key, drw_value in drawers.items():
                    if result["drawer_mel_qty"] == "":
                        result["drawer_mel_qty"] = str(drw_value["qty"])
                        result["drawer_mel"] = drw_key
                    elif result["drawer_mel_qty"] != "":
                        result["drawer_mel_qty"] += "/" + str(drw_value["qty"])
                        result["drawer_mel"] += " / " + drw_key
            elif drw_type == "wood":
                for drw_key, drw_value in drawers.items():
                    if result["wood_drawer_qty"] == "":
                        result["wood_drawer_qty"] = str(drw_value["qty"])
                        result["wood_drawer"] = drw_key
                    elif result["wood_drawer_qty"] != "":
                        result["wood_drawer_qty"] += "/" + str(drw_value["qty"])
                        result["wood_drawer"] += " / " + drw_key
        return result

    def __write_door_section_info(self, page, walls):
        doors = self.__get_walls_doors_types(walls)
        hampers_doors = self.__get_hamper_doors_types(walls)
        hinge_result = self.etl_object.part_walls_query("hinge", walls)
        self.data_dict[page]["glass_inset_qty"] = doors["glass_inset_qty"]
        self.data_dict[page]["glass_inset"] = doors["glass_inset"]
        self.data_dict[page]["door_mel_qty"] = doors["door_mel_qty"]
        self.data_dict[page]["door_mel"] = doors["door_mel"]
        self.data_dict[page]["wood_door_qty"] = doors["wood_door_qty"]
        self.data_dict[page]["wood_door"] = doors["wood_door"]
        self.data_dict[page]["lucite_qty"] = ""
        self.data_dict[page]["lucite"] = ""
        self.data_dict[page]["hinge_qty"] = ""
        self.data_dict[page]["hinge"] = ""
        self.data_dict[page]["door_hardware_qty"] = ""
        self.data_dict[page]["door_hardware"] = ""
        self.data_dict[page]["hamper_face_qty"] = hampers_doors["hamper_face_qty"]
        self.data_dict[page]["hamper_face"] = hampers_doors["hamper_face"]
        self.data_dict[page]["hamper_hardware_qty"] = ""
        self.data_dict[page]["hamper_hardware"] = ""
        for key, value in hinge_result.items():
            qty = str(value.get("qty", 0))
            if self.data_dict[page]["hinge_qty"] != "":
                self.data_dict[page]["hinge_qty"] += " / "
                self.data_dict[page]["hinge"] += " / "
            self.data_dict[page]["hinge_qty"] += qty
            self.data_dict[page]["hinge"] += key
        

    def __write_countertop_info(self, page, walls):
        mel = self.etl_object.part_walls_query("melamine countertop", walls)
        gnt = self.etl_object.part_walls_query("granite countertop", walls)
        self.data_dict[page]["ct_type"] = ''
        self.data_dict[page]["ct_color"] = ''
        self.data_dict[page]["ct_chip"] = ''
        self.data_dict[page]["ct_client"] = False
        if len(mel) > 0:
            for key, _ in mel.items():
                if self.data_dict[page]["ct_type"] != '':
                    self.data_dict[page]["ct_type"] += ' / '
                    self.data_dict[page]["ct_color"] += ' / '
                self.data_dict[page]["ct_type"] += 'Melamine'
                self.data_dict[page]["ct_color"] += key
        if len(gnt) > 0:
            for key, _ in gnt.items():
                if self.data_dict[page]["ct_type"] != '':
                    self.data_dict[page]["ct_type"] += ' / '
                    self.data_dict[page]["ct_color"] += ' / '
                self.data_dict[page]["ct_type"] += 'Granite'
                self.data_dict[page]["ct_color"] += key

    def __write_install_info(self, page, walls):
        self.data_dict[page]["tear_out"] = False
        self.data_dict[page]["block_wall"] = False
        self.data_dict[page]["elevator"] = False
        self.data_dict[page]["touch_up"] = False
        self.data_dict[page]["new_construction"] = False
        self.data_dict[page]["stairs"] = False
        self.data_dict[page]["floor_type"] = ''
        self.data_dict[page]["basebrd"] = ''
        self.data_dict[page]["parking"] = ''
        self.data_dict[page]["door_type"] = ''

    def __write_material_info(self, page, walls):
        self.data_dict[page]["int_color"] = self.int_color.get("int_color", '')
        self.data_dict[page]["veneer"] = self.int_color.get("veneer", '')
        self.data_dict[page]["ext_color"] = self.ext_colors
        self.data_dict[page]["edge"] = ''
        self.data_dict[page]["edge_dolce"] = self.trim_color.get("edge_dolce", False)
        self.data_dict[page]["edge_3m_pvc"] = self.trim_color.get("edge_3m_pvc", False)
        self.data_dict[page]["trim_color"] = self.trim_color.get("trim_color", '')
        self.data_dict[page]["full_backs"] = self.full_backs

    def __write_job_info(self, page, paging, walls):
        self.data_dict[page]["signature"] = ''
        self.data_dict[page]["install_date"] = ''
        self.data_dict[page]["job_number"] = ''
        self.data_dict[page]["sheet"] = paging
        self.data_dict[page]["customer_name"] = self.job_info.get("customer_name", '')
        self.data_dict[page]["cphone"] = self.job_info.get("cphone", '')
        self.data_dict[page]["designer"] = self.job_info.get("designer", '')
        self.data_dict[page]["proj_notes"] = self.job_info.get("proj_notes", '')
        self.data_dict[page]["design_date"] = self.job_info.get("design_date", '')
        self.data_dict[page]["leadid"] = self.job_info.get("lead_id", '')
        self.data_dict[page]["room_name"] = self.room_name
            
