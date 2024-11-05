// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// %%% COMMENT
/// </summary>
internal static class KernelProcessEventSerializer
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="processEvent"></param>
    /// <returns></returns>
    public static string ToJson(this KernelProcessEvent processEvent)
    {
        EventContainer<KernelProcessEvent> containedEvents = new(TypeInfo.GetAssemblyQualifiedType(processEvent.Data), processEvent);
        return JsonSerializer.Serialize(containedEvents);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="jsonEvents"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static IEnumerable<KernelProcessEvent> ToKernelProcessEvents(this IEnumerable<string> jsonEvents)
    {
        foreach (string json in jsonEvents)
        {
            EventContainer<KernelProcessEvent> eventContainer =
                JsonSerializer.Deserialize<EventContainer<KernelProcessEvent>>(json) ??
                throw new KernelException($"Unable to deserialize {nameof(KernelProcessEvent)} queue.");
            yield return eventContainer.Payload with { Data = TypeInfo.ConvertValue(eventContainer.DataTypeName, eventContainer.Payload.Data) };
        }
    }
}
