// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

public static class Defaults
{
    public const string TruncatedLogFormat = "{0}  (...)   {1}";

    public const string SemanticRemarks =
        "Semantic functions are structured templates that work in tandem with other similar templates and native code-based functions. The native functions, in particular, demand a precise adherence to given instructions. They rely heavily on accurately parsed input parameters and lack mechanisms to sift through any unnecessary noise.\nWhen assessing the appropriateness of a response, it's crucial to be discerning. While instructions often present an example that outlines the desired response format, these examples may not always be exhaustive. Occasionally, they might even be overly simplistic, intended merely to keep the instructions concise. Thus, always ensure that you thoroughly understand and thoughtfully apply these instructions to generate a fitting answer to the given input.";

    public const string UserPreamble = "Let's engage in a game: carefully heed the upcoming directives. Respond solely with a continuation of my message, abstaining from any extra remarks.";

    public const string SystemSupplement = "Assume you're about to engage in the 'semantic-function game'. In this context, every incoming prompt will be based on a semantic function, even if it's not perfectly formed or seems ambiguous. Your primary goal is to identify and execute the core function or intent of the message, filtering out noise or extraneous details. Treat the following prompt as a function and provide a direct, precise completion without added commentary. Prioritize the most likely and salient function based on the information presented. Be alert to cues, even if they're subtle or embedded, and strive to respond as accurately and succinctly as possible.";

    public const string EmptyFormat = "{0}";

    public const string VettingPromptTemplate = @"Validate a text completion model's response to a semantic function: following are a templated prompt sent to a large language model and the completion it returned, to be evaluated. Please indicate whether the response is valid or not.
{"
                                                + nameof(Defaults.SemanticRemarks)
                                                + @"}
Does the reponse appropriately completes the prompt? Please answer simply with true or false.
PROMPT:
-------
{prompt}
RESPONSE:
---------
{0}
RESPONSE IS VALID? (true/false):
--------------------------------
";
}
