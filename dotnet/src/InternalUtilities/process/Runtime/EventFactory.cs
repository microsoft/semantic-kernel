// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel.Process.Runtime;

/// <summary>
/// A factory class for creating <see cref="ProcessEvent"/> and <see cref="KernelProcessEvent"/> instances.
/// </summary>
internal static class EventFactory
{
    /// <summary>
    /// Creates a new <see cref="KernelProcessEvent"/> instance.
    /// </summary>
    /// <param name="id">The source Id of the event.</param>
    /// <param name="data">A data object.</param>
    /// <param name="logger">A logger for capturing failure diagnostic</param>
    /// <returns>An instance of <see cref="KernelProcessEvent"/></returns>
    internal static KernelProcessEvent CreateKernelProcessEvent(string id, object? data, ILogger? logger = null)
    {
        if (data is null)
        {
            return new KernelProcessEvent { Id = id };
        }

        Type dataType = data.GetType();
        Type eventType = typeof(KernelProcessEvent<>).MakeGenericType(dataType);
        KernelProcessEvent processEvent =
            (KernelProcessEvent?)Activator.CreateInstance(eventType) ??
            throw new KernelException($"Failed to instantiate {nameof(KernelProcessEvent)} with data of type: {dataType.Name} [{id}].").Log(logger);

        AssignProperty(eventType, processEvent, nameof(KernelProcessEvent.Id), id);
        // NOTE: Type parameter for name resolution is of no consequence here.
        AssignProperty(eventType, processEvent, nameof(KernelProcessEvent<object>.Data), data);

        return processEvent;
    }

    /// <summary>
    /// Creates a new <see cref="ProcessEvent"/> instance.
    /// </summary>
    /// <param name="eventNamespace">The namespace of the event.</param>
    /// <param name="sourceId">The source Id of the event.</param>
    /// <param name="data">A data object.</param>
    /// <param name="visibility">The visibility of the event.</param>
    /// <param name="logger">A logger for capturing failures</param>
    /// <returns>An instance of <see cref="ProcessEvent"/></returns>
    internal static ProcessEvent CreateProcessEvent(string eventNamespace, string sourceId, object? data, KernelProcessEventVisibility visibility = KernelProcessEventVisibility.Internal, ILogger? logger = null)
    {
        if (data is null)
        {
            return new ProcessEvent(eventNamespace, sourceId)
            {
                Visibility = visibility
            };
        }

        Type dataType = data.GetType();
        Type eventType = typeof(ProcessEvent<>).MakeGenericType(dataType);
        ProcessEvent processEvent =
            (ProcessEvent?)Activator.CreateInstance(eventType, eventNamespace, sourceId) ??
            throw new KernelException($"Failed to instantiate {nameof(ProcessEvent)} with data of type: {dataType.Name} [{sourceId}].").Log(logger);

        // NOTE: Type parameter for name resolution is of no consequence here.
        AssignProperty(eventType, processEvent, nameof(ProcessEvent<object>.Data), data);
        AssignProperty(eventType, processEvent, nameof(ProcessEvent.Visibility), visibility);

        return processEvent;
    }

    private static void AssignProperty(Type type, object instance, string propertyName, object value)
    {
        type.GetProperty(propertyName)?.SetValue(instance, value);
    }
}
