// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Wrapper class for the workflow.
/// </summary>
public class WorkflowWrapper
{
    /// <summary>
    /// Gets or sets the workflow.
    /// </summary>
    [YamlMember(Alias = "workflow")]
    [JsonPropertyName("workflow")]
    public Workflow? Workflow { get; set; }
}

/// <summary>
/// The main workflow specification.
/// </summary>
public class Workflow
{
    /// <summary>
    /// Gets or sets the format version.
    /// </summary>
    [YamlMember(Alias = "format_version")]
    [JsonPropertyName("format_version")]
    public string FormatVersion { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the workflow version.
    /// </summary>
    [YamlMember(Alias = "workflow_version")]
    [JsonPropertyName("workflow_version")]
    public string WorkflowVersion { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the name of the workflow.
    /// </summary>
    [YamlMember(Alias = "name")]
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the description of the workflow.
    /// </summary>
    [YamlMember(Alias = "description")]
    [JsonPropertyName("description")]
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets the suggested inputs for the workflow.
    /// </summary>
    [YamlMember(Alias = "suggested_inputs")]
    [JsonPropertyName("suggested_inputs")]
    public SuggestedInputs? SuggestedInputs { get; set; }

    /// <summary>
    /// Gets or sets the inputs for the workflow.
    /// </summary>
    [YamlMember(Alias = "inputs")]
    [JsonPropertyName("inputs")]
    public Inputs? Inputs { get; set; }

    /// <summary>
    /// Gets or sets the variables for the workflow.
    /// </summary>
    [YamlMember(Alias = "variables")]
    [JsonPropertyName("variables")]
    public Dictionary<string, Variable>? Variables { get; set; }

    /// <summary>
    /// Gets or sets the schemas for the workflow.
    /// </summary>
    [YamlMember(Alias = "schemas")]
    [JsonPropertyName("schemas")]
    public Dictionary<string, WorkflowSchema>? Schemas { get; set; }

    /// <summary>
    /// Gets or sets the nodes for the workflow.
    /// </summary>
    [YamlMember(Alias = "nodes")]
    [JsonPropertyName("nodes")]
    public List<Node>? Nodes { get; set; }

    /// <summary>
    /// Gets or sets the orchestration steps for the workflow.
    /// </summary>
    [YamlMember(Alias = "orchestration")]
    [JsonPropertyName("orchestration")]
    public List<OrchestrationStep>? Orchestration { get; set; }

    /// <summary>
    /// Gets or sets the upgrade strategies for the workflow.
    /// </summary>
    [YamlMember(Alias = "upgrade")]
    [JsonPropertyName("upgrade")]
    public List<UpgradeStrategy>? Upgrade { get; set; }

    /// <summary>
    /// Gets or sets the error handling steps for the workflow.
    /// </summary>
    [YamlMember(Alias = "error_handling")]
    [JsonPropertyName("error_handling")]
    public ErrorHandling? ErrorHandling { get; set; }
}

/// <summary>
/// Suggested inputs for the workflow.
/// </summary>
public class SuggestedInputs
{
    /// <summary>
    /// Gets or sets the suggested events.
    /// </summary>
    [YamlMember(Alias = "events")]
    [JsonPropertyName("events")]
    public List<SuggestedEvent>? Events { get; set; }
}

/// <summary>
/// Suggested event for the workflow.
/// </summary>
public class SuggestedEvent
{
    /// <summary>
    /// Gets or sets the type of the event.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the payload of the event.
    /// </summary>
    [YamlMember(Alias = "payload")]
    [JsonPropertyName("payload")]
    public Dictionary<string, object>? Payload { get; set; }
}

/// <summary>
/// Inputs for the workflow.
/// </summary>
public class Inputs
{
    /// <summary>
    /// Gets or sets the events for the workflow.
    /// </summary>
    [YamlMember(Alias = "events")]
    [JsonPropertyName("events")]
    public InputEvents? Events { get; set; }

    /// <summary>
    /// Gets or sets the messages for the workflow inputs.
    /// </summary>
    [YamlMember(Alias = "messages")]
    [JsonPropertyName("messages")]
    public Messages? Messages { get; set; }
}

/// <summary>
/// Events for the workflow.
/// </summary>
public class InputEvents
{
    /// <summary>
    /// Gets or sets the cloud events for the workflow.
    /// </summary>
    [YamlMember(Alias = "cloud_events")]
    [JsonPropertyName("cloud_events")]
    public List<CloudEvent>? CloudEvents { get; set; }
}

/// <summary>
/// Messages for the workflow inputs.
/// </summary>
public class Messages
{
}

/// <summary>
/// Cloud event for the workflow.
/// </summary>
public class CloudEvent
{
    /// <summary>
    /// Gets or sets the type of the cloud event.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the data schema of the cloud event.
    /// </summary>
    [YamlMember(Alias = "data_schema")]
    [JsonPropertyName("data_schema")]
    public object? DataSchema { get; set; }

    /// <summary>
    /// Gets or sets the filters for the cloud event.
    /// </summary>
    [YamlMember(Alias = "filters")]
    [JsonPropertyName("filters")]
    public List<Filter>? Filters { get; set; }
}

/// <summary>
/// Filter for the cloud event.
/// </summary>
public class Filter
{
    /// <summary>
    /// Gets or sets the filter expression.
    /// </summary>
    [YamlMember(Alias = "filter")]
    [JsonPropertyName("filter")]
    public string FilterExpression { get; set; } = string.Empty;
}

/// <summary>
/// Variable for the workflow.
/// </summary>
public class Variable
{
    /// <summary>
    /// Gets or sets the type of the variable.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the default value of the variable.
    /// </summary>
    [YamlMember(Alias = "default")]
    [JsonPropertyName("default")]
    public object? Default { get; set; }

    /// <summary>
    /// Gets or sets the scope of the variable.
    /// </summary>
    [YamlMember(Alias = "scope")]
    [JsonPropertyName("scope")]
    public string? Scope { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether the variable is mutable.
    /// </summary>
    [YamlMember(Alias = "is_mutable")]
    [JsonPropertyName("is_mutable")]
    public bool? IsMutable { get; set; }

    /// <summary>
    /// Gets or sets the access control list for the variable.
    /// </summary>
    [YamlMember(Alias = "acls")]
    [JsonPropertyName("acls")]
    public List<WorkflowAccessControl>? Acls { get; set; }
}

/// <summary>
/// Access control for the variable.
/// </summary>
public class WorkflowAccessControl
{
    /// <summary>
    /// Gets or sets the node for the access control.
    /// </summary>
    [YamlMember(Alias = "node")]
    [JsonPropertyName("node")]
    public string Node { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the access level for the node.
    /// </summary>
    [YamlMember(Alias = "access")]
    [JsonPropertyName("access")]
    public string Access { get; set; } = string.Empty;
}

/// <summary>
/// Schema for the workflow.
/// </summary>
public class WorkflowSchema
{
    /// <summary>
    /// Gets or sets the type of the schema.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the properties of the schema.
    /// </summary>
    [YamlMember(Alias = "properties")]
    [JsonPropertyName("properties")]
    public Dictionary<string, SchemaProperty>? Properties { get; set; }

    /// <summary>
    /// Gets or sets the required properties of the schema.
    /// </summary>
    [YamlMember(Alias = "required")]
    [JsonPropertyName("required")]
    public List<string>? Required { get; set; }
}

/// <summary>
/// Property of the schema.
/// </summary>
public class SchemaProperty
{
    /// <summary>
    /// Gets or sets the type of the schema property.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string? Type { get; set; }

    /// <summary>
    /// Gets or sets the items of the schema property.
    /// </summary>
    [YamlMember(Alias = "items")]
    [JsonPropertyName("items")]
    public SchemaItems? Items { get; set; }

    /// <summary>
    /// Gets or sets the reference of the schema property.
    /// </summary>
    [YamlMember(Alias = "$ref")]
    [JsonPropertyName("$ref")]
    public string? Ref { get; set; }
}

/// <summary>
/// Items of the schema property.
/// </summary>
public class SchemaItems
{
    /// <summary>
    /// Gets or sets the type of the schema items.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string? Type { get; set; }
}

/// <summary>
/// Node in the workflow.
/// </summary>
public class Node
{
    /// <summary>
    /// Gets or sets the ID of the node.
    /// </summary>
    [YamlMember(Alias = "id")]
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the type of the node.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the version of the node.
    /// </summary>
    [YamlMember(Alias = "version")]
    [JsonPropertyName("version")]
    public string Version { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the description of the node.
    /// </summary>
    [YamlMember(Alias = "description")]
    [JsonPropertyName("description")]
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets the agent of the node.
    /// </summary>
    [YamlMember(Alias = "agent")]
    [JsonPropertyName("agent")]
    public WorkflowAgent? Agent { get; set; }

    /// <summary>
    /// Gets or sets the inputs of the node.
    /// </summary>
    [YamlMember(Alias = "inputs")]
    [JsonPropertyName("inputs")]
    public Dictionary<string, NodeInput>? Inputs { get; set; }

    /// <summary>
    /// Gets or sets the agent input mapping of the node.
    /// </summary>
    [YamlMember(Alias = "agent_input_mapping")]
    [JsonPropertyName("agent_input_mapping")]
    public Dictionary<string, string>? AgentInputMapping { get; set; }

    /// <summary>
    /// Gets or sets the on invoke hook of the node.
    /// </summary>
    [YamlMember(Alias = "on_invoke")]
    [JsonPropertyName("on_invoke")]
    public List<OnEventAction>? OnInvoke { get; set; }

    /// <summary>
    /// Gets or sets the on error hook of the node.
    /// </summary>
    [YamlMember(Alias = "on_error")]
    [JsonPropertyName("on_error")]
    public List<OnEventAction>? OnError { get; set; }

    /// <summary>
    /// Gets or sets the on complete actions of the node.
    /// </summary>
    [YamlMember(Alias = "on_complete")]
    [JsonPropertyName("on_complete")]
    public List<OnEventAction>? OnComplete { get; set; }
}

/// <summary>
/// Agent of the node.
/// </summary>
public class WorkflowAgent
{
    /// <summary>
    /// Gets or sets the type of the agent.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the ID of the agent.
    /// </summary>
    [YamlMember(Alias = "id")]
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;
}

/// <summary>
/// Input of the node.
/// </summary>
public class NodeInput
{
    /// <summary>
    /// Gets or sets the type of the node input.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string? Type { get; set; }

    /// <summary>
    /// Gets or sets the schema of the node input.
    /// </summary>
    [YamlMember(Alias = "schema")]
    [JsonPropertyName("schema")]
    public SchemaReference? Schema { get; set; }
}

/// <summary>
/// Reference to a schema.
/// </summary>
public class SchemaReference
{
    /// <summary>
    /// Gets or sets the reference.
    /// </summary>
    [YamlMember(Alias = "$ref")]
    [JsonPropertyName("$ref")]
    public string? Ref { get; set; }
}

///// <summary>
///// Hook for the node.
///// </summary>
//public class NodeHook
//{
//    /// <summary>
//    /// Gets or sets the events emitted by the hook.
//    /// </summary>
//    [YamlMember(Alias = "emits")]
//    [JsonPropertyName("emits")]
//    public List<EventEmission>? Emits { get; set; }

//    /// <summary>
//    /// Gets or sets the variable updates by the hook.
//    /// </summary>
//    [YamlMember(Alias = "updates")]
//    [JsonPropertyName("updates")]
//    public List<VariableUpdate>? Updates { get; set; }
//}

/// <summary>
/// Action to be taken on completion.
/// </summary>
public class OnEventAction
{
    /// <summary>
    /// Gets or sets the condition for the action.
    /// </summary>
    [YamlMember(Alias = "on_condition")]
    [JsonPropertyName("on_condition")]
    public DeclarativeProcessCondition? OnCondition { get; set; }
}

/// <summary>
/// Condition for an action.
/// </summary>
public class DeclarativeProcessCondition
{
    /// <summary>
    /// Gets or sets the type of the condition.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the expression of the condition.
    /// </summary>
    [YamlMember(Alias = "expression")]
    [JsonPropertyName("expression")]
    public string? Expression { get; set; }

    /// <summary>
    /// Gets or sets the events emitted by the condition.
    /// </summary>
    [YamlMember(Alias = "emits")]
    [JsonPropertyName("emits")]
    public List<EventEmission>? Emits { get; set; }

    /// <summary>
    /// Gets or sets the variable updates by the condition.
    /// </summary>
    [YamlMember(Alias = "updates")]
    [JsonPropertyName("updates")]
    public List<VariableUpdate>? Updates { get; set; }
}

/// <summary>
/// Event emission for a condition or hook.
/// </summary>
public class EventEmission
{
    /// <summary>
    /// Gets or sets the type of the event.
    /// </summary>
    [YamlMember(Alias = "event_type")]
    [JsonPropertyName("event_type")]
    public string EventType { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the schema of the event.
    /// </summary>
    [YamlMember(Alias = "schema")]
    [JsonPropertyName("schema")]
    public SchemaReference? Schema { get; set; }

    /// <summary>
    /// Gets or sets the payload of the event.
    /// </summary>
    [YamlMember(Alias = "payload")]
    [JsonPropertyName("payload")]
    public object? Payload { get; set; }
}

/// <summary>
/// Variable update for a condition or hook.
/// </summary>
public class VariableUpdate
{
    /// <summary>
    /// Gets or sets the variable to be updated.
    /// </summary>
    [YamlMember(Alias = "variable")]
    [JsonPropertyName("variable")]
    public string Variable { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the operation to be performed on the variable.
    /// </summary>
    [YamlMember(Alias = "operation")]
    [JsonPropertyName("operation")]
    public string Operation { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the value to be assigned to the variable.
    /// </summary>
    [YamlMember(Alias = "value")]
    [JsonPropertyName("value")]
    public string Value { get; set; } = string.Empty;
}

/// <summary>
/// Orchestration step in the workflow.
/// </summary>
public class OrchestrationStep
{
    /// <summary>
    /// Gets or sets the condition to listen for.
    /// </summary>
    [YamlMember(Alias = "listen_for")]
    [JsonPropertyName("listen_for")]
    public ListenCondition? ListenFor { get; set; }

    /// <summary>
    /// Gets or sets the actions to be taken.
    /// </summary>
    [YamlMember(Alias = "then")]
    [JsonPropertyName("then")]
    public List<ThenAction>? Then { get; set; }
}

/// <summary>
/// Condition to listen for in an orchestration step.
/// </summary>
public class ListenCondition
{
    /// <summary>
    /// Gets or sets the event to listen for.
    /// </summary>
    [YamlMember(Alias = "event")]
    [JsonPropertyName("event")]
    public string? Event { get; set; }

    /// <summary>
    /// Gets or sets the source of the event.
    /// </summary>
    [YamlMember(Alias = "from")]
    [JsonPropertyName("from")]
    public string? From { get; set; }

    /// <summary>
    /// Gets or sets the filters for the event.
    /// </summary>
    [YamlMember(Alias = "all_of")]
    [JsonPropertyName("all_of")]
    public List<ListenEvent>? AllOf { get; set; }
}

/// <summary>
/// Represents an event to listen for in the workflow.
/// </summary>
public class ListenEvent
{
    /// <summary>
    /// Gets or sets the event name.
    /// </summary>
    [YamlMember(Alias = "event")]
    [JsonPropertyName("event")]
    public string Event { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the source of the event.
    /// </summary>
    [YamlMember(Alias = "from")]
    [JsonPropertyName("from")]
    public string From { get; set; } = string.Empty;
}

/// <summary>
/// Represents an action to be taken in the workflow.
/// </summary>
public class ThenAction
{
    /// <summary>
    /// Gets or sets the node to execute.
    /// </summary>
    [YamlMember(Alias = "node")]
    [JsonPropertyName("node")]
    public string Node { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the inputs for the node.
    /// </summary>
    [YamlMember(Alias = "inputs")]
    [JsonPropertyName("inputs")]
    public Dictionary<string, string>? Inputs { get; set; }
}

/// <summary>
/// Represents an upgrade strategy for the workflow.
/// </summary>
public class UpgradeStrategy
{
    /// <summary>
    /// Gets or sets the version range from which the upgrade is applicable.
    /// </summary>
    [YamlMember(Alias = "from_versions")]
    [JsonPropertyName("from_versions")]
    public VersionRange? FromVersions { get; set; }

    /// <summary>
    /// Gets or sets the strategy for the upgrade.
    /// </summary>
    [YamlMember(Alias = "strategy")]
    [JsonPropertyName("strategy")]
    public string Strategy { get; set; } = string.Empty;
}

/// <summary>
/// Represents a range of versions.
/// </summary>
public class VersionRange
{
    /// <summary>
    /// Gets or sets the minimum version.
    /// </summary>
    [YamlMember(Alias = "min_version")]
    [JsonPropertyName("min_version")]
    public string MinVersion { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the maximum version (exclusive).
    /// </summary>
    [YamlMember(Alias = "max_version_exclusive")]
    [JsonPropertyName("max_version_exclusive")]
    public string MaxVersionExclusive { get; set; } = string.Empty;
}

/// <summary>
/// Represents error handling configuration for the workflow.
/// </summary>
public class ErrorHandling
{
    /// <summary>
    /// Gets or sets the steps to be taken on error.
    /// </summary>
    [YamlMember(Alias = "on_error")]
    [JsonPropertyName("on_error")]
    public List<ErrorHandlingStep>? OnError { get; set; }

    /// <summary>
    /// Gets or sets the default actions to be taken on error.
    /// </summary>
    [YamlMember(Alias = "default")]
    [JsonPropertyName("default")]
    public List<ThenAction>? Default { get; set; }
}

/// <summary>
/// Represents a step to be taken for error handling.
/// </summary>
public class ErrorHandlingStep
{
    /// <summary>
    /// Gets or sets the condition to listen for.
    /// </summary>
    [YamlMember(Alias = "listen_for")]
    [JsonPropertyName("listen_for")]
    public ErrorListenCondition? ListenFor { get; set; }

    /// <summary>
    /// Gets or sets the actions to be taken.
    /// </summary>
    [YamlMember(Alias = "then")]
    [JsonPropertyName("then")]
    public List<ThenAction>? Then { get; set; }
}

/// <summary>
/// Represents a condition to listen for in error handling.
/// </summary>
public class ErrorListenCondition
{
    /// <summary>
    /// Gets or sets the event name.
    /// </summary>
    [YamlMember(Alias = "event")]
    [JsonPropertyName("event")]
    public string Event { get; set; } = string.Empty;
}
