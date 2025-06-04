// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a freezable object.
/// </summary>
[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "This class is an internal utility.")]
[ExcludeFromCodeCoverage]
internal sealed class Freezable
{
    public bool IsFrozen { get; private set; }

    /// <summary>
    /// Makes the current instance unmodifiable.
    /// </summary>
    public void Freeze()
    {
        if (this.IsFrozen)
        {
            return;
        }

        this.IsFrozen = true;
    }

    /// <summary>
    /// Throws an <see cref="InvalidOperationException"/> if the object is frozen.
    /// </summary>
    /// <exception cref="InvalidOperationException"></exception>
    public void ThrowIfFrozen()
    {
        if (this.IsFrozen)
        {
            throw new InvalidOperationException("The object is frozen and cannot be modified.");
        }
    }
}
