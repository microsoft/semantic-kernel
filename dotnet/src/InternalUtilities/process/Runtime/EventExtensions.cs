// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Process.Runtime;

/// <summary>
/// Extension methods for <see cref="ProcessEvent"/> and <see cref="KernelProcessEvent"/>.
/// </summary>
internal static class EventExtensions
{
    /// <summary>
    /// Retrieve the <see cref="KernelProcessEvent{TData}.Data"/> value if event is generic, otherwise return null.
    /// </summary>
    public static object? GetData(this KernelProcessEvent kernelProcessEvent)
    {
        Type processType = kernelProcessEvent.GetType();
        if (!processType.IsGenericType)
        {
            return null;
        }

        // NOTE: Type parameter for name resolution is of no consequence here.
        return processType.GetProperty(nameof(KernelProcessEvent<object>.Data))!.GetValue(kernelProcessEvent);
    }

    /// <summary>
    /// Retrieve the <see cref="ProcessEvent{TData}.Data"/> value if event is generic, otherwise return null.
    /// </summary>
    public static object? GetData(this ProcessEvent processEvent)
    {
        Type processType = processEvent.GetType();
        if (!processType.IsGenericType)
        {
            return null;
        }

        // NOTE: Type parameter for name resolution is of no consequence here.
        return processType.GetProperty(nameof(ProcessEvent<object>.Data))!.GetValue(processEvent);
    }

    /// <summary>
    /// Creates a new <see cref="ProcessEvent{TData}"/> from a <see cref="KernelProcessEvent"/>.
    /// </summary>
    /// <param name="kernelProcessEvent">The <see cref="KernelProcessEvent"/></param>
    /// <param name="eventNamespace">The namespace of the event.</param>
    /// <param name="logger">A logger for capturing failure diagnostic</param>
    public static ProcessEvent ToProcessEvent(this KernelProcessEvent kernelProcessEvent, string eventNamespace, ILogger? logger = null) =>
        EventFactory.CreateProcessEvent(eventNamespace, kernelProcessEvent.Id, kernelProcessEvent.GetData(), kernelProcessEvent.Visibility, logger);

    /// <summary>
    /// Creates a new <see cref="ProcessEvent{TData}"/> from a <see cref="KernelProcessEvent"/>.
    /// </summary>
    /// <param name="kernelProcessEvent">The <see cref="KernelProcessEvent"/></param>
    /// <param name="Namespace">The namespace of the event.</param>
    /// <param name="isError">Indicates the event represents a runtime error / exception raised internally by the framework.</param>
    public static ProcessEvent<TData> ToProcessEvent<TData>(this KernelProcessEvent<TData> kernelProcessEvent, string Namespace, bool isError = false) =>
        new(Namespace, kernelProcessEvent.Id)
        {
            Data = kernelProcessEvent.Data,
            Visibility = kernelProcessEvent.Visibility,
            IsError = isError,
        };
}
