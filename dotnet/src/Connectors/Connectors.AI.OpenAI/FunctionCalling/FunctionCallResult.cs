// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling;

using System.Collections.Generic;


/// <summary>
///  The function call to be made returned by the LLM
/// </summary>
public class FunctionCallResult
{

    /// <summary>
    /// Name of the function chosen
    /// </summary>
    public string Function { get; set; } = string.Empty;

    /// <summary>
    ///  Parameter values
    /// </summary>
    public List<FunctionCallParameter> Parameters { get; set; } = new();

}
