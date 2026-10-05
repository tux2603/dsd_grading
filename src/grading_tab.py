from functools import partial

import flet as ft

from grader_data import GraderData
from qar_submission import QARSubmissionData
from rubric_data import RubricItemScore


@ft.component
def FileDisplayPanel(qar_submission_data: QARSubmissionData) -> ft.Column:
    sub_files = [*qar_submission_data.source_files, *qar_submission_data.output_files]

    # Filter out vcd files for now
    # TODO: add support for vcd files in the future
    sub_files = [file for file in sub_files if not file.endswith('.vcd')]

    file_selection_dropdown = ft.Dropdown(
        value=qar_submission_data.selected_file,
        on_select=qar_submission_data.select_file_event,
        options=[
            ft.dropdown.Option(
                key=file,
                text=file
            ) for file in sub_files
        ]
    )

    file_contents = qar_submission_data.selected_file_contents if qar_submission_data.selected_file_contents else 'Select a file to view its contents.'

    file_view_pane = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.ADAPTIVE,
        controls=[
            ft.Markdown(
                value=file_contents,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                expand=True,
            )
        ]
    )

    return ft.Column(
        expand=2,
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    ft.Text('Select File to View:'),
                    file_selection_dropdown
                ]
            ),
            file_view_pane
        ]
    )

@ft.component
def RubricFeedbackItem(rubric_item_score: RubricItemScore) -> ft.Column:
    header = ft.Text(
        f'{rubric_item_score.rubric_item.description}',
    )

    if rubric_item_score.rubric_item.is_bonus:
        controls: list[ft.Control] = [
            header,
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    ft.Checkbox(
                        value=rubric_item_score.score == rubric_item_score.rubric_item.points,
                        on_change=rubric_item_score.on_bonus_change
                    ),
                    ft.Text('Bonus applied'),
                ]
            )
        ]
    else:
        controls: list[ft.Control] = [
            header,
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    ft.Text('Score: '),
                    ft.TextField(
                        value=str(rubric_item_score.score),
                        on_change=rubric_item_score.on_score_change,
                        on_submit=rubric_item_score.on_score_change,
                        width=100
                    ),
                    ft.Text(f' / {rubric_item_score.rubric_item.points} points')
                ]
            ),
            ft.TextField(
                value=rubric_item_score.feedback,
                on_change=lambda e: setattr(rubric_item_score, 'feedback', e.control.value),
                on_submit=lambda e: setattr(rubric_item_score, 'feedback', e.control.value),
                label='Feedback',
                multiline=True,
                min_lines=1,
                expand=True
            )
        ]

    return ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        controls=controls
    )

@ft.component
def FeedbackPanel(qar_submission_data: QARSubmissionData) -> ft.Column:

    feedback_items = [RubricFeedbackItem(rubric_item_score) for rubric_item_score in qar_submission_data.rubric_scores]

    # Separate feedback items with a divider
    separated_feedback = []
    for i, item in enumerate(feedback_items):
        separated_feedback.append(item)
        if i < len(feedback_items) - 1:
            separated_feedback.append(ft.Divider())

    return ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Text('Feedback:'),
            # I need this to have a scroll bar if necessary
            ft.Column(
                expand=True,
                scroll=ft.ScrollMode.ADAPTIVE,
                alignment=ft.MainAxisAlignment.START,
                controls=separated_feedback
            )
        ]
    )


@ft.component
def GradingTab(grader_data: GraderData, page: ft.Page) -> ft.Row:
    if grader_data.current_submission is None:
        return ft.Row(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text('No submissions selected for grading.')
            ]
        )

    sub = grader_data.current_submission

    submission_navigation_panel = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                tooltip='Previous Submission',
                on_click=grader_data.prev_submission
            ),
            ft.Text(f'Submission {grader_data.current_submission_index + 1} of {len(grader_data.qar_submissions)}'),
            ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD,
                tooltip='Next Submission',
                on_click=grader_data.next_submission
            )
        ]
    )

    submission_status_panel = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Icon(
                ft.Icons.ERROR if sub.error_occurred else ft.Icons.CHECK,
                color=ft.Colors.RED if sub.error_occurred else ft.Colors.GREEN
            ),
            ft.Text(
                f'(Grading script was {'unsuccesful' if sub.error_occurred else 'successful'})',
                theme_style=ft.TextThemeStyle.BODY_SMALL,
            )
        ]
    )

    rubric_panel = FeedbackPanel(qar_submission_data=sub)

    left_column = FileDisplayPanel(qar_submission_data=sub)

    upload_partial = partial(sub.upload_bitstream_event, page=page)

    right_column = ft.Column(
        expand=1,
        alignment=ft.MainAxisAlignment.START,
        controls=[
            submission_navigation_panel,
            submission_status_panel,
            rubric_panel,
            ft.Divider(),
            ft.Container(
                alignment=ft.Alignment.CENTER_RIGHT,
                content=ft.Button(
                    'Upload Bitstream',
                    on_click=upload_partial
                )
            )
        ]
    )

    return ft.Row(
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        controls=[
            left_column,
            ft.VerticalDivider(),
            right_column
        ]
    )
