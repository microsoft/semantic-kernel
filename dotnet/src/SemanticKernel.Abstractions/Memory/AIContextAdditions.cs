// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A class containing any additional context that the AI may need to provide a meaningful response
/// as supplied by an <see cref="AIContextBehavior"/>.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class AIContextAdditions
{
    /// <summary>
    /// Any additional instructions to pass to the AI model.
    /// </summary>
    public string? AdditionalInstructions { get; set; }

    /// <summary>
    /// A list of functions/tools to make available to the AI model.
    /// </summary>
    public List<AIFunction> AIFunctions { get; set; } = new();
}
