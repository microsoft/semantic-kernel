// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines an agent.
/// </summary>
[ExcludeFromCodeCoverage]
public sealed class AgentDefinition
{
    /// <summary>
    /// Gets or sets the version of the schema being used.
    /// </summary>
    public string? Version
    {
        get => this._version;
        set
        {
            Verify.NotNull(value);
            this._version = value;
        }
    }

    /// <summary>
    /// Gets or sets the id of the deployed agent.
    /// </summary>
    public string? Id
    {
        get => this._id;
        set
        {
            Verify.NotNull(value);
            this._id = value;
        }
    }

    /// <summary>
    /// Gets or sets the type of the  agent.
    /// </summary>
    public string? Type
    {
        get => this._type;
        set
        {
            Verify.NotNull(value);
            this._type = value;
        }
    }

    /// <summary>
    /// Gets or sets the name of the  agent.
    /// </summary>
    public string? Name
    {
        get => this._name;
        set
        {
            Verify.NotNull(value);
            this._name = value;
        }
    }

    /// <summary>
    /// Gets or sets the description of the agent.
    /// </summary>
    public string? Description
    {
        get => this._description;
        set
        {
            Verify.NotNull(value);
            this._description = value;
        }
    }

    /// <summary>
    /// Gets or sets the instructions for the agent to use.
    /// </summary>
    public string? Instructions
    {
        get => this._instructions;
        set
        {
            Verify.NotNull(value);
            this._instructions = value;
        }
    }

    /// <summary>
    /// Gets or sets the metadata associated with the agent.
    /// </summary>
    public IDictionary<string, object?>? Metadata
    {
        get => this._metadata;
        set
        {
            Verify.NotNull(value);
            this._metadata = value;
        }
    }

    /// <summary>
    /// Gets or sets the model used by the agent.
    /// </summary>
    public ModelDefinition? Model
    {
        get => this._model;
        set
        {
            Verify.NotNull(value);
            this._model = value;
        }
    }

    /// <summary>
    /// Gets or sets the collection of input variables used by the agent.
    /// </summary>
    public IList<InputVariable> Inputs
    {
        get => this._inputs ??= [];
        set
        {
            Verify.NotNull(value);
            this._inputs = value;
        }
    }

    /// <summary>
    /// Gets or sets the collection of output variables supported by the agent.
    /// </summary>
    public IList<OutputVariable> Outputs
    {
        get => this._outputs ??= [];
        set
        {
            Verify.NotNull(value);
            this._outputs = value;
        }
    }

    /// <summary>
    /// Gets or sets the template options used by the agent.
    /// </summary>
    public TemplateOptions? Template
    {
        get => this._template;
        set
        {
            Verify.NotNull(value);
            this._template = value;
        }
    }

    /// <summary>
    /// Gets or sets the collection of tools used by the agent.
    /// </summary>
    public IList<AgentToolDefinition> Tools
    {
        get => this._tools ??= [];
        set
        {
            Verify.NotNull(value);
            this._tools = value;
        }
    }

    #region
    private string? _version;
    private string? _type;
    private string? _id;
    private string? _name;
    private string? _description;
    private string? _instructions;
    private IDictionary<string, object?>? _metadata;
    private ModelDefinition? _model;
    private IList<InputVariable>? _inputs;
    private IList<OutputVariable>? _outputs;
    private TemplateOptions? _template;
    private IList<AgentToolDefinition>? _tools;
    #endregion
}
