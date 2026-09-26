import os
import re


class QARSubmission:
    def __init__(self, qar_file: str, working_dir: str) -> None:
        if not os.path.isfile(os.path.join(working_dir, qar_file)):
            raise FileNotFoundError(f'QAR file \'{qar_file}\' does not exist.')

        self._extracted = False

        # Get the student name and submission name
        match = re.match(r'^(\w+)_\d+_\d+_(.+?)\.qar$', qar_file)

        if not match:
            raise ValueError(f'QAR file \'{qar_file}\' does not match the expected format.')

        self._student_name = match.group(1)
        self._submission_name = match.group(2)


    @property
    def student_name(self) -> str:
        return self._student_name

    @property
    def submission_name(self) -> str:
        return self._submission_name
