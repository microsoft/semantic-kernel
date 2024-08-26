# Copyright (c) Microsoft. All rights reserved.


def formatted_system_message(subject: str):
    """Return a formatted system message."""
    return f"""
    You are an expert in {subject}. You answer multiple choice questions on this topic.
    """


def formatted_question(
    question: str, answer_a: str, answer_b: str, answer_c: str, answer_d: str
):
    """Return a formatted question."""
    return f"""
    Question: {question}

    Which of the following answers is correct?

    A. {answer_a}
    B. {answer_b}
    C. {answer_c}
    D. {answer_d}

    State ONLY the letter corresponding to the correct answer without any additional text.
    """


def expected_answer_to_letter(answer: str):
    """Return the letter corresponding to the expected answer.

    The dataset contains numbers as answers, this function converts them to letters.
    """
    return ["A", "B", "C", "D"][int(answer)]
