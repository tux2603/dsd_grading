import os
import tempfile
import zipfile
from datetime import datetime

import flet as ft
import platformdirs

from qar_submission import QARSubmission


class Grader:
    def __init__(self, *, app_directory: str|None = None) -> None:
        # TODO: do we really need this?
        self._zip_file_path: str|None = None

        if app_directory is None:
            app_directory = platformdirs.user_data_dir(
                appname='ECE3140',
                appauthor='TechGrading'
            )

        self.app_directory = app_directory
        self._working_dir: str|None = None
        self._student_submissions: list[QARSubmission] = []

        self._file_tab: tuple[ft.Tab, ft.Control]|None = None
        self._grading_tab: tuple[ft.Tab, ft.Control]|None = None
        self._grades_tab: tuple[ft.Tab, ft.Control]|None = None



    ########################################
    ###### PROPERTIES FOR UI ELEMENTS ######
    ########################################

    @property
    def zip_management_column(self) -> ft.Column:
        upload_row_controls = [
            # Zip file selection column
            ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text('Upload a Zip File'),
                    ft.Button(
                        content='Browse',
                        on_click=self.handle_pick_zip_file
                    )
                ]
            ),
            ft.Container(
                alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    'or',
                    theme_style=ft.TextThemeStyle.BODY_SMALL,
                    color=ft.Colors.ON_SURFACE
                )
            ),
            # Folder selection column
            ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        'Select and Existing Directory'
                    ),
                    ft.Button(
                        content='Browse',
                        on_click=lambda e: print('Select existing directory button clicked')
                    )
                ]
            )
        ]

        return ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=upload_row_controls
                ),
                ft.Divider(),
                ft.Text('Select student submissions to grade'),
                ft.ListView(
                    expand=True,
                    # Check list of student submissions
                    controls=[
                        # Check list tiles with very little spacing and padding
                        ft.ListTile(
                            title=f'{submission.student_name} - {submission.submission_name}',
                            leading=ft.Checkbox(
                                value=False,
                                on_change=lambda e: print(f'Checkbox for {e.control.parent.title} changed to {e.control.value}')
                            ),
                            dense=True,
                        ) for submission in self._student_submissions
                    ]
                ) if self._student_submissions else ft.Text(
                    '(No student submissions found)',
                    theme_style=ft.TextThemeStyle.BODY_SMALL,
                    color=ft.Colors.ON_SURFACE
                )
            ]
        )


    @property
    def file_tab(self) -> tuple[ft.Tab, ft.Control]:
        if self._file_tab is not None:
            return self._file_tab

        tab = ft.Tab(
            label='File',
            icon=ft.Icons.FOLDER
        )

        # Create three columns for the file tab. The first column will manage zip file uploads,
        # the second column will manage simulation scripts, and the third column will manage the rubric

        script_management_column_controls: list[ft.Control] = [
            ft.Text('Simulation Scripts')
        ]

        rubric_management_column_controls: list[ft.Control] = [
            ft.Text('Rubrics')
        ]

        control = ft.Row(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                self.zip_management_column,
                ft.VerticalDivider(),
                ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.START,
                    controls=script_management_column_controls
                ),
                ft.VerticalDivider(),
                ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.START,
                    controls=rubric_management_column_controls
                )
            ]
        )

        self._file_tab = tab, control

        return self._file_tab


    @property
    def grading_tab(self) -> tuple[ft.Tab, ft.Control]:
        if self._grading_tab is not None:
            return self._grading_tab

        tab = ft.Tab(
            label='Grading',
            icon=ft.Icons.CHECKLIST
        )

        control = ft.Container(
            alignment=ft.Alignment.CENTER,
            content=ft.Text('Grading content'),
        )

        self._grading_tab = tab, control
        return self._grading_tab


    @property
    def grades_tab(self) -> tuple[ft.Tab, ft.Control]:
        if self._grades_tab is not None:
            return self._grades_tab

        tab = ft.Tab(
            label='Grades',
            icon=ft.Icons.SCORE
        )

        control = ft.Container(
            alignment=ft.Alignment.CENTER,
            content=ft.Text('Grades content'),
        )

        self._grades_tab = tab, control
        return self._grades_tab



    #################################################
    ##### GETTERS AND SETTERS FOR CONFIGURATION #####
    #################################################

    @property
    def app_directory(self) -> str:
        return self._app_directory


    @app_directory.setter
    def app_directory(self, value: str) -> None:
        if not os.path.isdir(value):
            os.makedirs(value, exist_ok=True)
        self._app_directory = value


    @property
    def working_dir(self) -> str|None:
        return self._working_dir



    ##########################################
    ###### ASYNC HANDLERS FOR UI EVENTS ######
    ##########################################

    async def handle_pick_zip_file(self, e: ft.Event[ft.Button]):
        files = await ft.FilePicker().pick_files(
            allow_multiple=False,
            allowed_extensions=['zip'],
            initial_directory=os.getcwd()
        )

        if files:
            file_path = files[0].path if files[0].path else files[0].name

            if not os.path.isfile(file_path):
                raise FileNotFoundError(f'File {file_path} does not exist.')

            self._extract_zip_file(file_path)

            print(f'Zip file {file_path} extracted to {self.working_dir}')



    ####################################################
    ###### FILE MANAGEMENT AND EXTRACTION METHODS ######
    ####################################################

    def _extract_zip_file(self, zip_file_path: str) -> None:
        # Get just the filename from the path
        filename = os.path.basename(zip_file_path)
        timestamp = datetime.now().strftime('%Y%mm%d_%H%M%S')  # noqa: DTZ005

        # Create a directory to extract the zip file into
        extract_dir = tempfile.mkdtemp(dir=self.app_directory, prefix=f'{filename[:-4]}_{timestamp}_')

        self._working_dir = extract_dir

        # Extract the zip file into the directory
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        self._index_working_dir()


    def _reimport_directory(self, working_dir: str) -> None:
        self._working_dir = working_dir
        self._index_working_dir()


    def _index_working_dir(self) -> None:
        if self.working_dir is None:
            raise ValueError('Working directory is not set.')

        self._student_submissions.clear()

        # Find all of the qar files in the working directory and create a list of them
        for file in os.listdir(self.working_dir):
            if file.endswith('.qar'):
                submission = QARSubmission(file, self.working_dir)
                self._student_submissions.append(submission)
                print(f'Added submission {submission.submission_name} for student {submission.student_name}')

        if self._file_tab is not None:
            self._file_tab[0].update()  # Update the file tab to reflect the new submissions
        else:
            print('How the heck did you manage that?')
