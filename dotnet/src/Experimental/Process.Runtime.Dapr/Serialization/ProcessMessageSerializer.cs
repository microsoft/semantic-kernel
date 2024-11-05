// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// Serializer for <see cref="ProcessMessage"/> objects.
/// </summary>
/// <remarks>
/// Includes type info for <see cref="ProcessMessage.TargetEventData"/> and <see cref="ProcessMessage.Values"/>.
/// </remarks>
internal static class ProcessMessageSerializer
{
    /// <summary>
    /// Serialize <see cref="ProcessMessage"/> to JSON with type information.
    /// </summary>
    public static string ToJson(this ProcessMessage processMessage)
    {
        Dictionary<string, string?> typeMap = processMessage.Values.ToDictionary(kvp => kvp.Key, kvp => TypeInfo.GetAssemblyQualifiedType(kvp.Value));
        MessageContainer containedMessage = new(TypeInfo.GetAssemblyQualifiedType(processMessage.TargetEventData), typeMap, processMessage);
        return JsonSerializer.Serialize(containedMessage);
    }

    /// <summary>
    /// Deserialize a list of JSON messages into a list of <see cref="ProcessMessage"/> objects.
    /// </summary>
    /// <exception cref="KernelException">If any message fails deserialization</exception>
    public static IList<ProcessMessage> ToProcessMessages(this IEnumerable<string> jsonMessages)
    {
        return Deserialize().ToArray();

        IEnumerable<ProcessMessage> Deserialize()
        {
            foreach (string json in jsonMessages)
            {
                MessageContainer containedMessage =
                    JsonSerializer.Deserialize<MessageContainer>(json) ??
                    throw new KernelException($"Unable to deserialize {nameof(ProcessMessage)} queue.");

                yield return Process(containedMessage);
            }
        }
    }

    private static ProcessMessage Process(MessageContainer messageContainer)
    {
        ProcessMessage processMessage = messageContainer.Message;

        if (processMessage.Values.Count == 0)
        {
            return processMessage;
        }

        processMessage =
            processMessage with
            {
                TargetEventData = TypeInfo.ConvertValue(messageContainer.DataTypeName, processMessage.TargetEventData),
                Values = messageContainer.ValueTypeNames.ToDictionary(kvp => kvp.Key, kvp => TypeInfo.ConvertValue(kvp.Value, processMessage.Values[kvp.Key]))
            };

        return processMessage;
    }
}
