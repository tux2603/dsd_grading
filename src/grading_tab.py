import flet as ft

from grader_data import GraderData
from qar_submission import QARSubmissionData


@ft.component
def FileDisplayPanel(qar_submission_data: QARSubmissionData) -> ft.Column:
    sub_files = [*qar_submission_data.source_files, *qar_submission_data.output_files]

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
                    file_selection_dropdown,
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.ERROR if qar_submission_data.error_occurred else ft.Icons.CHECK,
                                color=ft.Colors.RED if qar_submission_data.error_occurred else ft.Colors.GREEN
                            ),
                            ft.Text(
                                f'(Grading script was {'unsuccesful' if qar_submission_data.error_occurred else 'successful'})',
                                theme_style=ft.TextThemeStyle.BODY_SMALL,
                            )
                        ]
                    )
                ]
            ),
            file_view_pane
        ]
    )

@ft.component
def RubricFeedbackItem(rubric_item_score) -> ft.Column:
    # Description of the rubric item
    # [textbox] / {score} points
    # [big box for feedback]
    return ft.Column(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Text(
                f'{rubric_item_score.rubric_item.description}',
            ),
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
            )
        ]
    )

@ft.component
def FeedbackPanel(qar_submission_data: QARSubmissionData) -> ft.Column:
    return ft.Column(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Text('Feedback:'),
            ft.Column(
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    RubricFeedbackItem(
                        rubric_item_score=rubric_item_score
                    ) for rubric_item_score in qar_submission_data.rubric_scores
                ]
            )
        ]
    )


@ft.component
def GradingTab(grader_data: GraderData) -> ft.Row:
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

    rubric_panel = FeedbackPanel(qar_submission_data=sub)

    left_column = FileDisplayPanel(qar_submission_data=sub)

    right_column = ft.Column(
        expand=1,
        alignment=ft.MainAxisAlignment.START,
        controls=[
            submission_navigation_panel,
            ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    rubric_panel
                ]
            ),
            ft.Button(
                'Upload Submission',
                on_click=lambda e: print('Upload Submission button clicked')
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
