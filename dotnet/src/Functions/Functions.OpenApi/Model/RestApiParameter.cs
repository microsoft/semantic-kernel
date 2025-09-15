// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API parameter.
/// </summary>
public sealed class RestApiParameter
{
    /// <summary>
    /// The parameter name.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// The parameter argument name.
    /// If provided, the argument name will be used to search for the parameter value in function arguments.
    /// If no value is found using the argument name, the original name - <see cref="RestApiParameter.Name"/> will be used for the search instead.
    /// </summary>
    public string? ArgumentName
    {
        get => this._argumentName;
        set
        {
            this._freezable.ThrowIfFrozen();
            this._argumentName = value;
        }
    }

    /// <summary>
    /// The parameter type - string, integer, number, boolean, array and object.
    /// </summary>
    internal string Type { get; }

    /// <summary>
    /// The parameter type modifier that refines the generic parameter type to a more specific one.
    /// More details can be found at https://swagger.io/docs/specification/data-models/data-types
    /// </summary>
    public string? Format { get; }

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
    public RestApiParameterLocation Location { get; }

    /// <summary>
    /// The parameter style - defines how multiple values are delimited.
    /// </summary>
    public RestApiParameterStyle? Style { get; }

    /// <summary>
    /// Type of array item for parameters of "array" type.
    /// </summary>
    internal string? ArrayItemType { get; }

    /// <summary>
    /// The default value.
    /// </summary>
    public object? DefaultValue { get; }

    /// <summary>
    /// Specifies whether arrays and objects should generate separate parameters for each array item or object property.
    /// </summary>
    public bool Expand { get; }

    /// <summary>
    /// The schema of the parameter.
    /// </summary>
    public KernelJsonSchema? Schema
    {
        get => this._schema;
        set
        {
            this._freezable.ThrowIfFrozen();
            this._schema = value;
        }
    }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiParameter"/> class.
    /// </summary>
    /// <param name="name">The parameter name.</param>
    /// <param name="type">The parameter type.</param>
    /// <param name="isRequired">Flag specifying if the parameter is required or not.</param>
    /// <param name="expand">Specifies whether arrays and objects should generate separate parameters for each array item or object property.</param>
    /// <param name="location">The parameter location.</param>
    /// <param name="style">The parameter style - defines how multiple values are delimited.</param>
    /// <param name="arrayItemType">Type of array item for parameters of "array" type.</param>
    /// <param name="defaultValue">The parameter default value.</param>
    /// <param name="description">The parameter description.</param>
    /// <param name="format">The parameter type modifier that refines the generic parameter type to a more specific one.
    /// More details can be found at https://swagger.io/docs/specification/data-models/data-types</param>
    /// <param name="schema">The parameter schema.</param>
    internal RestApiParameter(
        string name,
        string type,
        bool isRequired,
        bool expand,
        RestApiParameterLocation location,
        RestApiParameterStyle? style = null,
        string? arrayItemType = null,
        object? defaultValue = null,
        string? description = null,
        string? format = null,
        KernelJsonSchema? schema = null)
    {
        this.Name = name;
        this.Type = type;
        this.IsRequired = isRequired;
        this.Expand = expand;
        this.Location = location;
        this.Style = style;
        this.ArrayItemType = arrayItemType;
        this.DefaultValue = defaultValue;
        this.Description = description;
        this.Format = format;
        this.Schema = schema;
    }
    internal void Freeze()
    {
        this._freezable.Freeze();
    }

    private readonly Freezable _freezable = new();
    private string? _argumentName;
    private KernelJsonSchema? _schema;
}
