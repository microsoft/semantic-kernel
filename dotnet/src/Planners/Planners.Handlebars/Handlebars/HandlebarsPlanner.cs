// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using HandlebarsDotNet.Helpers.Enums;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Represents a Handlebars planner.
/// </summary>
public sealed class HandlebarsPlanner
{
    /// <summary>
    /// Represents static options for all Handlebars Planner prompt templates.
    /// </summary>
    public static readonly HandlebarsPromptTemplateOptions PromptTemplateOptions = new()
    {
        // Options for built-in Handlebars helpers
        Categories = new Category[] { Category.DateTime },
        UseCategoryPrefix = false,

        // Custom helpers
        RegisterCustomHelpers = HandlebarsPromptTemplateExtensions.RegisterCustomCreatePlanHelpers,
    };

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlebarsPlanner"/> class.
    /// </summary>
    /// <param name="options">Configuration options for Handlebars Planner.</param>
    public HandlebarsPlanner(HandlebarsPlannerOptions? options = default)
    {
        this._options = options ?? new HandlebarsPlannerOptions();
        this._templateFactory = new HandlebarsPromptTemplateFactory(options: PromptTemplateOptions);
        this._options.ExcludedPlugins.Add("Planner_Excluded");
    }

    /// <summary>Creates a plan for the specified goal.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="goal">The goal for which a plan should be created.</param>
    /// <param name="arguments"> Optional. Context arguments to pass to the planner. </param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The created plan.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="goal"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="goal"/> is empty or entirely composed of whitespace.</exception>
    /// <exception cref="KernelException">A plan could not be created.</exception>
    public Task<HandlebarsPlan> CreatePlanAsync(Kernel kernel, string goal, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(goal);

        var logger = kernel.LoggerFactory.CreateLogger(typeof(HandlebarsPlanner)) ?? NullLogger.Instance;

        return PlannerInstrumentation.CreatePlanAsync(
            static (HandlebarsPlanner planner, Kernel kernel, string goal, KernelArguments? arguments, CancellationToken cancellationToken)
                => planner.CreatePlanCoreAsync(kernel, goal, arguments, cancellationToken),
            this, kernel, goal, arguments, logger, cancellationToken);
    }

    #region private

    private readonly HandlebarsPlannerOptions _options;

    private readonly HandlebarsPromptTemplateFactory _templateFactory;

    /// <summary>
    /// Error message if kernel does not contain sufficient functions to create a plan.
    /// </summary>
    private const string InsufficientFunctionsError = "Additional helpers or information may be required";

    private async Task<HandlebarsPlan> CreatePlanCoreAsync(Kernel kernel, string goal, KernelArguments? arguments, CancellationToken cancellationToken = default)
    {
        // Get CreatePlan prompt template
        var functionsMetadata = await kernel.Plugins.GetFunctionsAsync(this._options, null, null, cancellationToken).ConfigureAwait(false);
        var availableFunctions = this.GetAvailableFunctionsManual(functionsMetadata, out var complexParameterTypes, out var complexParameterSchemas);
        var createPlanPrompt = await this.GetHandlebarsTemplateAsync(kernel, goal, arguments, availableFunctions, complexParameterTypes, complexParameterSchemas, cancellationToken).ConfigureAwait(false);
        ChatHistory chatMessages = this.GetChatHistoryFromPrompt(createPlanPrompt);

        // Get the chat completion results
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var completionResults = await chatCompletionService.GetChatMessageContentAsync(chatMessages, executionSettings: this._options.ExecutionSettings, cancellationToken: cancellationToken).ConfigureAwait(false);

        // Check if plan could not be created due to insufficient functions
        if (completionResults.Content is not null && completionResults.Content.IndexOf(InsufficientFunctionsError, StringComparison.OrdinalIgnoreCase) >= 0)
        {
            var functionNames = availableFunctions.ToList().Select(func => $"{func.PluginName}{this._templateFactory.NameDelimiter}{func.Name}");
            throw new KernelException($"[{HandlebarsPlannerErrorCodes.InsufficientFunctionsForGoal}] Unable to create plan for goal with available functions.\nGoal: {goal}\nAvailable Functions: {string.Join(", ", functionNames)}\nPlanner output:\n{completionResults}");
        }

        Match match = Regex.Match(completionResults.Content, @"```\s*(handlebars)?\s*(.*)\s*```", RegexOptions.Singleline);
        if (!match.Success)
        {
            throw new KernelException($"[{HandlebarsPlannerErrorCodes.InvalidTemplate}] Could not find the plan in the results\nPlanner output:\n{completionResults}");
        }

        var planTemplate = match.Groups[2].Value.Trim();
        planTemplate = MinifyHandlebarsTemplate(planTemplate);

        return new HandlebarsPlan(planTemplate, createPlanPrompt);
    }

    private List<KernelFunctionMetadata> GetAvailableFunctionsManual(
        IEnumerable<KernelFunctionMetadata> availableFunctions,
        out HashSet<HandlebarsParameterTypeMetadata> complexParameterTypes,
        out Dictionary<string, string> complexParameterSchemas)
    {
        complexParameterTypes = new();
        complexParameterSchemas = new();

        var functionsMetadata = new List<KernelFunctionMetadata>();
        foreach (var kernelFunction in availableFunctions)
        {
            // Extract any complex parameter types for isolated render in prompt template
            var parametersMetadata = new List<KernelParameterMetadata>();
            foreach (var parameter in kernelFunction.Parameters)
            {
                var paramToAdd = this.SetComplexTypeDefinition(parameter, complexParameterTypes, complexParameterSchemas);
                parametersMetadata.Add(paramToAdd);
            }

            var returnParameter = kernelFunction.ReturnParameter.ToKernelParameterMetadata(kernelFunction.Name);
            returnParameter = this.SetComplexTypeDefinition(returnParameter, complexParameterTypes, complexParameterSchemas);

            // Need to override function metadata in case parameter metadata changed (e.g., converted primitive types from schema objects)
            var functionMetadata = new KernelFunctionMetadata(kernelFunction.Name)
            {
                PluginName = kernelFunction.PluginName,
                Description = kernelFunction.Description,
                Parameters = parametersMetadata,
                ReturnParameter = returnParameter.ToKernelReturnParameterMetadata()
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
            if (type.TryGetGenericResultType(out var taskResultType))
            {
                parameter = new(parameter) { ParameterType = taskResultType }; // Actual Return Type
            }

            complexParameterTypes.UnionWith(parameter.ParameterType!.ToHandlebarsParameterTypeMetadata());
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
        Kernel kernel,
        string goal,
        KernelArguments? predefinedArguments,
        List<KernelFunctionMetadata> availableFunctions,
        HashSet<HandlebarsParameterTypeMetadata> complexParameterTypes,
        Dictionary<string, string> complexParameterSchemas,
        CancellationToken cancellationToken)
    {
        // Set-up prompt context
        var predefinedArgumentsWithTypes = predefinedArguments?.ToDictionary(
            kvp => kvp.Key,
            kvp => new
            {
                Type = kvp.Value?.GetType().GetFriendlyTypeName(),
                Value = JsonSerializer.Serialize(kvp.Value, JsonOptionsCache.WriteIndented)
            }
        );

        var additionalContext = this._options.GetAdditionalPromptContext is not null
            ? await this._options.GetAdditionalPromptContext.Invoke().ConfigureAwait(false)
            : null;

        var arguments = new KernelArguments()
            {
                { "functions", availableFunctions},
                { "goal", goal },
                { "predefinedArguments", predefinedArgumentsWithTypes},
                { "nameDelimiter", this._templateFactory.NameDelimiter},
                { "insufficientFunctionsErrorMessage", InsufficientFunctionsError},
                { "allowLoops", this._options.AllowLoops },
                { "complexTypeDefinitions", complexParameterTypes.Count > 0 && complexParameterTypes.Any(p => p.IsComplex) ? complexParameterTypes.Where(p => p.IsComplex) : null},
                { "complexSchemaDefinitions", complexParameterSchemas.Count > 0 ? complexParameterSchemas : null},
                { "lastPlan", this._options.LastPlan },
                { "lastError", this._options.LastError },
                { "additionalContext", !string.IsNullOrWhiteSpace(additionalContext) ? additionalContext : null },
            };

        // Construct prompt from Partials and Prompt Template
        var createPlanPrompt = this.ConstructHandlebarsPrompt("CreatePlanPrompt");

        // Render the prompt
        var promptTemplateConfig = new PromptTemplateConfig()
        {
            Template = createPlanPrompt,
            TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            Name = "Planner_Excluded-CreateHandlebarsPlan",
        };

        var handlebarsTemplate = this._templateFactory.Create(promptTemplateConfig);
        return await handlebarsTemplate!.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(true);
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

    #endregion
}
