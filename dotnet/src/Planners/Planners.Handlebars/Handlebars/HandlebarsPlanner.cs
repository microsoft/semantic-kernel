// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using HandlebarsDotNet.Helpers.Enums;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Enum error codes for Handlebars planner exceptions.
/// </summary>
public enum HandlebarsPlannerErrorCodes
{
    /// <summary>
    /// Error code for hallucinated helpers.
    /// </summary>
    HallucinatedHelpers,

    /// <summary>
    /// Error code for invalid Handlebars template.
    /// </summary>
    InvalidTemplate,

    /// <summary>
    /// Error code for insufficient functions to complete the goal.
    /// </summary>
    InsufficientFunctionsForGoal,
}

/// <summary>
/// Represents a Handlebars planner.
/// </summary>
public sealed class HandlebarsPlanner
{
    /// <summary>
    /// Error message if kernel does not contain sufficient functions to create a plan.
    /// </summary>
    private const string InsufficientFunctionsError = "Additional helpers may be required";

    /// <summary>
    /// Represents static options for all Handlebars Planner prompt templates.
    /// </summary>
    public static readonly HandlebarsPromptTemplateOptions PromptTemplateOptions = new()
    {
        // Options for built-in Handlebars helpers
        Categories = new Category[] { Category.Math },
        UseCategoryPrefix = false,

        // Custom helpers
        RegisterCustomHelpers = HandlebarsPromptTemplateExtensions.RegisterCustomCreatePlanHelpers,
    };

    /// <summary>
    /// Gets the stopwatch used for measuring planning time.
    /// </summary>
    public Stopwatch Stopwatch { get; } = new();

    private readonly HandlebarsPlannerConfig _config;

    private HandlebarsPromptTemplateFactory _templateFactory { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlebarsPlanner"/> class.
    /// </summary>
    /// <param name="config">The configuration for Planner.</param>
    public HandlebarsPlanner(HandlebarsPlannerConfig? config = default)
    {
        this._config = config ?? new HandlebarsPlannerConfig();
        this._templateFactory = new HandlebarsPromptTemplateFactory(options: PromptTemplateOptions);
    }

    /// <summary>Creates a plan for the specified goal.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="goal">The goal for which a plan should be created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The created plan.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="goal"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="goal"/> is empty or entirely composed of whitespace.</exception>
    /// <exception cref="KernelException">A plan could not be created.</exception>
    public Task<HandlebarsPlan> CreatePlanAsync(Kernel kernel, string goal, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(goal);

        var logger = kernel.LoggerFactory.CreateLogger(typeof(HandlebarsPlanner));

        return PlannerInstrumentation.CreatePlanAsync(
            static (HandlebarsPlanner planner, Kernel kernel, string goal, CancellationToken cancellationToken)
                => planner.CreatePlanCoreAsync(kernel, goal, cancellationToken),
            this, kernel, goal, logger, cancellationToken);
    }

    private async Task<HandlebarsPlan> CreatePlanCoreAsync(Kernel kernel, string goal, CancellationToken cancellationToken = default)
    {
        var availableFunctions = this.GetAvailableFunctionsManual(kernel, out var complexParameterTypes, out var complexParameterSchemas, cancellationToken);
        var createPlanPrompt = await this.GetHandlebarsTemplateAsync(kernel, goal, availableFunctions, complexParameterTypes, complexParameterSchemas).ConfigureAwait(false);
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Extract the chat history from the rendered prompt
        string pattern = @"<(user~|system~|assistant~)>(.*?)<\/\1>";
        MatchCollection matches = Regex.Matches(createPlanPrompt, pattern, RegexOptions.Singleline);

        // Add the chat history to the chat
        ChatHistory chatMessages = this.GetChatHistoryFromPrompt(createPlanPrompt);

        // Get the chat completion results
        var completionResults = await chatCompletionService.GetChatMessageContentAsync(chatMessages, cancellationToken: cancellationToken).ConfigureAwait(false);

        if (completionResults.Content is not null && completionResults.Content.Contains(InsufficientFunctionsError))
        {
            var functionNames = availableFunctions.ToList().Select(func => $"{func.PluginName}{this._templateFactory.NameDelimiter}{func.Name}");
            throw new KernelException($"[{HandlebarsPlannerErrorCodes.InsufficientFunctionsForGoal}] Unable to create plan for goal with available functions.\nGoal: {goal}\nAvailable Functions: {string.Join(", ", functionNames)}\nPlanner output:\n{completionResults}");
        }

        Match match = Regex.Match(completionResults.Content, @"```\s*(handlebars)?\s*(.*)\s*```", RegexOptions.Singleline);
        if (!match.Success)
        {
            throw new KernelException($"[{HandlebarsPlannerErrorCodes.InvalidTemplate}] Could not find the plan in the results");
        }

        var planTemplate = match.Groups[2].Value.Trim();
        planTemplate = MinifyHandlebarsTemplate(planTemplate);

        return new HandlebarsPlan(planTemplate, createPlanPrompt);
    }

    private List<KernelFunctionMetadata> GetAvailableFunctionsManual(
        Kernel kernel,
        out HashSet<HandlebarsParameterTypeMetadata> complexParameterTypes,
        out Dictionary<string, string> complexParameterSchemas,
        CancellationToken cancellationToken = default)
    {
        complexParameterTypes = new();
        complexParameterSchemas = new();

        var availableFunctions = kernel.Plugins.GetFunctionsMetadata()
            .Where(s => !this._config.ExcludedPlugins.Contains(s.PluginName, StringComparer.OrdinalIgnoreCase)
                && !this._config.ExcludedFunctions.Contains(s.Name, StringComparer.OrdinalIgnoreCase)
                && !s.Name.Contains("Planner_Excluded"))
            .ToList();

        var functionsMetadata = new List<KernelFunctionMetadata>();
        foreach (var skFunction in availableFunctions)
        {
            // Extract any complex parameter types for isolated render in prompt template
            var parametersMetadata = new List<KernelParameterMetadata>();
            foreach (var parameter in skFunction.Parameters)
            {
                var paramToAdd = this.SetComplexTypeDefinition(parameter, complexParameterTypes, complexParameterSchemas);
                parametersMetadata.Add(paramToAdd);
            }

            var returnParameter = skFunction.ReturnParameter.ToSKParameterMetadata(skFunction.Name);
            returnParameter = this.SetComplexTypeDefinition(returnParameter, complexParameterTypes, complexParameterSchemas);

            // Need to override function metadata in case parameter metadata changed (e.g., converted primitive types from schema objects)
            var functionMetadata = new KernelFunctionMetadata(skFunction.Name)
            {
                PluginName = skFunction.PluginName,
                Description = skFunction.Description,
                Parameters = parametersMetadata,
                ReturnParameter = returnParameter.ToSKReturnParameterMetadata()
            };
            functionsMetadata.Add(functionMetadata);
        }

        return functionsMetadata;
    }

    // Extract any complex types or schemas for isolated render in prompt template
    private KernelParameterMetadata SetComplexTypeDefinition(
        KernelParameterMetadata parameter,
        HashSet<HandlebarsParameterTypeMetadata> complexParameterTypes,
        Dictionary<string, string> complexParameterSchemas)
    {
        // TODO (@teresaqhoang): Handle case when schema and ParameterType can exist i.e., when ParameterType = RestApiResponse
        if (parameter.ParameterType is not null)
        {
            // Async return type - need to extract the actual return type and override ParameterType property
            var type = parameter.ParameterType;
            if (type.TryGetTaskResultType(out var taskResultType))
            {
                parameter = new(parameter) { ParameterType = taskResultType }; // Actual Return Type
            }

            complexParameterTypes.UnionWith(parameter.ParameterType.ToHandlebarsParameterTypeMetadata());
        }
        else if (parameter.Schema is not null)
        {
            // Parse the schema to extract any primitive types and set in ParameterType property instead
            var parsedParameter = parameter.ParseJsonSchema();
            if (parsedParameter.Schema is not null)
            {
                complexParameterSchemas[parameter.GetSchemaTypeName()] = parameter.Schema.RootElement.ToJsonString();
            }

            parameter = parsedParameter;
        }

        return parameter;
    }

    private ChatHistory GetChatHistoryFromPrompt(string prompt)
    {
        // Extract the chat history from the rendered prompt
        string pattern = @"<(user~|system~|assistant~)>(.*?)<\/\1>";
        MatchCollection matches = Regex.Matches(prompt, pattern, RegexOptions.Singleline);

        // Add the chat history to the chat
        var chatMessages = new ChatHistory();
        foreach (Match m in matches.Cast<Match>())
        {
            string role = m.Groups[1].Value;
            string message = m.Groups[2].Value;

            switch (role)
            {
                case "user~":
                    chatMessages.AddUserMessage(message);
                    break;
                case "system~":
                    chatMessages.AddSystemMessage(message);
                    break;
                case "assistant~":
                    chatMessages.AddAssistantMessage(message);
                    break;
            }
        }

        return chatMessages;
    }

    private async Task<string> GetHandlebarsTemplateAsync(
        Kernel kernel, string goal,
        List<KernelFunctionMetadata> availableFunctions,
        HashSet<HandlebarsParameterTypeMetadata> complexParameterTypes,
        Dictionary<string, string> complexParameterSchemas)
    {
        var createPlanPrompt = this.ReadPrompt("CreatePlanPrompt.handlebars");
        var arguments = new KernelArguments()
            {
                { "functions", availableFunctions},
                { "goal", goal },
                { "nameDelimiter", this._templateFactory.NameDelimiter},
                { "insufficientFunctionsErrorMessage", InsufficientFunctionsError},
                { "allowLoops", this._config.AllowLoops },
                { "complexTypeDefinitions", complexParameterTypes.Count > 0 && complexParameterTypes.Any(p => p.IsComplex) ? complexParameterTypes.Where(p => p.IsComplex) : null},
                { "complexSchemaDefinitions", complexParameterSchemas.Count > 0 ? complexParameterSchemas : null},
                { "lastPlan", this._config.LastPlan },
                { "lastError", this._config.LastError }
            };

        var promptTemplateConfig = new PromptTemplateConfig()
        {
            Template = createPlanPrompt,
            TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            Name = "CreatePlan",
        };

        var handlebarsTemplate = this._templateFactory.Create(promptTemplateConfig);

        return await handlebarsTemplate!.RenderAsync(kernel, arguments, CancellationToken.None).ConfigureAwait(true);
    }

    private static string MinifyHandlebarsTemplate(string template)
    {
        // This regex pattern matches '{{', then any characters including newlines (non-greedy), then '}}'
        string pattern = @"(\{\{[\s\S]*?}})";

        // Replace all occurrences of the pattern in the input template
        return Regex.Replace(template, pattern, m =>
        {
            // For each match, remove the whitespace within the handlebars, except for spaces
            // that separate different items (e.g., 'json' and '(get')
            return Regex.Replace(m.Value, @"\s+", " ").Replace(" {", "{").Replace(" }", "}").Replace(" )", ")");
        });
    }
}
