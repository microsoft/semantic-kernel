// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builder class for defining conditions to listen for in a process.
/// </summary>
public sealed class ListenForBuilder
{
    private readonly ProcessBuilder _processBuilder;
    private ListenForTargetBuilder? _targetBuilder;

    /// <summary>
    /// Initializes a new instance of the <see cref="ListenForBuilder"/> class.
    /// </summary>
    /// <param name="processBuilder">The process builder.</param>
    public ListenForBuilder(ProcessBuilder processBuilder)
    {
        this._processBuilder = processBuilder;
    }

    /// <summary>
    /// Listens for an input event.
    /// </summary>
    /// <param name="eventName"></param>
    /// <param name="condition"></param>
    /// <returns></returns>
    internal ListenForTargetBuilder InputEvent(string eventName, KernelProcessEdgeCondition? condition = null)
    {
        this._targetBuilder = new ListenForTargetBuilder([new(eventName, this._processBuilder, condition)], this._processBuilder);
        return this._targetBuilder;
    }

    /// <summary>
    /// Defines a message to listen for from a specific process step.
    /// </summary>
    /// <param name="messageType">The type of the message.</param>
    /// <param name="from">The process step from which the message originates.</param>
    /// <param name="condition">Condition that must be met for the message to be processed</param>
    /// <returns>A builder for defining the target of the message.</returns>
    public ListenForTargetBuilder Message(string messageType, ProcessStepBuilder from, KernelProcessEdgeCondition? condition = null)
    {
        Verify.NotNullOrWhiteSpace(messageType, nameof(messageType));
        Verify.NotNull(from, nameof(from));

        this._targetBuilder = new ListenForTargetBuilder([new(messageType, from, condition)], this._processBuilder);
        return this._targetBuilder;
    }

    /// <summary>
    /// Defines a message to listen for from a specific process step.
    /// </summary>
    /// <param name="from">The process step from which the message originates.</param>
    /// <param name="condition">Condition that must be met for the message to be processed</param>
    /// <returns>A builder for defining the target of the message.</returns>
    public ListenForTargetBuilder OnResult(ProcessStepBuilder from, KernelProcessEdgeCondition? condition = null)
    {
        Verify.NotNull(from, nameof(from));

        this._targetBuilder = new ListenForTargetBuilder([new("Invoke.OnResult", from, condition)], this._processBuilder);
        return this._targetBuilder;
    }

    /// <summary>
    /// Defines a condition to listen for all of the specified message sources.
    /// </summary>
    /// <param name="messageSources">The list of message sources.</param>
    /// <returns>A builder for defining the target of the messages.</returns>
    public ListenForTargetBuilder AllOf(List<MessageSourceBuilder> messageSources)
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));

        // verify mapped message sources output events do exist
        foreach (var source in messageSources)
        {
            var messageSourceType = source.GetType();
            Type? eventTypeData = null;
            if (messageSourceType.IsGenericType && messageSourceType.GetGenericTypeDefinition() == typeof(TypedMessageSourceBuilder<>))
            {
                eventTypeData = messageSourceType.GenericTypeArguments.FirstOrDefault();
            }

            if (source.Source is ProcessBuilder sourceProcessBuilder)
            {
                sourceProcessBuilder.AddInputEventToProcess(source.MessageType, eventTypeData);
            }
            else
            {
                if (!source.Source.OutputStepEvents.ContainsKey(source.MessageType))
                {
                    throw new InvalidOperationException($"Output Event {source.MessageType} is not emitted by {source.Source.StepId}");
                }
            }
        }

        var edgeGroup = new KernelProcessEdgeGroupBuilder(this.GetGroupId(messageSources), messageSources);
        this._targetBuilder = new ListenForTargetBuilder(messageSources, this._processBuilder, edgeGroup: edgeGroup);
        return this._targetBuilder;
    }

    private string GetGroupId(List<MessageSourceBuilder> messageSources)
    {
        var sortedKeys = messageSources
            .Select(source => $"{source.Source.StepId}.{source.MessageType}")
            .OrderBy(id => id, StringComparer.OrdinalIgnoreCase)
            .ToList();

        return GenerateHash(sortedKeys);
    }

    /// <summary>
    /// Produces a base-64 encoded hash for a set of input strings.
    /// </summary>
    /// <param name="keys">A set of input strings</param>
    /// <returns>A base-64 encoded hash</returns>
    private static string GenerateHash(IEnumerable<string> keys)
    {
        byte[] buffer = Encoding.UTF8.GetBytes(string.Join(":", keys));

#if NET
        Span<byte> hash = stackalloc byte[32];
        SHA256.HashData(buffer, hash);
#else
        using SHA256 shaProvider = SHA256.Create();
        byte[] hash = shaProvider.ComputeHash(buffer);
#endif

        return Convert.ToBase64String(hash);
    }
}
