// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Process;
/// <summary>
/// Attribute to set Process related steps to link Process Events to specific functions to execute when the event is emitted outside the Process
/// </summary>
/// <typeparam name="TEvents">Enum that contains all process events that could be subscribed to</typeparam>
public abstract class KernelProcessEventsSubscriber<TEvents> where TEvents : Enum
{
    /// <summary>
    /// Attribute to set Process related steps to link Process Events to specific functions to execute when the event is emitted outside the Process
    /// </summary>
    [AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
    public class ProcessEventSubscriberAttribute : Attribute
    {
        /// <summary>
        /// Gets the enum of the event that the function is linked to
        /// </summary>
        public TEvents EventEnum { get; }

        /// <summary>
        /// Gets the string of the event name that the function is linked to
        /// </summary>
        public string EventName { get; }

        /// <summary>
        /// Initializes the attribute.
        /// </summary>
        /// <param name="eventEnum">Specific Process Event enum</param>
        public ProcessEventSubscriberAttribute(TEvents eventEnum)
        {
            this.EventEnum = eventEnum;
            this.EventName = Enum.GetName(typeof(TEvents), eventEnum) ?? "";
        }
    }
}
