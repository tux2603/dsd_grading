import flet as ft

from file_management_tab import FileTab
from grader_data import GraderData
from grading_tab import GradingTab
from results_tab import ResultsTab


@ft.component
def AppView(grader_data: GraderData, page: ft.Page) -> list[ft.Control]:
    file_tab = FileTab(grader_data=grader_data, page=page)
    grading_tab = GradingTab(grader_data=grader_data, page=page)
    results_tab = ResultsTab(grader_data=grader_data, page=page)

    tabs: list[ft.Control] = [file_tab, grading_tab, results_tab]

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
                        ),
                        ft.Tab(
                            label='Results',
                            icon=ft.Icons.LIST
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
    page.window.full_screen = True
    page.title = 'ECE 3140 Grading Tool'
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def exit_fullscreen():
        page.window.full_screen = False
        page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == 'Escape':
            exit_fullscreen()

    page.on_keyboard_event = on_keyboard

    page.render(AppView, grader_data=grader_data, page=page)
