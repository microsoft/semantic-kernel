// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

public static class Defaults
{
    public const string TruncatedLogFormat = "{0}  (...)   {1}";

    public const string SemanticRemarks =
        "Note that semantic functions are employed within pipelines comprising other templated semantic functions intertwined with native code based functions. The latter might require stricter adherence to the instructions provided to parse input parameters, without any means to filter out potential noise.\nBe wise in your appraisal of what is an acceptable response to those instructions. Instructions often include an example with a simple input and the expected completion format, although this is not systematic, and sometimes the provided example is trivial as it was meant to keep the instructions short and should be properly extrapolated for an acceptable answer to the actual input.";

    public const string UserPreamble = "Let's play a game: answer like a semantic-function: please read the following instructions, and simply answer with a text completion of my message, without adding any personal comment. Let's go !";

    public const string SystemSupplement = "User is now playing a game where he is writing messages in the form of semantic functions. That means you are expected to strictly answer with a completion of his message, without adding any additional comments.";

    public const string EmptyFormat = "{0}";

    public const string VettingPromptTemplate = @"Validate a text completion model's response to a semantic function: following are a templated prompt sent to a large language model and the completion it returned, to be evaluated. Please indicate whether the response is valid or not.
{SemanticSupplement}
Does the reponse appropriately completes the prompt? Please answer simply with true or false.
PROMPT:
-------
{prompt}
RESPONSE:
---------
{response}
RESPONSE IS VALID? (true/false):
--------------------------------
";

}
