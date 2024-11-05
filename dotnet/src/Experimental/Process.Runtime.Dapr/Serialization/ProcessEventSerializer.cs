// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// %%% COMMENT
/// </summary>
internal static class ProcessEventSerializer
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="processEvent"></param>
    /// <returns></returns>
    public static string ToJson(this ProcessEvent processEvent)
    {
        EventContainer<ProcessEvent> containedEvent = new(TypeInfo.GetAssemblyQualifiedType(processEvent.Data), processEvent);
        return JsonSerializer.Serialize(containedEvent);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="jsonEvents"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static IEnumerable<ProcessEvent> ToProcessEvents(this IEnumerable<string> jsonEvents)
    {
        foreach (string json in jsonEvents)
        {
            EventContainer<ProcessEvent> eventContainer =
                JsonSerializer.Deserialize<EventContainer<ProcessEvent>>(json) ??
                throw new KernelException($"Unable to deserialize {nameof(ProcessEvent)} queue.");
            yield return eventContainer.Payload with { Data = TypeInfo.ConvertValue(eventContainer.DataTypeName, eventContainer.Payload.Data) };
        }
    }
}
