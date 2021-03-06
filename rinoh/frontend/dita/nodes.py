# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
import re

from ... import styleds
from ...dimension import DimensionUnit, PT, INCH, CM, MM, PICA
from ...reference import TITLE
from ...reference import PAGE

from ..xml.elementtree import Parser

from . import BodyElement, BodySubElement, InlineElement, GroupingElement


class Map(BodyElement):
    def tree(self):
        return ([styleds.SetMetadataFlowable(title=self.get('title'))]
                + self.children_flowables())


class TopicRef(BodyElement):
    def build_flowable(self):
        from . import DITAReader
        reader = DITAReader()
        with open(self.get('href')) as file:
            return reader.parse(file)


class Concept(GroupingElement):
    grouped_flowables_class = styleds.Section

    def tree(self):
        section, = self.flowables()
        return section


class ConBody(GroupingElement):
    pass


class Task(GroupingElement):
    grouped_flowables_class = styleds.Section

    def tree(self):
        section, = self.flowables()
        return section


class ShortDesc(BodyElement):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content(), style='shortdesc')


class TaskBody(GroupingElement):
    pass


class Context(GroupingElement):
    pass


class P(BodyElement):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content())


class Steps(BodyElement):
    style = None

    def build_flowables(self):
        try:
            for flowable in self.stepsection.flowables():
                yield flowable
        except AttributeError:
            pass
        yield styleds.List([step.process() for step in self.step],
                           style=self.style)


class StepSection(BodyElement):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content())


class Step(BodySubElement):
    def process(self):
        return self.children_flowables()


class Cmd(BodyElement):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content())


class Result(GroupingElement):
    pass


class Related_Links(GroupingElement):
    pass


class Link(BodyElement):
    def build_flowable(self):
        xml_path = self.node._root._roottree._filename
        target_path = os.path.join(os.path.dirname(xml_path), self.get('href'))
        parser = Parser(None)
        xml_tree = parser.parse(target_path)
        target_id = xml_tree.getroot().get('id')
        section_ref = styleds.Reference(target_id, type=TITLE)
        page_ref = styleds.Reference(target_id, type=PAGE)
        return styleds.Paragraph(section_ref + ' on page ' + page_ref)


RE_LENGTH_PERCENT_UNITLESS = re.compile(r'^(?P<value>\d+)(?P<unit>[a-z%]*)$')

PIXEL = DimensionUnit(1 / 100 * INCH)

DOCUTILS_UNIT_TO_DIMENSION = {'': PIXEL,
                              'pc': PICA,
                              'pt': PT,
                              'px': PIXEL,
                              'in': INCH,
                              'cm': CM,
                              'mm': MM,
                              'em': None}


def convert_quantity(quantity_string):
    if quantity_string is None:
        return None
    value, unit = RE_LENGTH_PERCENT_UNITLESS.match(quantity_string).groups()
    return float(value) * DOCUTILS_UNIT_TO_DIMENSION[unit]


class Image(BodyElement, InlineElement):
    @property
    def image_path(self):
        href = self.get('href')
        xml_path = self.node._root._roottree._filename
        return os.path.normcase(os.path.join(os.path.dirname(xml_path), href))

    @property
    def arguments(self):
        # height = convert_quantity(self.get('height'))
        width = convert_quantity(self.get('width'))
        scale = self.get('scale', 100) / 100
        return dict(width=width, scale=scale)

    def build_flowable(self):
        return styleds.Image(self.image_path, **self.arguments)

    def build_styled_text(self, strip_leading_whitespace):
        return styleds.InlineImage(self.image_path, **self.arguments)


class UL(BodyElement):
    def build_flowable(self):
        return styleds.List([list(item.flowables()) for item in self.li],
                            style='enumerated')


class LI(GroupingElement):
    def build_flowables(self, **kwargs):
        if self.text:
            yield styleds.Paragraph(self.process_content())
        for flowable in self.children_flowables():
            yield flowable
