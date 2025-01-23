// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Process Step. Derive from this class to create a new Step for a Process.
/// </summary>
public abstract class KernelProcessProxyStep<TProcessEvents> : KernelProcessStep<KernelProxyStepState> where TProcessEvents : Enum
{
    internal static class ProxyAttributesBase
    {
        public static string GetEventName(TProcessEvents eventEnum)
        {
            return Enum.GetName(typeof(TProcessEvents), eventEnum) ?? "";
        }
    }

    [AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
    public sealed class KernelProcessExternalEventProxyAttribute : Attribute
    {
        /// <summary>
        /// Gets the string of the event name that the function is linked to
        /// </summary>
        public string ExternalProcessEventName { get; }

        public KernelProcessExternalEventProxyAttribute(string externalProcessEventName)
        {
            this.ExternalProcessEventName = externalProcessEventName;
        }
    }

    [AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
    public sealed class KernelProcessEventProxyAttribute : Attribute
    {
        /// <summary>
        /// Gets the enum of the event that the function is linked to
        /// </summary>
        public TProcessEvents ProcessEventEnum { get; }

        /// <summary>
        /// Gets the string of the event name that the function is linked to
        /// </summary>
        public string ProcessEventName { get; }

        public KernelProcessEventProxyAttribute(TProcessEvents processEventEnum)
        {
            this.ProcessEventEnum = processEventEnum;
            this.ProcessEventName = ProxyAttributesBase.GetEventName(processEventEnum);
        }
    }

    [AttributeUsage(AttributeTargets.Parameter, AllowMultiple = false)]
    public sealed class KernelProcessEventProxyParameterAttribute : Attribute
    {
        /// <summary>
        /// Gets the enum of the event that the function is linked to
        /// </summary>
        public TProcessEvents ProcessEventEnum { get; }

        /// <summary>
        /// Gets the string of the event name that the function is linked to
        /// </summary>
        public string ProcessEventName { get; }

        public KernelProcessEventProxyParameterAttribute(TProcessEvents processEventEnum)
        {
            this.ProcessEventEnum = processEventEnum;
            this.ProcessEventName = ProxyAttributesBase.GetEventName(processEventEnum);
        }
    }

    [AttributeUsage(AttributeTargets.Parameter, AllowMultiple = false)]
    public sealed class KernelProcessExternalEventProxyParameterAttribute : Attribute
    {
        /// <summary>
        /// Gets the string of the event name that the function is linked to
        /// </summary>
        public string ExternalProcessEventName { get; }

        public KernelProcessExternalEventProxyParameterAttribute(string externalProcessEventName)
        {
            this.ExternalProcessEventName = externalProcessEventName;
        }
    }

    internal KernelProxyStepState? _state;

    public abstract Task InitializeServerConnection();

    /// <inheritdoc/>
    public sealed override async ValueTask ActivateAsync(KernelProcessStepState<KernelProxyStepState> state)
    {
        this._state = state.State;
        await this.InitializeServerConnection().ConfigureAwait(false);
    }

    public string GetProcessEventName(TProcessEvents eventEnum)
    {
        return Enum.GetName(typeof(TProcessEvents), eventEnum) ?? "";
    }

    public ValueTask EmitEventAsync(KernelProcessStepContext context, TProcessEvents eventId, object? data = null, KernelProcessEventVisibility visibility = KernelProcessEventVisibility.Internal)
    {
        return context.EmitEventAsync(this.GetProcessEventName(eventId), data, visibility);
    }
}

// This may not be necessary, potentially this can be setup outside of the step and just used from Service Provider
public class KernelProxyStepState
{
    public string ServerUrl { get; set; }
    /// <summary>
    /// key: external event name, value: process event id name
    /// </summary>
    public Dictionary<string, string> InputEventsMap { get; set; }
    public Dictionary<string, string> OutputEventsMap { get; set; }
}
