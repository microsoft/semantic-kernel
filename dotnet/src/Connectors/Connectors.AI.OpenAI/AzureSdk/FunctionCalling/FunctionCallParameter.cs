// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk.FunctionCalling;

/// <summary>
///  A parameter for a function call
/// </summary>
public class FunctionCallParameter
{
    /// <summary>
    ///  Constructor
    /// </summary>
    /// <param name="name"></param>
    /// <param name="value"></param>
    public FunctionCallParameter(string name, string value)
    {
        Name = name;
        Value = value;
    }


    /// <summary>
    ///  Name of the parameter
    /// </summary>
    public string Name { get; set; }

    /// <summary>
    ///  Value of the parameter
    /// </summary>
    public string Value { get; set; }
}
