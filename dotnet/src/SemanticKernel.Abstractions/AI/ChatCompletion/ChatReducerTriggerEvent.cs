// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Defines the events that can trigger a reducer in the chat history management.
/// </summary>
public enum ChatReducerTriggerEvent
{
    /// <summary>
    /// Trigger the reducer when a new message is added.
    /// </summary>
    /// <remarks>
    /// This trigger occurs after a message is added to the chat history, allowing the reducer
    /// to process the messages before they are used in subsequent operations.
    /// </remarks>
    AfterMessageAdded,

    /// <summary>
    /// Trigger the reducer before messages are retrieved from the provider.
    /// </summary>
    /// <remarks>
    /// This trigger occurs just before the chat history is passed to the model provider,
    /// allowing the reducer to trim or process messages before they are sent.
    /// </remarks>
    BeforeMessagesRetrieval,

    /// <summary>
    /// Trigger the reducer after each tool call response is received from the provider.
    /// </summary>
    /// <remarks>
    /// This trigger occurs each time a tool/function result is received (FunctionResultContent),
    /// allowing the reducer to manage history size during long-running agentic workflows with
    /// multiple tool calls that could exceed token limits.
    /// </remarks>
    AfterToolCallResponseReceived
}
