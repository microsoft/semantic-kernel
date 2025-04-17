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

    /// <summary>
    /// Gets or sets the time at which the text search is performed.
    /// </summary>
    public TextRagSearchTime SearchTime { get; init; } = TextRagSearchTime.BeforeAIInvoke;

    /// <summary>
    /// Gets or sets the name of the plugin method that will be made available for searching
    /// if the <see cref="SearchTime"/> option is set to <see cref="TextRagSearchTime.ViaPlugin"/>.
    /// </summary>
    public string? PluginSearchFunctionName { get; init; }

    /// <summary>
    /// Gets or sets the description of the plugin method that will be made available for searching
    /// if the <see cref="SearchTime"/> option is set to <see cref="TextRagSearchTime.ViaPlugin"/>.
    /// </summary>
    public string? PluginSearchFunctionDescription { get; init; }

    /// <summary>
    /// The time at which the text search is performed.
    /// </summary>
    public enum TextRagSearchTime
    {
        /// <summary>
        /// A search is performed each time that the AI is invoked just before the AI is invoked
        /// and the results are provided to the AI via the invocation context.
        /// </summary>
        BeforeAIInvoke,

        /// <summary>
        /// A search may be performed by the AI on demand via a plugin.
        /// </summary>
        ViaPlugin
    }
}
