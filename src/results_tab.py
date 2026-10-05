from functools import partial

import flet as ft

from grader_data import GraderData
from qar_submission import QARSubmissionData


async def _copy_feedback_to_clipboard(e: ft.Event[ft.IconButton], feedback: str, page: ft.Page) -> None:
    await ft.Clipboard().set(feedback)
    page.show_dialog(ft.SnackBar(ft.Text('Feedback copied to clipboard!'),
        open=True,
        duration=1000,
        bgcolor=ft.Colors.GREEN_100
    ))


@ft.component
def SubmissionListTile(submission: QARSubmissionData, page: ft.Page) -> ft.ListTile:
    max_points = sum(score.rubric_item.points for score in submission.rubric_scores if not score.rubric_item.is_bonus)
    points_achieved = sum(score.score for score in submission.rubric_scores)

    feedback_strs = []

    for score in submission.rubric_scores:
        if not score.rubric_item.is_bonus:
            points_off = score.rubric_item.points - score.score
            if points_off > 0:
                feedback_strs.append(f'{score.feedback} ({points_off} point{'s' if points_off != 1 else ''} deducted)')
            elif score.feedback:
                feedback_strs.append(f'{score.feedback} (no points deducted)')
        elif score.score > 0:
                feedback_strs.append(f'{score.rubric_item.description} (+{score.score} bonus point{'s' if score.score != 1 else ''} awarded)')

    feedback_str = '\n'.join(feedback_strs) if feedback_strs else 'No feedback provided.'
    copy_feedback = partial(_copy_feedback_to_clipboard, feedback=feedback_str, page=page)

    return ft.ListTile(
        title=ft.Text(f'{submission.student_name} - {submission.submission_name}'),
        subtitle=ft.Column(
            controls=[
                ft.Text(f'Score: {points_achieved}/{max_points}'),
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.COPY,
                            tooltip='Copy feedback to clipboard',
                            on_click=copy_feedback
                        ),
                        ft.Column(
                            controls=[ft.Text(feedback) for feedback in feedback_strs],
                            spacing=2,
                        )
                    ]
                )
            ],
            spacing=5,
        ),
        leading=ft.Icon(ft.Icons.PERSON),
        trailing=ft.Icon(
            ft.Icons.CHECK_CIRCLE if not submission.error_occurred else ft.Icons.ERROR,
            color=ft.Colors.GREEN if not submission.error_occurred else ft.Colors.RED
        ),
    )


@ft.component
def ResultsTab(grader_data: GraderData, page: ft.Page) -> ft.Column:
    return ft.Column(
        controls=[
            ft.ListView(
                expand=True,
                spacing=5,
                padding=10,
                divider_thickness=1,
                controls=[
                    SubmissionListTile(submission=submission, page=page)
                    for submission in grader_data.qar_submissions
                ],
            ),
        ],
    )
