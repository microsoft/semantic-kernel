// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// Serializer for <see cref="ProcessEvent"/> objects.
/// </summary>
/// <remarks>
/// Includes type info for <see cref="ProcessEvent.Data"/>.
/// </remarks>
internal static class ProcessEventSerializer
{
    /// <summary>
    /// Serialize <see cref="ProcessEvent"/> to JSON with type information.
    /// </summary>
    public static string ToJson(this ProcessEvent processEvent)
    {
        EventContainer<ProcessEvent> containedEvent = new(TypeInfo.GetAssemblyQualifiedType(processEvent.Data), processEvent);
        return JsonSerializer.Serialize(containedEvent);
    }

    /// <summary>
    /// Deserialize a list of JSON events into a list of <see cref="ProcessEvent"/> objects.
    /// </summary>
    /// <exception cref="KernelException">If any event fails deserialization</exception>
    public static IList<ProcessEvent> ToProcessEvents(this IEnumerable<string> jsonEvents)
    {
        return Deserialize().ToArray();

        IEnumerable<ProcessEvent> Deserialize()
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
}
