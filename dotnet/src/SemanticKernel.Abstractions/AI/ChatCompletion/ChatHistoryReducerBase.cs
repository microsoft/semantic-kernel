// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Abstract base class for implementing trigger-aware chat history reducers.
/// </summary>
public abstract class ChatHistoryReducerBase : IChatHistoryReducerWithTrigger
{
    /// <inheritdoc/>
    public IReadOnlyCollection<ChatReducerTriggerEvent> TriggerEvents { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryReducerBase"/> class.
    /// </summary>
    /// <param name="triggerEvents">The events that should trigger this reducer. Defaults to BeforeMessagesRetrieval if not specified.</param>
    protected ChatHistoryReducerBase(params ChatReducerTriggerEvent[] triggerEvents)
    {
        this.TriggerEvents = triggerEvents.Length > 0
            ? triggerEvents.ToArray()
            : new[] { ChatReducerTriggerEvent.BeforeMessagesRetrieval };
    }

    /// <inheritdoc/>
    public bool ShouldTriggerOn(ChatReducerTriggerEvent triggerEvent)
    {
        return this.TriggerEvents.Contains(triggerEvent);
    }

    /// <inheritdoc/>
    public abstract System.Threading.Tasks.Task<IEnumerable<ChatMessageContent>?> ReduceAsync(
        IReadOnlyList<ChatMessageContent> chatHistory,
        System.Threading.CancellationToken cancellationToken = default);
}
