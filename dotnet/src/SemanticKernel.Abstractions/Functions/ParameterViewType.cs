// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable CA1720 // Identifier contains type name

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Represents the type for the parameter view.
/// </summary>
public class ParameterViewType : IEquatable<ParameterViewType>
{
    /// <summary>
    /// The name of the parameter view type
    /// </summary>
    private readonly string _name;

    /// <summary>
    /// Represents the "string" parameter view type.
    /// </summary>
    public static readonly ParameterViewType String = new("string");

    /// <summary>
    /// Represents the "number" parameter view type.
    /// </summary>
    public static readonly ParameterViewType Number = new("number");

    /// <summary>
    /// Represents the "object" parameter view type.
    /// </summary>
    public static readonly ParameterViewType Object = new("object");

    /// <summary>
    /// Represents the "array" parameter view type.
    /// </summary>
    public static readonly ParameterViewType Array = new("array");

    /// <summary>
    /// Represents the "boolean" parameter view type.
    /// </summary>
    public static readonly ParameterViewType Boolean = new("boolean");

    /// <summary>
    /// Initializes a new instance of the <see cref="ParameterViewType"/> class.
    /// </summary>
    /// <param name="name">The name of the parameter view type.</param>
    public ParameterViewType(string name)
    {
        Verify.NotNullOrWhiteSpace(name, nameof(name));

        this._name = name;
    }

    /// <summary>
    /// Gets the name of the parameter view type.
    /// </summary>
    public string Name => this._name;

    /// <summary>
    /// Returns a string representation of the parameter view type.
    /// </summary>
    /// <returns>A string representing the parameter view type.</returns>
    public override string ToString() => this._name;

    /// <summary>
    /// Determines whether this instance of <see cref="ParameterViewType"/> is equal to another instance.
    /// </summary>
    /// <param name="other">The <see cref="ParameterViewType"/> to compare with this instance.</param>
    /// <returns><c>true</c> if the instances are equal; otherwise, <c>false</c>.</returns>
    public bool Equals(ParameterViewType other)
    {
        if (other is null)
        {
            return false;
        }

        return string.Equals(this.Name, other.Name, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Determines whether this instance of <see cref="ParameterViewType"/> is equal to another object.
    /// </summary>
    /// <param name="obj">The object to compare with this instance.</param>
    /// <returns><c>true</c> if the instances are equal; otherwise, <c>false</c>.</returns>
    public override bool Equals(object obj)
    {
        return obj is ParameterViewType other && this.Equals(other);
    }

    /// <summary>
    /// Returns the hash code for this instance.
    /// </summary>
    /// <returns>A hash code for the current instance.</returns>
    public override int GetHashCode()
    {
        return this.Name.GetHashCode();
    }
}
