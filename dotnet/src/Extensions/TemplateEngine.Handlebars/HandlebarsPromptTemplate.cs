// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using HandlebarsDotNet;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Handlebars;

internal class HandlebarsPromptTemplate : IPromptTemplate
{
    /// <summary>
    /// Constructor for PromptTemplate.
    /// </summary>
    /// <param name="templateString">Prompt template string.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration</param>
    /// <param name="loggerFactory">Logger factory</param>
    public HandlebarsPromptTemplate(string templateString, PromptTemplateConfig promptTemplateConfig, ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this._logger = this._loggerFactory.CreateLogger(typeof(HandlebarsPromptTemplate));
        this._templateString = templateString;
        this._promptTemplateConfig = promptTemplateConfig;
        this._parameters = new(() => this.InitParameters());
    }

    /// <inheritdoc/>
    public IReadOnlyList<ParameterView> Parameters => this._parameters.Value;

    /// <inheritdoc/>
    public async Task<string> RenderAsync(SKContext executionContext, CancellationToken cancellationToken = default)
    {
        var handlebars = HandlebarsDotNet.Handlebars.Create();

        var functionViews = executionContext.Functions.GetFunctionViews();

        foreach (FunctionView functionView in functionViews)
        {
            var skfunction = executionContext.Functions.GetFunction(functionView.PluginName, functionView.Name);
#pragma warning disable VSTHRD101 // Avoid unsupported async delegates
            handlebars.RegisterHelper($"{functionView.PluginName}_{functionView.Name}", async (writer, hcontext, parameters) =>
            {
                var result = await skfunction.InvokeAsync(executionContext).ConfigureAwait(true);
                writer.WriteSafeString(result.GetValue<string>());
            });
#pragma warning restore VSTHRD101 // Avoid unsupported async delegates
        }

        var template = handlebars.Compile(this._templateString);

        var prompt = template(this.GetVariables(executionContext));

        return await Task.FromResult(prompt).ConfigureAwait(true);
    }

    #region private
    private readonly ILoggerFactory _loggerFactory;
    private readonly ILogger _logger;
    private readonly string _templateString;
    private readonly PromptTemplateConfig _promptTemplateConfig;
    private readonly Lazy<IReadOnlyList<ParameterView>> _parameters;

    private List<ParameterView> InitParameters()
    {
        // Parameters from prompt template configuration
        Dictionary<string, ParameterView> result = new(this._promptTemplateConfig.Input.Parameters.Count, StringComparer.OrdinalIgnoreCase);
        foreach (var p in this._promptTemplateConfig.Input.Parameters)
        {
            result[p.Name] = new ParameterView(p.Name, p.Description, p.DefaultValue);
        }

        return result.Values.ToList();
    }

    private Dictionary<string, string> GetVariables(SKContext executionContext)
    {
        Dictionary<string, string> variables = new();
        foreach (var p in this._promptTemplateConfig.Input.Parameters)
        {
            if (!string.IsNullOrEmpty(p.DefaultValue))
            {
                variables[p.Name] = p.DefaultValue;
            }
        }

        foreach (var kvp in executionContext.Variables)
        {
            variables.Add(kvp.Key, kvp.Value);
        }

        return variables;
    }

    #endregion

}
