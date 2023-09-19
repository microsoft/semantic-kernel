// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Model;

/// <summary>
/// The REST API operation parameter.
/// </summary>
public sealed class RestApiOperationParameter
{
    /// <summary>
    /// The parameter name.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// The property alternative name. It can be used as an alternative name in contexts where the original name can't be used.
    /// </summary>
    public string? AlternativeName { get; set; }

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
    /// The parameter style - defines how multiple values are delimited.
    /// </summary>
    public RestApiOperationParameterStyle? Style { get; }

    /// <summary>
    /// Type of array item for parameters of "array" type.
    /// </summary>
    public string? ArrayItemType { get; }

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
    /// <param name="style">The parameter style - defines how multiple values are delimited.</param>
    /// <param name="arrayItemType">Type of array item for parameters of "array" type.</param>
    /// <param name="defaultValue">The parameter default value.</param>
    /// <param name="description">The parameter description.</param>
    public RestApiOperationParameter(
        string name,
        string type,
        bool isRequired,
        RestApiOperationParameterLocation location,
        RestApiOperationParameterStyle? style = null,
        string? arrayItemType = null,
        string? defaultValue = null,
        string? description = null)
    {
        this.Name = name;
        this.Type = type;
        this.IsRequired = isRequired;
        this.Location = location;
        this.Style = style;
        this.ArrayItemType = arrayItemType;
        this.DefaultValue = defaultValue;
        this.Description = description;
    }
}
