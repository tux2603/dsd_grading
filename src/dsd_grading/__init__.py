from functools import partial

import flet as ft
import platformdirs

from app_data import AppData
from grader_data import GraderData
from ui import main as main_ui


def main() -> None:
    print("Starting the DSD Grader!")

    app_dir = platformdirs.user_data_dir(
        appname='ECE3140',
        appauthor='TechGrading'
    )

    app_data = AppData(app_dir=app_dir)
    grader_data = GraderData(app_data=app_data)

    main_ui_partial = partial(main_ui, grader_data=grader_data)
    ft.run(main_ui_partial)
