// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Process;
/// <summary>
/// Provides a stage by stage way of building a <see cref="ProcessBuilder"/><br/>
/// Allows the mapping of each Process multiple <see cref="KernelProcessStep"/> with SK Process Events for
/// provided an abstraction layer that makes it easier to generate a working ProcessBuilder.
/// </summary>
/// <typeparam name="TEvent">Enum containing the events to be used internally and externally between multiple <see cref="KernelProcessStep"/> </typeparam>
public class ProcessEventStepMapper<TEvent> where TEvent : Enum
{
    private readonly ProcessBuilder _process;

    private readonly Dictionary<TEvent, string> _eventsNamesMap;

    private readonly Dictionary<TEvent, StepDetails<TEvent>> _eventStepIdMap;
    private readonly Dictionary<string, ProcessStepBuilder> _stepBuilderMap;
    private readonly Dictionary<TEvent, bool> _linkedEvents;

    private readonly HashSet<TEvent> _externalInputEvents;
    private readonly HashSet<TEvent> _externalOutputEvents;

    private string GetEventName(TEvent eventType)
    {
        return this._eventsNamesMap[eventType];
    }

    /// <summary>
    /// Returns a validated <see cref="ProcessBuilder"/> that has all process events linked
    /// </summary>
    /// <returns></returns>
    /// <exception cref="InvalidOperationException"></exception>
    public ProcessBuilder GetProcess()
    {
        // TODO: Add additional validation to try to ensure the process created is valid
        if (this._externalInputEvents.Count == 0)
        {
            throw new InvalidOperationException("SK Processes must have at least 1 event linked as an external input event");
        }

        if (this._externalOutputEvents.Count == 0)
        {
            throw new InvalidOperationException("SK Processes must have at least 1 event linked as an external output event");
        }

        var unlinkedEvents = this._linkedEvents.Where(kvp => !kvp.Value).ToList();
        if (unlinkedEvents != null && unlinkedEvents.Count != 0)
        {
            var unlinkedEventNames = string.Join(",", unlinkedEvents.Select(kvp => this.GetEventName(kvp.Key)));
            throw new InvalidOperationException($"Found events without links: {unlinkedEventNames}. Make sure to link all events before making use of process");
        }

        return this._process;
    }

    protected void AddStepFromType<TStep>(Dictionary<TEvent, TargetDetails<TEvent>> functionEventMap, string? stepName = null) where TStep : KernelProcessStep
    {
        var stepBuilder = this._process.AddStepFromType<TStep>(stepName);
        var stepId = stepBuilder.Id!;

        this._stepBuilderMap[stepId] = stepBuilder;
        // Registering event with function
        foreach (var functionEventPair in functionEventMap)
        {
            this._eventStepIdMap[functionEventPair.Key] = new()
            {
                StepId = stepId,
                FunctionName = functionEventPair.Value.FunctionName,
                ParameterName = functionEventPair.Value.ParameterName,
                StepOutputEvents = functionEventPair.Value.StepOutputEvents,
            };

            // If output events defined also adding it to map for easier access
            foreach (var outputEvent in functionEventPair.Value.StepOutputEvents)
            {
                this._eventStepIdMap[outputEvent.Key] = new()
                {
                    StepId = stepId,
                    FunctionName = functionEventPair.Value.FunctionName,
                    ParameterName = functionEventPair.Value.ParameterName,
                    StepOutputEvents = { { outputEvent.Key, outputEvent.Value } }
                };
            }
        }
    }

    /// <summary>
    /// Links SK Process previously defined events
    /// </summary>
    /// <exception cref="InvalidOperationException"></exception>
    protected void LinkInternalEvents(TEvent sourceInputEvent, TEvent targetOutputEvent)
    {
        if (
            this._eventStepIdMap.TryGetValue(sourceInputEvent, out var sourceStepDetails) &&
            this._stepBuilderMap.TryGetValue(sourceStepDetails.StepId, out var sourceStepBuilder) &&
            this._eventStepIdMap.TryGetValue(targetOutputEvent, out var targetStepDetails) &&
            this._stepBuilderMap.TryGetValue(targetStepDetails.StepId, out var targetStepBuilder))
        {
            var sourceEventName = this.GetEventName(sourceInputEvent);
            var outputEventName = this.GetEventName(targetOutputEvent);

            if (sourceStepDetails.StepOutputEvents.Count > 1)
            {
                throw new InvalidOperationException($"Output event {outputEventName} is not linked to step {sourceStepBuilder.Name}");
            }

            var sourceOutputEvent = sourceStepDetails.StepOutputEvents.First().Key;

            if (sourceStepDetails.StepOutputEvents.TryGetValue(sourceOutputEvent!, out var internalStepOutputEvent))
            {
                sourceStepBuilder
                    .OnEvent(internalStepOutputEvent)
                    .SendEventTo(new ProcessFunctionTargetBuilder(targetStepBuilder, functionName: targetStepDetails.FunctionName, parameterName: targetStepDetails.ParameterName));

                this._linkedEvents[sourceInputEvent] = true;
                this._linkedEvents[targetOutputEvent] = true;
                this._linkedEvents[sourceOutputEvent!] = true;
            }
            else
            {
                throw new InvalidOperationException($"Event {this.GetEventName(sourceOutputEvent!)} not linked to event source {this.GetEventName(sourceInputEvent)}");
            }
        }
        else
        {
            throw new InvalidOperationException("Events must be linked to an event first with AddStepFromType or AddStepFromType first before linking");
        }
    }
    /// <summary>
    /// Links specific events as triggers of the SK Process.<br/>
    ///
    /// At least 1 event should be linked as an external input to be able to trigger this SK Process
    /// </summary>
    /// <param name="externalSourceEvent">Event that could be send externally to trigger the process</param>
    /// <param name="targetSourceEvent">Event previously assigned to a step/process that will get triggered on receiving the externalSourceEvent </param>
    /// <exception cref="InvalidOperationException"></exception>
    protected void LinkExternalInputEvent(TEvent externalSourceEvent, TEvent targetSourceEvent)
    {
        if (
            this._eventStepIdMap.TryGetValue(targetSourceEvent, out var targetStepDetails) &&
            this._stepBuilderMap.TryGetValue(targetStepDetails.StepId, out var targetStepBuilder))
        {
            this._process
                .OnExternalEvent(this.GetEventName(externalSourceEvent))
                .SendEventTo(new ProcessFunctionTargetBuilder(targetStepBuilder, functionName: targetStepDetails.FunctionName, parameterName: targetStepDetails.ParameterName));

            this._linkedEvents[externalSourceEvent] = true;
            this._linkedEvents[targetSourceEvent] = true;

            this._externalInputEvents.Add(externalSourceEvent);
        }
        else
        {
            throw new InvalidOperationException("Events must be linked to an event first with AddStepFromType or AddStepFromType first before linking");
        }
    }

    /// <summary>
    /// Links specific events as output evetns that could potentially be subscribed to by other steps or processes in a parent process
    /// </summary>
    /// <param name="sourceInputEvent"></param>
    /// <param name="sourceOutputExternalEvent"></param>
    /// <exception cref="InvalidOperationException"></exception>
    protected void LinkExternalOutputEvent(TEvent sourceInputEvent, TEvent sourceOutputExternalEvent)
    {
        if (
            this._eventStepIdMap.TryGetValue(sourceInputEvent, out var sourceStepDetails) &&
            this._stepBuilderMap.TryGetValue(sourceStepDetails.StepId, out var sourceStepBuilder))
        {
            sourceStepBuilder
                .OnEvent(this.GetEventName(sourceOutputExternalEvent))
                // TODO => abstract StopProcess to replace with broadcast externally or stopProcess
                .StopProcess();

            this._linkedEvents[sourceInputEvent] = true;
            this._linkedEvents[sourceOutputExternalEvent] = true;

            this._externalOutputEvents.Add(sourceOutputExternalEvent);
        }
        else
        {
            throw new InvalidOperationException("Events must be linked to an event first with AddStepFromType or AddStepFromType first before linking");
        }
    }

    /// <summary>
    /// Returns a list of the process events assigned as external input triggers on the creation of the SK Process
    /// </summary>
    /// <returns>List of event names</returns>
    public List<string> GetExternalInputTriggerEvents()
    {
        return this._externalInputEvents.Select(e => this.GetEventName(e)).ToList();
    }

    /// <summary>
    /// Returns a list of the process events assigned as external output events on the creation of the SK Process
    /// </summary>
    /// <returns>List of event names</returns>
    public List<string> GetExternalOutputEvents()
    {
        return this._externalOutputEvents.Select(e => this.GetEventName(e)).ToList();
    }

    /// <summary>
    /// <see cref="ProcessEventStepMapper{TEvent}"/> constructor that initializes the events to be used in the SK Process
    /// </summary>
    /// <param name="processName">name to be assigned to the SK Process</param>
    public ProcessEventStepMapper(string processName)
    {
        this._process = new ProcessBuilder(processName);

        this._eventsNamesMap = Enum.GetValues(typeof(TEvent)).Cast<TEvent>().ToDictionary(e => e, e => e.ToString());
        this._linkedEvents = Enum.GetValues(typeof(TEvent)).Cast<TEvent>().ToDictionary(e => e, e => false);

        this._eventStepIdMap = [];
        this._stepBuilderMap = [];

        this._externalInputEvents = [];
        this._externalOutputEvents = [];
    }
}

/// <summary>
/// Details of the <see cref="KernelProcessStep" /> to be linked to a SK process event
/// like StepId, FunctionName, ParameterName and StepOutputEvents
/// </summary>
/// <typeparam name="TEvent">Enum containing the events to be used internally and externally between multiple <see cref="KernelProcessStep"/> </typeparam>
public record TargetDetails<TEvent> where TEvent : Enum
{
    /// <summary>
    /// Plugin Function name that is invoked on the specific step/plugin. <br/>
    /// Should be specified if the SK Plugin/Step has multiple public functions.
    /// </summary>
    public string? FunctionName { get; set; } = null;
    /// <summary>
    /// Name of the parameter of the SK function to be invoked. <br/>
    /// Should be specified if the SK Plugin/Step function has multiple parameters
    /// </summary>
    public string? ParameterName { get; set; } = null;
    /// <summary>
    /// Map of the Process Event and the Step Event.<br/>
    /// StepOutputEvents should be defined if the specific SK Step Function outputs more that one SK Process Event
    /// </summary>
    public Dictionary<TEvent, string> StepOutputEvents { get; set; } = [];
}

/// <summary>
/// Details of the <see cref="KernelProcessStep" /> to be linked to a SK process event
/// like StepId and <see cref="TargetDetails{TEvent}"/> properties
/// </summary>
/// <typeparam name="TEvent">Enum containing the events to be used internally and externally between multiple <see cref="KernelProcessStep"/> </typeparam>
public record StepDetails<TEvent> : TargetDetails<TEvent> where TEvent : Enum
{
    /// <summary>
    /// Unique identifier of the built <see cref="ProcessStepBuilder"/>
    /// </summary>
    public string StepId { get; set; } = string.Empty;
}
