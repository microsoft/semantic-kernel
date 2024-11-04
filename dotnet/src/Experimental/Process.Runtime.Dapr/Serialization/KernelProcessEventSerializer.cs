// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
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
    /// <param name="processEvents"></param>
    /// <returns></returns>
    public static string Write(IEnumerable<KernelProcessEvent> processEvents)
    {
        EventContainer<KernelProcessEvent>[] containedEvents = Prepare(processEvents).ToArray();
        return JsonSerializer.Serialize(containedEvents);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="json"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static IEnumerable<KernelProcessEvent> Read(string json)
    {
        EventContainer<KernelProcessEvent>[] containedEvents =
            JsonSerializer.Deserialize<EventContainer<KernelProcessEvent>[]>(json) ??
            throw new KernelException($"Unable to deserialize {nameof(KernelProcessEvent)} queue.");

        return Process(containedEvents);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="processEvents"></param>
    /// <returns></returns>
    private static IEnumerable<EventContainer<KernelProcessEvent>> Prepare(IEnumerable<KernelProcessEvent> processEvents)
    {
        foreach (KernelProcessEvent processEvent in processEvents)
        {
            yield return new EventContainer<KernelProcessEvent>(TypeInfo.FromObject(processEvent.Data), processEvent);
        }
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="eventContainers"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static IEnumerable<KernelProcessEvent> Process(IEnumerable<EventContainer<KernelProcessEvent>> eventContainers)
    {
        foreach (EventContainer<KernelProcessEvent> eventContainer in eventContainers)
        {
            KernelProcessEvent processEvent = eventContainer.Payload;

            if (processEvent.Data == null)
            {
                yield return processEvent;
            }

            if (eventContainer.DataType == null)
            {
                throw new KernelException($"{nameof(KernelProcessEvent)} persisted without type information for {nameof(KernelProcessEvent.Data)} property.");
            }

            TypeInfo processEventTypeInfo = eventContainer.DataType;

            Type dataType = TypeInfo.Resolve(processEventTypeInfo);
            if (processEvent.Data!.GetType() == dataType)
            {
                yield return processEvent;
            }

            var eventData = ((JsonElement)processEvent.Data!).Deserialize(dataType!);
            processEvent = processEvent with { Data = eventData };

            yield return processEvent;
        }
    }
}
