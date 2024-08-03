// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
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
public sealed partial class HandlebarsPlanner
{
    /// <summary>
    /// Represents static options for all Handlebars Planner prompt templates.
    /// </summary>
    public static readonly HandlebarsPromptTemplateOptions PromptTemplateOptions = new()
    {
        // Options for built-in Handlebars helpers
        Categories = [Category.DateTime],
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

    private async Task<HandlebarsPlan> CreatePlanCoreAsync(Kernel kernel, string goal, KernelArguments? arguments, CancellationToken cancellationToken = default)
    {
        string? createPlanPrompt = null;
        ChatMessageContent? modelResults = null;

        try
        {
            // Get CreatePlan prompt template
            var functionsMetadata = await kernel.Plugins.GetFunctionsAsync(this._options, null, null, cancellationToken).ConfigureAwait(false);
            var availableFunctions = this.GetAvailableFunctionsManual(functionsMetadata, out var complexParameterTypes, out var complexParameterSchemas);
            createPlanPrompt = await this.GetHandlebarsTemplateAsync(kernel, goal, arguments, availableFunctions, complexParameterTypes, complexParameterSchemas, cancellationToken).ConfigureAwait(false);
            ChatHistory chatMessages = this.GetChatHistoryFromPrompt(createPlanPrompt);

            // Get the chat completion results
            var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
            modelResults = await chatCompletionService.GetChatMessageContentAsync(chatMessages, executionSettings: this._options.ExecutionSettings, cancellationToken: cancellationToken).ConfigureAwait(false);

            MatchCollection matches = ParseRegex().Matches(modelResults.Content ?? string.Empty);
            if (matches.Count < 1)
            {
                throw new KernelException($"[{HandlebarsPlannerErrorCodes.InvalidTemplate}] Could not find the plan in the results. Additional helpers or input may be required.\n\nPlanner output:\n{modelResults.Content}");
            }
            else if (matches.Count > 1)
            {
                throw new KernelException($"[{HandlebarsPlannerErrorCodes.InvalidTemplate}] Identified multiple Handlebars templates in model response. Please try again.\n\nPlanner output:\n{modelResults.Content}");
            }

            var planTemplate = matches[0].Groups[2].Value.Trim();
            planTemplate = MinifyHandlebarsTemplate(planTemplate);

            return new HandlebarsPlan(planTemplate, createPlanPrompt);
        }
        catch (KernelException ex)
        {
            throw new PlanCreationException(
                "CreatePlan failed. See inner exception for details.",
                createPlanPrompt,
                modelResults,
                ex
            );
        }
    }

    private List<KernelFunctionMetadata> GetAvailableFunctionsManual(
        IEnumerable<KernelFunctionMetadata> availableFunctions,
        out HashSet<HandlebarsParameterTypeMetadata> complexParameterTypes,
        out Dictionary<string, string> complexParameterSchemas)
    {
        complexParameterTypes = [];
        complexParameterSchemas = [];

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
        if (parameter.Schema is not null)
        {
            // Class types will have a defined schema, but we want to handle those as built-in complex types below
            if (parameter.ParameterType is not null && parameter.ParameterType!.IsClass)
            {
                parameter = new(parameter) { Schema = null };
            }
            else
            {
                // Parse the schema to extract any primitive types and set in ParameterType property instead
                var parsedParameter = parameter.ParseJsonSchema();
                if (parsedParameter.Schema is not null)
                {
                    complexParameterSchemas[parameter.GetSchemaTypeName()] = parameter.Schema.RootElement.ToJsonString();
                }

                return parsedParameter;
            }
        }

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
                default:
                    Debug.Fail($"Unexpected role: {role}");
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
                { "allowLoops", this._options.AllowLoops },
                { "complexTypeDefinitions", complexParameterTypes.Count > 0 && complexParameterTypes.Any(p => p.IsComplex) ? complexParameterTypes.Where(p => p.IsComplex) : null},
                { "complexSchemaDefinitions", complexParameterSchemas.Count > 0 ? complexParameterSchemas : null},
                { "lastPlan", this._options.LastPlan },
                { "lastError", this._options.LastError },
                { "additionalContext", !string.IsNullOrWhiteSpace(additionalContext) ? additionalContext : null },
            };

        // Construct prompt from Partials and Prompt Template
        var createPlanPrompt = this.ConstructHandlebarsPrompt("CreatePlanPrompt", promptOverride: this._options.CreatePlanPromptHandler?.Invoke());

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
        // Replace all occurrences of the pattern in the input template
        return MinifyRegex().Replace(template, m =>
        {
            // For each match, remove the whitespace within the handlebars, except for spaces
            // that separate different items (e.g., 'json' and '(get')
            return WhitespaceRegex().Replace(m.Value, " ").Replace(" {", "{").Replace(" }", "}").Replace(" )", ")");
        });
    }

    /// <summary>
    /// Regex breakdown:
    /// (```\s*handlebars){1}\s*: Opening backticks, starting boundary for HB template
    /// ((([^`]|`(?!``))+): Any non-backtick character or one backtick character not followed by 2 more consecutive backticks
    /// (\s*```){1}: Closing backticks, closing boundary for HB template
    /// </summary>
#if NET
    [GeneratedRegex(@"(```\s*handlebars){1}\s*(([^`]|`(?!``))+)(\s*```){1}", RegexOptions.Multiline)]
    private static partial Regex ParseRegex();

    [GeneratedRegex(@"\{\{[\s\S]*?}}")]
    private static partial Regex MinifyRegex();

    [GeneratedRegex(@"\s+")]
    private static partial Regex WhitespaceRegex();
#else
    private static readonly Regex s_parseRegex = new(@"(```\s*handlebars){1}\s*(([^`]|`(?!``))+)(\s*```){1}", RegexOptions.Multiline | RegexOptions.Compiled);
    private static Regex ParseRegex() => s_parseRegex;

    private static readonly Regex s_minifyRegex = new(@"(\{\{[\s\S]*?}})");
    private static Regex MinifyRegex() => s_minifyRegex;

    private static readonly Regex s_whitespaceRegex = new(@"\s+");
    private static Regex WhitespaceRegex() => s_whitespaceRegex;
#endif
    #endregion
}
