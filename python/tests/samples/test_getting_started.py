# Copyright (c) Microsoft. All rights reserved.

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from pytest import mark
from traitlets.config import Config

c = Config()

c.RegexRemovePreprocessor.patterns = ["^!pip .*"]
c.ExecutePreprocessor.exclude_input_prompt = True


def run_notebook(notebook_name: str):
    with open(f"samples/getting_started/{notebook_name}") as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3", config=c)
    ep.preprocess(nb, {"metadata": {"path": "samples/getting_started/"}})


@mark.parametrize(
    "name",
    [
        "00-getting-started.ipynb",
        "01-basic-loading-the-kernel.ipynb",
        "02-running-prompts-from-file.ipynb",
        "03-prompt-function-inline.ipynb",
        "04-kernel-arguments-chat.ipynb",
        "05-using-the-planner.ipynb",
        "06-memory-and-embeddings.ipynb",
        "07-hugging-face-for-plugins.ipynb",
        "08-native-function-inline.ipynb",
        "09-groundedness-checking.ipynb",
        "10-multiple-results-per-prompt.ipynb",
        "11-streaming-completions.ipynb",
    ],
)
def test_notebooks(name):
    run_notebook(name)
