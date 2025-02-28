// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using System.Web;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;
using Spectre.Console;
using Spectre.Console.Cli;
using Spectre.Console.Json;

public class DemoCommand : AsyncCommand<DemoCommand.Settings>
{
    public class Settings : CommandSettings
    {
        [CommandOption("--debug")]
        public bool? EnableLogging { get; set; }
    }

    private static readonly Lazy<IConfigurationRoot> s_configurationRoot = new(() =>
        new ConfigurationBuilder()
            .AddJsonFile("appsettings.Development.json", optional: true, reloadOnChange: true)
            .Build());

    private static IConfigurationRoot configuration => s_configurationRoot.Value;

    private const string CopilotAgentPluginsDirectory = "CopilotAgentPlugins";
    public override async Task<int> ExecuteAsync(CommandContext context, Settings settings)
    {
        var availableCopilotPlugins = Directory.GetDirectories($"../../../Concepts/Resources/Plugins/{CopilotAgentPluginsDirectory}");

        var selectedKernelName = AnsiConsole.Prompt(
            new SelectionPrompt<string>()
                .Title("[green]SELECT KERNEL TO USE:[/]")
                .AddChoices([
                    "azureopenai",
                    "openai",
                    "ollama"
                ]));

        var enableLogging = settings.EnableLogging == true;

        var (kernel, promptSettings) = selectedKernelName switch
        {
            "azureopenai" => InitializeAzureOpenAiKernel(configuration, enableLogging: enableLogging),
            "openai" => InitializeOpenAiKernel(configuration, enableLogging: enableLogging),
            "ollama" => InitializeKernelForOllama(configuration, enableLogging: enableLogging),
            _ => throw new InvalidOperationException($"Invalid kernel selection. {selectedKernelName} is not a valid kernel.")
        };
        kernel.AutoFunctionInvocationFilters.Add(new ExpectedSchemaFunctionFilter());

        while (true)
        {
            const string LOAD_COPILOT_AGENT_PLUGIN = "Load Copilot Agent plugin(s)";
            const string LOAD_ALL_COPILOT_AGENT_PLUGINS = "Load all available Copilot Agent plugins";
            const string UNLOAD_ALL_PLUGINS = "Unload all plugins";
            const string SHOW_COPILOT_AGENT_MANIFEST = "Show Copilot Agent manifest";
            const string EXECUTE_GOAL = "Execute a goal";
            const string LIST_LOADED_PLUGINS = "List loaded plugins";
            const string LIST_LOADED_PLUGINS_WITH_FUNCTIONS = "List loaded plugins with functions";
            const string LIST_LOADED_PLUGINS_WITH_FUNCTIONS_AND_PARAMETERS = "List loaded plugins with functions and parameters";
            const string EXIT = "Exit";
            AnsiConsole.WriteLine();
            var selection = AnsiConsole.Prompt(
                new SelectionPrompt<string>()
                    .Title("SELECT AN OPTION:")
                    .PageSize(10)
                    .AddChoices([LOAD_COPILOT_AGENT_PLUGIN, LOAD_ALL_COPILOT_AGENT_PLUGINS, UNLOAD_ALL_PLUGINS, SHOW_COPILOT_AGENT_MANIFEST, EXECUTE_GOAL, LIST_LOADED_PLUGINS, LIST_LOADED_PLUGINS_WITH_FUNCTIONS, LIST_LOADED_PLUGINS_WITH_FUNCTIONS_AND_PARAMETERS, EXIT]));

            switch (selection)
            {
                case LOAD_COPILOT_AGENT_PLUGIN:
                    await this.LoadCopilotAgentPluginAsync(kernel, configuration, availableCopilotPlugins).ConfigureAwait(false);
                    break;
                case LOAD_ALL_COPILOT_AGENT_PLUGINS:
                    await this.LoadCopilotAgentPluginAsync(kernel, configuration, availableCopilotPlugins, loadAllPlugins: true).ConfigureAwait(false);
                    break;
                case UNLOAD_ALL_PLUGINS:
                    kernel.Plugins.Clear();
                    AnsiConsole.MarkupLine("[bold green]All plugins unloaded successfully.[/]");
                    break;
                case SHOW_COPILOT_AGENT_MANIFEST:
                    await this.ShowCopilotAgentManifestAsync(availableCopilotPlugins).ConfigureAwait(false);
                    break;
                case EXECUTE_GOAL:
                    await this.ExecuteGoalAsync(kernel, promptSettings).ConfigureAwait(false);
                    break;
                case LIST_LOADED_PLUGINS:
                    this.ListLoadedPlugins(kernel);
                    break;
                case LIST_LOADED_PLUGINS_WITH_FUNCTIONS:
                    this.ListLoadedPlugins(kernel, withFunctions: true);
                    break;
                case LIST_LOADED_PLUGINS_WITH_FUNCTIONS_AND_PARAMETERS:
                    this.ListLoadedPlugins(kernel, withFunctions: true, withParameters: true);
                    break;
                case EXIT:
                    return 0;
                default:
                    AnsiConsole.MarkupLine("[red]Invalid selection.[/]");
                    break;
            }
        }
    }
    private async Task LoadCopilotAgentPluginAsync(Kernel kernel, IConfigurationRoot configuration, string[] availableCopilotPlugins, bool loadAllPlugins = false)
    {
        await this.LoadPluginAsync(kernel, configuration, availableCopilotPlugins, this.AddCopilotAgentPluginAsync, loadAllPlugins).ConfigureAwait(false);
    }

    private async Task ShowCopilotAgentManifestAsync(string[] availableCopilotPlugins)
    {
        await this.ShowManifestAsync(availableCopilotPlugins, GetCopilotAgentManifestPath).ConfigureAwait(false);
    }
    private static string GetCopilotAgentManifestPath(string name) => Path.Combine(Directory.GetCurrentDirectory(), "../../../Concepts/Resources/Plugins", CopilotAgentPluginsDirectory, name, $"{name[..^6].ToLowerInvariant()}-apiplugin.json");

    private async Task ShowManifestAsync(string[] availableApiManifestPlugins, Func<string, string> nameLookup)
    {
        var selectedPluginName = AnsiConsole.Prompt(
            new SelectionPrompt<string>()
                .Title("[green]SELECT PLUGIN TO SHOW API MANIFEST:[/]")
                .PageSize(10)
                .AddChoices(availableApiManifestPlugins.Select(p => p.Split(Path.DirectorySeparatorChar).Last())));

        var apiManifest = await File.ReadAllTextAsync(nameLookup(selectedPluginName)).ConfigureAwait(false);
        var jsonText = new JsonText(apiManifest);
        AnsiConsole.Write(
            new Panel(jsonText)
                .Header(selectedPluginName)
                .Collapse()
                .RoundedBorder()
                .BorderColor(Color.Yellow));
    }
    private void ListLoadedPlugins(Kernel kernel, bool withFunctions = false, bool withParameters = false)
    {
        var root = new Tree("[bold]LOADED PLUGINS[/]");
        foreach (var plugin in kernel.Plugins)
        {
            var pluginNode = root.AddNode($"[bold green]{plugin.Name}[/]");
            if (!withFunctions)
            {
                continue;
            }

            foreach (var function in plugin.GetFunctionsMetadata())
            {
                var functionNode = pluginNode.AddNode($"[italic green]{function.Name}[/]{Environment.NewLine}  {function.Description}");

                if (!withParameters)
                {
                    continue;
                }

                if (function.Parameters.Count == 0)
                {
                    functionNode.AddNode("[red]No parameters[/]");
                    continue;
                }

                foreach (var param in function.Parameters)
                {
                    functionNode.AddNode($"[italic green]{param.Name}[/]{Environment.NewLine}  {param.Description}");
                }
            }
        }

        if (kernel.Plugins.Count == 0)
        {
            root.AddNode("[red]No plugin loaded.[/]");
        }

        AnsiConsole.Write(root);
    }

    private async Task LoadPluginAsync(Kernel kernel, IConfigurationRoot configuration, IEnumerable<string> availableManifestPlugins, Func<Kernel, IConfigurationRoot, string, Task> loader, bool loadAllPlugins = false)
    {
        // get unloaded plugins
        var pluginNames = availableManifestPlugins.Select(p => p.Split(Path.DirectorySeparatorChar).Last())
            .Where(p => !kernel.Plugins.Any(loadedPlugin => p == loadedPlugin.Name))
            .ToList();

        if (pluginNames.Count == 0)
        {
            AnsiConsole.MarkupLine("[red]No additional plugin available to load.[/]");
            return;
        }

        var selectedPluginNames = loadAllPlugins ?
            pluginNames :
            AnsiConsole.Prompt(
                new MultiSelectionPrompt<string>()
                    .Title("[green]SELECT PLUGINS TO LOAD:[/]")
                    .PageSize(10)
                    .AddChoices(pluginNames));

        foreach (var selectedPluginName in selectedPluginNames)
        {
            await AnsiConsole.Status()
                .Spinner(Spinner.Known.Dots)
                .SpinnerStyle(Style.Parse("yellow"))
                .StartAsync($"loading {selectedPluginName}...", async ctx =>
                {
                    await loader(kernel, configuration, selectedPluginName).ConfigureAwait(false);
                }).ConfigureAwait(false);
        }
    }

    private async Task ExecuteGoalAsync(Kernel kernel, PromptExecutionSettings promptExecutionSettings)
    {
        var goal = AnsiConsole.Ask<string>("Enter your goal:");
        var result = await kernel.InvokePromptAsync(goal, new KernelArguments(promptExecutionSettings)).ConfigureAwait(false);
        var panel = new Panel($"[bold]Result[/]{Environment.NewLine}{Environment.NewLine}[green italic]{Markup.Escape(result.ToString())}[/]");
        AnsiConsole.Write(panel);
    }

    private static (Kernel, PromptExecutionSettings) InitializeKernelForOllama(IConfiguration configuration, bool enableLogging)
    {
        var engineConfig = configuration.GetSection("Ollama");
        var chatModelId = engineConfig["ChatModelId"];
        var endpoint = engineConfig["Endpoint"];
        if (string.IsNullOrEmpty(chatModelId) || string.IsNullOrEmpty(endpoint))
        {
            throw new InvalidOperationException("Please provide valid Ollama configuration in appsettings.Development.json file.");
        }

        var builder = Kernel.CreateBuilder();
        if (enableLogging)
        {
            builder.Services.AddLogging(loggingBuilder =>
                {
                    loggingBuilder.AddFilter(level => true);
                    loggingBuilder.AddProvider(new SemanticKernelLoggerProvider());
                });
        }
#pragma warning disable SKEXP0070 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
#pragma warning disable SKEXP0001
        return (builder.AddOllamaChatCompletion(
                chatModelId,
                new Uri(endpoint)).Build(),
                new OllamaPromptExecutionSettings
                {
                    FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(
                    options: new FunctionChoiceBehaviorOptions
                    {
                        AllowStrictSchemaAdherence = true
                    }
                )
                });
#pragma warning restore SKEXP0001
#pragma warning restore SKEXP0070 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    }

    private static (Kernel, PromptExecutionSettings) InitializeAzureOpenAiKernel(IConfiguration configuration, bool enableLogging)
    {
        var azureOpenAIConfig = configuration.GetSection("AzureOpenAI");
        var apiKey = azureOpenAIConfig["ApiKey"];
        var chatDeploymentName = azureOpenAIConfig["ChatDeploymentName"];
        var chatModelId = azureOpenAIConfig["ChatModelId"];
        var endpoint = azureOpenAIConfig["Endpoint"];

        if (string.IsNullOrEmpty(apiKey) || string.IsNullOrEmpty(chatDeploymentName) || string.IsNullOrEmpty(chatModelId) || string.IsNullOrEmpty(endpoint))
        {
            throw new InvalidOperationException("Please provide valid AzureOpenAI configuration in appsettings.Development.json file.");
        }

        var builder = Kernel.CreateBuilder();
        if (enableLogging)
        {
            builder.Services.AddLogging(loggingBuilder =>
                {
                    loggingBuilder.AddFilter(level => true);
                    loggingBuilder.AddProvider(new SemanticKernelLoggerProvider());
                });
        }
        return (builder.AddAzureOpenAIChatCompletion(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey,
                modelId: chatModelId).Build(),
#pragma warning disable SKEXP0001
                new AzureOpenAIPromptExecutionSettings
                {
                    FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(
                    options: new FunctionChoiceBehaviorOptions
                    {
                        AllowStrictSchemaAdherence = true
                    }
                )
                });
#pragma warning restore SKEXP0001
    }

    public static (Kernel, PromptExecutionSettings) InitializeOpenAiKernel(IConfiguration configuration, bool enableLogging)
    {
        // Extract configuration settings specific to OpenAI
        var openAIConfig = configuration.GetSection("OpenAI");
        var apiKey = openAIConfig["ApiKey"];
        var modelId = openAIConfig["ModelId"];

        if (string.IsNullOrEmpty(apiKey) || string.IsNullOrEmpty(modelId))
        {
            throw new InvalidOperationException("Please provide valid OpenAI configuration in appsettings.Development.json file.");
        }

        var builder = Kernel.CreateBuilder();
        if (enableLogging)
        {
            builder.Services.AddLogging(loggingBuilder =>
                {
                    loggingBuilder.AddFilter(level => true);
                    loggingBuilder.AddProvider(new SemanticKernelLoggerProvider());
                });
        }

        return (builder.AddOpenAIChatCompletion(
            apiKey: apiKey,
            modelId: modelId).Build(),
#pragma warning disable SKEXP0001
            new OpenAIPromptExecutionSettings
            {
                FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(
                options: new FunctionChoiceBehaviorOptions
                {
                    AllowStrictSchemaAdherence = true
                })
            });
#pragma warning restore SKEXP0001

    }
    private static AuthenticateRequestAsyncCallback? GetApiKeyAuthProvider(string apiKey, string parameterName, bool inHeader)
    {
        return async (request, cancellationToken) =>
        {
            if (inHeader)
            {
                request.Headers.Add(parameterName, apiKey);
            }
            else
            {
                var uriBuilder = new UriBuilder(request.RequestUri ?? throw new InvalidOperationException("The request URI is null."));
                var query = HttpUtility.ParseQueryString(uriBuilder.Query);
                query[parameterName] = apiKey;
                uriBuilder.Query = query.ToString();
                request.RequestUri = uriBuilder.Uri;
            }

            await Task.CompletedTask.ConfigureAwait(false);
        };
    }

    private readonly BearerAuthenticationProviderWithCancellationToken _bearerAuthenticationProviderWithCancellationToken = new(configuration);

    private async Task AddCopilotAgentPluginAsync(Kernel kernel, IConfigurationRoot configuration, string pluginName)
    {
        var copilotAgentPluginParameters = new CopilotAgentPluginParameters
        {
            FunctionExecutionParameters = new()
            {
                { "https://graph.microsoft.com/v1.0", new OpenApiFunctionExecutionParameters(authCallback: this._bearerAuthenticationProviderWithCancellationToken.AuthenticateRequestAsync, enableDynamicOperationPayload: false, enablePayloadNamespacing: true) { ParameterFilter = s_restApiParameterFilter} },
                { "https://api.nasa.gov/planetary", new OpenApiFunctionExecutionParameters(authCallback: GetApiKeyAuthProvider("DEMO_KEY", "api_key", false), enableDynamicOperationPayload: false, enablePayloadNamespacing: true)}
            },
        };

        try
        {
            KernelPlugin plugin =
            await kernel.ImportPluginFromCopilotAgentPluginAsync(
                pluginName,
                GetCopilotAgentManifestPath(pluginName),
                copilotAgentPluginParameters)
                .ConfigureAwait(false);
            AnsiConsole.MarkupLine($"[bold green] {pluginName} loaded successfully.[/]");
        }
        catch (Exception ex)
        {
            AnsiConsole.MarkupLine($"[red]Failed to load {pluginName}.[/]");
            kernel.LoggerFactory.CreateLogger("Plugin Creation").LogError(ex, "Plugin creation failed. Message: {0}", ex.Message);
            throw new AggregateException($"Plugin creation failed for {pluginName}", ex);
        }
    }
    #region MagicDoNotLookUnderTheHood
    private static readonly HashSet<string> s_fieldsToIgnore = new(
        [
            "@odata.type",
            "attachments",
            "allowNewTimeProposals",
            "bccRecipients",
            "bodyPreview",
            "calendar",
            "categories",
            "ccRecipients",
            "changeKey",
            "conversationId",
            "coordinates",
            "conversationIndex",
            "createdDateTime",
            "discriminator",
            "lastModifiedDateTime",
            "locations",
            "extensions",
            "flag",
            "from",
            "hasAttachments",
            "iCalUId",
            "id",
            "inferenceClassification",
            "internetMessageHeaders",
            "instances",
            "isCancelled",
            "isDeliveryReceiptRequested",
            "isDraft",
            "isOrganizer",
            "isRead",
            "isReadReceiptRequested",
            "multiValueExtendedProperties",
            "onlineMeeting",
            "onlineMeetingProvider",
            "onlineMeetingUrl",
            "organizer",
            "originalStart",
            "parentFolderId",
            "range",
            "receivedDateTime",
            "recurrence",
            "replyTo",
            "sender",
            "sentDateTime",
            "seriesMasterId",
            "singleValueExtendedProperties",
            "transactionId",
            "time",
            "uniqueBody",
            "uniqueId",
            "uniqueIdType",
            "webLink",
        ],
        StringComparer.OrdinalIgnoreCase
    );
    private const string RequiredPropertyName = "required";
    private const string PropertiesPropertyName = "properties";
    /// <summary>
    /// Trims the properties from the request body schema.
    /// Most models in strict mode enforce a limit on the properties.
    /// </summary>
    /// <param name="schema">Source schema</param>
    /// <returns>the trimmed schema for the request body</returns>
    private static KernelJsonSchema? TrimPropertiesFromRequestBody(KernelJsonSchema? schema)
    {
        if (schema is null)
        {
            return null;
        }

        var originalSchema = JsonSerializer.Serialize(schema.RootElement);
        var node = JsonNode.Parse(originalSchema);
        if (node is not JsonObject jsonNode)
        {
            return schema;
        }

        TrimPropertiesFromJsonNode(jsonNode);

        return KernelJsonSchema.Parse(node.ToString());
    }
    private static void TrimPropertiesFromJsonNode(JsonNode jsonNode)
    {
        if (jsonNode is not JsonObject jsonObject)
        {
            return;
        }
        if (jsonObject.TryGetPropertyValue(RequiredPropertyName, out var requiredRawValue) && requiredRawValue is JsonArray requiredArray)
        {
            jsonNode[RequiredPropertyName] = new JsonArray(requiredArray.Where(x => x is not null).Select(x => x!.GetValue<string>()).Where(x => !s_fieldsToIgnore.Contains(x)).Select(x => JsonValue.Create(x)).ToArray());
        }
        if (jsonObject.TryGetPropertyValue(PropertiesPropertyName, out var propertiesRawValue) && propertiesRawValue is JsonObject propertiesObject)
        {
            var properties = propertiesObject.Where(x => s_fieldsToIgnore.Contains(x.Key)).Select(static x => x.Key).ToArray();
            foreach (var property in properties)
            {
                propertiesObject.Remove(property);
            }
        }
        foreach (var subProperty in jsonObject)
        {
            if (subProperty.Value is not null)
            {
                TrimPropertiesFromJsonNode(subProperty.Value);
            }
        }
    }
#pragma warning disable SKEXP0040
    private static readonly RestApiParameterFilter s_restApiParameterFilter = (RestApiParameterFilterContext context) =>
    {
#pragma warning restore SKEXP0040
        if (("me_sendMail".Equals(context.Operation.Id, StringComparison.OrdinalIgnoreCase) ||
            ("me_calendar_CreateEvents".Equals(context.Operation.Id, StringComparison.OrdinalIgnoreCase)) &&
            "payload".Equals(context.Parameter.Name, StringComparison.OrdinalIgnoreCase)))
        {
            context.Parameter.Schema = TrimPropertiesFromRequestBody(context.Parameter.Schema);
            return context.Parameter;
        }
        return context.Parameter;
    };
    private sealed class ExpectedSchemaFunctionFilter : IAutoFunctionInvocationFilter
    {//TODO: this eventually needs to be added to all CAP or DA but we're still discussing where should those facilitators live
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            await next(context).ConfigureAwait(false);

            if (context.Result.ValueType == typeof(RestApiOperationResponse))
            {
                var openApiResponse = context.Result.GetValue<RestApiOperationResponse>();
                if (openApiResponse?.ExpectedSchema is not null)
                {
                    openApiResponse.ExpectedSchema = null;
                }
            }
        }
    }
    #endregion
}
