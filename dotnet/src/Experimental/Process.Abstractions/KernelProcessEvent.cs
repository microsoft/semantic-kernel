// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

// TODO: May not need this and instead just nee to hide usage of EmitEventAsync with KernelProcessEvent only
public record KernelProcessEventBase
{
    /// <summary>
    /// The unique identifier for the event.
    /// </summary>
    public string Id { get; init; } = string.Empty;

    /// <summary>
    /// An optional data payload associated with the event.
    /// </summary>
    public object? Data { get; init; }
}


/// <summary>
/// A class representing an event that can be emitted from a <see cref="KernelProcessStep"/>. This type is convertible to and from CloudEvents.
/// </summary>
public record KernelProcessEvent : KernelProcessEventBase
{
    /// <summary>
    /// The visibility of the event. Defaults to <see cref="KernelProcessEventVisibility.Internal"/>.
    /// </summary>
    public KernelProcessEventVisibility Visibility { get; set; } = KernelProcessEventVisibility.Internal;

    public KernelProcessEvent()
    {
        // Default constructor initializes with default values
    }

    public KernelProcessEvent(KernelProcessEventBase eventData)
    {
        this.Id = eventData.Id;
        this.Data = eventData.Data;
    }
}

/// <summary>
/// A strongly typed version of <see cref="KernelProcessEvent"/> that allows for a specific type of data payload.
/// </summary>
/// <typeparam name="TData"></typeparam>
public record KernelProcessEvent<TData> : KernelProcessEvent where TData : class
{
    /// <summary>
    /// The data payload associated with the event, strongly typed.
    /// </summary>
    public new TData? Data
    {
        get => (TData?)base.Data;
        init => base.Data = value;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessEvent{TData}"/> class with default values.
    /// </summary>
    public KernelProcessEvent()
    {
        this.Visibility = KernelProcessEventVisibility.Internal;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessEvent{TData}"/> class with the specified id, data, and visibility.
    /// </summary>
    /// <param name="id"></param>
    /// <param name="data"></param>
    /// <param name="visibility"></param>
    public KernelProcessEvent(string id, TData? data, KernelProcessEventVisibility visibility = KernelProcessEventVisibility.Internal)
    {
        this.Id = id;
        this.Data = data;
        this.Visibility = visibility;
    }
}
