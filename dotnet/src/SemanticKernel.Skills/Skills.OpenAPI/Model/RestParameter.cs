// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;
/// <summary>
/// The Rest parameter.
/// </summary>
internal class RestParameter
{
    /// <summary>
    /// The parameter name.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// Flag specifying if the parameter is required or not.
    /// </summary>
    public bool IsRequired { get; }

    /// <summary>
    /// The parameter type.
    /// </summary>
    public RestParameterType Type { get; }

    /// <summary>
    /// The default value.
    /// </summary>
    public string DefaultValue { get; }

    /// <summary>
    /// Creates an instance of a <see cref="RestParameter"/> class.
    /// </summary>
    /// <param name="name">The parameter name.</param>
    /// <param name="isRequired">Flag specifying if the parameter is required or not.</param>
    /// <param name="type">The parameter name.</param>
    /// <param name="defaultValue">The parameter default value.</param>
    public RestParameter(string name, bool isRequired, RestParameterType type, string defaultValue)
    {
        this.Name = name;
        this.IsRequired = isRequired;
        this.Type = type;
        this.DefaultValue = defaultValue;
    }
}
