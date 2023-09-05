// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling;

using System.Collections.Generic;
using System.Linq;


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


    /// <summary>
    ///  Compare two FunctionCallResults
    /// </summary>
    /// <param name="obj"></param>
    /// <returns></returns>
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
