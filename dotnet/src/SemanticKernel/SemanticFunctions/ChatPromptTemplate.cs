// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json.Nodes;
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
public sealed class ChatPromptTemplate : IChatPromptTemplate
{
    private readonly string _template;
    private readonly IPromptTemplateEngine _templateEngine;

    // ReSharper disable once NotAccessedField.Local
    private readonly ILogger _log = NullLogger.Instance;

    // ReSharper disable once NotAccessedField.Local
    private readonly ChatPromptTemplateConfig _promptConfig;

    private JsonArray _messages; 

    /// <summary>
    /// Constructor for PromptTemplate.
    /// </summary>
    /// <param name="template">Template.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="kernel">Kernel in which template is to take effect.</param>
    public ChatPromptTemplate(string template, ChatPromptTemplateConfig promptTemplateConfig, IKernel kernel)
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
    public ChatPromptTemplate(
        string template,
        ChatPromptTemplateConfig promptTemplateConfig,
        IPromptTemplateEngine promptTemplateEngine,
        ILogger? log = null)
    {
        this._template = template;
        this._templateEngine = promptTemplateEngine;
        this._promptConfig = promptTemplateConfig;
        this._messages = new JsonArray();
        if (log != null) { this._log = log; }
    }

    private JsonObject GetJsonObject(string message, string role)
    {
        var jObj = new JsonObject();
        jObj.Add("role", role);
        jObj.Add("content", message);
        return jObj;
    }

    public void AddSystemMessage(string message)
    {
        this.AddMessage(message, "system");
    }

    public void AddUserMessage(string message)
    {
        this.AddMessage(message, "user");
    }

    public void AddAssistantMessage(string message)
    {
        this.AddMessage(message, "assistant");
    }

    public void AddMessage(string role, string message)
    {
        this._messages.Add(this.GetJsonObject(message, role));
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
        foreach (ChatPromptTemplateConfig.InputParameter? p in this._promptConfig.Input.Parameters)
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
    /// <returns>Prompt rendered to string</returns>
    public async Task<JsonArray> RenderMessagesAsync(SKContext executionContext)
    {
        var rendered_messages = new JsonArray();

        foreach (var message in this._messages)
        {
            rendered_messages.Add(message);
        }
        var latest_user_message = await this._templateEngine.RenderAsync(this._template, executionContext);
        var jObj = new JsonObject();
        jObj.Add("role", "user");
        jObj.Add("content", latest_user_message);
        rendered_messages.Add(jObj);
        
        return rendered_messages;
    }
}
