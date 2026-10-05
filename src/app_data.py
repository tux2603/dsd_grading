import os
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime

import flet as ft


@ft.observable
@dataclass
class AppData:
    app_dir: str
    _working_dir: str|None = field(default=None, init=False)
    _quartus_path: str|None = field(default=None, init=False)
    _ghdl_path: str|None = field(default=None, init=False)

    @property
    def working_dir(self) -> str:
        if not os.path.exists(self.app_dir):
            os.makedirs(self.app_dir)

        if self._working_dir is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # noqa: DTZ005
            self._working_dir = tempfile.mkdtemp(dir=self.app_dir, prefix=f'dsd_grading_{timestamp}_')
        return self._working_dir

    @property
    def quartus_path(self) -> str:
        if self._quartus_path is None:
            # First, check to see of quartus_sh is already in the path
            if shutil.which('quartus_sh') is not None:
                self._quartus_path = os.path.dirname(shutil.which('quartus_sh'))  # ty: ignore[no-matching-overload]
            else:
                # Check some default paths
                # TODO: make this a little bit more robust
                default_paths = [
                    r'E:\altera_lite25.1std\quartus\bin64',
                    r'C:\altera_lite\25.1std\quartus\bin64',
                    r'/opt/intelFPGA_lite/25.1std/quartus/bin',
                    r'/opt/intelFPGA/25.1std/quartus/bin',
                ]

                for path in default_paths:
                    if os.path.isfile(os.path.join(path, 'quartus_sh.exe')):
                        self._quartus_path = path
                        break

            # If we still haven't found it, raise an error
            if self._quartus_path is None:
                raise FileNotFoundError('quartus_sh not found in PATH or default locations. Please install Quartus or add it to your PATH.')

        return self._quartus_path

    @property
    def ghdl_path(self) -> str:
        if self._ghdl_path is None:
            # First, check to see of ghdl is already in the path
            if shutil.which('ghdl') is not None:
                self._ghdl_path = os.path.dirname(shutil.which('ghdl'))  # ty: ignore[no-matching-overload]
            else:
                # Check some default paths
                default_paths = [
                    r'E:\ghdl\bin',
                    r'C:\ghdl\bin',
                    r'/usr/local/bin',
                    r'/usr/bin'
                ]

                for path in default_paths:
                    if os.path.isfile(os.path.join(path, 'ghdl.exe')):
                        self._ghdl_path = path
                        break

            # If we still haven't found it, raise an error
            if self._ghdl_path is None:
                raise FileNotFoundError('ghdl not found in PATH or default locations. Please install GHDL or add it to your PATH.')

        return self._ghdl_path
