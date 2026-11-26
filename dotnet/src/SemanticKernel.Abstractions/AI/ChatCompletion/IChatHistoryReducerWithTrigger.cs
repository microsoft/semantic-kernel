// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Interface for reducing chat history with support for trigger-based reduction.
/// </summary>
/// <remarks>
/// This interface extends <see cref="IChatHistoryReducer"/> by allowing reducers to be
/// configured with specific trigger events that determine when the reduction should occur.
/// </remarks>
public interface IChatHistoryReducerWithTrigger : IChatHistoryReducer
{
    /// <summary>
    /// Gets the trigger events that should invoke this reducer.
    /// </summary>
    /// <remarks>
    /// A reducer can be configured to respond to one or more trigger events.
    /// If multiple events are specified, the reducer will be invoked on any of those events.
    /// </remarks>
    IReadOnlyCollection<ChatReducerTriggerEvent> TriggerEvents { get; }

    /// <summary>
    /// Determines if the reducer should be invoked for the specified trigger event.
    /// </summary>
    /// <param name="triggerEvent">The trigger event being evaluated.</param>
    /// <returns><see langword="true"/> if the reducer should be invoked; otherwise, <see langword="false"/>.</returns>
    bool ShouldTriggerOn(ChatReducerTriggerEvent triggerEvent);
}
