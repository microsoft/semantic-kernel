// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using YamlDotNet.Serialization;

namespace WorkflowEngine.Models;

public class WorkflowWrapper
{
    [YamlMember(Alias = "workflow")]
    [JsonPropertyName("workflow")]
    public Workflow? Workflow { get; set; }
}

/// <summary>
/// The main workflow specification
/// </summary>
public class Workflow
{
    [YamlMember(Alias = "format_version")]
    [JsonPropertyName("format_version")]
    public string FormatVersion { get; set; } = string.Empty;

    [YamlMember(Alias = "workflow_version")]
    [JsonPropertyName("workflow_version")]
    public string WorkflowVersion { get; set; } = string.Empty;

    [YamlMember(Alias = "name")]
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [YamlMember(Alias = "description")]
    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [YamlMember(Alias = "suggested_inputs")]
    [JsonPropertyName("suggested_inputs")]
    public SuggestedInputs? SuggestedInputs { get; set; }

    [YamlMember(Alias = "inputs")]
    [JsonPropertyName("inputs")]
    public Inputs? Inputs { get; set; }

    [YamlMember(Alias = "variables")]
    [JsonPropertyName("variables")]
    public Dictionary<string, Variable>? Variables { get; set; }

    [YamlMember(Alias = "schemas")]
    [JsonPropertyName("schemas")]
    public Dictionary<string, Schema>? Schemas { get; set; }

    [YamlMember(Alias = "nodes")]
    [JsonPropertyName("nodes")]
    public List<Node>? Nodes { get; set; }

    [YamlMember(Alias = "orchestration")]
    [JsonPropertyName("orchestration")]
    public List<OrchestrationStep>? Orchestration { get; set; }

    [YamlMember(Alias = "upgrade")]
    [JsonPropertyName("upgrade")]
    public List<UpgradeStrategy>? Upgrade { get; set; }

    [YamlMember(Alias = "error_handling")]
    [JsonPropertyName("error_handling")]
    public ErrorHandling? ErrorHandling { get; set; }
}

public class SuggestedInputs
{
    [YamlMember(Alias = "events")]
    [JsonPropertyName("events")]
    public List<SuggestedEvent>? Events { get; set; }
}

public class SuggestedEvent
{
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [YamlMember(Alias = "payload")]
    [JsonPropertyName("payload")]
    public Dictionary<string, object>? Payload { get; set; }
}

public class Inputs
{
    [YamlMember(Alias = "events")]
    [JsonPropertyName("events")]
    public Events? Events { get; set; }
}

public class Events
{
    [YamlMember(Alias = "cloud_events")]
    [JsonPropertyName("cloud_events")]
    public List<CloudEvent>? CloudEvents { get; set; }
}

public class CloudEvent
{
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [YamlMember(Alias = "data_schema")]
    [JsonPropertyName("data_schema")]
    public object? DataSchema { get; set; }

    [YamlMember(Alias = "filters")]
    [JsonPropertyName("filters")]
    public List<Filter>? Filters { get; set; }
}

public class Filter
{
    [YamlMember(Alias = "filter")]
    [JsonPropertyName("filter")]
    public string FilterExpression { get; set; } = string.Empty;
}

public class Variable
{
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [YamlMember(Alias = "default")]
    [JsonPropertyName("default")]
    public object? Default { get; set; }

    [YamlMember(Alias = "scope")]
    [JsonPropertyName("scope")]
    public string? Scope { get; set; }

    [YamlMember(Alias = "is_mutable")]
    [JsonPropertyName("is_mutable")]
    public bool? IsMutable { get; set; }

    [YamlMember(Alias = "acls")]
    [JsonPropertyName("acls")]
    public List<AccessControl>? Acls { get; set; }
}

public class AccessControl
{
    [YamlMember(Alias = "node")]
    [JsonPropertyName("node")]
    public string Node { get; set; } = string.Empty;

    [YamlMember(Alias = "access")]
    [JsonPropertyName("access")]
    public string Access { get; set; } = string.Empty;
}

public class Schema
{
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [YamlMember(Alias = "properties")]
    [JsonPropertyName("properties")]
    public Dictionary<string, SchemaProperty>? Properties { get; set; }

    [YamlMember(Alias = "required")]
    [JsonPropertyName("required")]
    public List<string>? Required { get; set; }
}

public class SchemaProperty
{
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string? Type { get; set; }

    [YamlMember(Alias = "items")]
    [JsonPropertyName("items")]
    public SchemaItems? Items { get; set; }

    [YamlMember(Alias = "$ref")]
    [JsonPropertyName("$ref")]
    public string? Ref { get; set; }
}

public class SchemaItems
{
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string? Type { get; set; }
}

public class Node
{
    [YamlMember(Alias = "id")]
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [YamlMember(Alias = "version")]
    [JsonPropertyName("version")]
    public string Version { get; set; } = string.Empty;

    [YamlMember(Alias = "description")]
    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [YamlMember(Alias = "agent")]
    [JsonPropertyName("agent")]
    public Agent? Agent { get; set; }

    [YamlMember(Alias = "inputs")]
    [JsonPropertyName("inputs")]
    public Dictionary<string, NodeInput>? Inputs { get; set; }

    [YamlMember(Alias = "agent_input_mapping")]
    [JsonPropertyName("agent_input_mapping")]
    public Dictionary<string, string>? AgentInputMapping { get; set; }

    [YamlMember(Alias = "on_invoke")]
    [JsonPropertyName("on_invoke")]
    public NodeHook? OnInvoke { get; set; }

    [YamlMember(Alias = "on_error")]
    [JsonPropertyName("on_error")]
    public NodeHook? OnError { get; set; }

    [YamlMember(Alias = "on_complete")]
    [JsonPropertyName("on_complete")]
    public List<OnCompleteAction>? OnComplete { get; set; }
}

public class Agent
{
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [YamlMember(Alias = "id")]
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;
}

public class NodeInput
{
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string? Type { get; set; }

    [YamlMember(Alias = "schema")]
    [JsonPropertyName("schema")]
    public SchemaReference? Schema { get; set; }
}

public class SchemaReference
{
    [YamlMember(Alias = "$ref")]
    [JsonPropertyName("$ref")]
    public string? Ref { get; set; }
}

public class NodeHook
{
    [YamlMember(Alias = "emits")]
    [JsonPropertyName("emits")]
    public List<EventEmission>? Emits { get; set; }

    [YamlMember(Alias = "updates")]
    [JsonPropertyName("updates")]
    public List<VariableUpdate>? Updates { get; set; }
}

public class OnCompleteAction
{
    [YamlMember(Alias = "on_condition")]
    [JsonPropertyName("on_condition")]
    public Condition? OnCondition { get; set; }
}

public class Condition
{
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [YamlMember(Alias = "expression")]
    [JsonPropertyName("expression")]
    public string? Expression { get; set; }

    [YamlMember(Alias = "emits")]
    [JsonPropertyName("emits")]
    public List<EventEmission>? Emits { get; set; }

    [YamlMember(Alias = "updates")]
    [JsonPropertyName("updates")]
    public List<VariableUpdate>? Updates { get; set; }
}

public class EventEmission
{
    [YamlMember(Alias = "event_type")]
    [JsonPropertyName("event_type")]
    public string EventType { get; set; } = string.Empty;

    [YamlMember(Alias = "schema")]
    [JsonPropertyName("schema")]
    public SchemaReference? Schema { get; set; }

    [YamlMember(Alias = "payload")]
    [JsonPropertyName("payload")]
    public object? Payload { get; set; }
}

public class VariableUpdate
{
    [YamlMember(Alias = "variable")]
    [JsonPropertyName("variable")]
    public string Variable { get; set; } = string.Empty;

    [YamlMember(Alias = "operation")]
    [JsonPropertyName("operation")]
    public string Operation { get; set; } = string.Empty;

    [YamlMember(Alias = "value")]
    [JsonPropertyName("value")]
    public string Value { get; set; } = string.Empty;
}

public class OrchestrationStep
{
    [YamlMember(Alias = "listen_for")]
    [JsonPropertyName("listen_for")]
    public ListenCondition? ListenFor { get; set; }

    [YamlMember(Alias = "then")]
    [JsonPropertyName("then")]
    public List<ThenAction>? Then { get; set; }
}

public class ListenCondition
{
    [YamlMember(Alias = "event")]
    [JsonPropertyName("event")]
    public string? Event { get; set; }

    [YamlMember(Alias = "from")]
    [JsonPropertyName("from")]
    public string? From { get; set; }

    [YamlMember(Alias = "all_of")]
    [JsonPropertyName("all_of")]
    public List<ListenEvent>? AllOf { get; set; }
}

public class ListenEvent
{
    [YamlMember(Alias = "event")]
    [JsonPropertyName("event")]
    public string Event { get; set; } = string.Empty;

    [YamlMember(Alias = "from")]
    [JsonPropertyName("from")]
    public string From { get; set; } = string.Empty;
}

public class ThenAction
{
    [YamlMember(Alias = "node")]
    [JsonPropertyName("node")]
    public string Node { get; set; } = string.Empty;

    [YamlMember(Alias = "inputs")]
    [JsonPropertyName("inputs")]
    public Dictionary<string, string>? Inputs { get; set; }
}

public class UpgradeStrategy
{
    [YamlMember(Alias = "from_versions")]
    [JsonPropertyName("from_versions")]
    public VersionRange? FromVersions { get; set; }

    [YamlMember(Alias = "strategy")]
    [JsonPropertyName("strategy")]
    public string Strategy { get; set; } = string.Empty;
}

public class VersionRange
{
    [YamlMember(Alias = "min_version")]
    [JsonPropertyName("min_version")]
    public string MinVersion { get; set; } = string.Empty;

    [YamlMember(Alias = "max_version_exclusive")]
    [JsonPropertyName("max_version_exclusive")]
    public string MaxVersionExclusive { get; set; } = string.Empty;
}

public class ErrorHandling
{
    [YamlMember(Alias = "on_error")]
    [JsonPropertyName("on_error")]
    public List<ErrorHandlingStep>? OnError { get; set; }

    [YamlMember(Alias = "default")]
    [JsonPropertyName("default")]
    public List<ThenAction>? Default { get; set; }
}

public class ErrorHandlingStep
{
    [YamlMember(Alias = "listen_for")]
    [JsonPropertyName("listen_for")]
    public ErrorListenCondition? ListenFor { get; set; }

    [YamlMember(Alias = "then")]
    [JsonPropertyName("then")]
    public List<ThenAction>? Then { get; set; }
}

public class ErrorListenCondition
{
    [YamlMember(Alias = "event")]
    [JsonPropertyName("event")]
    public string Event { get; set; } = string.Empty;
}
