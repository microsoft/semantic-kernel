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

    private void InvokeProcessEvent(string eventName, object? data)
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

    private void Subscribe(string eventName, MethodInfo method)
    {
        if (this._eventHandlers.TryGetValue(eventName, out List<MethodInfo>? eventHandlers) && eventHandlers != null)
        {
            eventHandlers.Add(method);
            return;
        }

        throw new InvalidOperationException($"Cannot link method {method.Name} to event {eventName}, must make use of EmitAsProcessEvent first or remove unused event from event subscriber.");
    }

    public void LinkStepEventToProcessEvent(string stepEventId, string processEventId)
    {
        this._stepEventProcessEventMap.Add(stepEventId, processEventId);
        if (!this._eventHandlers.ContainsKey(processEventId))
        {
            this._eventHandlers.Add(processEventId, []);
        }
    }

    public bool TryGetLinkedProcessEvent(string stepEventId, out string? processEvent)
    {
        return this._stepEventProcessEventMap.TryGetValue(stepEventId, out processEvent);
    }

    public void TryInvokeProcessEventFromStepMessage(string stepEventId, object? data)
    {
        if (this.TryGetLinkedProcessEvent(stepEventId, out string? processEvent) && !string.IsNullOrEmpty(processEvent))
        {
            this.InvokeProcessEvent(processEvent!, data);
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
        if (this._processEventSubscriberType != null)
        {
            throw new InvalidOperationException("Already linked process to another event subscriber class");
        }

        var methods = typeof(TEventListeners).GetMethods(BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.DeclaredOnly);
        if (methods.Length == 0)
        {
            throw new InvalidOperationException($"The Event Listener type {typeof(TEventListeners).Name} has no functions to extract subscribe methods");
        }

        bool annotationsFound = false;
        foreach (var method in methods)
        {
            if (method.GetCustomAttributes(typeof(KernelProcessEventsSubscriber<>.ProcessEventSubscriberAttribute), false).FirstOrDefault() is KernelProcessEventsSubscriber<TEvents>.ProcessEventSubscriberAttribute attribute)
            {
                if (attribute.EventEnum.GetType() != typeof(TEvents))
                {
                    throw new InvalidOperationException($"The event type {attribute.EventEnum.GetType().Name} does not match the expected type {typeof(TEvents).Name}");
                }

                this.Subscribe(attribute.EventName, method);
                annotationsFound = true;
            }
        }

        if (!annotationsFound)
        {
            throw new InvalidOperationException($"The Event Listener type {typeof(TEventListeners).Name} has functions with no ProcessEventSubscriber Annotations");
        }

        this._subscriberServiceProvider = serviceProvider;
        this._processEventSubscriberType = typeof(TEventListeners);
    }

    public IEnumerable<string> GetLinkedStepIdsToProcessEventName(string processEventId)
    {
        return this._stepEventProcessEventMap
            .Where(kv => kv.Value == processEventId)
            .Select(kv => kv.Key);
    }

    public KernelProcessEventsSubscriberInfo() { }
}
