// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.TestSettings;

/// <summary>
/// Defines the method to use to count tokens in prompts inputs and results, to account for MaxTokens and to compute costs.
/// </summary>
public enum TokenCountFunction
{
    Gpt3Tokenizer,
    WordCount,
}
