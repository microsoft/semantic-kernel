// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel.SemanticFunctions;

/// <summary>
/// Prompt template.
/// </summary>
public sealed class PromptTemplate : IPromptTemplate
{
    private readonly string _template;
    private readonly IPromptTemplateEngineProvider _templateEngineProvider;

    // ReSharper disable once NotAccessedField.Local
    private readonly PromptTemplateConfig _promptConfig;

    /// <summary>
    /// Constructor for PromptTemplate.
    /// </summary>
    /// <param name="template">Template.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="kernel">Kernel in which template is to take effect.</param>
    public PromptTemplate(string template, PromptTemplateConfig promptTemplateConfig, IKernel kernel)
        : this(template, promptTemplateConfig, kernel.PromptTemplateEngineProvider)
    {
    }

    /// <summary>
    /// Constructor for PromptTemplate.
    /// </summary>
    /// <param name="template">Template.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="promptTemplateEngineProvider">Prompt template engine.</param>
    public PromptTemplate(
        string template,
        PromptTemplateConfig promptTemplateConfig,
        IPromptTemplateEngineProvider promptTemplateEngineProvider)
    {
        this._template = template;
        this._templateEngineProvider = promptTemplateEngineProvider;
        this._promptConfig = promptTemplateConfig;
    }

    /// <summary>
    /// Get the list of parameters used by the function, using JSON settings and template variables.
    /// TODO: consider caching results - though cache invalidation will add extra complexity
    /// </summary>
    /// <returns>List of parameters</returns>
    public IList<ParameterView> GetParameters()
    {
        // Parameters from config.json
        Dictionary<string, ParameterView> result = new(StringComparer.OrdinalIgnoreCase);
        foreach (var p in this._promptConfig.Input.Parameters)
        {
            result[p.Name] = new ParameterView(p.Name, p.Description, p.DefaultValue);
        }

        return result.Values.ToList();
    }

    /// <summary>
    /// Render the template using the information in the context
    /// </summary>
    /// <param name="executionContext">Kernel execution context helpers</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Prompt rendered to string</returns>
    public async Task<string> RenderAsync(SKContext executionContext, CancellationToken cancellationToken)
    {
        var templateEngine = this._templateEngineProvider.Create(this._promptConfig.Format);
        return await templateEngine.RenderAsync(this._template, executionContext, cancellationToken).ConfigureAwait(false);
    }
}
