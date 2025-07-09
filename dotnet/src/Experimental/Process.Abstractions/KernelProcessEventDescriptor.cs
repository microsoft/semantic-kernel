// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a descriptor for a kernel process event, including its name and associated type.
/// It allows ensuring that events are uniquely defined before runtime and also determines the type of data that the event carries.
/// </summary>
/// <remarks>This class provides metadata about a kernel process event, including its name and the type of data it
/// carries. It is commonly used to define and identify events in a kernel process event system.</remarks>
/// <typeparam name="T">The type of the event data associated with the kernel process event data.</typeparam>
public class KernelProcessEventDescriptor<T>
{
    /// <summary>
    /// Name of the event emitted by the Process Step.
    /// </summary>
    public string EventName { get; }
    /// <summary>
    /// Type of the event data associated with the event.
    /// </summary>
    public Type EventType { get; }

    /// <summary>
    /// Constructor for the KernelProcessEventDescriptor class.
    /// </summary>
    /// <param name="eventName">The name of the event emitted by the Process Step.</param>
    /// <exception cref="ArgumentException">Thrown when the event name is null or empty.</exception>
    public KernelProcessEventDescriptor(string eventName)
    {
        if (string.IsNullOrWhiteSpace(eventName))
        {
            throw new ArgumentException("Event name cannot be null or empty.", nameof(eventName));
        }

        this.EventName = eventName;
        this.EventType = typeof(T);
    }
}
