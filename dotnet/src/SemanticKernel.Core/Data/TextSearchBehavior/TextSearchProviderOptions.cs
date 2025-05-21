// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains options for the <see cref="TextSearchProvider"/>.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class TextSearchProviderOptions
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
    public RagBehavior SearchTime { get; init; } = RagBehavior.BeforeAIInvoke;

    /// <summary>
    /// Gets or sets the name of the plugin method that will be made available for searching
    /// if the <see cref="SearchTime"/> option is set to <see cref="RagBehavior.OnDemandFunctionCalling"/>.
    /// </summary>
    /// <value>
    /// Defaults to &quot;Search&quot; if not set.
    /// </value>
    public string? PluginFunctionName { get; init; }

    /// <summary>
    /// Gets or sets the description of the plugin method that will be made available for searching
    /// if the <see cref="SearchTime"/> option is set to <see cref="RagBehavior.OnDemandFunctionCalling"/>.
    /// </summary>
    /// <value>
    /// Defaults to &quot;Allows searching for additional information to help answer the user question.&quot; if not set.
    /// </value>
    public string? PluginFunctionDescription { get; init; }

    /// <summary>
    /// When providing the text chunks to the AI model on invocation, this string is prefixed
    /// to those chunks, in order to provide some context to the model.
    /// </summary>
    /// <value>
    /// Defaults to &quot;Consider the following information from source documents when responding to the user:&quot;
    /// </value>
    public string? ContextPrompt { get; init; }

    /// <summary>
    /// When providing the text chunks to the AI model on invocation, this string is postfixed
    /// to those chunks, in order to instruct the model to include citations.
    /// </summary>
    /// <value>
    /// Defaults to &quot;## Additional Context\nInclude citations to the source document with document name and link if document name and link is available.:&quot;
    /// </value>
    public string? IncludeCitationsPrompt { get; init; }

    /// <summary>
    /// Optional delegate to override the default context creation implementation.
    /// </summary>
    /// <remarks>
    /// <para>
    /// If provided, this delegate will be used to do the following:
    /// 1. Create the output context provided by the <see cref="TextSearchProvider"/> when invoking the AI model.
    /// 2. Create the response text when invoking the component via a plugin.
    /// </para>
    /// <para>
    /// Note that the delegate should include the context prompt and the
    /// include citations prompt if they are required in the output.
    /// The <see cref="ContextPrompt"/> and <see cref="IncludeCitationsPrompt"/> settings
    /// will not be used if providing this delegate.
    /// </para>
    /// </remarks>
    public Func<List<TextSearchResult>, string>? ContextFormatter { get; init; }

    /// <summary>
    /// Choices for controlling the behavior of the <see cref="TextSearchProvider"/>.
    /// </summary>
    public enum RagBehavior
    {
        /// <summary>
        /// A search is performed each time that the model/agent is invoked just before invocation
        /// and the results are provided to the model/agent via the invocation context.
        /// </summary>
        BeforeAIInvoke,

        /// <summary>
        /// A search may be performed by the model/agent on demand via function calling.
        /// </summary>
        OnDemandFunctionCalling
    }
}
