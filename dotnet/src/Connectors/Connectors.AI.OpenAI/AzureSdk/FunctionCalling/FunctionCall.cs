// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk.FunctionCalling;

using System.Collections.Generic;


public record SKFunctionCall
{
    /// <summary>
    /// Rationale given by the LLM for choosing the function
    /// </summary>
    public string Rationale { get; set; } = string.Empty;

    /// <summary>
    /// Name of the function chosen
    /// </summary>
    public string Function { get; set; } = string.Empty;

    /// <summary>
    ///  Parameter values
    /// </summary>
    public List<Parameter> Parameters { get; set; } = new();

    public string? SetContextVariable { get; set; }

    public string? AppendToResult { get; set; }
}


public class Parameter
{
    public string Name { get; set; }
    public string Value { get; set; }
}
