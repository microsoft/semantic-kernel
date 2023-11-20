// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Represents a Handlebars planner.
/// </summary>
public sealed class HandlebarsPlanner
{
    /// <summary>
    /// The key for the available kernel functions.
    /// </summary>
    public const string AvailableKernelFunctionsKey = "AVAILABLE_KERNEL_FUNCTIONS";

    /// <summary>
    /// Gets the stopwatch used for measuring planning time.
    /// </summary>
    public Stopwatch Stopwatch { get; } = new();

    private readonly Kernel _kernel;

    private readonly HandlebarsPlannerConfig _config;

    private readonly HashSet<HandlebarsParameterTypeView> _parameterTypes = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlebarsPlanner"/> class.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="config">The configuration.</param>
    public HandlebarsPlanner(Kernel kernel, HandlebarsPlannerConfig? config = default)
    {
        this._kernel = kernel;
        this._config = config ?? new HandlebarsPlannerConfig();
    }

    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The plan.</returns>
    /// <exception cref="SKException">Thrown when the plan cannot be created.</exception>
    public async Task<HandlebarsPlan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        var availableFunctions = this.GetAvailableFunctionsManual(cancellationToken);
        var handlebarsTemplate = this.GetHandlebarsTemplate(this._kernel, goal, availableFunctions);
        var chatCompletion = this._kernel.GetService<IChatCompletion>();

        // Extract the chat history from the rendered prompt
        string pattern = @"<(user~|system~|assistant~)>(.*?)<\/\1>";
        MatchCollection matches = Regex.Matches(handlebarsTemplate, pattern, RegexOptions.Singleline);

        // Add the chat history to the chat
        ChatHistory chatMessages = this.GetChatHistoryFromPrompt(handlebarsTemplate, chatCompletion);

        // Get the chat completion results
        var completionResults = await chatCompletion.GetChatCompletionsAsync(chatMessages, cancellationToken: cancellationToken).ConfigureAwait(false);
        var completionMessage = await completionResults[0].GetChatMessageAsync(cancellationToken).ConfigureAwait(false);

        var resultContext = this._kernel.CreateNewContext();
        resultContext.Variables.Update(completionMessage.Content);

        if (resultContext.Result.IndexOf("Additional helpers may be required", StringComparison.OrdinalIgnoreCase) >= 0)
        {
            var functionNames = availableFunctions.ToList().Select(func => $"{func.PluginName}{HandlebarsTemplateEngineExtensions.ReservedNameDelimiter}{func.Name}");
            throw new SKException($"Unable to create plan for goal with available functions.\nGoal: {goal}\nAvailable Functions: {string.Join(", ", functionNames)}\nPlanner output:\n{resultContext.Result}");
        }

        Match match = Regex.Match(resultContext.Result, @"```\s*(handlebars)?\s*(.*)\s*```", RegexOptions.Singleline);
        if (!match.Success)
        {
            throw new SKException("Could not find the plan in the results");
        }

        var template = match.Groups[2].Value.Trim(); // match.Success ? match.Groups[2].Value.Trim() : resultContext.Result;

        template = template.Replace("compare.equal", "equal");
        template = template.Replace("compare.lessThan", "lessThan");
        template = template.Replace("compare.greaterThan", "greaterThan");
        template = template.Replace("compare.lessThanOrEqual", "lessThanOrEqual");
        template = template.Replace("compare.greaterThanOrEqual", "greaterThanOrEqual");
        template = template.Replace("compare.greaterThanOrEqual", "greaterThanOrEqual");

        template = MinifyHandlebarsTemplate(template);
        return new HandlebarsPlan(this._kernel, template);
    }

    private List<FunctionView> GetAvailableFunctionsManual(CancellationToken cancellationToken = default)
    {
        return this._kernel.Plugins.GetFunctionViews()
            .Where(s => !this._config.ExcludedPlugins.Contains(s.PluginName, StringComparer.OrdinalIgnoreCase)
                && !this._config.ExcludedFunctions.Contains(s.Name, StringComparer.OrdinalIgnoreCase)
                && !s.Name.Contains("Planner_Excluded"))
            .ToList();
    }

    private ChatHistory GetChatHistoryFromPrompt(string prompt, IChatCompletion chatCompletion)
    {
        // Extract the chat history from the rendered prompt
        string pattern = @"<(user~|system~|assistant~)>(.*?)<\/\1>";
        MatchCollection matches = Regex.Matches(prompt, pattern, RegexOptions.Singleline);

        // Add the chat history to the chat
        ChatHistory chatMessages = chatCompletion.CreateNewChat();
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

    private string GetHandlebarsTemplate(Kernel kernel, string goal, List<FunctionView> availableFunctions)
    {
        var plannerTemplate = this.ReadPrompt("skPrompt.handlebars", this._config.AllowLoops ? null : "NoLoops");
        var variables = new Dictionary<string, object?>()
            {
                { "functions", availableFunctions},
                { "goal", goal },
                { "reservedNameDelimiter", HandlebarsTemplateEngineExtensions.ReservedNameDelimiter},
                { "complexTypeDefinitions", this._parameterTypes.Count > 0 && this._parameterTypes.Any(p => p.IsComplexType) ? this._parameterTypes.Where(p => p.IsComplexType) : null},
                { "lastPlan", this._config.LastPlan },
                { "lastError", this._config.LastError }
            };

        return HandlebarsTemplateEngineExtensions.Render(kernel, kernel.CreateNewContext(), plannerTemplate, variables);
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
