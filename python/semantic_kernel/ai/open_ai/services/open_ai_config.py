# Copyright (c) Microsoft. All rights reserved.

from typing import Optional, List, Dict, Any
from semantic_kernel.diagnostics.verify import Verify
import json

# TODO: allow for overriding endpoints


class OpenAIConfig:
    """
    The OpenAI configuration.
    """

    # OpenAI model name, see https://platform.openai.com/docs/models
    model_id: str
    # OpenAI API key, see https://platform.openai.com/account/api-keys
    api_key: str
    # OpenAI organization ID. This is usually optional unless your
    # account belongs to multiple organizations.
    org_id: Optional[str]

    def __init__(
        self, model_id: str, api_key: str, org_id: Optional[str] = None
    ) -> None:
        """Initializes a new instance of the OpenAIConfig class.

        Arguments:
            model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
        """
        Verify.not_empty(model_id, "The model ID is empty")
        Verify.not_empty(api_key, "The API key is empty")

        self.model_id = model_id
        self.api_key = api_key
        self.org_id = org_id


class ChatCompletionConfig(OpenAIConfig):
    """
    OpenAI configuration class for Chat Completions API.
    """

    # OpenAI Completion Config Parameters
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-suffix
    suffix: str
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-max_tokens
    max_tokens: int
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-temperature
    temperature: float
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-top_p
    top_p: int
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-n
    n: int
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-stream
    stream: bool
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-stop
    stop: Optional[List[str]]
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-presence_penalty
    presence_penalty: float
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-frequency_penalty
    frequency_penalty: float
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-best_of
    logit_bias: object
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-user
    user: Optional[str]

    def __init__(self, model_id: str, api_key: str, org_id: Optional[str] = None,
                 suffix: Optional[str] = None, max_tokens: int = 16,
                 temperature: float = 1.0, top_p: int = 1, n: int = 1,
                 stream: bool = False, stop: Optional[List[str]] = None,
                 presence_penalty: float = 0.0, frequency_penalty: float = 0.0,
                 logit_bias: Optional[Dict[str, Any]] = None, user: str = None) -> None:
        """Initializes a new instance of the OpenAIConfig class.

            Arguments:
                model_id {str} -- OpenAI model name, see
                    https://platform.openai.com/docs/models

                api_key {str} -- OpenAI API key, see
                    https://platform.openai.com/account/api-keys

                org_id {Optional[str]} -- OpenAI organization ID.
                    This is usually optional unless your
                    account belongs to multiple organizations.

                suffix {str} -- The suffix that comes after a 
                    completion of inserted text. Optional, 
                    defaults to null.

                max_tokens {int} -- The maximum number of tokens 
                    to generate in the completion. Optional, 
                    defaults to 16. The token count of your prompt
                    plus max_tokens cannot exceed the model's 
                    context length.

                temperature {float} -- What sampling temperature to 
                    use, between 0 and 2. Higher values like 0.8 
                    will make the output more random, while lower 
                    values like 0.2 will make it more focused and 
                    deterministic. Optional, defaults to 1.

                top_p {float} -- An alternative to sampling with 
                    temperature, called nucleus sampling, where the 
                    model considers the results of the tokens with
                    top_p probability mass. So 0.1 means only the 
                    tokens comprising the top 10% probability mass
                    are considered. Optional, defaults to 1.

                n {int} -- How many completions to generate for 
                    each prompt. Optional, defaults to 1.

                stream {bool} -- Whether to stream back partial
                    progress. If set, tokens will be sent as
                    data-only server-sent events as they become
                    available, with the stream terminated by a
                    data: [DONE] message. Optional, defaults to
                    false.

                stop {str or list} -- Up to 4 sequences where
                    the API will stop generating further tokens.
                    The returned text will not contain the stop
                    sequence. Optional, defaults to null.

                presence_penalty {float} -- Number between -2.0
                    and 2.0. Positive values penalize new tokens
                    based on whether they appear in the text so
                    far, increasing the model's likelihood to
                    talk about new topics. Optional, defaults
                    to 0.

                frequency_penalty {float} -- Number between -2.0
                    and 2.0. Positive values penalize new tokens
                    based on their existing frequency in the text
                    so far, decreasing the model's likelihood to
                    repeat the same line verbatim. Optional,
                    defaults to 0.

                logit_bias {dict} -- Modify the likelihood of
                    specified tokens appearing in the completion.
                    Accepts a json object that maps tokens
                    (specified by their token ID in the GPT
                    tokenizer) to an associated bias value from
                    -100 to 100. You can use this tokenizer tool
                    (which works for both GPT-2 and GPT-3) to
                    convert text to token IDs. Mathematically,
                    the bias is added to the logits generated by
                    the model prior to sampling. The exact effect
                    will vary per model, but values between -1 and
                    1 should decrease or increase likelihood of
                    selection; values like -100 or 100 should
                    result in a ban or exclusive selection of the
                    relevant token.

                user {str} -- A unique identifier representing
                    your end-user, which can help OpenAI to monitor
                    and detect abuse.
        """

        super().__init__(model_id=model_id, api_key=api_key, org_id=org_id)
        self.suffix = suffix
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.n = n
        self.stream = stream
        self.stop = stop
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.logit_bias = logit_bias
        self.user = user


class CompletionConfig(ChatCompletionConfig):
    """
    OpenAI configuration class for Completions API.
    """

    # OpenAI Completion Config Parameters
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-suffix
    suffix: str
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-max_tokens
    max_tokens: int
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-temperature
    temperature: float
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-top_p
    top_p: int
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-n
    n: int
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-stream
    stream: bool
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-logprobs
    logprobs: int
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-echo
    echo: bool
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-stop
    stop: Optional[List[str]]
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-frequency_penalty
    frequency_penalty: float
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-presence_penalty
    presence_penalty: float
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-best_of
    best_of: int
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-best_of
    logit_bias: object
    # https://platform.openai.com/docs/api-reference/completions/create#completions/create-user
    user: Optional[str]

    def __init__(self, model_id: str, api_key: str, org_id: Optional[str] = None,
                 suffix: Optional[str] = None, max_tokens: int = 16,
                 temperature: float = 1.0, top_p: int = 1, n: int = 1,
                 stream: bool = False, logprobs: int = 0, echo: bool = False,
                 stop: Optional[List[str]] = None, presence_penalty: float = 0.0,
                 frequency_penalty: float = 0.0, best_of: int = 1,
                 logit_bias: Optional[Dict[str, Any]] = None, user: str = None) -> None:
        """Initializes a new instance of the OpenAIConfig class.

            Arguments:
                model_id {str} -- OpenAI model name, see
                    https://platform.openai.com/docs/models

                api_key {str} -- OpenAI API key, see
                    https://platform.openai.com/account/api-keys

                org_id {Optional[str]} -- OpenAI organization ID.
                    This is usually optional unless your
                    account belongs to multiple organizations.

                suffix {str} -- The suffix that comes after a 
                    completion of inserted text. Optional, 
                    defaults to null.

                max_tokens {int} -- The maximum number of tokens 
                    to generate in the completion. Optional, 
                    defaults to 16. The token count of your prompt
                    plus max_tokens cannot exceed the model's 
                    context length.

                temperature {float} -- What sampling temperature to 
                    use, between 0 and 2. Higher values like 0.8 
                    will make the output more random, while lower 
                    values like 0.2 will make it more focused and 
                    deterministic. Optional, defaults to 1.

                top_p {float} -- An alternative to sampling with 
                    temperature, called nucleus sampling, where the 
                    model considers the results of the tokens with
                    top_p probability mass. So 0.1 means only the 
                    tokens comprising the top 10% probability mass
                    are considered. Optional, defaults to 1.

                n {int} -- How many completions to generate for 
                    each prompt. Optional, defaults to 1.

                stream {bool} -- Whether to stream back partial
                    progress. If set, tokens will be sent as
                    data-only server-sent events as they become
                    available, with the stream terminated by a
                    data: [DONE] message. Optional, defaults to
                    false.

                logprobs {int} -- Include the log probabilities
                    on the logprobs most likely tokens, as well
                    the chosen tokens. For example, if logprobs
                    is 5, the API will return a list of the 5
                    most likely tokens. The API will always
                    return the logprob of the sampled token, so
                    there may be up to logprobs+1 elements in
                    the response. Optional, defaults to null.

                echo {bool} -- Echo back the prompt in addition
                    to the completion. Optional, defaults to
                    false.

                stop {str or list} -- Up to 4 sequences where
                    the API will stop generating further tokens.
                    The returned text will not contain the stop
                    sequence. Optional, defaults to null.

                presence_penalty {float} -- Number between -2.0
                    and 2.0. Positive values penalize new tokens
                    based on whether they appear in the text so
                    far, increasing the model's likelihood to
                    talk about new topics. Optional, defaults
                    to 0.

                frequency_penalty {float} -- Number between -2.0
                    and 2.0. Positive values penalize new tokens
                    based on their existing frequency in the text
                    so far, decreasing the model's likelihood to
                    repeat the same line verbatim. Optional,
                    defaults to 0.

                best_of {int} -- Generates best_of completions
                    server-side and returns the "best" (the one
                    with the highest log probability per token).
                    Results cannot be streamed.Optional, defaults
                    to 1.

                logit_bias {dict} -- Modify the likelihood of
                    specified tokens appearing in the completion.
                    Accepts a json object that maps tokens
                    (specified by their token ID in the GPT
                    tokenizer) to an associated bias value from
                    -100 to 100. You can use this tokenizer tool
                    (which works for both GPT-2 and GPT-3) to
                    convert text to token IDs. Mathematically,
                    the bias is added to the logits generated by
                    the model prior to sampling. The exact effect
                    will vary per model, but values between -1 and
                    1 should decrease or increase likelihood of
                    selection; values like -100 or 100 should
                    result in a ban or exclusive selection of the
                    relevant token.

                user {str} -- A unique identifier representing
                    your end-user, which can help OpenAI to monitor
                    and detect abuse.
        """

        super().__init__(model_id=model_id, api_key=api_key, org_id=org_id, suffix=suffix,
                         max_tokens=max_tokens, temperature=temperature, top_p=top_p, n=n,
                         stream=stream, stop=stop, presence_penalty=presence_penalty,
                         frequency_penalty=frequency_penalty, logit_bias=logit_bias,
                         user=user)
        self.logprobs = logprobs
        self.echo = echo
        self.best_of = best_of
