// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Events;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;

/// <summary>
/// Class for storing event handler and event args for function events.
/// </summary>
/// <typeparam name="TEventArgs"></typeparam>
internal sealed class EventHandlerWrapper<TEventArgs> where TEventArgs : SKEventArgs
{
    /// <summary>
    /// Initializes a new instance of the <see cref="EventHandlerWrapper{TEventArgs}"/> class.
    /// </summary>
    /// <param name="eventHandler">Event handler.</param>
    public EventHandlerWrapper(EventHandler<TEventArgs>? eventHandler)
    {
        this.Handler = eventHandler!;
    }

    /// <summary>
    /// Gets or sets the event args.
    /// </summary>
    public TEventArgs? EventArgs { get; internal set; }

    /// <summary>
    /// Gets the event handler.
    /// </summary>
    internal EventHandler<TEventArgs>? Handler { get; }
}
