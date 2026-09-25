from functools import partial

import flet as ft

from grader import Grader


def main(page: ft.Page, *, grader: Grader) -> None:
    page.title = "ECE 3140 Grading Tool"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    file_tab, file_container = grader.file_tab
    grading_tab, grading_container = grader.grading_tab
    grades_tab, grades_container = grader.grades_tab

    tabs: list[ft.Control] = [file_tab, grading_tab, grades_tab]
    containers: list[ft.Control] = [file_container, grading_container, grades_container]

    tab_ui = ft.Tabs(
        length=len(tabs),
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=tabs
                ),
                ft.TabBarView(
                    expand=True,
                    controls=containers
                )
            ]
        )
    )

    page.add(tab_ui)

if __name__ == "__main__":
    main_ui_partial = partial(main, grader=Grader())
    ft.run(main_ui_partial)
