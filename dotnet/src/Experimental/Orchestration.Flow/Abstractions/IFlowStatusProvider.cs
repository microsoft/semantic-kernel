// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

namespace Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

/// <summary>
/// The flow status provider interface.
/// </summary>
public interface IFlowStatusProvider
{
    /// <summary>
    /// Get the state of current execution session.
    /// </summary>
    /// <param name="sessionId">The session id</param>
    /// <returns>The variables</returns>
    Task<ExecutionState> GetExecutionStateAsync(string sessionId);

    /// <summary>
    /// Save the state for current execution session.
    /// </summary>
    /// <param name="sessionId">The session id</param>
    /// <param name="state">The execution state</param>
    /// <returns>Task</returns>
    Task SaveExecutionStateAsync(string sessionId, ExecutionState state);

    /// <summary>
    /// Get the chat history for current execution session.
    /// </summary>
    /// <param name="sessionId">The session id</param>
    /// <param name="stepId">The step id</param>
    /// <returns></returns>
    Task<ChatHistory?> GetChatHistoryAsync(string sessionId, string stepId);

    /// <summary>
    /// Save the chat history for current execution session.
    /// </summary>
    /// <param name="sessionId">The session id</param>
    /// <param name="stepId">The step id</param>
    /// <param name="history">The chat history</param>
    /// <returns></returns>
    Task SaveChatHistoryAsync(string sessionId, string stepId, ChatHistory history);

    /// <summary>
    /// Get the ReAct history for current execution <see cref="FlowStep"/>.
    /// </summary>
    /// <param name="sessionId">The session id</param>
    /// <param name="stepId">The step id</param>
    /// <returns>The list of ReAct steps for current flow step.</returns>
    Task<List<ReActStep>> GetReActStepsAsync(string sessionId, string stepId);

    /// <summary>
    /// Save the ReAct history for current execution step to <see cref="Memory"/>.
    /// </summary>
    /// <param name="sessionId">The session id</param>
    /// <param name="stepId">The step id</param>
    /// <param name="steps">The executed steps</param>
    /// <returns>Task</returns>
    Task SaveReActStepsAsync(string sessionId, string stepId, List<ReActStep> steps);
}
