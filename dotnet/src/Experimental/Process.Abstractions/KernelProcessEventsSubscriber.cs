// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Process.Interfaces;

namespace Microsoft.SemanticKernel.Process;

public class KernelProcessEventsSubscriber
{
    public IServiceProvider? ServiceProvider { get; init; }

    protected KernelProcessEventsSubscriber() { }
}

/// <summary>
/// Attribute to set Process related steps to link Process Events to specific functions to execute when the event is emitted outside the Process
/// </summary>
/// <typeparam name="TEvents">Enum that contains all process events that could be subscribed to</typeparam>
public class KernelProcessEventsSubscriber<TEvents> : KernelProcessEventsSubscriber where TEvents : Enum
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessEventsSubscriber{TEvents}"/> class.
    /// </summary>
    public KernelProcessEventsSubscriber() { }

    /// <summary>
    /// Attribute to set Process related steps to link Process Events to specific functions to execute when the event is emitted outside the Process
    /// </summary>
    [AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
    public sealed class ProcessEventSubscriberAttribute : Attribute, IDaprPubsubEventInfo
    {
        private string GetEventName(TEvents eventEnum)
        {
            return Enum.GetName(typeof(TEvents), eventEnum) ?? "";
        }

        /// <summary>
        /// Gets the enum of the event that the function is linked to
        /// </summary>
        public TEvents EventEnum { get; }

        /// <summary>
        /// Gets the string of the event name that the function is linked to
        /// </summary>
        public string EventName { get; }

        #region Dapr Runtime related properties
        /// <summary>
        /// When using Dapr Runtime, pubsub name is required to know where to send the specific Dapr event
        /// </summary>
        public string? DaprPubsub { get; }

        /// <summary>
        /// When using Dapr runtime, If daprTopic provided topic will be used instead of eventName, if not provided default will be eventName
        /// </summary>
        public string? DaprTopic { get; }
        #endregion

        /// <summary>
        /// Initializes the attribute.
        /// </summary>
        /// <param name="eventEnum">Specific Process Event enum</param>
        public ProcessEventSubscriberAttribute(TEvents eventEnum)
        {
            this.EventEnum = eventEnum;
            this.EventName = this.GetEventName(eventEnum);
            // No Dapr related properties specified
            this.DaprPubsub = null;
            this.DaprTopic = null;
        }

        public ProcessEventSubscriberAttribute(TEvents eventEnum, string daprPubSub, string? daprTopic = null)
        {
            this.EventEnum = eventEnum;
            this.EventName = this.GetEventName(eventEnum);
            // Dapr related properties specified
            // If not providing alternate topic name, process event name is used as topic
            this.DaprPubsub = daprPubSub;
            this.DaprTopic = daprTopic ?? this.EventName;
        }
    }
}
