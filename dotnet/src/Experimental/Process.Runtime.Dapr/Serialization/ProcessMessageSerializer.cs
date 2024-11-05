// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// %%% COMMENT
/// </summary>
internal static class ProcessMessageSerializer
{
    public static string Write(IEnumerable<ProcessMessage> processMessages)
    {
        MessageContainer[] containedEvents = Prepare(processMessages).ToArray();
        return JsonSerializer.Serialize(containedEvents);
    }

    public static IEnumerable<ProcessMessage> Read(string json)
    {
        MessageContainer[] containedMessages =
            JsonSerializer.Deserialize<MessageContainer[]>(json) ??
            throw new KernelException($"Unable to deserialize {nameof(ProcessMessage)} queue.");

        return Process(containedMessages);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="processMessages"></param>
    /// <returns></returns>
    private static IEnumerable<MessageContainer> Prepare(IEnumerable<ProcessMessage> processMessages)
    {
        foreach (ProcessMessage processMessage in processMessages)
        {
            Dictionary<string, string?> typeMap = processMessage.Values.ToDictionary(kvp => kvp.Key, kvp => TypeInfo.GetAssemblyQualifiedType(kvp.Value));
            yield return new MessageContainer(TypeInfo.GetAssemblyQualifiedType(processMessage.TargetEventData), typeMap, processMessage);
        }
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="messageContainers"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    private static IEnumerable<ProcessMessage> Process(IEnumerable<MessageContainer> messageContainers)
    {
        foreach (MessageContainer messageContainer in messageContainers)
        {
            ProcessMessage processMessage = messageContainer.Message;

            if (processMessage.Values.Count == 0)
            {
                yield return processMessage;
            }

            processMessage =
                processMessage with
                {
                    TargetEventData = TypeInfo.ConvertValue(messageContainer.DataTypeName, processMessage.TargetEventData),
                    Values = messageContainer.ValueTypeNames.ToDictionary(kvp => kvp.Key, kvp => TypeInfo.ConvertValue(kvp.Value, processMessage.Values[kvp.Key]))
                };

            yield return processMessage;
        }
    }
}
