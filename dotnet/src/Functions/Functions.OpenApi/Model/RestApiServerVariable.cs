// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API server variable.
/// </summary>
[Experimental("SKEXP0040")]
public sealed class RestApiServerVariable
{
    /// <summary>
    /// The variable argument name.
    /// If provided, the argument name will be used to search for the corresponding variable value in function arguments.
    /// If no property value is found using the argument name, the original name represented by the  <see cref="RestApiServer.Variables"/> dictionary key will be used for the search instead.
    /// </summary>
    public string? ArgumentName
    {
        get => this._argumentName;
        set
        {
            this.ThrowIfFrozen();
            this._argumentName = value;
        }
    }

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
    public IReadOnlyList<string>? Enum { get; }

    /// <summary>
    /// Construct a new <see cref="RestApiServerVariable"/> object.
    /// </summary>
    /// <param name="defaultValue">The default value to use for substitution.</param>
    /// <param name="description">An optional description for the server variable.</param>
    /// <param name="enumValues">An enumeration of string values to be used if the substitution options are from a limited set.</param>
    internal RestApiServerVariable(string defaultValue, string? description = null, List<string>? enumValues = null)
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

    /// <summary>
    /// Makes the current instance unmodifiable.
    /// </summary>
    internal void Freeze()
    {
        if (this._isFrozen)
        {
            return;
        }

        this._isFrozen = true;
    }

    /// <summary>
    /// Throws an <see cref="InvalidOperationException"/> if the <see cref="RestApiServerVariable"/> is frozen.
    /// </summary>
    /// <exception cref="InvalidOperationException"></exception>
    private void ThrowIfFrozen()
    {
        if (this._isFrozen)
        {
            throw new InvalidOperationException("RestApiOperationServerVariable is frozen and cannot be modified.");
        }
    }

    private string? _argumentName;
    private bool _isFrozen = false;
}
