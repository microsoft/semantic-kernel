// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling;

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;


/// <summary>
///  The function call to be made returned by the LLM
/// </summary>
public class FunctionCallResult
{

    /// <summary>
    /// Name of the function chosen
    /// </summary>
    [JsonPropertyName("function")]
    public string Function { get; set; } = string.Empty;

    /// <summary>
    ///  Parameter values
    /// </summary>
    [JsonPropertyName("parameters")]
    public List<FunctionCallParameter> Parameters { get; set; } = new();


    public override bool Equals(object? obj)
    {
        if (obj is FunctionCallResult otherFunctionCallResult)
        {
            // You might need to adjust this comparison depending on what makes two FunctionCallResult equal in your context
            bool functionEquality = otherFunctionCallResult.Function.Trim().Equals(Function.Trim(), System.StringComparison.Ordinal);
            bool parametersEquality = otherFunctionCallResult.Parameters.SequenceEqual(Parameters);
            return functionEquality && parametersEquality;
        }

        return base.Equals(obj);
    }

}
