// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API Operation Server Variable.
/// </summary>
public sealed class RestApiOperationServerVariable
{
    /// <summary>
    /// An optional description for the server variable. CommonMark syntax MAY be used for rich text representation.
    /// </summary>
    public string? Description { get; }

    /// <summary>
    /// REQUIRED. The default value to use for substitution, and to send, if an alternate value is not supplied.
    /// Unlike the Schema Object's default, this value MUST be provided by the consumer.
    /// </summary>
    public string Default { get; }

    /// <summary>
    /// An enumeration of string values to be used if the substitution options are from a limited set.
    /// </summary>
    public List<string>? Enum { get; }

    /// <summary>
    /// Construct a new <see cref="RestApiOperationServerVariable"/> object.
    /// </summary>
    /// <param name="defaultValue">The default value to use for substitution.</param>
    /// <param name="description">An optional description for the server variable.</param>
    /// <param name="enumValues">An enumeration of string values to be used if the substitution options are from a limited set.</param>
    public RestApiOperationServerVariable(string defaultValue, string? description = null, List<string>? enumValues = null)
    {
        this.Default = defaultValue;
        this.Description = description;
        this.Enum = enumValues;
    }

    /// <summary>
    /// Return true if the value is valid based on the enumeration of string values to be used.
    /// </summary>
    /// <param name="value">Value to be used as a substitution.</param>
    public bool IsValid(string? value)
    {
        return this.Enum?.Contains(value!) ?? true;
    }
}
