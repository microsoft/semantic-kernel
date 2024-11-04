// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Process.Runtime;

/// <summary>
/// Extension methods for <see cref="ProcessEvent"/> and <see cref="KernelProcessEvent"/>.
/// </summary>
internal static class EventExtensions
{
    /// <summary>
    /// Creates a new <see cref="ProcessEvent"/> from a <see cref="KernelProcessEvent"/>.
    /// </summary>
    /// <param name="kernelProcessEvent">The <see cref="KernelProcessEvent"/></param>
    /// <param name="eventNamespace">The namespace of the event.</param>
    /// <param name="isError">// %%% COMMENT</param>
    public static ProcessEvent ToProcessEvent(this KernelProcessEvent kernelProcessEvent, string eventNamespace, bool isError = false) =>
        new(eventNamespace, kernelProcessEvent.Id)
        {
            Data = kernelProcessEvent.Data,
            Visibility = kernelProcessEvent.Visibility,
            IsError = isError,
        };
}
