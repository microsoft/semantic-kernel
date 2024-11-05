// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// %%% COMMENT
/// </summary>
internal static class ProcessEventSerializer
{
    public static string Write(IEnumerable<ProcessEvent> processEvents)
    {
        EventContainer<ProcessEvent>[] containedEvents = Prepare(processEvents).ToArray();
        return JsonSerializer.Serialize(containedEvents);
    }

    public static IEnumerable<ProcessEvent> Read(string json)
    {
        EventContainer<ProcessEvent>[] containedEvents =
            JsonSerializer.Deserialize<EventContainer<ProcessEvent>[]>(json) ??
            throw new KernelException($"Unable to deserialize {nameof(ProcessEvent)} queue.");

        return Process(containedEvents);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="processEvents"></param>
    /// <returns></returns>
    private static IEnumerable<EventContainer<ProcessEvent>> Prepare(IEnumerable<ProcessEvent> processEvents)
    {
        foreach (ProcessEvent processEvent in processEvents)
        {
            yield return new EventContainer<ProcessEvent>(TypeInfo.GetAssemblyQualifiedType(processEvent.Data), processEvent);
        }
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="eventContainers"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    private static IEnumerable<ProcessEvent> Process(IEnumerable<EventContainer<ProcessEvent>> eventContainers)
    {
        foreach (EventContainer<ProcessEvent> eventContainer in eventContainers)
        {
            yield return eventContainer.Payload with { Data = TypeInfo.ConvertValue(eventContainer.DataTypeName, eventContainer.Payload.Data) };
        }
    }
}
