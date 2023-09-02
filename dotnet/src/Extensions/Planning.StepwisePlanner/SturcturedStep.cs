// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Stepwise;

using Connectors.AI.OpenAI.FunctionCalling;


public class StructuredStep : FunctionCallResult
{
    public string? Thought { get; set; }

    public string? Observation { get; set; }

    public string? FinalAnswer { get; set; }

    public string? OriginalResponse { get; set; }
}
