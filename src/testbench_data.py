import os
from dataclasses import dataclass, field

import flet as ft

from app_data import AppData


@ft.observable
@dataclass
class TestbenchData:
    app_data: AppData
    testbench_file: str
    selected: bool = True

    _testbench_name: str|None = field(init=False, default=None)

    @property
    def testbench_name(self) -> str:
        if self._testbench_name is None:
            self._testbench_name = os.path.splitext(os.path.basename(self.testbench_file))[0]

        return self._testbench_name

    def selected_event(self, e: ft.Event[ft.Checkbox]) -> None:
        self.selected = e.control.value if e.control.value is not None else False
