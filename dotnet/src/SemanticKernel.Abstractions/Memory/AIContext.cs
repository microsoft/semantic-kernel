// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A class containing any context that should be provided to the AI model
/// as supplied by an <see cref="AIContextProvider"/>.
/// </summary>
/// <remarks>
/// Each <see cref="AIContextProvider"/> has the ability to provide its own context for each invocation.
/// The <see cref="AIContext"/> class contains the additional context supplied by the <see cref="AIContextProvider"/>.
/// This context will be combined with context supplied by other providers before being passed to the AI model.
/// This context is per invocation, and will not be stored as part of the chat history.
/// </remarks>
[Experimental("SKEXP0130")]
public sealed class AIContext
{
    /// <summary>
    /// Any instructions to pass to the AI model in addition to any other prompts
    /// that it may already have (in the case of an agent), or chat history that may
    /// already exist.
    /// </summary>
    public string? Instructions { get; set; }

    /// <summary>
    /// A list of functions/tools to make available to the AI model for the current invocation.
    /// </summary>
    public IList<AIFunction> AIFunctions { get; set; } = [];
}
