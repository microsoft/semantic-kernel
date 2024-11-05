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
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="processMessage"></param>
    /// <returns></returns>
    public static string ToJson(this ProcessMessage processMessage)
    {
        Dictionary<string, string?> typeMap = processMessage.Values.ToDictionary(kvp => kvp.Key, kvp => TypeInfo.GetAssemblyQualifiedType(kvp.Value));
        MessageContainer containedMessage = new(TypeInfo.GetAssemblyQualifiedType(processMessage.TargetEventData), typeMap, processMessage);
        return JsonSerializer.Serialize(containedMessage);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="jsonMessages"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static IEnumerable<ProcessMessage> ToProcessMessages(this IEnumerable<string> jsonMessages)
    {
        foreach (string json in jsonMessages)
        {
            MessageContainer containedMessage =
                JsonSerializer.Deserialize<MessageContainer>(json) ??
                throw new KernelException($"Unable to deserialize {nameof(ProcessMessage)} queue.");

            yield return Process(containedMessage);
        }
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="messageContainer"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
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
