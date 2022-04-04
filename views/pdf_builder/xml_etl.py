import os
import sys
import xml.etree.ElementTree as ET
from snap import sn_paths
try:
    import pandas as pd
    import numpy  as np
except ModuleNotFoundError:
    python_lib_path = os.path.join(sn_paths.ROOT_DIR, "python_lib")
    sys.path.append(python_lib_path)
import pandas as pd
import numpy as np

class SnapXML_ETL:
    def __init__(self, xml_file, cc_items_csv):
        self.xml_file = xml_file
        self.cc_items_csv = cc_items_csv
        self.dataframe = self.process()

    def __parts_query(self, queried_xml_root):
        results = {}
        for part in queried_xml_root:
            part_id = part.attrib.get("ID", None)
            part_material_id = part.attrib.get("MatID", None)
            part_label_id = part.attrib.get("LabelID", None)
            part_name = part.findtext('Name')
            part_quantity = part.findtext('Quantity')
            part_type = part.findtext('Type')
            part_style = part.findtext('Style')
            if part_style == None:
                part_style = 0
            results[part_id] = {
                "material_id": part_material_id,
                "label_id": part_label_id,
                "name": part_name,
                "quantity": part_quantity,
                "type": part_type,
                "extra_style": part_style
            }
        return results

    def __materials_query(self, queried_xml_root):
        results = {}
        for part in queried_xml_root:
            mat_id = part.attrib.get("ID", None)
            mat_name = part.findtext('Name')
            mat_sku = part.findtext('SKU')
            results[mat_id] = {
                "name": mat_name,
                "sku": mat_sku
            }
        return results

    def __labels_query(self, queried_xml_root):
        results = {}
        for part in queried_xml_root:
            label_id = part.attrib.get("ID", None)
            part_id = part.attrib.get("PartID", None)
            wall = None
            sku = None
            style = ''
            # Use the iterator to deal with repeated children and still in order
            part_iterator = iter(part)
            for _ in range(int(len(part) / 3)):
                name = next(part_iterator).text
                type = next(part_iterator).text
                value = next(part_iterator).text
                if name == 'sku':
                    sku = value
                if name == 'wallname':
                    wall = value
                if name == 'style':
                    style = value
            results[label_id] = {
                "part_id": part_id,
                "sku": sku,
                "wall": wall,
                "style": style
            }
        return results

    def __transform(self, dataframes):
        labels, materials, parts, assy_parts, nested_parts, skus = dataframes
        df = pd.concat([parts, assy_parts, nested_parts])
        # print(df.to_string())

        # Join materials dataframe
        df = pd.merge(df,
                      materials,
                      left_on="material_id",
                      right_index=True,
                      how='outer'
                      )
        df = df.rename(
            columns={'name_x': 'name', 'name_y': 'material_name', 'sku': 'material_sku'})

        # Join Labels Dataframe
        df = pd.merge(df,
                      labels,
                      left_on="label_id",
                      right_index=True,
                      how='outer'
                      )
        df = df.rename(columns={'sku': 'label_sku'})

        # Join SKU dataframe
        df = pd.merge(df,
                      skus,
                      left_on="label_sku",
                      right_index=True,
                      how='outer'
                      )

        # Cleanup
        df["material_name"] = df["material_name"].replace(np.nan, 0)
        df["material_sku"] = df["material_sku"].replace(np.nan, 0)
        df["part_id"] = df["part_id"].replace(np.nan, 0)
        df["wall"] = df["wall"].replace(np.nan, 0)
        df.drop('material_sku', axis=1, inplace=True)
        df.drop('part_id', axis=1, inplace=True)
        df.drop('material_id', axis=1, inplace=True)
        df.drop('label_id', axis=1, inplace=True)
        df = df.rename(
            columns={'label_sku': 'sku', 'VendorItemNum': 'vendor_item_number'})
        df["is_panel"] = np.where(df["type"] == "panel", True, False)
        df["is_hardware"] = np.where(df["type"] == "hardware", True, False)
        return df

    def __get_dataframes(self, queries):
        root, assy, nested, mfg_labels, materials = queries
        labels_df = pd.DataFrame.from_dict(
            self.__labels_query(mfg_labels),
            orient='index')

        materials_df = pd.DataFrame.from_dict(
            self.__materials_query(materials),
            orient='index')

        parts_df = pd.DataFrame.from_dict(
            self.__parts_query(root),
            orient='index')

        assy_parts_df = pd.DataFrame.from_dict(
            self.__parts_query(assy),
            orient='index')

        nested_parts_df = pd.DataFrame.from_dict(
            self.__parts_query(nested),
            orient='index')
        

        skus_df = pd.read_csv(self.cc_items_csv,
                              usecols=['SKU', 'VendorItemNum'],
                              index_col='SKU',
                              )
        skus_df.index.name = None
        dataframes = (labels_df, 
                      materials_df,
                      parts_df, 
                      assy_parts_df, 
                      nested_parts_df,
                      skus_df)
        return dataframes

    def __extract(self):
        xml_tree = ET.parse(self.xml_file)
        xml_root = xml_tree.getroot()

        root_parts_xml_query = xml_root.findall('./Job/Item/Part')
        assy_parts_xml_query = xml_root.findall('./Job/Item/Assembly/Part')
        nested_parts_xml_query = xml_root.findall('./Job/Item/Assembly/Assembly/Part')
        mfg_labels_xml_query = xml_root.findall('./Job/Manufacturing/Label')
        materials_xml_query = xml_root.findall('./Job/Material')
        queries = (root_parts_xml_query, 
                   assy_parts_xml_query,
                   nested_parts_xml_query,
                   mfg_labels_xml_query, 
                   materials_xml_query)
        return queries

    def part_query(self, part_name, wall_letter):
        wall_name = f'Wall {wall_letter}'
        if 'island' in wall_letter.lower():
            wall_name = wall_letter
        result = {}
        element_part = self.dataframe[(self.dataframe["name"].str.contains(f"{part_name}", case=False)) & (
            self.dataframe["wall"] == f"{wall_name}") & (self.dataframe["is_panel"] == True) & (self.dataframe["extra_style"] == 0)]
        element_hw = self.dataframe[(self.dataframe["name"].str.contains(f"{part_name}", case=False)) & (
            self.dataframe["wall"] == f"{wall_name}") & (self.dataframe["is_hardware"] == True)]
        styled_part = self.dataframe[(self.dataframe["name"].str.contains(f"{part_name}", case=False)) & (
            self.dataframe["wall"] == f"{wall_name}") & (self.dataframe["extra_style"] != 0)]
        inset_style = self.dataframe[(self.dataframe["name"].str.contains(f"{part_name}", case=False)) & (
            self.dataframe["wall"] == f"{wall_name}") & (self.dataframe["style"] != '')]
        grouped_part = element_part.groupby("material_name")["quantity"].count()
        grouped_part_qty = grouped_part.count()
        grouped_hw = element_hw.groupby("vendor_item_number")["quantity"].count()
        grouped_hw_qty = grouped_hw.count()
        grouped_style = styled_part.groupby("extra_style")["quantity"].count()
        grouped_style_qty = grouped_style.count()
        grouped_ins_style = inset_style.groupby("style")["quantity"].count()
        grouped_ins_style_qty = grouped_ins_style.count()

        if grouped_part_qty > 0:
            gp_dict = grouped_part.to_dict()
            value = next(iter(gp_dict))
            qty = 0
            for key, val in gp_dict.items():
                if result.get(key):
                    result[key]["qty"] += val
                    result[key]["extra_style"] = False
                elif result.get(key) is None:
                    result[key] = {
                        "qty": val,
                        "extra_style": False
                    }
        if grouped_hw_qty > 0:
            gw_dict = grouped_hw.to_dict()
            value = next(iter(gw_dict))
            qty = 0
            for key, val in gw_dict.items():
                if result.get(key):
                    result[key]["qty"] += val
                    result[key]["extra_style"] = False
                elif result.get(key) is None:
                    result[key] = {
                        "qty": val,
                        "extra_style": False
                    }
        if grouped_style_qty > 0:
            qty = 0
            st_dict = grouped_style.to_dict()
            for key, val in st_dict.items():
                if result.get(key):
                    result[key]["qty"] += val
                    result[key]["extra_style"] = True
                elif result.get(key) is None:
                    result[key] = {
                        "qty": val,
                        "extra_style": True 
                    }
        if grouped_ins_style_qty > 0:
            qty = 0
            gis_dict = grouped_ins_style.to_dict()
            for key, val in gis_dict.items():
                if result.get(key):
                    result[key]["qty"] += val
                    result[key]["extra_style"] = True
                elif result.get(key) is None:
                    result[key] = {
                        "qty": val,
                        "extra_style": True
                    }
        return result

    def part_walls_query(self, part_name, walls_list):
        full_result = {}
        for wall_letter in walls_list:
            wall_result = self.part_query(part_name, wall_letter)
            for part, counts in wall_result.items():
                existing = full_result.get(part)
                if existing is not None:
                    full_result[part]["qty"] += counts["qty"]
                elif existing is None:
                    full_result[part] = counts
        return full_result

    def process(self):
        queries = self.__extract()
        dataframes = self.__get_dataframes(queries)
        return self.__transform(dataframes)
