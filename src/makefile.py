from dataclasses import dataclass, field
from io import TextIOWrapper


@dataclass
class MakefileTarget:
    name: str
    dependencies: list[str]
    commands: list[str] = field(default_factory=list)
    is_phony: bool = False
    exclude_from_all: bool = False

    def __str__(self) -> str:
        deps = ' '.join(self.dependencies)
        cmds = '\n\t'.join(self.commands)
        return f'{self.name:s}: {deps}\n\t{cmds}'


@dataclass
class MakefileVariable:
    name: str
    value: str

    def __str__(self) -> str:
        return f'{self.name:s} = {self.value:s}'


class Makefile:
    def __init__ (self, variables: list[MakefileVariable]|None = None, targets: list[MakefileTarget]|None = None) -> None:
        self.variables : list[MakefileVariable] = variables if variables is not None else []
        self.targets : list[MakefileTarget] = targets if targets is not None else []

    def __str__(self) -> str:
        variables_str = '\n'.join(str(var) for var in self.variables)
        targets_str = '\n\n'.join(str(target) for target in self.targets)
        phony_str = f'.PHONY: all {' '.join(target.name for target in self.targets if target.is_phony)}' if any(target.is_phony for target in self.targets) else ''
        all_str = f'all: {' '.join(target.name for target in self.targets if not target.exclude_from_all)}' if self.targets else ''

        return f'{variables_str}\n\n{phony_str}\n\n{all_str}\n\n{targets_str}'

    def add_variable(self, variable: MakefileVariable) -> None:
        self.variables.append(variable)

    def add_target(self, target: MakefileTarget) -> None:
        self.targets.append(target)

    def write(self, file: TextIOWrapper) -> None:
        file.write(str(self))
