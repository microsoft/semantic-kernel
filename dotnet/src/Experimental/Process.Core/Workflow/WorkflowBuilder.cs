// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Process.Internal;
using YamlDotNet.RepresentationModel;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builds a workflow from a YAML definition.
/// </summary>
internal class WorkflowBuilder
{
    private readonly Dictionary<string, ProcessStepBuilder> _stepBuilders = [];
    private readonly Dictionary<string, CloudEvent> _inputEvents = [];
    private string? _yaml;

    /// <summary>
    /// Builds a process from a workflow definition.
    /// </summary>
    /// <param name="workflow">An instance of <see cref="Workflow"/>.</param>
    /// <param name="yaml">Workflow definition in YAML format.</param>
    /// <param name="stepTypes">Collection of preloaded step types.</param>
    public async Task<KernelProcess?> BuildProcessAsync(Workflow workflow, string yaml, Dictionary<string, Type>? stepTypes = null)
    {
        this._yaml = yaml;
        var stepBuilders = new Dictionary<string, ProcessStepBuilder>();

        if (workflow.Nodes is null || workflow.Nodes.Count == 0)
        {
            throw new ArgumentException("Workflow nodes are not specified.");
        }

        if (workflow.Inputs is null)
        {
            throw new ArgumentException("Workflow inputs are not specified.");
        }

        // TODO: Process outputs
        // TODO: Process variables

        ProcessBuilder processBuilder = new(workflow.Id, description: workflow.Description, stateType: typeof(ProcessDefaultState));

        if (workflow.Inputs.Events?.CloudEvents is not null)
        {
            foreach (CloudEvent inputEvent in workflow.Inputs.Events.CloudEvents)
            {
                await this.AddInputEventAsync(inputEvent, processBuilder).ConfigureAwait(false);
            }
        }

        if (workflow.Inputs.Messages is not null)
        {
            await this.AddInputMessagesEventAsync(processBuilder).ConfigureAwait(false);
        }

        // Process the nodes
        foreach (var step in workflow.Nodes)
        {
            await this.AddStepAsync(step, processBuilder, stepTypes).ConfigureAwait(false);
        }

        // Process the orchestration
        if (workflow.Orchestration is not null)
        {
            await this.BuildOrchestrationAsync(workflow.Orchestration, processBuilder).ConfigureAwait(false);
        }

        return processBuilder.Build();
    }

    #region Inputs

    private Task AddInputEventAsync(CloudEvent inputEvent, ProcessBuilder processBuilder)
    {
        this._inputEvents[inputEvent.Type] = inputEvent;
        return Task.CompletedTask;
    }

    private Task AddInputMessagesEventAsync(ProcessBuilder processBuilder)
    {
        string inputMessageEventType = "input_message_received";
        this._inputEvents[inputMessageEventType] = new CloudEvent() { Type = inputMessageEventType };
        return Task.CompletedTask;
    }

    #endregion

    #region Nodes and Steps

    internal async Task AddStepAsync(Node node, ProcessBuilder processBuilder, Dictionary<string, Type>? stepTypes = null)
    {
        Verify.NotNull(node);

        if (node.Type == "dotnet")
        {
            await this.BuildDotNetStepAsync(node, processBuilder, stepTypes).ConfigureAwait(false);
        }
        else if (node.Type == "python")
        {
            await this.BuildPythonStepAsync(node, processBuilder).ConfigureAwait(false);
        }
        else if (node.Type == "declarative")
        {
            await this.BuildDeclarativeStepAsync(node, processBuilder).ConfigureAwait(false);
        }
        else
        {
            throw new ArgumentException($"Unsupported node type: {node.Type}");
        }
    }

    private Task BuildDeclarativeStepAsync(Node node, ProcessBuilder processBuilder)
    {
        Verify.NotNull(node);

        // Check for built-in step types
        if (node.Id.Equals("End", StringComparison.OrdinalIgnoreCase))
        {
            var endBuilder = processBuilder.AddEndStep();
            this._stepBuilders["End"] = endBuilder;
            return Task.CompletedTask;
        }

        AgentDefinition? agentDefinition = node.Agent ?? throw new KernelException("Declarative steps must have an agent defined.");
        var stepBuilder = processBuilder.AddStepFromAgent(agentDefinition, node.Id);
        if (stepBuilder is not ProcessAgentBuilder agentBuilder)
        {
            throw new KernelException($"Failed to build step from agent definition: {node.Id}");
        }

        // ########################### Parsing on_complete and on_error conditions ###########################

        if (node.OnComplete != null)
        {
            if (node.OnComplete.Any(c => c is null || c.OnCondition is null))
            {
                throw new ArgumentException("A complete on_complete condition is required for declarative steps.");
            }

            agentBuilder.OnComplete([.. node.OnComplete.Select(c => c.OnCondition!)]);
        }

        if (node.OnError != null)
        {
            if (node.OnError.Any(c => c is null || c.OnCondition is null))
            {
                throw new ArgumentException("A complete on_complete condition is required for declarative steps.");
            }

            agentBuilder.OnComplete([.. node.OnError.Select(c => c.OnCondition!)]);
        }

        // ########################### Parsing node inputs ###########################

        if (node.Inputs != null)
        {
            var inputMapping = this.ExtractNodeInputs(node.Id);
            //agentBuilder.WithNodeInputs(node.Inputs); TODO: What to do here?
        }

        this._stepBuilders[node.Id] = stepBuilder;
        return Task.CompletedTask;
    }

    private Task BuildPythonStepAsync(Node node, ProcessBuilder processBuilder)
    {
        throw new KernelException("Python nodes are not supported in the dotnet runtime.");
    }

    private Task BuildDotNetStepAsync(Node node, ProcessBuilder processBuilder, Dictionary<string, Type>? stepTypes = null)
    {
        Verify.NotNull(node);

        if (node.Agent is null || string.IsNullOrEmpty(node.Agent.Type))
        {
            throw new ArgumentException($"The agent specified in the Node with id {node.Id} is not fully specified.");
        }

        // For dotnet node type, the agent type specifies the assembly qualified namespace of the class to be executed.
        Type? dotnetAgentType = null;
        try
        {
            if (stepTypes is not null && stepTypes.TryGetValue(node.Agent.Type, out var type) && type is not null)
            {
                dotnetAgentType = type;
            }
            else
            {
                dotnetAgentType = Type.GetType(node.Agent.Type);
            }
        }
        catch (TypeLoadException tle)
        {
            throw new KernelException($"Failed to load the agent for node with id {node.Id}.", tle);
        }

        if (dotnetAgentType == null)
        {
            throw new KernelException("The agent type specified in the node is not found.");
        }

        var stepBuilder = processBuilder.AddStepFromType(dotnetAgentType, id: node.Id);
        this._stepBuilders[node.Id] = stepBuilder;
        return Task.CompletedTask;
    }

    #endregion

    #region Orchestration

    private Task BuildOrchestrationAsync(List<OrchestrationStep> orchestrationSteps, ProcessBuilder processBuilder)
    {
        // If there are no orchestration steps, return
        if (orchestrationSteps.Count == 0)
        {
            return Task.CompletedTask;
        }

        // Process the orchestration steps
        foreach (var step in orchestrationSteps)
        {
            ListenCondition? listenCondition = step.ListenFor;
            if (listenCondition is null)
            {
                throw new ArgumentException("A complete listen_for condition is required for orchestration steps.");
            }

            List<ThenAction>? thenActions = step.Then;
            if (thenActions is null || thenActions.Count == 0)
            {
                throw new ArgumentException("At least one then action is required for orchestration steps.");
            }

            ProcessStepEdgeBuilder? edgeBuilder = null;

            if (listenCondition.AllOf != null && listenCondition.AllOf.Count > 0)
            {
                MessageSourceBuilder GetSourceBuilder(ListenEvent listenEvent)
                {
                    var sourceBuilder = this.FindSourceBuilder(new() { Event = listenEvent.Event, From = listenEvent.From }, processBuilder);
                    return new MessageSourceBuilder
                    (
                        messageType: listenEvent.Event,
                        source: this._stepBuilders[listenEvent.From],
                        null // TODO: Pass through condition.
                    );
                }

                // Handle AllOf condition
                edgeBuilder = processBuilder.ListenFor().AllOf(listenCondition.AllOf.Select(c => GetSourceBuilder(c)).ToList());
            }
            else if (!string.IsNullOrWhiteSpace(listenCondition.Event) && !string.IsNullOrWhiteSpace(listenCondition.From))
            {
                // Find the source of the edge, it could either be a step, or an input event.
                if (this._stepBuilders.TryGetValue(listenCondition.From, out ProcessStepBuilder? sourceStepBuilder))
                {
                    // The source is a step.
                    edgeBuilder = sourceStepBuilder.OnEvent(listenCondition.Event);
                }
                else if (listenCondition.From.Equals("_workflow_", StringComparison.OrdinalIgnoreCase) && this._inputEvents.ContainsKey(listenCondition.Event))
                {
                    // The source is an input event.
                    edgeBuilder = processBuilder.OnInputEvent(listenCondition.Event);
                }
                else
                {
                    throw new ArgumentException($"An orchestration is referencing a node with Id `{listenCondition.From}` that does not exist.");
                }
            }
            else
            {
                throw new ArgumentException("A complete listen_for condition is required for orchestration steps.");
            }

            // Now that we have a validated edge source, we can add the then actions
            foreach (var action in thenActions)
            {
                if (action is null || string.IsNullOrWhiteSpace(action.Node))
                {
                    throw new ArgumentException("A complete then action is required for orchestration steps.");
                }

                if (!this._stepBuilders.TryGetValue(action.Node, out ProcessStepBuilder? destinationStepBuilder))
                {
                    if (action.Node.Equals("End", StringComparison.OrdinalIgnoreCase))
                    {
                        edgeBuilder.StopProcess();
                        continue;
                    }

                    throw new ArgumentException($"An orchestration is referencing a node with Id `{action.Node}` that does not exist.");
                }

                // Add the edge to the node
                edgeBuilder = edgeBuilder.SendEventTo(new ProcessFunctionTargetBuilder(destinationStepBuilder));
            }
        }

        return Task.CompletedTask;
    }

    #endregion

    #region FromProcess

    /// <summary>
    /// Builds a workflow from a kernel process.
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
    public static Task<Workflow> BuildWorkflow(KernelProcess process)
    {
        Verify.NotNull(process);

        Workflow workflow = new()
        {
            Id = process.State.Id ?? throw new KernelException("The process must have an Id set"),
            Description = process.Description,
            FormatVersion = "1.0",
            Name = process.State.Name,
            Nodes = [new Node { Id = "End", Type = "declarative", Version = "1.0", Description = "Terminal state" }],
            Variables = [],
        };

        // Add variables
        foreach (var thread in process.Threads)
        {
            workflow.Variables.Add(thread.Key, new VariableDefinition()
            {
                Type = VariableType.Thread,
            });
        }

        if (process.UserStateType != null)
        {
            // Get all public properties
            PropertyInfo[] properties = process.UserStateType.GetProperties(BindingFlags.Public | BindingFlags.Instance);

            // Loop through each property and output its type
            foreach (PropertyInfo property in properties)
            {
                if (property.PropertyType == typeof(List<ChatMessageContent>))
                {
                    workflow.Variables.Add(property.Name, new VariableDefinition()
                    {
                        Type = VariableType.Messages,
                    });

                    continue;
                }

                var schema = KernelJsonSchemaBuilder.Build(property.PropertyType);
                var schemaJson = JsonSerializer.Serialize(schema.RootElement);

                var deserializer = new DeserializerBuilder()
                .WithNamingConvention(UnderscoredNamingConvention.Instance)
                .IgnoreUnmatchedProperties()
                .Build();

                var yamlSchema = deserializer.Deserialize(schemaJson) ?? throw new KernelException("Failed to deserialize schema.");
                workflow.Variables.Add(property.Name, new VariableDefinition { Type = VariableType.UserDefined, Schema = yamlSchema });
            }
        }

        // Add edges
        var orchestration = new List<OrchestrationStep>();
        foreach (var edge in process.Edges)
        {
            // Get all the input events
            OrchestrationStep orchestrationStep = new()
            {
                ListenFor = new ListenCondition()
                {
                    From = "_workflow_",
                    Event = ResolveEventName(edge.Key)
                },
                Then = [.. edge.Value.Select(e => ThenAction.FromKernelProcessEdge(e, null))]
            };

            orchestration.Add(orchestrationStep);
        }

        var steps = process.Steps;
        foreach (var step in steps)
        {
            workflow.Nodes?.Add(BuildNode(step, orchestration));
        }

        workflow.Orchestration = orchestration;
        return Task.FromResult(workflow);
    }

    private static Node BuildNode(KernelProcessStepInfo step, List<OrchestrationStep> orchestrationSteps)
    {
        Verify.NotNullOrWhiteSpace(step?.State?.Id, nameof(step.State.Id));

        if (step is KernelProcessAgentStep agentStep)
        {
            return BuildAgentNode(agentStep, orchestrationSteps);
        }

        var innerStepTypeString = step.InnerStepType.AssemblyQualifiedName;
        if (string.IsNullOrWhiteSpace(innerStepTypeString))
        {
            throw new InvalidOperationException("Attempt to build a workflow node from step with no Id");
        }

        var node = new Node()
        {
            Id = step.State.Id,
            Type = "dotnet",
            Agent = new AgentDefinition()
            {
                Type = innerStepTypeString,
                Id = step.State.Id
            }
        };

        foreach (var edge in step.Edges)
        {
            OrchestrationStep orchestrationStep = new()
            {
                ListenFor = new ListenCondition()
                {
                    From = step.State.Id,
                    Event = edge.Key,
                    Condition = edge.Value.FirstOrDefault()?.Condition.DeclarativeDefinition
                },
                Then = [.. edge.Value.Select(e =>
                {
                    if (e.OutputTarget is KernelProcessFunctionTarget functionTarget)
                    {
                        return new ThenAction()
                        {
                            Node = functionTarget.StepId switch
                            {
                                ProcessConstants.EndStepName => "End",
                                string s => s
                            }
                        };
                    }

                    throw new KernelException($"The edge target is not a function target: {e.OutputTarget}");
                })]
            };

            orchestrationSteps.Add(orchestrationStep);
        }

        return node;
    }

    private static Node BuildAgentNode(KernelProcessAgentStep agentStep, List<OrchestrationStep> orchestrationSteps)
    {
        Verify.NotNull(agentStep);

        if (agentStep.AgentDefinition is null || string.IsNullOrWhiteSpace(agentStep.State?.Id) || string.IsNullOrWhiteSpace(agentStep.AgentDefinition.Type))
        {
            throw new InvalidOperationException("Attempt to build a workflow node from step with no Id");
        }

        var node = new Node()
        {
            Id = agentStep.State.Id!,
            Type = agentStep.AgentDefinition.Type!,
            Agent = agentStep.AgentDefinition,
            HumanInLoopType = agentStep.HumanInLoopMode,
            OnComplete = ToEventActions(agentStep.Actions?.DeclarativeActions?.OnComplete),
            OnError = ToEventActions(agentStep.Actions?.DeclarativeActions?.OnError),
            Inputs = agentStep.Inputs.ToDictionary((kvp) => kvp.Key, (kvp) =>
            {
                var value = kvp.Value;
                var schema = KernelJsonSchemaBuilder.Build(value);
                var schemaJson = JsonSerializer.Serialize(schema.RootElement);

                var deserializer = new DeserializerBuilder()
                .WithNamingConvention(UnderscoredNamingConvention.Instance)
                .IgnoreUnmatchedProperties()
                .Build();

                var yamlSchema = deserializer.Deserialize(schemaJson);
                if (yamlSchema is null)
                {
                    throw new KernelException("Failed to deserialize schema.");
                }

                return yamlSchema;
            })
        };

        // re-group the edges to account for different conditions
        var conditionGroupedEdges = agentStep.Edges
            .SelectMany(kvp => kvp.Value, (kvp, k) => new { key = kvp.Key, edge = k })
            .GroupBy(e => new { e.key, e.edge.Condition?.DeclarativeDefinition })
            .ToDictionary(g => g.Key, g => g.ToList());

        foreach (var edge in conditionGroupedEdges)
        {
            OrchestrationStep orchestrationStep = new()
            {
                ListenFor = new ListenCondition()
                {
                    From = agentStep.State.Id,
                    Event = ResolveEventName(edge.Key.key),
                    Condition = edge.Key.DeclarativeDefinition
                },
                Then = [.. edge.Value.Select(e => ThenAction.FromKernelProcessEdge(e.edge, defaultThread: agentStep.ThreadName))]
            };

            orchestrationSteps.Add(orchestrationStep);
        }

        return node;
    }

    private static string ResolveEventName(string eventName)
    {
        Verify.NotNullOrWhiteSpace(eventName);

        if (eventName.EndsWith("Invoke.OnResult", StringComparison.Ordinal) || eventName.EndsWith(ProcessConstants.Declarative.OnCompleteEvent, StringComparison.OrdinalIgnoreCase))
        {
            return ProcessConstants.Declarative.OnExitEvent;
        }
        if (eventName.EndsWith(ProcessConstants.Declarative.OnErrorEvent, StringComparison.Ordinal))
        {
            return ProcessConstants.Declarative.OnErrorEvent;
        }
        if (eventName.EndsWith(ProcessConstants.Declarative.OnEnterEvent, StringComparison.Ordinal))
        {
            return ProcessConstants.Declarative.OnEnterEvent;
        }
        if (eventName.EndsWith(ProcessConstants.Declarative.OnExitEvent, StringComparison.Ordinal))
        {
            return ProcessConstants.Declarative.OnExitEvent;
        }

        // remove the first part of the event name before the first period
        int index = eventName.IndexOf(ProcessConstants.EventIdSeparator);
        if (index > 0)
        {
            eventName = eventName[(index + 1)..];
        }

        return eventName;
    }

    private static List<OnEventAction>? ToEventActions(KernelProcessDeclarativeConditionHandler? handler)
    {
        if (handler is null)
        {
            return null;
        }

        List<OnEventAction> actions = [];
        if (handler.EvalConditions is not null && handler.EvalConditions.Count > 0)
        {
            actions.AddRange(handler.EvalConditions.Select(h =>
            {
                return new OnEventAction
                {
                    OnCondition = new DeclarativeProcessCondition
                    {
                        Type = DeclarativeProcessConditionType.Eval,
                        Expression = h.Expression,
                        Emits = h.Emits,
                        Updates = h.Updates
                    }
                };
            }));
        }

        if (handler.AlwaysCondition is not null)
        {
            actions.Add(
                new OnEventAction
                {
                    OnCondition = new DeclarativeProcessCondition
                    {
                        Type = DeclarativeProcessConditionType.Always,
                        Expression = handler.AlwaysCondition.Expression,
                        Emits = handler.AlwaysCondition.Emits,
                        Updates = handler.AlwaysCondition.Updates
                    }
                });
        }

        if (handler.DefaultCondition is not null)
        {
            actions.Add(
                new OnEventAction
                {
                    OnCondition = new DeclarativeProcessCondition
                    {
                        Type = DeclarativeProcessConditionType.Default,
                        Expression = handler.DefaultCondition.Expression,
                        Emits = handler.DefaultCondition.Emits,
                        Updates = handler.DefaultCondition.Updates
                    }
                });
        }

        return actions;
    }

    /// <summary>
    /// Find the source of the edge, it could either be a step, or an input event.
    /// </summary>
    /// <param name="listenCondition"></param>
    /// <param name="processBuilder"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    private ProcessStepEdgeBuilder FindSourceBuilder(ListenEvent listenCondition, ProcessBuilder processBuilder)
    {
        Verify.NotNull(listenCondition);

        ProcessStepEdgeBuilder? edgeBuilder = null;

        // Find the source of the edge, it could either be a step, or an input event.
        if (this._stepBuilders.TryGetValue(listenCondition.From, out ProcessStepBuilder? sourceStepBuilder))
        {
            // The source is a step.
            edgeBuilder = sourceStepBuilder.OnEvent(listenCondition.Event);
        }
        else if (listenCondition.From.Equals("$.inputs.events", StringComparison.OrdinalIgnoreCase) && this._inputEvents.ContainsKey(listenCondition.Event))
        {
            // The source is an input event.
            edgeBuilder = processBuilder.OnInputEvent(listenCondition.Event);
        }
        else
        {
            throw new ArgumentException($"An orchestration is referencing a node with Id `{listenCondition.From}` that does not exist.");
        }

        return edgeBuilder;
    }

    #endregion

    private Dictionary<string, JsonNode> ExtractNodeInputs(string nodeId)
    {
        var input = new StringReader(this._yaml ?? "");
        var yamlStream = new YamlStream();
        yamlStream.Load(input);

        var rootNode = yamlStream.Documents[0].RootNode;
        var agentsNode = rootNode["nodes"] as YamlSequenceNode;
        var node = agentsNode?.Children
            .OfType<YamlMappingNode>()
            .FirstOrDefault(node => node["id"]?.ToString() == nodeId);

        if (node is null || !node.Children.TryGetValue("inputs", out YamlNode? inputs) || input is null || inputs is not YamlMappingNode inputMap)
        {
            throw new KernelException("Failed to deserialize workflow.");
        }

        // This dance to convert the YamlMappingNode to a string and then back to a JsonSchema is rather inefficient, need to find a better option.
        // Serialize the YamlMappingNode to a Yaml string
        var serializer = new SerializerBuilder().Build();
        string rawYaml = serializer.Serialize(inputMap);

        // Deserialize the Yaml string to an object
        var deserializer = new DeserializerBuilder().WithNamingConvention(UnderscoredNamingConvention.Instance).Build();
        var yamlObject = deserializer.Deserialize(rawYaml);

        // Serialize the object to a JSON string
        var jsonSchema = JsonSerializer.Serialize(yamlObject);
        var jsonNode = JsonNode.Parse(jsonSchema) ?? throw new KernelException("Failed to parse schema.");

        var inputsDictionary = inputMap.Select(inputMap => new KeyValuePair<string, JsonNode>(inputMap.Key.ToString(), jsonNode))
            .ToDictionary(kvp => kvp.Key, kvp => kvp.Value);

        return inputsDictionary;
    }
}
