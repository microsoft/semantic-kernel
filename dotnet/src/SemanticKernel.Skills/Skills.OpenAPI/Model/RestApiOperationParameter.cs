// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;
/// <summary>
/// The REST API operation parameter.
/// </summary>
internal class RestApiOperationParameter
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
    public RestApiOperationParameterType Type { get; }

    /// <summary>
    /// The default value.
    /// </summary>
    public string DefaultValue { get; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationParameter"/> class.
    /// </summary>
    /// <param name="name">The parameter name.</param>
    /// <param name="isRequired">Flag specifying if the parameter is required or not.</param>
    /// <param name="type">The parameter type.</param>
    /// <param name="defaultValue">The parameter default value.</param>
    public RestApiOperationParameter(string name, bool isRequired, RestApiOperationParameterType type, string defaultValue)
    {
        this.Name = name;
        this.IsRequired = isRequired;
        this.Type = type;
        this.DefaultValue = defaultValue;
    }
}
