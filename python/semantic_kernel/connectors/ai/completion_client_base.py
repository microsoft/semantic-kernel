# Copyright (c) Microsoft. All rights reserved.

from abc import ABC


class CompletionClientBase(ABC):
    _prompt_tokens: int = 0
    _completion_tokens: int = 0
    _total_tokens: int = 0

    @property
    def prompt_tokens(self) -> int:
        """
        Gets the number of tokens used for the prompts.

        Returns:
            int -- The number of prompt tokens used.
        """
        return self._prompt_tokens
    
    @property
    def completion_tokens(self) -> int:
        """
        Gets the number of tokens used for the completions.

        Returns:
            int -- The number of completion tokens used.
        """
        return self._completion_tokens
    
    @property
    def total_tokens(self) -> int:
        """
        Gets the total number of tokens used.

        Returns:
            int -- The total number of tokens used.
        """
        return self._total_tokens
    
    def add_tokens(self, prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0) -> None:
        """
        Adds tokens to the total number of tokens used.

        Arguments:
            prompt_tokens {int} -- The number of tokens used for the prompts.
            completion_tokens {int} -- The number of tokens used for the completions.
            total_tokens {int} -- The total number of tokens used.
        """
        self._prompt_tokens += prompt_tokens
        self._completion_tokens += completion_tokens
        self._total_tokens += total_tokens
