// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Process.Internal;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A wrapper class that encapsulates the workflow definition for serialization and deserialization.
/// This class serves as the root container for workflow configurations in both YAML and JSON formats.
/// </summary>
public sealed class WorkflowWrapper
{
    /// <summary>
    /// Gets or sets the workflow definition contained within this wrapper.
    /// This property represents the complete workflow specification including all nodes, orchestration, and error handling.
    /// </summary>
    [YamlMember(Alias = "workflow")]
    [JsonPropertyName("workflow")]
    public Workflow? Workflow { get; set; }
}

/// <summary>
/// Represents the main workflow specification that defines the complete structure and behavior of a workflow.
/// A workflow consists of nodes, orchestration steps, variables, schemas, and error handling configurations.
/// </summary>
public sealed class Workflow
{
    /// <summary>
    /// Gets or sets the unique identifier of the workflow.
    /// This ID should be unique across all workflows within the system and is used for workflow identification and referencing.
    /// </summary>
    [YamlMember(Alias = "id")]
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the format version of the workflow specification.
    /// This version indicates the schema version used to define the workflow and ensures compatibility with the execution engine.
    /// </summary>
    [YamlMember(Alias = "format_version")]
    [JsonPropertyName("format_version")]
    public string FormatVersion { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the version of the workflow implementation.
    /// This version tracks the evolution of the workflow definition and allows for versioning of workflow logic.
    /// </summary>
    [YamlMember(Alias = "workflow_version")]
    [JsonPropertyName("workflow_version")]
    public string WorkflowVersion { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the human-readable name of the workflow.
    /// This name is used for display purposes and should clearly identify the workflow's purpose.
    /// </summary>
    [YamlMember(Alias = "name")]
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the optional description of the workflow.
    /// This description provides additional context about the workflow's purpose, behavior, and usage.
    /// </summary>
    [YamlMember(Alias = "description")]
    [JsonPropertyName("description")]
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets the suggested inputs for the workflow.
    /// These inputs provide examples or recommendations for how the workflow should be invoked.
    /// </summary>
    [YamlMember(Alias = "suggested_inputs")]
    [JsonPropertyName("suggested_inputs")]
    public SuggestedInputs? SuggestedInputs { get; set; }

    /// <summary>
    /// Gets or sets the input configuration for the workflow.
    /// This defines what types of inputs the workflow accepts, including events and messages.
    /// </summary>
    [YamlMember(Alias = "inputs")]
    [JsonPropertyName("inputs")]
    public Inputs? Inputs { get; set; }

    /// <summary>
    /// Gets or sets the variables defined within the workflow scope.
    /// These variables can be used throughout the workflow for state management and data passing between nodes.
    /// </summary>
    [YamlMember(Alias = "variables")]
    [JsonPropertyName("variables")]
    public Dictionary<string, VariableDefinition>? Variables { get; set; }

    /// <summary>
    /// Gets or sets the schemas used within the workflow.
    /// These schemas define the structure and validation rules for data used throughout the workflow.
    /// </summary>
    [YamlMember(Alias = "schemas")]
    [JsonPropertyName("schemas")]
    public Dictionary<string, WorkflowSchema>? Schemas { get; set; }

    /// <summary>
    /// Gets or sets the collection of nodes that make up the workflow.
    /// Each node represents a step or component in the workflow execution graph.
    /// </summary>
    [YamlMember(Alias = "nodes")]
    [JsonPropertyName("nodes")]
    public List<Node>? Nodes { get; set; }

    /// <summary>
    /// Gets or sets the orchestration steps that define the workflow execution flow.
    /// These steps specify the conditions and actions that control how the workflow progresses from node to node.
    /// </summary>
    [YamlMember(Alias = "orchestration")]
    [JsonPropertyName("orchestration")]
    public List<OrchestrationStep>? Orchestration { get; set; }

    /// <summary>
    /// Gets or sets the error handling configuration for the workflow.
    /// This defines how the workflow should respond to and recover from errors during execution.
    /// </summary>
    [YamlMember(Alias = "error_handling")]
    [JsonPropertyName("error_handling")]
    public ErrorHandling? ErrorHandling { get; set; }
}

/// <summary>
/// Defines the possible types of variables that can be used within a workflow.
/// Variables can represent different data structures and have different behaviors during workflow execution.
/// </summary>
public enum VariableType
{
    /// <summary>
    /// A thread type variable that represents a conversation thread or execution context.
    /// Thread variables maintain state and context across multiple interactions within the workflow.
    /// </summary>
    [JsonPropertyName("thread")]
    Thread,

    /// <summary>
    /// A message type variable that represents a collection of messages.
    /// Messages variables are used to store and pass communication data between workflow components.
    /// </summary>
    [JsonPropertyName("messages")]
    Messages,

    /// <summary>
    /// A user-defined variable with custom structure and behavior.
    /// User-defined variables allow for flexible data types specific to the workflow's requirements.
    /// </summary>
    [JsonPropertyName("user-defined")]
    UserDefined
}

/// <summary>
/// Represents the definition of a variable within a workflow, including its type, default value, and schema.
/// Variable definitions specify how variables should be initialized and validated during workflow execution.
/// </summary>
public sealed class VariableDefinition
{
    /// <summary>
    /// Gets or sets the type of the variable.
    /// The type determines how the variable is handled and what operations can be performed on it.
    /// </summary>
    public VariableType Type { get; set; } = VariableType.UserDefined;

    /// <summary>
    /// Gets or sets the default value of the variable.
    /// This value is used to initialize the variable when the workflow starts if no other value is provided.
    /// </summary>
    public object? DefaultValue { get; set; }

    /// <summary>
    /// Gets or sets the schema definition for the variable.
    /// The schema defines the structure, validation rules, and constraints for the variable's value.
    /// </summary>
    public object? Schema { get; set; }
}

/// <summary>
/// Contains suggested input configurations that provide guidance on how to invoke the workflow.
/// Suggested inputs help users understand the expected input format and provide examples for workflow execution.
/// </summary>
public sealed class SuggestedInputs
{
    /// <summary>
    /// Gets or sets the list of suggested events that can be used to trigger the workflow.
    /// These events serve as examples or templates for valid workflow inputs.
    /// </summary>
    [YamlMember(Alias = "events")]
    [JsonPropertyName("events")]
    public List<SuggestedEvent>? Events { get; set; }
}

/// <summary>
/// Represents a suggested event that demonstrates how to trigger the workflow with specific input data.
/// Suggested events provide examples of valid event types and their associated payloads.
/// </summary>
public sealed class SuggestedEvent
{
    /// <summary>
    /// Gets or sets the type identifier of the suggested event.
    /// This type should match one of the event types that the workflow is configured to handle.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the payload data for the suggested event.
    /// The payload contains the data structure and values that would be passed with this type of event.
    /// </summary>
    [YamlMember(Alias = "payload")]
    [JsonPropertyName("payload")]
    public Dictionary<string, object>? Payload { get; set; }
}

/// <summary>
/// Defines the input configuration for a workflow, specifying what types of data the workflow can accept.
/// Inputs can include both events and message collections, allowing for flexible workflow triggering mechanisms.
/// </summary>
public sealed class Inputs
{
    /// <summary>
    /// Gets or sets the event input configuration for the workflow.
    /// This defines which types of events can trigger the workflow and how they should be processed.
    /// </summary>
    [YamlMember(Alias = "events")]
    [JsonPropertyName("events")]
    public InputEvents? Events { get; set; }

    /// <summary>
    /// Gets or sets the message input configuration for the workflow.
    /// This allows the workflow to be triggered with a collection of messages rather than events.
    /// </summary>
    [YamlMember(Alias = "messages")]
    [JsonPropertyName("messages")]
    public Messages? Messages { get; set; }
}

/// <summary>
/// Contains the event input configuration for a workflow, defining which events can trigger execution.
/// Event inputs allow workflows to be triggered by various types of external or internal events.
/// </summary>
public sealed class InputEvents
{
    /// <summary>
    /// Gets or sets the list of cloud events that can trigger the workflow.
    /// Cloud events follow the CloudEvents specification and provide a standardized way to describe events.
    /// </summary>
    [YamlMember(Alias = "cloud_events")]
    [JsonPropertyName("cloud_events")]
    public List<CloudEvent>? CloudEvents { get; set; }
}

/// <summary>
/// Represents a collection of messages that can be used as input to a workflow.
/// This class extends List to provide a strongly-typed collection for message objects.
/// </summary>
public sealed class Messages : List<object>
{
}

/// <summary>
/// Represents a CloudEvent that can trigger workflow execution.
/// CloudEvents provide a standardized format for describing events in a vendor-neutral way.
/// </summary>
public sealed class CloudEvent
{
    /// <summary>
    /// Gets or sets the type of the cloud event.
    /// The event type identifies the nature of the event and determines how it should be processed.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the data schema for the cloud event's payload.
    /// The data schema defines the structure and validation rules for the event's data content.
    /// </summary>
    [YamlMember(Alias = "data_schema")]
    [JsonPropertyName("data_schema")]
    public object? DataSchema { get; set; }

    /// <summary>
    /// Gets or sets the list of filters that determine whether this event should trigger the workflow.
    /// Filters allow for conditional processing based on event content or metadata.
    /// </summary>
    [YamlMember(Alias = "filters")]
    [JsonPropertyName("filters")]
    public List<ProcessFilter>? Filters { get; set; }
}

/// <summary>
/// Represents a filter condition that can be applied to events or other workflow data.
/// Filters are used to conditionally process or route data based on specified criteria.
/// </summary>
public sealed class ProcessFilter
{
    /// <summary>
    /// Gets or sets the filter expression that defines the condition.
    /// The expression is evaluated against the event or data to determine if the filter matches.
    /// </summary>
    [YamlMember(Alias = "filter")]
    [JsonPropertyName("filter")]
    public string FilterExpression { get; set; } = string.Empty;
}

/// <summary>
/// Represents a variable within the workflow context, including its type, default value, and access controls.
/// Variables provide state management and data sharing capabilities within the workflow execution environment.
/// </summary>
public sealed class Variable
{
    /// <summary>
    /// Gets or sets the type identifier of the variable.
    /// The type determines how the variable is stored, accessed, and manipulated during execution.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the default value assigned to the variable when it is first created.
    /// This value is used if no explicit initialization value is provided.
    /// </summary>
    [YamlMember(Alias = "default")]
    [JsonPropertyName("default")]
    public object? Default { get; set; }

    /// <summary>
    /// Gets or sets the scope in which the variable is accessible.
    /// Scope determines which parts of the workflow can read and modify the variable.
    /// </summary>
    [YamlMember(Alias = "scope")]
    [JsonPropertyName("scope")]
    public string? Scope { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether the variable can be modified after initialization.
    /// Immutable variables provide read-only access after their initial assignment.
    /// </summary>
    [YamlMember(Alias = "is_mutable")]
    [JsonPropertyName("is_mutable")]
    public bool? IsMutable { get; set; }

    /// <summary>
    /// Gets or sets the access control list (ACL) that defines which nodes can access this variable.
    /// ACLs provide fine-grained security control over variable access within the workflow.
    /// </summary>
    [YamlMember(Alias = "acls")]
    [JsonPropertyName("acls")]
    public List<WorkflowAccessControl>? Acls { get; set; }
}

/// <summary>
/// Defines an access control entry that specifies permissions for a workflow node to access a variable.
/// Access control entries provide security and isolation by restricting variable access to authorized nodes.
/// </summary>
public sealed class WorkflowAccessControl
{
    /// <summary>
    /// Gets or sets the identifier of the node that is granted access.
    /// This should match the ID of a node defined in the workflow's node collection.
    /// </summary>
    [YamlMember(Alias = "node")]
    [JsonPropertyName("node")]
    public string Node { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the level of access granted to the node.
    /// Access levels typically include read, write, or read-write permissions.
    /// </summary>
    [YamlMember(Alias = "access")]
    [JsonPropertyName("access")]
    public string Access { get; set; } = string.Empty;
}

/// <summary>
/// Represents a schema definition used to validate and structure data within the workflow.
/// Schemas ensure data integrity and provide a contract for data exchange between workflow components.
/// </summary>
public sealed class WorkflowSchema
{
    /// <summary>
    /// Gets or sets the type of the schema (e.g., object, array, string).
    /// The type defines the fundamental structure that the schema validates.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the properties defined within the schema.
    /// Properties specify the individual fields and their validation rules for object-type schemas.
    /// </summary>
    [YamlMember(Alias = "properties")]
    [JsonPropertyName("properties")]
    public Dictionary<string, SchemaProperty>? Properties { get; set; }

    /// <summary>
    /// Gets or sets the list of required property names within the schema.
    /// Required properties must be present in any data that conforms to this schema.
    /// </summary>
    [YamlMember(Alias = "required")]
    [JsonPropertyName("required")]
    public List<string>? Required { get; set; }
}

/// <summary>
/// Represents a property definition within a schema, including its type, constraints, and references.
/// Schema properties define the validation rules and structure for individual fields within a schema.
/// </summary>
public sealed class SchemaProperty
{
    /// <summary>
    /// Gets or sets the data type of the schema property.
    /// The type determines what kind of values are valid for this property.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string? Type { get; set; }

    /// <summary>
    /// Gets or sets the item definition for array-type properties.
    /// This defines the structure and validation rules for elements within an array property.
    /// </summary>
    [YamlMember(Alias = "items")]
    [JsonPropertyName("items")]
    public SchemaItems? Items { get; set; }

    /// <summary>
    /// Gets or sets a reference to another schema definition.
    /// References allow for reuse of schema definitions and creation of complex nested structures.
    /// </summary>
    [YamlMember(Alias = "$ref")]
    [JsonPropertyName("$ref")]
    public string? Ref { get; set; }
}

/// <summary>
/// Defines the schema for items within an array-type schema property.
/// Schema items specify how individual elements in an array should be validated and structured.
/// </summary>
public sealed class SchemaItems
{
    /// <summary>
    /// Gets or sets the data type of the array items.
    /// This type applies to each individual element within the array.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string? Type { get; set; }
}

/// <summary>
/// Represents a single node within the workflow execution graph.
/// Nodes are the fundamental building blocks of a workflow, each performing a specific task or operation.
/// </summary>
public sealed class Node
{
    /// <summary>
    /// Gets or sets the unique identifier of the node within the workflow.
    /// This ID is used to reference the node in orchestration steps and other workflow configurations.
    /// </summary>
    [YamlMember(Alias = "id")]
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the type of the node, which determines its behavior and capabilities.
    /// Node types define the category of operation that the node performs within the workflow.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the version of the node implementation.
    /// Versioning allows for evolution of node behavior while maintaining backward compatibility.
    /// </summary>
    [YamlMember(Alias = "version")]
    [JsonPropertyName("version")]
    public string Version { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the optional description of the node's purpose and behavior.
    /// Descriptions provide documentation and context for understanding the node's role in the workflow.
    /// </summary>
    [YamlMember(Alias = "description")]
    [JsonPropertyName("description")]
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets the agent definition associated with this node.
    /// Agents provide the actual implementation and execution logic for the node.
    /// </summary>
    [YamlMember(Alias = "agent")]
    [JsonPropertyName("agent")]
    public AgentDefinition? Agent { get; set; }

    /// <summary>
    /// Gets or sets the human-in-the-loop (HITL) mode for this node.
    /// HITL mode determines when and how human intervention is required during node execution.
    /// </summary>
    [YamlMember(Alias = "human_in_loop_mode")]
    [JsonPropertyName("human_in_loop_mode")]
    public HITLMode? HumanInLoopType { get; set; } = null;

    /// <summary>
    /// Gets or sets the input configuration for the node.
    /// Inputs define what data the node expects to receive when it is executed.
    /// </summary>
    [YamlMember(Alias = "inputs")]
    [JsonPropertyName("inputs")]
    public Dictionary<string, object>? Inputs { get; set; }

    /// <summary>
    /// Gets or sets the mapping configuration for agent inputs.
    /// This mapping defines how workflow data is transformed and passed to the associated agent.
    /// </summary>
    [YamlMember(Alias = "agent_input_mapping")]
    [JsonPropertyName("agent_input_mapping")]
    public Dictionary<string, string>? AgentInputMapping { get; set; }

    /// <summary>
    /// Gets or sets the actions to be executed when the node encounters an error.
    /// Error actions provide a mechanism for graceful error handling and recovery.
    /// </summary>
    [YamlMember(Alias = "on_error")]
    [JsonPropertyName("on_error")]
    public List<OnEventAction>? OnError { get; set; } = null;

    /// <summary>
    /// Gets or sets the actions to be executed when the node completes successfully.
    /// Completion actions allow for post-processing and workflow continuation logic.
    /// </summary>
    [YamlMember(Alias = "on_complete")]
    [JsonPropertyName("on_complete")]
    public List<OnEventAction>? OnComplete { get; set; } = null;
}

/// <summary>
/// Represents an agent configuration within a workflow node.
/// Agents provide the concrete implementation for node functionality and define how the node operates.
/// </summary>
public sealed class WorkflowAgent
{
    /// <summary>
    /// Gets or sets the type of the agent.
    /// The agent type determines the implementation class and capabilities available to the node.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the unique identifier of the agent instance.
    /// This ID can be used to reference specific agent configurations or implementations.
    /// </summary>
    [YamlMember(Alias = "id")]
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;
}

/// <summary>
/// Defines the different types of input handling modes for agents within workflow nodes.
/// Input types determine how data is passed to and processed by the agent.
/// </summary>
public enum AgentInputType
{
    /// <summary>
    /// Inputs are assumed to be part of the conversation thread and are not passed separately.
    /// In this mode, the agent reads input from the current thread context.
    /// </summary>
    Thread,

    /// <summary>
    /// The agent expects structured input data passed directly as parameters.
    /// This mode provides explicit data passing with defined structure and validation.
    /// </summary>
    Structured
}

/// <summary>
/// Represents the input configuration for a workflow node.
/// Node inputs define the expected data structure and schema for information passed to the node.
/// </summary>
public sealed class NodeInputs
{
    /// <summary>
    /// Gets or sets the schema reference for the node's input structure.
    /// The schema defines the validation rules and structure for data passed to this node.
    /// </summary>
    [YamlMember(Alias = "schema")]
    [JsonPropertyName("schema")]
    public string? Schema { get; set; }
}

/// <summary>
/// Represents a reference to a schema definition.
/// Schema references allow for reuse of schema definitions across multiple workflow components.
/// </summary>
public sealed class SchemaReference
{
    /// <summary>
    /// Gets or sets the reference path to the schema definition.
    /// This reference follows JSON Schema reference syntax to point to another schema.
    /// </summary>
    [YamlMember(Alias = "$ref")]
    [JsonPropertyName("$ref")]
    public string? Ref { get; set; }
}

/// <summary>
/// Represents an action that can be executed in response to a workflow event.
/// Event actions provide the mechanism for conditional logic and dynamic workflow behavior.
/// </summary>
public sealed class OnEventAction
{
    /// <summary>
    /// Gets or sets the condition that must be met for this action to execute.
    /// Conditions allow for sophisticated conditional logic based on workflow state and event data.
    /// </summary>
    [YamlMember(Alias = "on_condition")]
    [JsonPropertyName("on_condition")]
    public DeclarativeProcessCondition? OnCondition { get; set; }
}

/// <summary>
/// Defines the types of conditions that can be used in workflow decision-making.
/// Condition types determine how and when conditional logic is evaluated.
/// </summary>
public enum DeclarativeProcessConditionType
{
    /// <summary>
    /// A condition that evaluates a custom expression against the current workflow state.
    /// Eval conditions provide maximum flexibility for custom conditional logic.
    /// </summary>
    [JsonPropertyName("eval")]
    Eval,

    /// <summary>
    /// A condition that always evaluates to true, regardless of context.
    /// Always conditions provide unconditional execution paths.
    /// </summary>
    [JsonPropertyName("always")]
    Always,

    /// <summary>
    /// A default condition that activates when no other conditions are met.
    /// Default conditions provide fallback behavior for unmatched scenarios.
    /// </summary>
    [JsonPropertyName("default")]
    Default
}

/// <summary>
/// Represents a condition that controls workflow execution flow and decision-making.
/// Conditions evaluate workflow state and determine which actions should be executed.
/// </summary>
public sealed class DeclarativeProcessCondition
{
    /// <summary>
    /// Gets or sets the type of condition evaluation to perform.
    /// The condition type determines how the condition expression is interpreted and evaluated.
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public DeclarativeProcessConditionType Type { get; set; } = DeclarativeProcessConditionType.Eval;

    /// <summary>
    /// Gets or sets the expression to evaluate for this condition.
    /// The expression syntax depends on the condition type and evaluation context.
    /// </summary>
    [YamlMember(Alias = "expression")]
    [JsonPropertyName("expression")]
    public string? Expression { get; set; }

    /// <summary>
    /// Gets or sets the list of events to emit when this condition is satisfied.
    /// Event emissions allow conditions to trigger additional workflow behavior.
    /// </summary>
    [YamlMember(Alias = "emits")]
    [JsonPropertyName("emits")]
    public List<EventEmission>? Emits { get; set; }

    /// <summary>
    /// Gets or sets the list of variable updates to perform when this condition is satisfied.
    /// Variable updates allow conditions to modify workflow state as part of their execution.
    /// </summary>
    [YamlMember(Alias = "updates")]
    [JsonPropertyName("updates")]
    public List<VariableUpdate>? Updates { get; set; }
}

/// <summary>
/// Represents an event emission that occurs when a condition is satisfied or an action is executed.
/// Event emissions provide a way to communicate state changes and trigger reactions throughout the workflow.
/// </summary>
public sealed class EventEmission
{
    /// <summary>
    /// Gets or sets the type identifier of the event being emitted.
    /// The event type determines how the event is processed and which listeners will respond to it.
    /// </summary>
    [YamlMember(Alias = "event_type")]
    [JsonPropertyName("event_type")]
    public string EventType { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the schema reference for the event's payload structure.
    /// The schema ensures that emitted events conform to expected data structures.
    /// </summary>
    [YamlMember(Alias = "schema")]
    [JsonPropertyName("schema")]
    public SchemaReference? Schema { get; set; }

    /// <summary>
    /// Gets or sets the data payload included with the emitted event.
    /// The payload contains the actual data that will be passed to event listeners.
    /// </summary>
    [YamlMember(Alias = "payload")]
    [JsonPropertyName("payload")]
    public object? Payload { get; set; }
}

/// <summary>
/// Represents a condition expression that can be evaluated against workflow data.
/// Condition expressions provide structured conditional logic for workflow decision-making.
/// </summary>
public sealed class ConditionExpression
{
    /// <summary>
    /// Gets or sets the path to the variable or data being evaluated.
    /// The path uses dot notation to navigate through complex data structures.
    /// </summary>
    public string Path { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the comparison operator used in the condition.
    /// The operator determines how the value at the path is compared to the condition value.
    /// </summary>
    public ConditionOperator Operator { get; set; } = ConditionOperator.Equal;

    /// <summary>
    /// Gets or sets the value to compare against the path value.
    /// This value is used with the operator to determine if the condition is satisfied.
    /// </summary>
    public object Value { get; set; } = string.Empty;
}

/// <summary>
/// Defines the comparison operators available for use in condition expressions.
/// Operators determine how values are compared in conditional logic.
/// </summary>
public enum ConditionOperator
{
    /// <summary>
    /// Tests whether two values are equal.
    /// </summary>
    [JsonPropertyName("equal")]
    Equal,
    /// <summary>
    /// Tests whether two values are not equal.
    /// </summary>
    NotEqual,
    /// <summary>
    /// Tests whether the left value is greater than the right value.
    /// </summary>
    GreaterThan,
    /// <summary>
    /// Tests whether the left value is less than the right value.
    /// </summary>
    LessThan,
    /// <summary>
    /// Tests whether the left value is greater than or equal to the right value.
    /// </summary>
    GreaterThanOrEqual,
    /// <summary>
    /// Tests whether the left value is less than or equal to the right value.
    /// </summary>
    LessThanOrEqual
}

/// <summary>
/// Defines the types of operations that can be performed when updating workflow state variables.
/// Update operations provide different ways to modify variable values during workflow execution.
/// </summary>
public enum StateUpdateOperations
{
    /// <summary>
    /// Sets the variable to a specific value, replacing any existing value.
    /// </summary>
    [YamlMember(Alias = "set")]
    [JsonPropertyName("set")]
    Set,

    /// <summary>
    /// Increments the variable's value by a specified amount.
    /// This operation is typically used with numeric variables.
    /// </summary>
    [YamlMember(Alias = "increment")]
    [JsonPropertyName("increment")]
    Increment,

    /// <summary>
    /// Decrements the variable's value by a specified amount.
    /// This operation is typically used with numeric variables.
    /// </summary>
    [YamlMember(Alias = "decrement")]
    [JsonPropertyName("decrement")]
    Decrement
}

/// <summary>
/// Defines the modes for human-in-the-loop (HITL) interaction within workflow nodes.
/// HITL modes determine when and how human intervention is required during workflow execution.
/// </summary>
public enum HITLMode
{
    /// <summary>
    /// Always requires human input before the node can proceed with execution.
    /// This mode ensures that human oversight is mandatory for every execution of the node.
    /// </summary>
    [YamlMember(Alias = "always")]
    [JsonPropertyName("always")]
    Always,

    /// <summary>
    /// Never requires human input and allows the node to execute automatically.
    /// This mode provides fully automated execution without human intervention.
    /// </summary>
    [YamlMember(Alias = "never")]
    [JsonPropertyName("never")]
    Never,
}

/// <summary>
/// Represents an update operation to be performed on a workflow variable.
/// Variable updates allow workflows to modify state based on conditions and execution flow.
/// </summary>
[DataContract]
public sealed class VariableUpdate
{
    /// <summary>
    /// Gets or sets the path to the variable to be updated.
    /// The path uses dot notation to specify the exact location of the variable in the state.
    /// </summary>
    [YamlMember(Alias = "path")]
    [JsonPropertyName("path")]
    [DataMember]
    public string Path { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the operation to be performed on the variable.
    /// The operation determines how the variable's value will be modified (set, increment, decrement).
    /// </summary>
    [YamlMember(Alias = "operation")]
    [JsonPropertyName("operation")]
    [DataMember]
    public StateUpdateOperations Operation { get; set; }

    /// <summary>
    /// Gets or sets the value to be used in the update operation.
    /// For set operations, this becomes the new value. For increment/decrement, this is the amount to change.
    /// </summary>
    [YamlMember(Alias = "value")]
    [JsonPropertyName("value")]

    public object? Value { get; set; } = string.Empty;
}

/// <summary>
/// Represents a single step in the workflow orchestration that defines conditional execution logic.
/// Orchestration steps control the flow of execution by listening for events and taking appropriate actions.
/// </summary>
public sealed class OrchestrationStep
{
    /// <summary>
    /// Gets or sets the condition that this orchestration step listens for.
    /// The listen condition determines when this step should be activated and executed.
    /// </summary>
    [YamlMember(Alias = "listen_for")]
    [JsonPropertyName("listen_for")]
    public ListenCondition? ListenFor { get; set; }

    /// <summary>
    /// Gets or sets the list of actions to execute when the listen condition is satisfied.
    /// These actions define what should happen when the orchestration step is triggered.
    /// </summary>
    [YamlMember(Alias = "then")]
    [JsonPropertyName("then")]
    public List<ThenAction>? Then { get; set; }
}

/// <summary>
/// Represents a condition that an orchestration step listens for to determine when to execute its actions.
/// Listen conditions can be based on events, state changes, or complex logical expressions.
/// </summary>
public sealed class ListenCondition
{
    /// <summary>
    /// Gets or sets the specific event name to listen for.
    /// When specified, the condition will trigger when this event is emitted.
    /// </summary>
    [YamlMember(Alias = "event")]
    [JsonPropertyName("event")]
    public string? Event { get; set; }

    /// <summary>
    /// Gets or sets the source of the event being listened for.
    /// This specifies which node or component must emit the event for the condition to trigger.
    /// </summary>
    [YamlMember(Alias = "from")]
    [JsonPropertyName("from")]
    public string? From { get; set; }

    /// <summary>
    /// Gets or sets a custom condition expression for more complex logic.
    /// This allows for sophisticated conditional logic beyond simple event matching.
    /// </summary>
    [YamlMember(Alias = "condition")]
    [JsonPropertyName("condition")]
    public string? Condition { get; set; }

    /// <summary>
    /// Gets or sets a list of events that must all occur for the condition to be satisfied.
    /// This provides AND logic for multiple event requirements.
    /// </summary>
    [YamlMember(Alias = "all_of")]
    [JsonPropertyName("all_of")]
    public List<ListenEvent>? AllOf { get; set; }
}

/// <summary>
/// Represents a specific event to listen for in workflow orchestration.
/// Listen events specify both the event name and its source for precise event matching.
/// </summary>
public sealed class ListenEvent
{
    /// <summary>
    /// Gets or sets the name of the event to listen for.
    /// This identifies the specific type of event that should trigger the condition.
    /// </summary>
    [YamlMember(Alias = "event")]
    [JsonPropertyName("event")]
    public string Event { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the source identifier from which the event must originate.
    /// This ensures the event comes from the expected node or component.
    /// </summary>
    [YamlMember(Alias = "from")]
    [JsonPropertyName("from")]
    public string From { get; set; } = string.Empty;
}

/// <summary>
/// Represents an action to be executed as part of workflow orchestration logic.
/// Actions define what should happen when orchestration conditions are met.
/// </summary>
public sealed class ThenAction
{
    /// <summary>
    /// Gets or sets the type of action to be performed.
    /// The action type determines the specific operation (node invocation, state update, event emission).
    /// </summary>
    [YamlMember(Alias = "type")]
    [JsonPropertyName("type")]
    public ActionType Type { get; set; }

    /// <summary>
    /// Gets or sets the identifier of the node to execute when the action type is NodeInvocation.
    /// This specifies which workflow node should be activated.
    /// </summary>
    [YamlMember(Alias = "node")]
    [JsonPropertyName("node")]
    public string? Node { get; set; }

    /// <summary>
    /// Gets or sets the input mappings to pass to the invoked node.
    /// These inputs provide data that the target node needs for execution.
    /// </summary>
    [YamlMember(Alias = "inputs")]
    [JsonPropertyName("inputs")]
    public Dictionary<string, string>? Inputs { get; set; }

    /// <summary>
    /// Gets or sets the expression that resolves to messages to be passed to the node.
    /// This allows for dynamic message passing based on workflow state.
    /// </summary>
    [YamlMember(Alias = "messages_in")]
    [JsonPropertyName("messages_in")]
    public List<string>? MessagesIn { get; set; }

    /// <summary>
    /// Gets or sets the thread identifier to send the event to.
    /// This specifies which conversation thread should receive the action's output.
    /// </summary>
    [YamlMember(Alias = "thread")]
    [JsonPropertyName("thread")]
    public string? Thread { get; set; }

    /// <summary>
    /// Gets or sets the path to the variable to be updated when the action type is Update.
    /// This specifies which workflow variable should be modified.
    /// </summary>
    [YamlMember(Alias = "path")]
    [JsonPropertyName("path")]
    public string? Path { get; set; }

    /// <summary>
    /// Gets or sets the operation to be performed on the variable when the action type is Update.
    /// This determines how the variable's value should be changed.
    /// </summary>
    [YamlMember(Alias = "operation")]
    [JsonPropertyName("operation")]
    public StateUpdateOperations? Operation { get; set; }

    /// <summary>
    /// Gets or sets the value to be used in the update operation or as event payload.
    /// For updates, this is the value to set, increment by, or decrement by.
    /// </summary>
    [YamlMember(Alias = "value")]
    [JsonPropertyName("value")]
    public object? Value { get; set; }

    /// <summary>
    /// Gets or sets the type of message to emit when the action type is Emit.
    /// This specifies what kind of event should be generated by the action.
    /// </summary>
    [YamlMember(Alias = "event_type")]
    [JsonPropertyName("event_type")]
    public string? EmitMessageType { get; set; }

    /// <summary>
    /// Gets or sets the payload data to include with the emitted message.
    /// This provides the data content that will be sent with the emitted event.
    /// </summary>
    [YamlMember(Alias = "payload")]
    [JsonPropertyName("payload")]
    public Dictionary<string, string>? EmitMessagePayload { get; set; }

    /// <summary>
    /// Creates a new instance of the <see cref="ThenAction"/> class from a <see cref="KernelProcessEdge"/>.
    /// This factory method converts internal kernel edge representations to workflow action configurations.
    /// </summary>
    /// <param name="edge">The kernel process edge to convert.</param>
    /// <param name="defaultThread">The default thread identifier to use if none is specified.</param>
    /// <returns>A new <see cref="ThenAction"/> instance representing the edge's behavior.</returns>
    /// <exception cref="KernelException">Thrown when the edge target type is not supported.</exception>
    public static ThenAction FromKernelProcessEdge(KernelProcessEdge edge, string? defaultThread)
    {
        if (edge.OutputTarget is KernelProcessStateTarget stateTarget)
        {
            return new ThenAction
            {
                Type = ActionType.Update,
                Path = stateTarget.VariableUpdate.Path,
                Operation = stateTarget.VariableUpdate.Operation,
                Value = stateTarget.VariableUpdate.Value
            };
        }
        if (edge.OutputTarget is KernelProcessFunctionTarget functionTarget)
        {
            return new ThenAction()
            {
                Type = ActionType.NodeInvocation,
                Node = functionTarget.StepId == ProcessConstants.EndStepName ? "End" : functionTarget.StepId,
            };
        }
        if (edge.OutputTarget is KernelProcessEmitTarget emitTarget)
        {
            return new ThenAction
            {
                Type = ActionType.Emit,
                EmitMessageType = emitTarget.EventName,
                EmitMessagePayload = emitTarget.Payload,
            };
        }
        if (edge.OutputTarget is KernelProcessAgentInvokeTarget agentInvokeTarget)
        {
            return new ThenAction()
            {
                Type = ActionType.NodeInvocation,
                Node = agentInvokeTarget.StepId == ProcessConstants.EndStepName ? "End" : agentInvokeTarget.StepId,
                Inputs = agentInvokeTarget.InputEvals,
                MessagesIn = agentInvokeTarget.MessagesInEval,
                Thread = agentInvokeTarget.ThreadEval
            };
        }

        throw new KernelException("Unsupported target type");
    }
}

/// <summary>
/// Defines the types of actions that can be performed in workflow orchestration.
/// Action types determine what kind of operation should be executed when conditions are met.
/// </summary>
public enum ActionType
{
    /// <summary>
    /// An action that invokes a specific workflow node to execute its logic.
    /// Node invocation actions transfer control to another part of the workflow.
    /// </summary>
    NodeInvocation,

    /// <summary>
    /// An action that updates the value of a workflow variable or state.
    /// Update actions allow workflows to modify their internal state during execution.
    /// </summary>
    Update,

    /// <summary>
    /// An action that emits an event to notify other parts of the workflow.
    /// Emit actions provide a communication mechanism between workflow components.
    /// </summary>
    Emit
}

/// <summary>
/// Represents a version range specification for compatibility checking.
/// Version ranges allow workflows to specify which versions of components they are compatible with.
/// </summary>
public sealed class VersionRange
{
    /// <summary>
    /// Gets or sets the minimum version included in this range.
    /// The minimum version is inclusive, meaning this version is considered part of the range.
    /// </summary>
    [YamlMember(Alias = "min_version")]
    [JsonPropertyName("min_version")]
    public string MinVersion { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the maximum version excluded from this range.
    /// The maximum version is exclusive, meaning this version is not included in the range.
    /// </summary>
    [YamlMember(Alias = "max_version_exclusive")]
    [JsonPropertyName("max_version_exclusive")]
    public string MaxVersionExclusive { get; set; } = string.Empty;
}

/// <summary>
/// Represents the error handling configuration for a workflow.
/// Error handling defines how the workflow should respond to and recover from various types of errors.
/// </summary>
public sealed class ErrorHandling
{
    /// <summary>
    /// Gets or sets the specific error handling steps that respond to particular error conditions.
    /// These steps provide targeted error handling for specific scenarios or error types.
    /// </summary>
    [YamlMember(Alias = "on_error")]
    [JsonPropertyName("on_error")]
    public List<ErrorHandlingStep>? OnError { get; set; }

    /// <summary>
    /// Gets or sets the default actions to be taken when no specific error handling matches.
    /// Default actions provide fallback behavior for unexpected or unhandled error conditions.
    /// </summary>
    [YamlMember(Alias = "default")]
    [JsonPropertyName("default")]
    public List<ThenAction>? Default { get; set; }
}

/// <summary>
/// Represents a single error handling step that responds to specific error conditions.
/// Error handling steps provide conditional logic for responding to different types of errors.
/// </summary>
public sealed class ErrorHandlingStep
{
    /// <summary>
    /// Gets or sets the condition that determines when this error handling step should be activated.
    /// The listen condition specifies which error events or conditions trigger this step.
    /// </summary>
    [YamlMember(Alias = "listen_for")]
    [JsonPropertyName("listen_for")]
    public ErrorListenCondition? ListenFor { get; set; }

    /// <summary>
    /// Gets or sets the actions to execute when the error condition is met.
    /// These actions define the error recovery or handling logic for the specific error scenario.
    /// </summary>
    [YamlMember(Alias = "then")]
    [JsonPropertyName("then")]
    public List<ThenAction>? Then { get; set; }
}

/// <summary>
/// Represents a condition that triggers error handling logic in the workflow.
/// Error listen conditions specify which types of errors should activate error handling steps.
/// </summary>
public sealed class ErrorListenCondition
{
    /// <summary>
    /// Gets or sets the name of the error event to listen for.
    /// This identifies the specific type of error that should trigger the associated error handling actions.
    /// </summary>
    [YamlMember(Alias = "event")]
    [JsonPropertyName("event")]
    public string Event { get; set; } = string.Empty;
}
