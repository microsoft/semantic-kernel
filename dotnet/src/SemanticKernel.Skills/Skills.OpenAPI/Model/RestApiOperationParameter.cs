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
    /// The parameter type - string, integer, number, boolean, array and object.
    /// </summary>
    public string Type { get; }

    /// <summary>
    /// The parameter description.
    /// </summary>
    public string? Description { get; }

    /// <summary>
    /// Flag specifying if the parameter is required or not.
    /// </summary>
    public bool IsRequired { get; }

    /// <summary>
    /// The parameter location.
    /// </summary>
    public RestApiOperationParameterLocation Location { get; }

    /// <summary>
    /// The default value.
    /// </summary>
    public string? DefaultValue { get; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationParameter"/> class.
    /// </summary>
    /// <param name="name">The parameter name.</param>
    /// <param name="type">The parameter type.</param>
    /// <param name="isRequired">Flag specifying if the parameter is required or not.</param>
    /// <param name="location">The parameter location.</param>
    /// <param name="defaultValue">The parameter default value.</param>
    /// <param name="description">The parameter description.</param>
    public RestApiOperationParameter(string name, string type, bool isRequired, RestApiOperationParameterLocation location, string? defaultValue, string? description = null)
    {
        this.Name = name;
        this.Type = type;
        this.IsRequired = isRequired;
        this.Location = location;
        this.DefaultValue = defaultValue;
        this.Description = description;
    }
}
