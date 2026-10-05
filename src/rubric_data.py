from dataclasses import dataclass, field

import flet as ft


@ft.observable
@dataclass
class RubricItem:
    name: str
    description: str
    points: int
    is_bonus: bool = False

@ft.observable
@dataclass
class RubricItemScore:
    rubric_item: RubricItem
    points_off: int = field(default=0, init=False)
    feedback: str = field(default='', init=False)

    # After init, set points off to the max if the rubric item is a bonus
    def __post_init__(self) -> None:
        if self.rubric_item.is_bonus:
            self.points_off = self.rubric_item.points

    @property
    def score(self) -> int:
        return self.rubric_item.points - self.points_off

    @score.setter
    def score(self, value: int) -> None:
        if value < 0:
            self.points_off = self.rubric_item.points
        elif value > self.rubric_item.points:
            self.points_off = 0
        else:
            self.points_off = self.rubric_item.points - value

    def on_score_change(self, e: ft.Event[ft.TextField]) -> None:
        try:
            new_score = int(e.control.value)
        except ValueError:
            new_score = 0

        if new_score < 0:
            new_score = 0
        elif new_score > self.rubric_item.points:
            new_score = self.rubric_item.points

        self.score = new_score

    def on_bonus_change(self, e: ft.Event[ft.Checkbox]) -> None:
        if e.control.value:
            self.score = self.rubric_item.points
        else:
            self.score = 0
