// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Internal;

/// <summary>
/// Fluent builder for initializing an <see cref="IAssistant"/> instance.
/// </summary>
internal sealed class AssistantBuilder : IAssistantBuilder
{
    private readonly IOpenAIRestContext _context;
    private readonly AssistantModel _model;

    /// <summary>
    /// Initializes a new instance of the <see cref="AssistantBuilder"/> class.
    /// </summary>
    public AssistantBuilder(IOpenAIRestContext restContext)
    {
        this._context = restContext;
        this._model = new AssistantModel();
    }

    /// <inheritdoc/>
    public async Task<IAssistant> BuildAsync(CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(this._model.Model))
        {
            throw new SKException("Model must be defined for assistant.");
        }

        if (string.IsNullOrWhiteSpace(this._model.Instructions))
        {
            throw new SKException("Instructions must be defined for assistant.");
        }

        return await Assistant.CreateAsync(this._context, this._model, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithDescription(string? description)
    {
        this._model.Description = description;

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithInstructions(string instructions)
    {
        this._model.Instructions = instructions;

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithMetadata(string key, object value)
    {
        this._model.Metadata[key] = value;

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithMetadata(IDictionary<string, object> metadata)
    {
        foreach (var kvp in metadata)
        {
            this._model.Metadata[kvp.Key] = kvp.Value;
        }

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithModel(string model)
    {
        this._model.Model = model;

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithName(string? name)
    {
        this._model.Name = name;

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithTool(FunctionView tool)
    {
        var functionName = tool.PluginName.IsNullOrWhitespace() ? tool.Name : $"{tool.PluginName}-{tool.Name}"; // TODO: @chris - consume & verify

        var required = new List<string>(tool.Parameters.Count);
        var parameters =
            tool.Parameters.ToDictionary(
                p => p.Name,
                p =>
                {
                    if (p.IsRequired ?? false)
                    {
                        required.Add(p.Name);
                    }

                    return
                        new OpenAIParameter
                        {
                            Type = p.Type?.Name ?? nameof(System.String),
                            Description = p.Description,
                        };
                });

        var payload =
            new AssistantModel.ToolModel
            {
                Type = "function",
                Function =
                    new()
                    {
                        Name = functionName,
                        Description = tool.Description,
                        Parameters =
                        {
                            Properties = parameters,
                            Required = required,
                        }
                    },
            };

        this._model.Tools.Add(payload);

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithTools(IEnumerable<FunctionView> tools)
    {
        foreach (var tool in tools)
        {
            this.WithTool(tool);
        }

        return this;
    }

    /// <inheritdoc/>
    public IAssistantBuilder WithTools(IKernel kernel)
    {
        this.WithTools(kernel.Functions.GetFunctionViews());

        return this;
    }
}
