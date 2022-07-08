from snap.views.pdf_builder.pdf_builder import Pdf_Builder
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import white
import json
import os

registerFont(TTFont('Calibri-Bold', 'calibrib.ttf'))
registerFont(TTFont('Calibri', 'calibri.ttf'))
GREY = (0.851, 0.851, 0.851)
REDWINE = (0.435, 0.078, 0.0)
BLACK = (0.0, 0.0, 0.0)
FORBIDDEN_STRINGS = ["Δ "]


class New_Template_Builder(Pdf_Builder):
    """subclass of Pdf_Builder for construction of pdf files with the new template.

    Attributes:
        path (str): Path where the .pdf file will be save
                    (include name and extension),
                    example: '\an_example\views_new.pdf'.
        print_paper_size (str): Name of the paper format,
                    example: 'LEGAL'.
        pagesize (tuple[int, int]): Tuple with the width and the
                                    height of the paper.
        c (Canvas): Canvas from reportlab for the .pdf generation.
        _dic_sections (dict): Dictionary with positions and names
                             of the sections.
        _dic_lines (dict): Dictionary with positions and lengths of lines.
        _dic_labels (dict): Dictionary with positions and names of the labels.
    """

    def __init__(self, path: str, print_paper_size: str) -> None:
        sections_path = os.path.join(os.path.dirname(__file__),
                                     "new_template_sections.json")
        labels_path = os.path.join(os.path.dirname(__file__),
                                   "new_template_labels.json")
        self.dic_sections = New_Template_Builder._open_json_file(sections_path)
        """The .json file in 'sections_path' contains:

        A list of dictionaries each represent a section in the block info:
            "label": the name of the section
            "position": a dictionary with the coordinates of the label in the
                        .pdf file, depending on the paper size (key)
        """
        self.dic_labels = New_Template_Builder._open_json_file(labels_path)
        """The .json file in 'labels_path' contains:

        A list of dictionaries each represent a label in the block info:
            "data": a dictionary with the name of the label and the position
            "bold": 1 if the label is bold
            "underline": 1 if the label is underlined
            "checkbox": 1 if the label has a checkbox
        """
        super().__init__(path, print_paper_size)

    @staticmethod
    def _open_json_file(file: str) -> dict:
        """Open a json file and return a dictionary."""
        with open(file) as f:
            json_file = json.load(f)
        return json_file

    def _draw_section(self, msg: str, position: tuple) -> None:
        """Create a section separation (rectangle with text column)
           in the canvas.

        Args:
            msg (str): The name of the section.
            position (tuple): Coordinates (x, y) of the lower left corner
                              of the rectangle.
        """
        self.c.setFont("Calibri-Bold", 9)
        self.c.setFillColorRGB(*GREY)
        self.c.setStrokeColorRGB(*REDWINE)
        posx, posy = position
        x, y, w, h, r = posx, posy, 18, 91, 3
        self.c.roundRect(x, y, w, h, r, stroke=1, fill=1)
        self.c.setFillColorRGB(*REDWINE)
        self.c.saveState()
        self.c.translate((posx + (w / 2)), h)
        # This draws the section label as a column of upright characters
        for char in msg:
            self.c.drawCentredString(0, 0, char)
            self.c.translate(0, -9)
        self.c.restoreState()
        self.c.setFillColorRGB(*BLACK)
        self.c.setStrokeColorRGB(*BLACK)

    def sanitize(self, string: str) -> str:
        for forbidden in FORBIDDEN_STRINGS:
            if forbidden in string:
                string = string.replace(forbidden, "")
        return string

    def draw_info(self, form_info: dict) -> None:
        """Draw the info about the project in the canvas.

        Args:
            form_info (dict): A dictionary with labels, values and positions.
        """
        bigger_fonts = ['customer_name', 'cphone', 'design_date', 'designer']
        bigger_fonts += ['signature', 'install_date', 'job_number', 'sheet']
        bigger_fonts += ['room_name', 'leadid']
        self.c.setFont("Calibri", 8)
        form = self.c.acroForm
        for idx, field in enumerate(form_info):
            varname = field["varname"]
            is_big = varname in bigger_fonts
            lbl, val = field["label"], field["value"]
            pos = field["position"][self.print_paper_size]
            if lbl != "" and not is_big:
                self.c.setFont("Calibri", 8)
                self.c.drawString(pos[0], pos[1], f'{lbl} ')
            elif lbl != "" and is_big:
                self.c.setFont("Calibri-Bold", 9)
                self.c.drawString(pos[0], pos[1], f'{lbl} ')
            form = self.c.acroForm
            if "line" in field.keys():
                line = field["line"]
                posx, posy = line["position"][self.print_paper_size]
                length = line["length"][self.print_paper_size]
            if not val or val == "None":
                val = ""
            if "checkbox" in field.keys():
                position = field["checkbox"]["position"][self.print_paper_size]
                self._draw_check_box(position, val)
                continue
            if field.get("line") and not is_big:
                sanitized = self.sanitize(val)
                form.textfield(
                    x=posx, y=posy, width=length, height=10,
                    fontSize=6, fillColor=white, borderStyle='underlined',
                    value=sanitized)
            if field.get("line") and is_big:
                sanitized = self.sanitize(val)
                form.textfield(
                    x=posx, y=posy, width=length, height=14,
                    fontSize=9, fillColor=white, borderStyle='underlined',
                    value=sanitized)

    def _draw_sections(self) -> None:
        """Draw a all section separators in the canvas."""
        for section in self.dic_sections:
            self._draw_section(section["label"],
                               section["position"][self.print_paper_size])

    def _draw_labels(self) -> None:
        """Write all labels in the block info."""
        for group in self.dic_labels:
            self._set_label_style(group)
            self._write_labels(group["data"])
            if(group["underline"] == 1):
                self._draw_underlines(group["data"])

    def _draw_underlines(self, group_label: dict) -> None:
        """Draw a group of underlines

        Args:
            group_label (dic): A dictionary with the coordinates of a
                               group of underlines.
        """
        for label in group_label:
            posx, posy = label["position"][self.print_paper_size]
            len_txt = stringWidth(label["label"], 'Calibri-Bold', 9)
            self.c.line(posx, posy - 2, posx + len_txt, posy - 2)

    def _draw_check_box(self, position: list, selected: bool) -> None:
        """Draw a check box"""
        form = self.c.acroForm
        posx = position[0]
        posy = position[1]
        form.checkbox(
            checked=selected,
            x=posx, y=posy,
            borderStyle='solid',
            borderWidth=1,
            size=9
        )

    def _set_label_style(self, group_label: dict) -> None:
        """Set the text style for a group of labels

        Args:
            group_label (dic): A dictionary with the style data of
                              a group of labels.
        """
        bold = group_label["bold"]
        if bold == 1:
            self.c.setFont("Calibri-Bold", 9)
        else:
            self.c.setFont("Calibri", 9)

    def _write_labels(self, dic_labels: dict) -> None:
        """Write labels in the block info.

        Args:
            dic_labels (dic): A dictionary with the data
                              for the block info.
        """
        for label in dic_labels:
            posx, posy = label["position"][self.print_paper_size]
            msg = label["label"]
            self.c.drawString(posx, posy, msg)

    def draw_logo(self, logo: str) -> None:
        """Draw the Classy Closets logo in the upper left of the canvas.
           (override)

        Args:
            logo (str): The path of the logo with directory,
                        name and extension.
        """
        if self.print_paper_size == 'LEGAL':
            self.c.drawImage(logo, 18, 542, width=150, height=57, mask='auto',
                            preserveAspectRatio=True)
        elif self.print_paper_size == 'ELEVENSEVENTEEN':
            self.c.drawImage(logo, 18, 720, width=150, height=57, mask='auto',
                            preserveAspectRatio=True)

    def draw_block_info(self) -> None:
        """Draw the block info of the template in the canvas (override)."""
        self._draw_sections()
        self._draw_labels()