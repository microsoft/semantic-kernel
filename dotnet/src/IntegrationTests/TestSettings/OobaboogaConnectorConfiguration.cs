// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.TestSettings;

/// <summary>
/// Represents a text completion provider instance with the corresponding given name and settings.
/// </summary>
public class OobaboogaConnectorConfiguration
{
    public string Name { get; set; } = "";

    public int BlockingPort { get; set; }

    public int StreamingPort { get; set; }

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    public int? MaxTokens { get; set; }

    public TokenCountFunction TokenCountFunction { get; set; } = TokenCountFunction.Gpt3Tokenizer;

    public decimal CostPerRequest { get; set; }

    public decimal? CostPer1000Token { get; set; }
}
