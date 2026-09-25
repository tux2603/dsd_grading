import flet as ft


class Grader:
    def __init__(self):
        self._zip_file_path: str|None = None



    ########################################
    ###### PROPERTIES FOR UI ELEMENTS ######
    ########################################

    @property
    def file_tab(self) -> tuple[ft.Tab, ft.Control]:
        tab = ft.Tab(
            label='File',
            icon=ft.Icons.FOLDER
        )

        # Create three columns for the file tab. The first column will manage zip file uploads,
        # the second column will manage simulation scripts, and the third column will manage the rubrics
        zip_management_column_controls: list[ft.Control] = [
            ft.Text("Zip File Upload")
        ]

        script_management_column_controls: list[ft.Control] = [
            ft.Text("Simulation Scripts")
        ]

        rubric_management_column_controls: list[ft.Control] = [
            ft.Text("Rubrics")
        ]

        control = ft.Row(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=zip_management_column_controls
                ),
                ft.VerticalDivider(),
                ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=script_management_column_controls
                ),
                ft.VerticalDivider(),
                ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=rubric_management_column_controls
                )
            ]
        )

        return tab, control

    @property
    def grading_tab(self) -> tuple[ft.Tab, ft.Control]:
        tab = ft.Tab(
            label='Grading',
            icon=ft.Icons.CHECKLIST
        )

        control = ft.Container(
            alignment=ft.Alignment.CENTER,
            content=ft.Text("Grading content"),
        )

        return tab, control

    @property
    def grades_tab(self) -> tuple[ft.Tab, ft.Control]:
        tab = ft.Tab(
            label='Grades',
            icon=ft.Icons.SCORE
        )

        control = ft.Container(
            alignment=ft.Alignment.CENTER,
            content=ft.Text("Grades content"),
        )

        return tab, control



    #################################################
    ##### GETTERS AND SETTERS FOR CONFIGURATION #####
    #################################################

    @property
    def zip_file_path(self) -> str:
        if self._zip_file_path is None:
            raise ValueError("Zip file path has not been set.")
        return self._zip_file_path

    @zip_file_path.setter
    def zip_file_path(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Zip file path must be a string.")

        # TODO: actually load in the zip file here

        self._zip_file_path = value
