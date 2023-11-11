// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using Microsoft.Extensions.Logging;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Assistant - Customizable entity that can be configured to respond to users’ messages
/// </summary>
public class Assistant : IPlugin
{
    private readonly Kernel _kernel;
    private readonly List<IPlugin> _plugins;
    private readonly List<IAIService> _aiServices;
    private readonly HttpClient _client = new();
    private readonly string _apiKey;
    private readonly string _model;
    private readonly List<ISKFunction> _functions;

    /// <summary>
    /// Assistant ID
    /// </summary>
    public string Id { get; private set; }

    /// <summary>
    /// Assistant name
    /// </summary>
    public string Name { get; private set; }

    /// <summary>
    /// Assistant description
    /// </summary>
    public string Description { get; private set; }

    /// <summary>
    /// System instructions that the assistant uses
    /// </summary>
    public string Instructions { get; private set; }

    IEnumerable<ISKFunction> IPlugin.Functions
    {
        get { return this._functions; }
    }

    // Allows the creation of an assistant from a YAML file
    /*public static Assistant FromConfiguration(
        string configurationFile,
        List<IAIService>? aiServices = null,
        List<IPlugin>? plugins = null,
        List<IPromptTemplateEngine>? promptTemplateEngines = null
    )
    {
        // Open the YAML configuration file
        var yamlContent = File.ReadAllText(configurationFile);
        var deserializer = new DeserializerBuilder()
            .WithTypeConverter(new ExecutionSettingsModelConverter())
            .Build();
        AssistantKernelModel assistantKernelModel = deserializer.Deserialize<AssistantKernelModel>(yamlContent);

        // Create the assistant kernel
        return new Assistant(
            assistantKernelModel.Name,
            assistantKernelModel.Description,
            assistantKernelModel.Template,
            aiServices,
            plugins,
            promptTemplateEngines
        );
    }*/

    public Assistant(
        string name,
        string description,
        string instructions,
        List<IAIService>? aiServices = null,
        List<IPlugin>? plugins = null,
        List<IPromptTemplateEngine>? promptTemplateEngines = null
    )
    {
        this.Name = name;
        this.Description = description;
        this.Instructions = instructions;
        this._aiServices = aiServices ?? new List<IAIService>();

        // Grab the first AI service for the apiKey and model for the Assistants API
        // This requires that the API key be made internal so it can be accessed here
        this._apiKey = string.Empty;// ((OpenAIChatCompletion)this._aiServices[0]).ApiKey;
        this._model = string.Empty;// ((OpenAIChatCompletion)this._aiServices[0]).ModelId;

        // Create a function collection using the plugins
        var functionCollection = new FunctionCollection();
        this._plugins = plugins ?? new List<IPlugin>();
        if (plugins != null)
        {
            foreach (IPlugin plugin in plugins)
            {
                foreach (ISKFunction function in plugin.Functions)
                {
                    functionCollection.AddFunction(function);
                }
            }
        }

        // Create an AI service provider using the AI services
        var services = new AIServiceCollection();
        Dictionary<Type, string> defaultIds = new() { };

        /*if (aiServices != null)
        {
            foreach (IAIService aiService in aiServices)
            {
                if (aiService is AzureOpenAIChatCompletion azureOpenAIChatCompletion)
                {
                    services.SetService<IAIService>(azureOpenAIChatCompletion.ModelId, azureOpenAIChatCompletion, true);
                }
            }
        }*/

        // Initialize the prompt template engine
        IPromptTemplateEngine? promptTemplateEngine = default;
        if (promptTemplateEngines != null && promptTemplateEngines.Count > 0)
        {
            promptTemplateEngine = promptTemplateEngines[0];
        }
        /*else
        {
            promptTemplateEngine = new HandlebarsPromptTemplateEngine();
        }*/

        // Create underlying kernel
        this._kernel = new SemanticKernel.Kernel(
            functionCollection,
            services.Build(),
            promptTemplateEngine,
            null!,
            NullHttpHandlerFactory.Instance,
            null
        );

        // Create functions so other kernels can use this kernel as a plugin
        // TODO: make it possible for the ask function to have additional parameters based on the instruction template
        /*this._functions = new List<ISKFunction>
        {
            NativeFunction.Create(
                this.AskAsync,
                null,
                null,
                this.Name,
                "Ask",
                this.Description,
                new List<ParameterView>
                {
                    new ParameterView("ask", "The question to ask the assistant"),
                },
                null
            )
        };*/
    }

    public List<FunctionView> GetFunctionViews()
    {
        var functionViews = new List<FunctionView>();

        foreach (var plugin in this._plugins)
        {
            foreach (var function in plugin.Functions)
            {
                FunctionView initialFunctionView = function.Describe();
                functionViews.Add(new FunctionView(
                    initialFunctionView.Name,
                    plugin.Name,
                    initialFunctionView.Description,
                    initialFunctionView.Parameters
                ));
            }
        }

        return functionViews;
    }


    public ISKFunction RegisterCustomFunction(ISKFunction customFunction)
    {
        return this._kernel.RegisterCustomFunction(customFunction);
    }

    public SKContext CreateNewContext(ContextVariables? variables = null, IReadOnlyFunctionCollection? functions = null, ILoggerFactory? loggerFactory = null, CultureInfo? culture = null)
    {
        return this._kernel.CreateNewContext(variables, functions, loggerFactory, culture);
    }

    public T GetService<T>(string? name = null) where T : IAIService
    {
        return this._kernel.GetService<T>(name);
    }

    public IAIService GetDefaultService(string? name = null)
    {
        return this._aiServices[0];
    }

    public List<IAIService> GetAllServices()
    {
        return this._aiServices;
    }

    private async Task InitializeAgentAsync()
    {
        // Create new agent if it doesn't exist
        if (this.Id == null)
        {
            var requestData = new
            {
                //model = ((AIService)this._aiServices[0]).ModelId
            };

            string url = "https://api.openai.com/v1/assistants";
            using var httpRequestMessage = HttpRequest.CreatePostRequest(url, requestData);

            httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
            httpRequestMessage.Headers.Add("OpenAI-Beta", "assistants=v1");

            using var response = await this._client.SendAsync(httpRequestMessage).ConfigureAwait(false);
            string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            AssistantModel assistantModel = JsonSerializer.Deserialize<AssistantModel>(responseBody)!;
            this.Id = assistantModel.Id;
        }
    }

    public IPromptTemplateEngine PromptTemplateEngine => this._kernel.PromptTemplateEngine;

    public IReadOnlyFunctionCollection Functions => this._kernel.Functions;

    public IDelegatingHandlerFactory HttpHandlerFactory => this._kernel.HttpHandlerFactory;
}
