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
    private readonly IPromptTemplateEngine _templateEngine;

    // ReSharper disable once NotAccessedField.Local
    private readonly PromptTemplateConfig _promptConfig;

    /// <summary>
    /// Constructor for PromptTemplate.
    /// </summary>
    /// <param name="template">Template.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="kernel">Kernel in which template is to take effect.</param>
    public PromptTemplate(string template, PromptTemplateConfig promptTemplateConfig, IKernel kernel)
        : this(template, promptTemplateConfig, kernel.PromptTemplateEngine)
    {
    }

    /// <summary>
    /// Constructor for PromptTemplate.
    /// </summary>
    /// <param name="template">Template.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="promptTemplateEngine">Prompt template engine.</param>
    public PromptTemplate(
        string template,
        PromptTemplateConfig promptTemplateConfig,
        IPromptTemplateEngine promptTemplateEngine)
    {
        this._template = template;
        this._templateEngine = promptTemplateEngine;
        this._promptConfig = promptTemplateConfig;

        this._params = new(() => this.InitParameters());
    }

    /// <summary>
    /// The list of parameters used by the function, using JSON settings and template variables.
    /// </summary>
    /// <returns>List of parameters</returns>
    public IReadOnlyList<ParameterView> Parameters
        => this._params.Value;

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

    private Lazy<IReadOnlyList<ParameterView>> _params;

    private List<ParameterView> InitParameters()
    {
        // Parameters from config.json
        Dictionary<string, ParameterView> result = new(this._promptConfig.Input.Parameters.Count, StringComparer.OrdinalIgnoreCase);
        foreach (var p in this._promptConfig.Input.Parameters)
        {
            result[p.Name] = new ParameterView(p.Name, p.Description, p.DefaultValue);
        }

        return result.Values.ToList();
    }
}
