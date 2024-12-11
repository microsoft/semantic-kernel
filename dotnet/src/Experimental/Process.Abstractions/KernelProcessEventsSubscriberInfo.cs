// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Interfaces;

namespace Microsoft.SemanticKernel;

public record EventSubscriptionActions
{
    public MethodInfo? LocalRuntimeAction { get; set; }

    public IDaprPubsubEventInfo? DaprRuntimeAction { get; set; }
}

public class KernelProcessEventsSubscriberInfo
{
    // key: process event id, value: actions linked to specific event and should be emitted when event triggered
    private readonly Dictionary<string, EventSubscriptionActions> _eventHandlers = [];

    // key: source id, value: list of full internal event id
    private readonly Dictionary<string, List<string>> _eventsBySourceMap = [];

    // key: full internal event id, value: process event id linked
    private readonly Dictionary<string, string> _stepEventProcessEventMap = [];

    // potentially _processEventSubscriberType, _subscriberServiceProvider, _processEventSubscriber can be converted to a dictionary to support
    // many unique subscriber classes that could be linked to different ServiceProviders
    private Type? _processEventSubscriberType = null;
    private IServiceProvider? _subscriberServiceProvider = null;
    private KernelProcessEventsSubscriber? _processEventSubscriber = null;

    private void InitializeProcessEventSubscriber()
    {
        if (this._processEventSubscriber == null && this._processEventSubscriberType != null)
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
    }

    /// <summary>
    /// Used by LocalRuntime to execute linked actions
    /// </summary>
    /// <param name="eventName"></param>
    /// <param name="data"></param>
    private void InvokeProcessEvent(string eventName, object? data)
    {
        if (this._processEventSubscriberType != null && this._eventHandlers.TryGetValue(eventName, out EventSubscriptionActions? linkedAction) && linkedAction != null)
        {
            this.InitializeProcessEventSubscriber();
            linkedAction.LocalRuntimeAction?.Invoke(this._processEventSubscriber, [data]);
        }
    }

    private void Subscribe(string eventName, MethodInfo method, IDaprPubsubEventInfo daprInfo)
    {
        if (this._eventHandlers.TryGetValue(eventName, out var linkedAction) && linkedAction != null)
        {
            linkedAction.LocalRuntimeAction = method;
            linkedAction.DaprRuntimeAction = daprInfo;
            return;
        }

        throw new InvalidOperationException($"Cannot link method {method.Name} to event {eventName}, must make use of EmitAsProcessEvent first or remove unused event from event subscriber.");
    }

    public KernelProcessEventsSubscriber? GetProcessEventsSubscriberInstance()
    {
        this.InitializeProcessEventSubscriber();
        return this._processEventSubscriber;
    }

    public void LinkStepEventToProcessEvent(string stepEventId, string processEventId, string sourceId)
    {
        this._stepEventProcessEventMap.Add(stepEventId, processEventId);
        if (!this._eventHandlers.ContainsKey(processEventId))
        {
            this._eventHandlers.Add(processEventId, new() { LocalRuntimeAction = null, DaprRuntimeAction = null });
        }

        if (!this._eventsBySourceMap.TryGetValue(sourceId, out List<string>? value))
        {
            value = [];
            this._eventsBySourceMap.Add(sourceId, value);
        }

        value.Add(stepEventId);
    }

    public bool TryGetLinkedProcessEvent(string stepEventId, out string? processEvent)
    {
        return this._stepEventProcessEventMap.TryGetValue(stepEventId, out processEvent);
    }

    public IDictionary<string, IDaprPubsubEventInfo> GetLinkedDaprPublishEventsInfoBySource(string sourceId)
    {
        var daprEventInfo = new Dictionary<string, IDaprPubsubEventInfo>();
        if (this._eventsBySourceMap.TryGetValue(sourceId, out var stepEvents) && stepEvents.Count > 0)
        {
            foreach (var stepEvent in stepEvents)
            {
                if (!string.IsNullOrEmpty(stepEvent) &&
                    this._stepEventProcessEventMap.TryGetValue(stepEvent, out var processEvent) && !string.IsNullOrEmpty(processEvent) &&
                    this._eventHandlers.TryGetValue(processEvent, out var eventAction) &&
                    eventAction != null && eventAction.DaprRuntimeAction != null)
                {
                    // validate dapr pubsub requirements
                    if (string.IsNullOrEmpty(eventAction.DaprRuntimeAction.DaprPubsub))
                    {
                        throw new InvalidOperationException($"Event subscriber for event {eventAction.DaprRuntimeAction.EventName} must have dapr pubsub defined");
                    }
                    if (string.IsNullOrEmpty(eventAction.DaprRuntimeAction.DaprTopic))
                    {
                        throw new InvalidOperationException($"Event subscriber for event {eventAction.DaprRuntimeAction.EventName} must have dapr topic defined");
                    }

                    daprEventInfo.Add(stepEvent, eventAction.DaprRuntimeAction);
                }
            }
        }

        return daprEventInfo;
    }

    /// <summary>
    /// Used in Localruntime only
    /// </summary>
    /// <param name="stepEventId"></param>
    /// <param name="data"></param>
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

                this.Subscribe(attribute.EventName, method, attribute);
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
