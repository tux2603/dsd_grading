from dataclasses import dataclass
from pathlib import Path

import lark


@dataclass
class GlobalAssignment:
    name: str
    value: str
    section_id: str|None = None

class QSFParser:
    def __init__ (self) -> None:
        with open(Path(__file__).parent / 'qsf_grammar.lark', 'r') as grammar_file:
            grammar = grammar_file.read()

        self.parser = lark.Lark(grammar, propagate_positions=True)
        self.global_assignments: list[GlobalAssignment] = []

    def parse(self, qsf_str: str) -> None:
        tree = self.parser.parse(qsf_str)

        self.global_assignments: list[GlobalAssignment] = []

        for global_assignment_tree in tree.find_data('global_assignment'):
            name = None
            value = None
            section_id = None

            for child in global_assignment_tree.children:
                if type(child) is lark.Token and child.type == 'NAME':
                    name = child.value
                elif type(child) is lark.Token and child.type == 'VALUE':
                    value = child.value
                elif type(child) is lark.Token and child.type == 'SECTION':
                    section_id = child.value

            if name is None or value is None:
                raise ValueError(f'Invalid global assignment at line {global_assignment_tree.meta.line}')

            self.global_assignments.append(GlobalAssignment(name=name, value=value, section_id=section_id))

    @property
    def vhdl_files(self) -> list[str]:
        return [assignment.value for assignment in self.global_assignments if assignment.name == 'VHDL_FILE']

    @property
    def vhdl_testbench_files(self) -> list[str]:
        return [assignment.value for assignment in self.global_assignments if assignment.name == 'VHDL_TEST_BENCH_FILE']

    @property
    def testbench_names(self) -> list[str]:
        return [assignment.value for assignment in self.global_assignments if assignment.name == 'EDA_TEST_BENCH_NAME' and assignment.section_id == 'eda_simulation']

    @property
    def top_level_entity(self) -> str:
        top_level_entities = [assignment.value for assignment in self.global_assignments if assignment.name == 'TOP_LEVEL_ENTITY']

        if len(top_level_entities) == 0:
            raise ValueError('No TOP_LEVEL_ENTITY found in QSF file.')
        elif len(top_level_entities) > 1:
            raise ValueError('Multiple TOP_LEVEL_ENTITY found in QSF file.')

        return top_level_entities[0]
