// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Process.Internal;

/// <summary>
/// Factory that helps create <see cref="KernelProcessProxyMessage"/>
/// </summary>
internal static class KernelProcessProxyMessageFactory
{
    /// <summary>
    /// Captures SK process event data into <see cref="KernelProcessProxyMessage"/>
    /// </summary>
    /// <param name="processId">id of the running process where the event is emitted from</param>
    /// <param name="triggerEventName">SK event name triggered inside the process</param>
    /// <param name="publishTopic">name to be used for publishing the event outside of the SK process</param>
    /// <param name="data">data contained from SK event to be emitted externally</param>
    /// <returns><see cref="KernelProcessProxyMessage"/></returns>
    internal static KernelProcessProxyMessage CreateProxyMessage(string processId, string triggerEventName, string publishTopic, object? data)
    {
        KernelProcessProxyMessage newMessage = new()
        {
            ProcessId = processId,
            TriggerEventId = triggerEventName,
            ExternalTopicName = publishTopic,
            EventData = data != null ? data as KernelProcessEventData : null
        };

        return newMessage;
    }
}
