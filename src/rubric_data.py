from dataclasses import dataclass, field

import flet as ft


@ft.observable
@dataclass
class RubricItem:
    name: str
    description: str
    points: int

@ft.observable
@dataclass
class RubricItemScore:
    rubric_item: RubricItem
    score: int = field(default=0, init=False)
    feedback: str = field(default='', init=False)

    def on_score_change(self, e: ft.Event[ft.TextField]) -> None:
        # First, if the score is not an integer, make it one
        try:
            new_score = int(e.control.value)
        except ValueError:
            new_score = 0

        if new_score < 0:
            new_score = 0
        elif new_score > self.rubric_item.points:
            new_score = self.rubric_item.points

        self.score = new_score
