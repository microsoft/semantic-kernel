// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Exception thrown when a plan cannot be created.
/// </summary>
public sealed class PlanCreationException : KernelException
{
    /// <summary>
    /// Gets the prompt template used to generate the plan.
    /// </summary>
    public string? CreatePlanPrompt { get; set; } = null;

    /// <summary>
    /// Completion results from the model; generally, this is the proposed plan.
    /// </summary>
    public ChatMessageContent? ModelResults { get; set; } = null;

    /// <summary>
    /// Initializes a new instance of the <see cref="PlanCreationException"/> class.
    /// </summary>
    public PlanCreationException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PlanCreationException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public PlanCreationException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PlanCreationException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public PlanCreationException(string? message, Exception? innerException) : base(message, innerException)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PlanCreationException"/> class.
    /// Exception thrown when a plan cannot be created containing the prompt and model results.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="createPlanPrompt">The prompt template used to generate the plan.</param>
    /// <param name="modelResults">Completion results from the model; generally, this is the proposed plan.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public PlanCreationException(string? message, string? createPlanPrompt, ChatMessageContent? modelResults, Exception? innerException = null) : base(message, innerException)
    {
        this.CreatePlanPrompt = createPlanPrompt;
        this.ModelResults = modelResults;
    }
}
