// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <summary>
/// Contains options affecting model building; passed to <see cref="VectorStoreRecordModelBuilder"/>.
/// </summary>
[Experimental("MEVD9001")]
public sealed class VectorStoreRecordModelBuildingOptions
{
    /// <summary>
    /// Whether multiple key properties are supported.
    /// </summary>
    public required bool SupportsMultipleKeys { get; set; }

    /// <summary>
    /// Whether multiple vector properties are supported.
    /// </summary>
    public required bool SupportsMultipleVectors { get; set; }

    /// <summary>
    /// Whether at least one vector property is required.
    /// </summary>
    public required bool RequiresAtLeastOneVector { get; set; }

    /// <summary>
    /// The set of types that are supported as key properties.
    /// </summary>
    public required HashSet<Type>? SupportedKeyPropertyTypes { get; set; }

    /// <summary>
    /// The set of types that are supported as data properties.
    /// </summary>
    public required HashSet<Type>? SupportedDataPropertyTypes { get; set; }

    /// <summary>
    /// The set of element types that are supported within collection types in data properties.
    /// </summary>
    public required HashSet<Type>? SupportedEnumerableDataPropertyTypes { get; set; }

    /// <summary>
    /// The set of types that are supported as vector properties.
    /// </summary>
    public required HashSet<Type>? SupportedVectorPropertyTypes { get; set; }

    /// <summary>
    /// Indicates that an external serializer will be used (e.g. System.Text.Json).
    /// </summary>
    public bool UsesExternalSerializer { get; set; }

    /// <summary>
    /// Indicates that the database requires the key property to have a special, reserved name.
    /// When set, the model builder will manage the key storage name, and users may not customize it.
    /// </summary>
    public string? ReservedKeyStorageName { get; set; }
}
