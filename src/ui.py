import flet as ft

from file_management_tab import FileTab
from grader_data import GraderData
from grading_tab import GradingTab


@ft.component
def AppView(grader_data: GraderData, page: ft.Page) -> list[ft.Control]:
    file_tab = FileTab(grader_data=grader_data, page=page)
    grading_tab = GradingTab(grader_data=grader_data)

    tabs: list[ft.Control] = [file_tab, grading_tab]

    return [ft.Tabs(
        length=len(tabs),
        selected_index=grader_data.selected_tab_index,
        on_change=lambda e: setattr(grader_data, 'selected_tab_index', e.control.selected_index),
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(
                            label='File',
                            icon=ft.Icons.FOLDER
                        ),
                        ft.Tab(
                            label='Grading',
                            icon=ft.Icons.SCHOOL
                        )
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=tabs
                )
            ]
        )
    )]

def main(page: ft.Page, grader_data: GraderData):
    page.title = 'ECE 3140 Grading Tool'
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    page.render(AppView, grader_data=grader_data, page=page)
