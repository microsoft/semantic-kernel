// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides settings for a kernel function.
/// </summary>
/// <remarks>
/// Used for deserialisation of yaml function configuration.
/// </remarks>
public class FunctionSettings
{
    /// <summary>
    /// Extra properties that may be included in the serialized execution settings.
    /// </summary>
    /// <remarks>
    /// Avoid using this property if possible. Instead, use one of the classes that extends <see cref="FunctionSettings"/>.
    /// </remarks>
    [JsonExtensionData]
    public IDictionary<string, object>? ExtensionData
    {
        get => this._extensionData;

        set
        {
            this.ThrowIfFrozen();
            this._extensionData = value;
        }
    }

    /// <summary>
    /// Gets a value that indicates whether the <see cref="FunctionSettings"/> are currently modifiable.
    /// </summary>
    [JsonIgnore]
    public bool IsFrozen { get; private set; }

    /// <summary>
    /// Makes the current <see cref="FunctionSettings"/> unmodifiable and sets its IsFrozen property to true.
    /// </summary>
    public virtual void Freeze()
    {
        if (this.IsFrozen)
        {
            return;
        }

        this.IsFrozen = true;

        if (this._extensionData is not null)
        {
            this._extensionData = new ReadOnlyDictionary<string, object>(this._extensionData);
        }
    }

    /// <summary>
    /// Creates a new <see cref="FunctionSettings"/> object that is a copy of the current instance.
    /// </summary>
    public virtual FunctionSettings Clone()
    {
        return new()
        {
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null
        };
    }

    /// <summary>
    /// Throws an <see cref="InvalidOperationException"/> if the <see cref="FunctionSettings"/> are frozen.
    /// </summary>
    /// <exception cref="InvalidOperationException"></exception>
    protected void ThrowIfFrozen()
    {
        if (this.IsFrozen)
        {
            throw new InvalidOperationException("FunctionExecutionSettings are frozen and cannot be modified.");
        }
    }

    #region private ================================================================================

    private IDictionary<string, object>? _extensionData;

    #endregion
}
