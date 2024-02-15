// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Provides extension methods for rendering Handlebars templates in the context of a Semantic Kernel.
/// </summary>
internal sealed class HandlebarsPlanCreationException : KernelException
{
    /// <summary>
    /// Gets the prompt template used to generate the plan.
    /// </summary>
    public string? CreatePlanPrompt { get; set; } = null;

    /// <summary>
    /// Completion results from the model, generally, the proposed handlebars template representing the plan.
    /// </summary>
    public ChatMessageContent? ModelResults { get; set; } = null;

    public HandlebarsPlanCreationException() : base()
    {
    }

    public HandlebarsPlanCreationException(string? message) : base(message)
    {
    }

    public HandlebarsPlanCreationException(string? message, System.Exception? innerException) : base(message, innerException)
    {
    }

    public HandlebarsPlanCreationException(string? message, string? createPlanPrompt, ChatMessageContent? modelResults, System.Exception? innerException = null) : base(message, innerException)
    {
        this.CreatePlanPrompt = createPlanPrompt;
        this.ModelResults = modelResults;
    }
}
