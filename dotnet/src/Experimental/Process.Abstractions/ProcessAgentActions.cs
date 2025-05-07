// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the actions that can be performed by a process agent.
/// </summary>
[DataContract]
public sealed class ProcessAgentActions
{
    /// <summary>
    /// Creates a new instance of the <see cref="ProcessAgentActions"/> class.
    /// </summary>
    /// <param name="codeActions">The code based actions. These are not serializable to a declarative format.</param>
    /// <param name="declarativeActions">The declarative action. These are required when building an exportable process.</param>
    /// <exception cref="ArgumentException"></exception>
    public ProcessAgentActions(
        ProcessAgentCodeActions? codeActions = null,
        ProcessAgentDeclarativeActions? declarativeActions = null)
    {
        this.CodeActions = codeActions;
        this.DeclarativeActions = declarativeActions;

        if (codeActions == null && declarativeActions == null)
        {
            throw new ArgumentException("At least one action must be provided.");
        }
    }

    /// <summary>
    /// The optional handler group for code-based actions.
    /// </summary>
    public ProcessAgentCodeActions? CodeActions { get; init; }

    /// <summary>
    /// The optional handler group for declarative actions.
    /// </summary>
    public ProcessAgentDeclarativeActions? DeclarativeActions { get; init; }
}

/// <summary>
/// Represents the code-based actions that can be performed by a process agent.
/// </summary>
public sealed class ProcessAgentCodeActions
{
    /// <summary>
    /// The optional handler group for OnComplete events.
    /// </summary>
    public Action<object?, KernelProcessStepContext>? OnComplete { get; init; }
    /// <summary>
    /// The optional handler group for OnError events.
    /// </summary>
    public Action<object?, KernelProcessStepContext>? OnError { get; init; }
}

/// <summary>
/// Represents the declarative actions that can be performed by a process agent.
/// </summary>
public class ProcessAgentDeclarativeActions
{
    /// <summary>
    /// The optional handler group for OnComplete events.
    /// </summary>
    public KernelProcessDeclarativeConditionHandler? OnComplete { get; init; }
    /// <summary>
    /// The optional handler group for OnError events.
    /// </summary>
    public KernelProcessDeclarativeConditionHandler? OnError { get; init; }
}
