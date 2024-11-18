// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Microsoft.SemanticKernel.Process;

namespace Microsoft.SemanticKernel;

public class KernelProcessEventsSubscriberInfo
{
    private readonly Dictionary<string, List<MethodInfo>> _eventHandlers = [];
    private readonly Dictionary<string, string> _stepEventProcessEventMap = [];

    // potentially _processEventSubscriberType, _subscriberServiceProvider, _processEventSubscriber can be converted to a dictionary to support
    // many unique subscriber classes that could be linked to different ServiceProviders
    private Type? _processEventSubscriberType = null;
    private IServiceProvider? _subscriberServiceProvider = null;
    private KernelProcessEventsSubscriber? _processEventSubscriber = null;

    protected void Subscribe(string eventName, MethodInfo method)
    {
        if (this._eventHandlers.TryGetValue(eventName, out List<MethodInfo>? eventHandlers) && eventHandlers != null)
        {
            eventHandlers.Add(method);
        }
    }

    public void LinkStepEventToProcessEvent(string stepEventId, string processEventId)
    {
        this._stepEventProcessEventMap.Add(stepEventId, processEventId);
        if (!this._eventHandlers.ContainsKey(processEventId))
        {
            this._eventHandlers.Add(processEventId, []);
        }
    }

    public void TryInvokeProcessEventFromStepMessage(string stepEventId, object? data)
    {
        if (this._stepEventProcessEventMap.TryGetValue(stepEventId, out var processEvent) && processEvent != null)
        {
            this.InvokeProcessEvent(processEvent, data);
        }
    }

    public void InvokeProcessEvent(string eventName, object? data)
    {
        if (this._processEventSubscriberType != null && this._eventHandlers.TryGetValue(eventName, out List<MethodInfo>? linkedMethods) && linkedMethods != null)
        {
            if (this._processEventSubscriber == null)
            {
                try
                {
                    this._processEventSubscriber = (KernelProcessEventsSubscriber?)Activator.CreateInstance(this._processEventSubscriberType, []);
                    this._processEventSubscriberType.GetProperty(nameof(KernelProcessEventsSubscriber.ServiceProvider))?.SetValue(this._processEventSubscriber, this._subscriberServiceProvider);
                }
                catch (Exception)
                {
                    throw new KernelException($"Could not create an instance of {this._processEventSubscriberType.Name} to be used in KernelProcessSubscriberInfo");
                }
            }

            foreach (var method in linkedMethods)
            {
                method.Invoke(this._processEventSubscriber, [data]);
            }
        }
    }

    /// <summary>
    /// Extracts the event properties and function details of the functions with the annotator
    /// <see cref="KernelProcessEventsSubscriber{TEvents}.ProcessEventSubscriberAttribute"/>
    /// </summary>
    /// <typeparam name="TEventListeners">Type of the class that make uses of the annotators and contains the functionality to be executed</typeparam>
    /// <typeparam name="TEvents">Enum that contains the process subscribable events</typeparam>
    /// <exception cref="InvalidOperationException"></exception>
    public void SubscribeToEventsFromClass<TEventListeners, TEvents>(IServiceProvider? serviceProvider = null) where TEventListeners : KernelProcessEventsSubscriber<TEvents> where TEvents : Enum
    {
        if (this._subscriberServiceProvider != null)
        {
            throw new KernelException("Already linked process to a specific service provider class");
        }

        var methods = typeof(TEventListeners).GetMethods(BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.DeclaredOnly);
        foreach (var method in methods)
        {
            if (method.GetCustomAttributes(typeof(KernelProcessEventsSubscriber<>.ProcessEventSubscriberAttribute), false).FirstOrDefault() is KernelProcessEventsSubscriber<TEvents>.ProcessEventSubscriberAttribute attribute)
            {
                if (attribute.EventEnum.GetType() != typeof(TEvents))
                {
                    throw new InvalidOperationException($"The event type {attribute.EventEnum.GetType().Name} does not match the expected type {typeof(TEvents).Name}");
                }

                this.Subscribe(attribute.EventName, method);
            }
        }

        this._subscriberServiceProvider = serviceProvider;
        this._processEventSubscriberType = typeof(TEventListeners);
    }

    public KernelProcessEventsSubscriberInfo() { }
}
