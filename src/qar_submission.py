import asyncio
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field

import anyio
import flet as ft

from app_data import AppData
from makefile import Makefile, MakefileTarget, MakefileVariable
from qsf_parser import QSFParser
from rubric_data import RubricItemScore
from testbench_data import TestbenchData


@ft.observable
@dataclass
class QARSubmissionData:
    app_data: AppData
    qar_file: str
    selected: bool = True
    error_occurred: bool = field(default=False, init=False)

    _extracted: bool = field(init=False, default=False)
    _extracted_dir: str|None = field(init=False, default=None)
    _student_name: str|None = field(init=False, default=None)
    _submission_name: str|None = field(init=False, default=None)
    _sim_dir: str|None = field(init=False, default=None)
    _makefile_prepared: bool = field(init=False, default=False)

    source_files: list[str] = field(default_factory=list, init=False)
    output_files: list[str] = field(default_factory=list, init=False)
    selected_file: str|None = field(default=None, init=False)
    selected_file_contents: str = field(default='', init=False)

    # TODO: add support for gold stars
    rubric_scores: list[RubricItemScore] = field(default_factory=list, init=False)

    @property
    def extracted(self) -> bool:
        return self._extracted

    @property
    def extracted_dir(self) -> str:
        if self._extracted_dir is None:
            raise ValueError('QAR submission has not been extracted yet.')
        return self._extracted_dir

    @property
    def student_name(self) -> str:
        if self._student_name is None:
            self._student_name, self._submission_name = self._parse_qar_file_name()

        return self._student_name

    @property
    def submission_name(self) -> str:
        if self._submission_name is None:
            self._student_name, self._submission_name = self._parse_qar_file_name()

        return self._submission_name

    def selected_event(self, e: ft.Event[ft.Checkbox]) -> None:
        self.selected = e.control.value if e.control.value is not None else False


    def select_file_event(self, e: ft.Event[ft.Dropdown]) -> None:
        self.selected_file = e.control.value if e.control.value is not None else None

        if self.selected_file is not None:
            selected_file_path = os.path.join(self.extracted_dir, 'sim', self.selected_file)
            with open(selected_file_path, 'r') as file:
                file_content = file.read()

            # Determine the language for syntax highlighting based on the file extension
            _, file_extension = os.path.splitext(self.selected_file)
            language = 'vhdl' if file_extension.lower() == '.vhd' else ''

            self.selected_file_contents = f'Contents of {self.selected_file}:\n~~~{language}\n{file_content}\n~~~'

    def upload_bitstream_event(self, e: ft.Event[ft.Button], page: ft.Page) -> None:
        if not self._extracted:
            raise ValueError('QAR submission has not been extracted yet. Cannot upload bitstream.')
        if not self._makefile_prepared:
            raise ValueError('Makefile has not been prepared yet. Cannot upload bitstream.')

        # Spawn the make process
        make_process = subprocess.run(
            ['make', 'upload'],
            cwd=self._extracted_dir,
            text=True,
            check=False
        )

        if make_process.returncode != 0:
            page.show_dialog(ft.SnackBar(
                ft.Text(f'Failed to upload bitstream for {self.student_name}'),
                open=True,
                duration=2000,
                bgcolor=ft.Colors.RED_100
            ))
        else:
            page.show_dialog(ft.SnackBar(
                ft.Text(f'Successfully uploaded bitstream for {self.student_name}'),
                open=True,
                duration=2000,
                bgcolor=ft.Colors.GREEN_100
            ))

    async def extract(self):
        if self._extracted:
            raise ValueError('QAR submission has already been extracted.')

        qsh_path = os.path.join(self.app_data.quartus_path, 'quartus_sh')
        extract_path = os.path.join(self.app_data.working_dir, f'{self.student_name}_{self.submission_name}_extracted')
        qar_path = os.path.join(self.app_data.working_dir, self.qar_file)

        process = await asyncio.create_subprocess_exec(
            qsh_path, '--restore', '-output', extract_path, qar_path,
        )

        return_code = await process.wait()
        _, stderr = await process.communicate()

        # Check to see that the command exitied successfully
        if return_code != 0:
            raise RuntimeError(f'Failed to extract QAR file {self.qar_file}. Error: {stderr}')

        # Copy in the testbench files if they are provided
        sim_path = os.path.join(extract_path, 'sim')
        if not os.path.exists(sim_path):
            os.makedirs(sim_path, exist_ok=True)

        self._extracted_dir = extract_path
        self._sim_dir = sim_path
        self._extracted = True
        print(f'extracted {self.student_name}')

    async def prepare_make_file(self, testbenches: list[TestbenchData]) -> None:
        if not self._extracted or self._sim_dir is None:
            await self.extract()

        # Parse the QSF file to find the synthesis and simulation files
        qsf_files = [f for f in os.listdir(self._extracted_dir) if f.endswith('.qsf')]

        if len(qsf_files) == 0:
            raise FileNotFoundError(f'No .qsf file found in extracted directory {self._extracted_dir}.')
        elif len(qsf_files) > 1:
            raise ValueError(f'Multiple .qsf files found in extracted directory {self._extracted_dir}. Please ensure there is only one QSF file.')

        qsf_file_path = os.path.join(self._extracted_dir, qsf_files[0])  # ty: ignore[no-matching-overload]

        qsf_parser = QSFParser()

        # with open(qsf_file_path, 'r') as qsf_file:
        #     qsf_parser.parse(qsf_file)
        async with await anyio.open_file(qsf_file_path, 'r') as qsf_file:
            contents = await qsf_file.read()
            qsf_parser.parse(contents)

        # Extract the file information from the QSF parser
        vhdl_files = qsf_parser.vhdl_files
        vhdl_tb_files = qsf_parser.vhdl_testbench_files
        tb_names = qsf_parser.testbench_names
        tb_names.extend([tb.testbench_name for tb in testbenches])

        self.source_files = []
        self.output_files = []

        # Copy all of the necessary files into the sim directory
        for vhdl_file in vhdl_files:
            src_path = os.path.join(self._extracted_dir, vhdl_file) # ty: ignore[no-matching-overload]
            dest_path = os.path.join(self._sim_dir, vhdl_file) # ty: ignore[no-matching-overload]
            shutil.copy(src_path, dest_path)
            self.source_files.append(os.path.basename(dest_path))

        for vhdl_tb_file in vhdl_tb_files:
            src_path = os.path.join(self._extracted_dir, vhdl_tb_file) # ty: ignore[no-matching-overload]
            dest_path = os.path.join(self._sim_dir, vhdl_tb_file) # ty: ignore[no-matching-overload]
            shutil.copy(src_path, dest_path)
            self.source_files.append(os.path.basename(dest_path))

        for tb in testbenches:
            src_path = tb.testbench_file
            dest_path = os.path.join(self._sim_dir, os.path.basename(tb.testbench_file)) # ty: ignore[no-matching-overload]
            shutil.copy(src_path, dest_path)
            self.source_files.append(os.path.basename(dest_path))

        # Find the qpf file in the extracted directory
        qpf_files = [f for f in os.listdir(self._extracted_dir) if f.endswith('.qpf')]
        if len(qpf_files) == 0:
            raise FileNotFoundError(f'No .qpf file found in extracted directory {self._extracted_dir}.')
        elif len(qpf_files) > 1:
            raise ValueError(f'Multiple .qpf files found in extracted directory {self._extracted_dir}. Please ensure there is only one project file.')

        qpf_file_name = qpf_files[0]

        # Start creating a makefile that will compile the project and run the simulation
        makefile = Makefile()

        # Add a target to build the project using quartus_sh
        tld_name = qsf_parser.top_level_entity
        makefile.add_variable(MakefileVariable(name='QSH', value=os.path.join(self.app_data.quartus_path, 'quartus_sh')))
        makefile.add_target(MakefileTarget(name=os.path.join('output_files', f'{tld_name}.sof'), dependencies=[qpf_file_name], commands=[
            f'$(QSH) --flow compile {qpf_file_name}'
        ]))

        # Add a target to run each of the tesbenches using ghdl
        makefile.add_variable(MakefileVariable(name='GHDL', value=os.path.join(self.app_data.ghdl_path, 'ghdl')))

        for tb_name in tb_names:
            vhdl_file_paths = [os.path.join('sim', vhdl_file) for vhdl_file in vhdl_files]
            # vhdl_tb_file_paths = [os.path.join('sim', vhdl_tb_file) for vhdl_tb_file in vhdl_tb_files]

            dependencies = list({*vhdl_file_paths, os.path.join('sim', f'{tb_name}.vhd')})
            target = os.path.join('sim', f'{tb_name}.vcd')
            data_log = os.path.join('sim', f'{tb_name}.log')

            makefile.add_target(MakefileTarget(name=target, dependencies=dependencies, is_phony=False, exclude_from_all=True, commands=[
                '$(GHDL) -i --std=08 $^',
                f'$(GHDL) -m --std=08 {tb_name}',
                f'$(GHDL) -r --std=08 {tb_name} --vcd=$@ >{data_log}'
            ]))

            self.output_files.append(os.path.basename(target))
            self.output_files.append(os.path.basename(data_log))

        # Add a target that runs all simulation targets
        sim_targets = [os.path.join('sim', f'{tb_name}.vcd') for tb_name in tb_names]
        makefile.add_target(MakefileTarget(name='simulate', dependencies=sim_targets, is_phony=True, commands=[
            'echo "All testbenches complete."'
        ]))

        # Add a target that uploads the bistream to the DE10-Nano board
        tld_name = qsf_parser.top_level_entity
        sof_path = os.path.join('output_files', f'{tld_name}.sof')
        qpgm_path = os.path.join(self.app_data.quartus_path, 'quartus_pgm')
        makefile.add_variable(MakefileVariable(name='QPGM', value=qpgm_path))
        makefile.add_target(MakefileTarget(name='upload', dependencies=[sof_path], is_phony=True, exclude_from_all=True, commands=[
            f'$(QPGM) -c USB-Blaster -m JTAG -o "p;{sof_path}@1"'
        ]))

        # Write the makefile to the extracted directory
        makefile_path = os.path.join(self._extracted_dir, 'Makefile') # ty: ignore[no-matching-overload]
        async with await anyio.open_file(makefile_path, 'w') as makefile_file:
            await makefile_file.write(str(makefile))

        print(f'Prepared makefile for student {self.student_name} in directory {self._extracted_dir}.')

        self._makefile_prepared = True

    def _parse_qar_file_name(self) -> tuple[str, str]:
        match = re.match(r'^(\w+)_\d+_\d+_(.+?)\.qar$', self.qar_file)
        if not match:
            raise ValueError(f'QAR file \'{self.qar_file}\' does not match the expected format.')
        return match.group(1), match.group(2)
