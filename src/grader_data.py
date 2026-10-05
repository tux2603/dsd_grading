import os
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from multiprocessing import Pool

import flet as ft

from app_data import AppData
from qar_submission import QARSubmissionData
from rubric_data import RubricItem, RubricItemScore
from testbench_data import TestbenchData


def _make_submission(submission_dir: str) -> bool:
    # pushd
    old_cwd = os.getcwd()
    os.chdir(submission_dir)

    print(f'Spawning make for {submission_dir}')
    result = subprocess.run(['make', '-j1', 'all'], check=False)
    success = result.returncode == 0

    if not success:
        print(f'Error occurred while making submission in {submission_dir}: {result.stderr}')

    # popd
    os.chdir(old_cwd)
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

    @property
    def current_submission(self) -> QARSubmissionData | None:
        if 0 <= self.current_submission_index < len(self.qar_submissions):
            return self.qar_submissions[self.current_submission_index]
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

        print(f'The new length of the qar_submissions list is: {len(self.qar_submissions)}')

    def add_testbench(self, testbench_file_path: str) -> None:
        testbench = TestbenchData(self.app_data, testbench_file_path)
        self.testbenches.append(testbench)

    def restore_archives(self) -> None:
        # convert this old code to a multiprocess
        extract_submission = lambda submission: submission.extract()

        selected_submissions = [submission for submission in self.qar_submissions if submission.selected and not submission.extracted]

        print(f'Processing {len(selected_submissions)} QAR submissions...')

        # TODO: does this actually help us at all? I think the GIL means that it won't
        with ThreadPoolExecutor() as executor:
            executor.map(extract_submission, selected_submissions)
        self.submissions_extracted = True

        print('Done extracting QAR submissions. Now building them...')

    def prepare_makefiles(self) -> None:
        for submission in self.qar_submissions:
            if submission.selected and submission.extracted:
                try:
                    submission.prepare_make_file(testbenches=self.testbenches)
                except (FileNotFoundError, ValueError) as ex:
                    print(f'Error occurred while preparing makefile for student {submission.student_name}: {ex}')
                    submission.error_occurred = True

        self.makefiles_prepared = True

    def make_all_submissions(self) -> None:
        selected_submissions = [submission for submission in self.qar_submissions if submission.selected and submission.extracted]

        print(f'Building {len(selected_submissions)} QAR submissions...')

        submission_dirs = [submission.extracted_dir for submission in selected_submissions]

        with Pool() as pool:
            results = pool.map(_make_submission, submission_dirs)

        for submission, success in zip(selected_submissions, results):
            print(f'Submission {submission.student_name}: {"Success" if success else "Failed"}')
            if not success:
                submission.error_occurred = True

        print('Done building QAR submissions.')
        self.submissions_made = True

    def start_grading(self, e: ft.Event[ft.Button]) -> None:
        self.started = True
        self.status_icon = ft.Icons.RUN_CIRCLE_OUTLINED
        self.restore_archives()
        self.prepare_makefiles()
        self.make_all_submissions()
        self.status_icon = ft.Icons.CHECK_CIRCLE_OUTLINED

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
