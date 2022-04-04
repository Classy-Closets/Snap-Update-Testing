import json
import os


class PDF_Form_Content:
    """Interface with some functions to fill the form data"""

    def __init__(self, form_info):
        self.form_info = form_info

    def get_tag_from_varname(self, varname):
        try:
            tag = next(
                filter(lambda tag: tag["varname"] == varname, self.form_info))
        except StopIteration:
            print(f"varname: {varname} was not found ! ! !")
            tag = None
            # raise
            # tag = next(
            #    filter(lambda tag: tag["varname"] == "test", self.form_info))
        return tag

    def set_value(self, varname, value):
        tag = self.get_tag_from_varname(varname)
        if tag is not None:
            tag["value"] = value


def fill_form(form, form_data):
    """Take the info from the form_data dict and put it in the form"""
    for key in form_data.keys():
        tag = form.get_tag_from_varname(key)
        if tag is not None:
            tag["value"] = form_data[key]
    return form.form_info
