// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Contains options for the <see cref="TextRagComponent"/>.
/// </summary>
public class TextRagComponentOptions
{
    private int _top = 3;

    /// <summary>
    /// Maximum number of results to return from the similarity search.
    /// </summary>
    /// <remarks>The value must be greater than 0.</remarks>
    /// <value>The default value is 3 if not set.</value>
    public int Top
    {
        get => this._top;
        init
        {
            if (value < 1)
            {
                throw new ArgumentOutOfRangeException(nameof(value), "Top must be greater than 0.");
            }

            this._top = value;
        }
    }
}
