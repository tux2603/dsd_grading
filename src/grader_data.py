import asyncio
import os
import random
import zipfile
from dataclasses import dataclass, field

import flet as ft
from aiomultiprocess import Pool

from app_data import AppData
from qar_submission import QARSubmissionData
from rubric_data import RubricItem, RubricItemScore
from testbench_data import TestbenchData


async def _make_submission(submission_dir: str) -> bool:
    print(f'Spawning make for {submission_dir}')

    process = await asyncio.create_subprocess_exec(
        'make', '-j1', 'all',
        cwd=submission_dir
    )

    return_code = await process.wait()
    _, stderr = await process.communicate()

    success = (return_code == 0)

    if not success:
        print(f'Error occurred while making submission in {submission_dir}: {stderr}')

    return success


@ft.observable
@dataclass
class GraderData:
    app_data: AppData
    qar_submissions: list[QARSubmissionData] = field(default_factory=list, init=False)
    testbenches: list[TestbenchData] = field(default_factory=list, init=False)
    submissions_extracted: bool = field(default=False, init=False)
    makefiles_prepared: bool = field(default=False, init=False)
    submissions_made: bool = field(default=False, init=False)
    started: bool = field(default=False, init=False)
    status_icon: ft.IconData = field(default=ft.Icons.PLAY_ARROW_ROUNDED, init=False)
    current_submission_index: int = field(default=0, init=False)
    selected_tab_index: int = field(default=0, init=False)
    rubric_items: list[RubricItem] = field(default_factory=list, init=False)
    _shuffled_order: list[int] = field(default_factory=list, init=False)

    @property
    def current_submission(self) -> QARSubmissionData | None:
        if 0 <= self.current_submission_index < len(self.qar_submissions):
            unshuffled_index = self._shuffled_order[self.current_submission_index]
            return self.qar_submissions[unshuffled_index]
        return None

    def extract_zip_file(self, zip_file_path: str) -> None:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(self.app_data.working_dir)

        self.qar_submissions.clear()

        # Find all of the QAR files in the working directory and create a list of them
        for file in os.listdir(self.app_data.working_dir):
            if file.endswith('.qar'):
                submission = QARSubmissionData(self.app_data, file)

                for rubric_item in self.rubric_items:
                    submission.rubric_scores.append(RubricItemScore(rubric_item=rubric_item))

                self.qar_submissions.append(submission)

        self._shuffled_order = list(range(len(self.qar_submissions)))
        random.shuffle(self._shuffled_order)

        print(f'The new length of the qar_submissions list is: {len(self.qar_submissions)}')

    def add_testbench(self, testbench_file_path: str) -> None:
        testbench = TestbenchData(self.app_data, testbench_file_path)
        self.testbenches.append(testbench)

    async def restore_archives(self) -> None:

        selected_submissions = [submission for submission in self.qar_submissions if submission.selected and not submission.extracted]

        print(f'Processing {len(selected_submissions)} QAR submissions...')
        tasks = []

        get_extract_coroutine = lambda submission: submission.extract()

        async with asyncio.TaskGroup() as tg:
            for submission in selected_submissions:
                tasks.append(tg.create_task(get_extract_coroutine(submission)))

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        self.submissions_extracted = True

        print('Done extracting QAR submissions. Now building them...')

    async def prepare_makefiles(self) -> None:
        for submission in self.qar_submissions:
            if submission.selected and submission.extracted:
                try:
                    await submission.prepare_make_file(testbenches=self.testbenches)
                except (FileNotFoundError, ValueError) as ex:
                    print(f'Error occurred while preparing makefile for student {submission.student_name}: {ex}')
                    submission.error_occurred = True

        self.makefiles_prepared = True

    async def make_all_submissions(self) -> None:
        selected_submissions = [submission for submission in self.qar_submissions if submission.selected and submission.extracted]

        print(f'Building {len(selected_submissions)} QAR submissions...')

        submission_dirs = [submission.extracted_dir for submission in selected_submissions]

        async with Pool() as pool:
            results = await pool.map(_make_submission, submission_dirs)

        for submission, success in zip(selected_submissions, results):
            print(f'Submission {submission.student_name}: {"Success" if success else "Failed"}')
            if not success:
                submission.error_occurred = True

        print('Done building QAR submissions.')
        self.submissions_made = True

    async def start_grading(self, e: ft.Event[ft.Button], page: ft.Page) -> None:
        self.started = True
        page.show_dialog(ft.SnackBar(
            ft.Text('Grading started. Please wait...'),
            open=True,
            duration=2000,
            bgcolor=ft.Colors.BLUE_100
        ))
        page.update()

        self.status_icon = ft.Icons.RUN_CIRCLE_OUTLINED
        await self.restore_archives()
        await self.prepare_makefiles()
        await self.make_all_submissions()
        self.status_icon = ft.Icons.CHECK_CIRCLE_OUTLINED

        page.show_dialog(ft.SnackBar(
            ft.Text('All submissions have been extracted and built'),
            open=True,
            duration=2000,
            bgcolor=ft.Colors.GREEN_100
        ))

    def prev_submission(self, e: ft.Event[ft.IconButton]) -> None:
        if self.current_submission_index > 0:
            self.current_submission_index -= 1

    def next_submission(self, e: ft.Event[ft.IconButton]) -> None:
        if self.current_submission_index < len(self.qar_submissions) - 1:
            self.current_submission_index += 1

    def add_rubric_item(self, rubric_item: RubricItem) -> None:
        self.rubric_items.append(rubric_item)

        for submission in self.qar_submissions:
            submission.rubric_scores.append(RubricItemScore(rubric_item=rubric_item))
