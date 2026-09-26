from functools import partial

import flet as ft

from grader import Grader
from main import main as main_ui
from qar_submission import QARSubmission

__all__ = ["Grader"]

def main() -> None:
    print("Starting the DSD Grader!")
    main_ui_partial = partial(main_ui, grader=Grader())
    ft.run(main_ui_partial)
