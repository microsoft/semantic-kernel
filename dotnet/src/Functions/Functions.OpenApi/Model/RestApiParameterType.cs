// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents the JSON schema type.
/// </summary>
[Experimental("SKEXP0040")]
[Flags]
[SuppressMessage("Naming", "CA1720:Identifier contains type name", Justification = "Type name is appropriate for the enum representing JSON schema types.")]
public enum RestApiParameterType
{
    /// <summary>
    /// Represents a null type.
    /// </summary>
    Null = 1,

    /// <summary>
    /// Represents a boolean type.
    /// </summary>
    Boolean = 2,

    /// <summary>
    /// Represents an integer type.
    /// </summary>
    Integer = 4,

    /// <summary>
    /// Represents a number type.
    /// </summary>
    Number = 8,

    /// <summary>
    /// Represents a string type.
    /// </summary>
    String = 16,

    /// <summary>
    /// Represents an object type.
    /// </summary>
    Object = 32,

    /// <summary>
    /// Represents an array type.
    /// </summary>
    Array = 64,
}
