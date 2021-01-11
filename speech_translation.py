import logging
import shutil
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

import fire

from DataFiltering import asr_mistakes
from DataFiltering import diff_lev
from DataFiltering import first_cleaning
from MergeSplit import split_merge
from SyntheticNoiseGeneration import difflib_comparison, suffix_analysis, pos_noise_analysis, add_noise

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%d-%m-%Y %H:%M:%S')
logging.write = lambda msg: logging.info(msg) if msg != '\n' else None

result_arg_prefix = "result_"


class Workflow(object):
    def __init__(self, **kwargs):
        if 'workdir' not in kwargs:
            kwargs['workdir'] = Path(tempfile.mkdtemp())
        else:
            kwargs['workdir'] = Path(kwargs['workdir'])
            kwargs['workdir'].mkdir(exist_ok=True)

        logging.info(f"Workdir folder: {kwargs['workdir'].absolute()}")

        # separate original input and input to functions
        self.kwargs = {k: Path(v) for k, v in kwargs.items()}
        self.inputs = self.kwargs.copy()

    def _intermediate_step_call_wrapper(self, function):
        def get_filename(original_path):
            return self.inputs['workdir'] / f"{function.__name__}_{original_path.name}"

        # Store resulting files in workdir
        self.inputs.update({k: get_filename(v) for k, v in self.inputs.items()
                            if result_arg_prefix in k})

        logging.info(f"Starting {function.__name__}")
        with redirect_stdout(logging):
            function(**self.inputs)
        logging.info(f"Finished {function.__name__}")

        # If function did not produce new file, symlink last input
        for target_name, target_file in self._filter_result_files(self.inputs).items():
            input_name = target_name.replace(result_arg_prefix, "")
            if input_name in self.inputs and Path(self.inputs[input_name]).exists() and not target_file.exists():
                shutil.copy2(self.inputs[input_name], target_file)

        # Feed results as next source
        self.inputs.update({k.replace(result_arg_prefix, ""): v for k, v in self.inputs.items()
                            if result_arg_prefix in k})

    def _finalize(self):
        # copy from temporary results names to final
        for name, path in self._filter_result_files(self.inputs).items():
            shutil.copy2(path, self.kwargs[name])

    @staticmethod
    def _filter_result_files(dictionary):
        return {k: v for k, v in dictionary.items() if result_arg_prefix in k}


class SpeechTranslation(Workflow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_split_merge(self):
        self._intermediate_step_call_wrapper(split_merge.generate_split_merge)
        self._finalize()

    def learn_noise_model(self):
        self._intermediate_step_call_wrapper(difflib_comparison.difflib_comparison)
        self._intermediate_step_call_wrapper(suffix_analysis.suffix_analysis)
        self._finalize()

    def apply_noise_model(self):
        self._intermediate_step_call_wrapper(add_noise.add_noise)
        self._finalize()

    def filter(self):
        self._intermediate_step_call_wrapper(first_cleaning.first_cleaning)
        self._intermediate_step_call_wrapper(asr_mistakes.asr_mistakes)
        self._intermediate_step_call_wrapper(diff_lev.diff_lev)
        self._finalize()


if __name__ == "__main__":
    fire.Fire(SpeechTranslation)
