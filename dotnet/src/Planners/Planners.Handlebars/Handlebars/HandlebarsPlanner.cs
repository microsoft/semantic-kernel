// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Represents a Handlebars planner.
/// </summary>
public sealed class HandlebarsPlanner
{
    private readonly HandlebarsPlannerConfig _config;

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlebarsPlanner"/> class.
    /// </summary>
    /// <param name="config">The configuration.</param>
    public HandlebarsPlanner(HandlebarsPlannerConfig? config = default)
    {
        this._config = config ?? new HandlebarsPlannerConfig();
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
        var availableFunctions = this.GetAvailableFunctionsManual(kernel, out var complexParameterTypes, out var complexParameterSchemas);
        var createPlanPrompt = this.GetHandlebarsTemplate(kernel, goal, availableFunctions, complexParameterTypes, complexParameterSchemas);
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Extract the chat history from the rendered prompt
        string pattern = @"<(user~|system~|assistant~)>(.*?)<\/\1>";
        MatchCollection matches = Regex.Matches(createPlanPrompt, pattern, RegexOptions.Singleline);

        // Add the chat history to the chat
        ChatHistory chatMessages = this.GetChatHistoryFromPrompt(createPlanPrompt, chatCompletionService);

        // Get the chat completion results
        var completionResults = await chatCompletionService.GetChatMessageContentAsync(chatMessages, cancellationToken: cancellationToken).ConfigureAwait(false);

        if (completionResults.Content?.IndexOf("Additional helpers may be required", StringComparison.OrdinalIgnoreCase) >= 0)
        {
            var functionNames = availableFunctions.ToList().Select(func => $"{func.PluginName}{HandlebarsTemplateEngineExtensions.ReservedNameDelimiter}{func.Name}");
            throw new KernelException($"Unable to create plan for goal with available functions.\nGoal: {goal}\nAvailable Functions: {string.Join(", ", functionNames)}\nPlanner output:\n{completionResults}");
        }

        Match match = Regex.Match(completionResults.Content, @"```\s*(handlebars)?\s*(.*)\s*```", RegexOptions.Singleline);
        if (!match.Success)
        {
            throw new KernelException("Could not find the plan in the results");
        }

        var planTemplate = match.Groups[2].Value.Trim();

        planTemplate = planTemplate.Replace("compare.equal", "equal");
        planTemplate = planTemplate.Replace("compare.lessThan", "lessThan");
        planTemplate = planTemplate.Replace("compare.greaterThan", "greaterThan");
        planTemplate = planTemplate.Replace("compare.lessThanOrEqual", "lessThanOrEqual");
        planTemplate = planTemplate.Replace("compare.greaterThanOrEqual", "greaterThanOrEqual");
        planTemplate = planTemplate.Replace("compare.greaterThanOrEqual", "greaterThanOrEqual");

        planTemplate = MinifyHandlebarsTemplate(planTemplate);
        return new HandlebarsPlan(planTemplate, createPlanPrompt);
    }

    private List<KernelFunctionMetadata> GetAvailableFunctionsManual(
        Kernel kernel,
        out HashSet<HandlebarsParameterTypeMetadata> complexParameterTypes,
        out Dictionary<string, string> complexParameterSchemas)
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
            if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(Task<>))
            {
                parameter = new(parameter) { ParameterType = type.GenericTypeArguments[0] }; // Actual Return Type
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

    private ChatHistory GetChatHistoryFromPrompt(string prompt, IChatCompletionService chatCompletionService)
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

    private string GetHandlebarsTemplate(
        Kernel kernel, string goal,
        List<KernelFunctionMetadata> availableFunctions,
        HashSet<HandlebarsParameterTypeMetadata> complexParameterTypes,
        Dictionary<string, string> complexParameterSchemas)
    {
        var plannerTemplate = this.ReadPrompt("CreatePlanPrompt.handlebars");
        var arguments = new KernelArguments()
            {
                { "functions", availableFunctions},
                { "goal", goal },
                { "reservedNameDelimiter", HandlebarsTemplateEngineExtensions.ReservedNameDelimiter},
                { "allowLoops", this._config.AllowLoops },
                { "complexTypeDefinitions", complexParameterTypes.Count > 0 && complexParameterTypes.Any(p => p.IsComplex) ? complexParameterTypes.Where(p => p.IsComplex) : null},
                { "complexSchemaDefinitions", complexParameterSchemas.Count > 0 ? complexParameterSchemas : null},
                { "lastPlan", this._config.LastPlan },
                { "lastError", this._config.LastError }
            };

        return HandlebarsTemplateEngineExtensions.Render(kernel, plannerTemplate, arguments);
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
