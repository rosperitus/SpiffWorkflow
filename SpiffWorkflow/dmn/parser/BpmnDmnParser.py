import glob

from lxml import etree

from ...bpmn.parser.util import xpath_eval, full_tag
from ...bpmn.parser.ValidationException import ValidationException

from ...bpmn.parser.BpmnParser import BpmnParser
from ...dmn.parser.DMNParser import DMNParser
from ..engine.DMNEngine import DMNEngine


class BpmnDmnParser(BpmnParser):

    def __init__(self):
        super().__init__()
        self.dmn_parsers = {}
        self.dmn_parsers_by_name = {}
        self.dmn_dependencies = set()

    def get_engine(self, decision_ref, node):
        if decision_ref not in self.dmn_parsers:
            options = ', '.join(list(self.dmn_parsers.keys()))
            raise ValidationException(
                'No DMN Diagram available with id "%s", Available DMN ids are: %s' %(decision_ref, options),
                node=node, filename='')
        dmn_parser = self.dmn_parsers[decision_ref]
        dmn_parser.parse()
        decision = dmn_parser.decision
        return DMNEngine(decision.decisionTables[0])

    def add_dmn_xml(self, node, filename=None):
        """
        Add the given lxml representation of the DMN file to the parser's set.
        """
        xpath = xpath_eval(node)
        dmn_parser = DMNParser(self, node, filename=filename)
        self.dmn_parsers[dmn_parser.get_id()] = dmn_parser
        self.dmn_parsers_by_name[dmn_parser.get_name()] = dmn_parser

    def add_dmn_file(self, filename):
        """
        Add the given DMN filename to the parser's set.
        """
        self.add_dmn_files([filename])

    def add_dmn_files_by_glob(self, g):
        """
        Add all filenames matching the provided pattern (e.g. *.bpmn) to the
        parser's set.
        """
        self.add_dmn_files(glob.glob(g))

    def add_dmn_files(self, filenames):
        """
        Add all filenames in the given list to the parser's set.
        """
        for filename in filenames:
            f = open(filename, 'r')
            try:
                self.add_dmn_xml(etree.parse(f).getroot(), filename=filename)
            finally:
                f.close()

    def get_dependencies(self):
        return self.process_dependencies.union(self.dmn_dependencies)

    def get_dmn_dependencies(self):
        return self.dmn_dependencies

    def _find_dependencies(self, process):
        super()._find_dependencies(process)
        parser_cls, cls = self._get_parser_class(full_tag('businessRuleTask'))
        for business_rule in process.xpath('.//bpmn:businessRuleTask',namespaces=self.namespaces):
            self.dmn_dependencies.add(parser_cls.get_decision_ref(business_rule))