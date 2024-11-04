// Copyright (c) Microsoft. All rights reserved.
using System;
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
    /// <param name="processEvents"></param>
    /// <returns></returns>
    public static IEnumerable<EventContainer<KernelProcessEvent>> Prepare(IEnumerable<KernelProcessEvent> processEvents)
    {
        foreach (KernelProcessEvent processEvent in processEvents)
        {
            yield return new EventContainer<KernelProcessEvent>(TypeInfo.FromObject(processEvent.Data), processEvent);
        }
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="EventContainers"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static IEnumerable<KernelProcessEvent> Process(IEnumerable<EventContainer<KernelProcessEvent>> EventContainers)
    {
        foreach (EventContainer<KernelProcessEvent> EventContainer in EventContainers)
        {
            KernelProcessEvent processEvent = EventContainer.Payload;

            if (processEvent.Data == null)
            {
                yield return processEvent;
            }

            if (EventContainer.DataType == null)
            {
                throw new KernelException($"{nameof(KernelProcessEvent)} persisted without type information for {nameof(KernelProcessEvent.Data)} property.");
            }

            TypeInfo processEventTypeInfo = EventContainer.DataType;

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
