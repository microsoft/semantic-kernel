// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling;

using System;


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


    public override bool Equals(object? obj)
    {
        if (obj is FunctionCallParameter other)
        {
            var nameEquality = Name.Trim().Equals(other.Name.Trim(), StringComparison.Ordinal);
            var valueEquality = Value.Trim().Equals(other.Value.Trim(), StringComparison.Ordinal);
            return nameEquality && valueEquality;
        }
        return base.Equals(obj);
    }


    public override int GetHashCode() => HashCode.Combine(Name, Value);
}
