﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData.ProviderServices;

/// <summary>
/// Represents a key property on a vector store record.
/// This is an internal support type meant for use by connectors only, and not for use by applications.
/// </summary>
[Experimental("MEVD9001")]
public class KeyPropertyModel(string modelName, Type type) : PropertyModel(modelName, type)
{
    /// <inheritdoc/>
    public override string ToString()
        => $"{this.ModelName} (Key, {this.Type.Name})";
}
