// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;

namespace Microsoft.SemanticKernel.SemanticFunctions;

/// <summary>
/// Prompt template.
/// </summary>
public sealed class PromptTemplate : IPromptTemplate
{
    private readonly string _template;
    private readonly IPromptTemplateEngine _templateEngine;

    // ReSharper disable once NotAccessedField.Local
    private readonly ILogger _log = NullLogger.Instance;

    // ReSharper disable once NotAccessedField.Local
    private readonly PromptTemplateConfig _promptConfig;

    /// <summary>
    /// Constructor for PromptTemplate.
    /// </summary>
    /// <param name="template">Template.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="kernel">Kernel in which template is to take effect.</param>
    public PromptTemplate(string template, PromptTemplateConfig promptTemplateConfig, IKernel kernel)
        : this(template, promptTemplateConfig, kernel.PromptTemplateEngine, kernel.Log)
    {
    }

    /// <summary>
    /// Constructor for PromptTemplate.
    /// </summary>
    /// <param name="template">Template.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="promptTemplateEngine">Prompt template engine.</param>
    /// <param name="log">Optional logger for prompt template.</param>
    public PromptTemplate(
        string template,
        PromptTemplateConfig promptTemplateConfig,
        IPromptTemplateEngine promptTemplateEngine,
        ILogger? log = null)
    {
        this._template = template;
        this._templateEngine = promptTemplateEngine;
        this._promptConfig = promptTemplateConfig;
        if (log != null) { this._log = log; }
    }

    /// <summary>
    /// Get the list of parameters used by the function, using JSON settings and template variables.
    /// TODO: consider caching results - though cache invalidation will add extra complexity
    /// </summary>
    /// <returns>List of parameters</returns>
    public IList<ParameterView> GetParameters()
    {
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        // Parameters from config.json
        List<ParameterView> result = new();
        foreach (PromptTemplateConfig.InputParameter? p in this._promptConfig.Input.Parameters)
        {
            if (p == null) { continue; }

            result.Add(new ParameterView
            {
                Name = p.Name,
                Description = p.Description,
                DefaultValue = p.DefaultValue
            });

            seen.Add(p.Name);
        }

        // Parameters from the template
        List<VarBlock> listFromTemplate = this._templateEngine.ExtractBlocks(this._template)
            .Where(x => x.Type == BlockTypes.Variable)
            .Select(x => (VarBlock)x)
            .Where(x => x != null)
            .ToList();

        foreach (VarBlock x in listFromTemplate)
        {
            if (seen.Contains(x.Name)) { continue; }

            result.Add(new ParameterView { Name = x.Name });
            seen.Add(x.Name);
        }

        return result;
    }

    /// <summary>
    /// Render the template using the information in the context
    /// </summary>
    /// <param name="executionContext">Kernel execution context helpers</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Prompt rendered to string</returns>
    public async Task<string> RenderAsync(SKContext executionContext, CancellationToken cancellationToken)
    {
        return await this._templateEngine.RenderAsync(this._template, executionContext, cancellationToken).ConfigureAwait(false);
    }
}
