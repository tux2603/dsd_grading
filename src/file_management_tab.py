import os
from functools import partial

import anyio
import flet as ft
import yaml

from grader_data import GraderData
from rubric_data import RubricItem


async def pick_zip_file(e: ft.Event[ft.Button], grader_data: GraderData) -> None:
    files = await ft.FilePicker().pick_files(
        allow_multiple=False,
        allowed_extensions=['zip'],
        initial_directory=os.getcwd()
    )

    if files:
        file_path = files[0].path if files[0].path else files[0].name

        if not os.path.isfile(file_path):
            raise ValueError(f'Selected path is not a file: {file_path}')

        grader_data.extract_zip_file(file_path)


def pick_directory(e: ft.Event[ft.Button], grader_data: GraderData) -> None:
    print('Pick directory button clicked')


async def pick_tb_file(e: ft.Event[ft.Button], grader_data: GraderData) -> None:
    files = await ft.FilePicker().pick_files(
        allow_multiple=True,
        allowed_extensions=['vhd', 'vhdl'],
        initial_directory=os.getcwd()
    )

    if files:
        for file in files:
            file_path = file.path if file.path else file.name

            if not os.path.isfile(file_path):
                raise ValueError(f'Selected path is not a file: {file_path}')

            grader_data.add_testbench(file_path)

async def pick_rubric_file(e: ft.Event[ft.Button], grader_data: GraderData) -> None:
    files = await ft.FilePicker().pick_files(
        allow_multiple=False,
        allowed_extensions=['yaml'],
        initial_directory=os.getcwd()
    )

    if files:
        file_path = files[0].path if files[0].path else files[0].name

        if not os.path.isfile(file_path):
            raise ValueError(f'Selected path is not a file: {file_path}')

        async with await anyio.open_file(file_path, 'r') as file:
            rubric_data = yaml.safe_load(await file.read())

            for item in rubric_data.get('rubric_items', []):
                name = item.get('name', '')
                description = item.get('description', '')
                points = item.get('points', 0)

                grader_data.add_rubric_item(RubricItem(
                    name=name,
                    description=description,
                    points=points
                ))


@ft.component
def ZipManagementColumn(grader_data: GraderData, pick_zip_file, pick_directory) -> ft.Column:
    pick_zip_partial = partial(pick_zip_file, grader_data=grader_data)
    zip_select_button = ft.Button(
        content='Browse',
        on_click=pick_zip_partial
    )

    pick_dir_partial = partial(pick_directory, grader_data=grader_data)
    dir_select_button = ft.Button(
        content='Browse',
        on_click=pick_dir_partial
    )

    student_submission_list = ft.ListView(
        expand=True,
        controls=[
            ft.ListTile(
                title=f'{submission.student_name} - {submission.submission_name}',
                leading=ft.Checkbox(
                    value=submission.selected,
                    on_change=submission.selected_event
                ),
                dense=True
            ) for submission in grader_data.qar_submissions
        ]
    )

    return ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text('Upload a ZIP file'),
                            zip_select_button
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
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text('Select an Existing Directory'),
                            dir_select_button
                        ]
                    )
                ]
            ),
            ft.Divider(),
            ft.Text('Select student submissions to grade'),
            student_submission_list if grader_data.qar_submissions else ft.Text(
                '(No student submissions found)',
                theme_style=ft.TextThemeStyle.BODY_SMALL,
                color=ft.Colors.ON_SURFACE_VARIANT
            )
        ]
    )


@ft.component
def TestbenchManagementColumn(grader_data: GraderData, pick_tb_file) -> ft.Column:
    pick_tb_partial = partial(pick_tb_file, grader_data=grader_data)
    tb_select_button = ft.Button(
        content='Browse',
        on_click=pick_tb_partial
    )


    return ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text('Upload Testbench Files'),
                            tb_select_button
                        ]
                    )
                ]
            ),
            ft.Divider(),
            ft.Text('Select testbenches to use for grading'),
            ft.ListView(
                expand=True,
                controls=[
                    ft.ListTile(
                        title=f'{tb.testbench_name}',
                        leading=ft.Checkbox(
                            value=tb.selected,
                            on_change=tb.selected_event
                        ),
                        dense=True
                    ) for tb in grader_data.testbenches
                ] if grader_data.testbenches else [
                    ft.Text(
                        '(No testbenches found)',
                        theme_style=ft.TextThemeStyle.BODY_SMALL,
                        color=ft.Colors.ON_SURFACE_VARIANT
                    )
                ]
            )
        ]
    )


@ft.component
def RubricManagementColumn(grader_data: GraderData) -> ft.Column:
    rubric_select_button = ft.Button(
        content='Browse',
        on_click=partial(pick_rubric_file, grader_data=grader_data)
    )

    return ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text('Upload Rubric Files'),
                            rubric_select_button
                        ]
                    )
                ]
            ),
            ft.Divider(),
            ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    ft.Text(
                        f'({item.points} point{'s' if item.points != 1 else ''}) {item.name}: {item.description}'
                    ) for item in grader_data.rubric_items
                ]
            )
        ]
    )


@ft.component
def FileTab(grader_data: GraderData, page: ft.Page) -> ft.Column:
    zip_management_column = ZipManagementColumn(grader_data=grader_data, pick_zip_file=pick_zip_file, pick_directory=pick_directory)
    testbench_management_column = TestbenchManagementColumn(grader_data=grader_data, pick_tb_file=pick_tb_file)
    rubric_management_column = RubricManagementColumn(grader_data=grader_data)

    return ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Row(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    zip_management_column,
                    ft.VerticalDivider(),
                    testbench_management_column,
                    ft.VerticalDivider(),
                    rubric_management_column
                ]
            ),
            ft.Divider(),
            ft.Row(
                alignment=ft.MainAxisAlignment.END,
                controls=[
                    ft.Button(
                        'Grade Submissions',
                        on_click=grader_data.start_grading,
                        icon=grader_data.status_icon,
                    )
                ]
            )
        ]
    )
