// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// Serializer for <see cref="KernelProcessEvent"/> objects.
/// </summary>
/// <remarks>
/// Includes type info for <see cref="KernelProcessEvent.Data"/>.
/// </remarks>
internal static class KernelProcessEventSerializer
{
    /// <summary>
    /// Serialize <see cref="KernelProcessEvent"/> to JSON with type information.
    /// </summary>
    public static string ToJson(this KernelProcessEvent processEvent)
    {
        EventContainer<KernelProcessEvent> containedEvents = new(TypeInfo.GetAssemblyQualifiedType(processEvent.Data), processEvent);
        return JsonSerializer.Serialize(containedEvents);
    }

    /// <summary>
    /// Deserialize a list of JSON events into a list of <see cref="KernelProcessEvent"/> objects.
    /// </summary>
    /// <exception cref="KernelException">If any event fails deserialization</exception>
    public static IList<KernelProcessEvent> ToKernelProcessEvents(this IEnumerable<string> jsonEvents)
    {
        return Deserialize().ToArray();

        IEnumerable<KernelProcessEvent> Deserialize()
        {
            foreach (string json in jsonEvents)
            {
                yield return json.ToKernelProcessEvent();
            }
        }
    }

    /// <summary>
    /// Deserialize a list of JSON events into a list of <see cref="KernelProcessEvent"/> objects.
    /// </summary>
    /// <exception cref="KernelException">If any event fails deserialization</exception>
    public static KernelProcessEvent ToKernelProcessEvent(this string jsonEvent)
    {
        EventContainer<KernelProcessEvent> eventContainer =
            JsonSerializer.Deserialize<EventContainer<KernelProcessEvent>>(jsonEvent) ??
            throw new KernelException($"Unable to deserialize {nameof(KernelProcessEvent)} queue.");
        return eventContainer.Payload with { Data = TypeInfo.ConvertValue(eventContainer.DataTypeName, eventContainer.Payload.Data) };
    }
}
