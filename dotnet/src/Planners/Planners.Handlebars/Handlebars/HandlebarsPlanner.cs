// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using HandlebarsDotNet.Helpers.Enums;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

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

        var logger = kernel.LoggerFactory.CreateLogger(typeof(HandlebarsPlanner)) ?? NullLogger.Instance;

        return PlannerInstrumentation.CreatePlanAsync(
            static (HandlebarsPlanner planner, Kernel kernel, string goal, CancellationToken cancellationToken)
                => planner.CreatePlanCoreAsync(kernel, goal, cancellationToken),
            this, kernel, goal, logger, cancellationToken);
    }

    #region private

    private readonly HandlebarsPlannerOptions _options;

    private HandlebarsPromptTemplateFactory _templateFactory { get; }

    /// <summary>
    /// Error message if kernel does not contain sufficient functions to create a plan.
    /// </summary>
    private const string InsufficientFunctionsError = "Additional helpers may be required";

    private async Task<HandlebarsPlan> CreatePlanCoreAsync(Kernel kernel, string goal, CancellationToken cancellationToken = default)
    {
        var executionSettings = this._options.ExecutionSettings ?? new PromptExecutionSettings()
        {
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.0 },
                { "top_p", 0.0 },
                { "presence_penalty", 0.0 },
                { "frequency_penalty", 0.0 },
            }
        };

        // Get CreatePlan prompt template
        var functionsManual = await kernel.Plugins.GetJsonSchemaFunctionsManualAsync(this._options, null, null /*logger*/, true, cancellationToken).ConfigureAwait(false);
        var createPlanPrompt = await this.GetHandlebarsTemplateAsync(kernel, goal, functionsManual, cancellationToken).ConfigureAwait(false);
        ChatHistory chatMessages = this.GetChatHistoryFromPrompt(createPlanPrompt);

        // Get the chat completion results
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var completionResults = await chatCompletionService.GetChatMessageContentAsync(chatMessages, executionSettings: executionSettings, cancellationToken: cancellationToken).ConfigureAwait(false);

        // Check if plan could not be created due to insufficient functions
        if (completionResults.Content is not null && completionResults.Content.IndexOf(InsufficientFunctionsError, StringComparison.OrdinalIgnoreCase) >= 0)
        {
            var availableFunctions = await kernel.Plugins.GetFunctionsAsync(this._options, null, null /*logger*/, cancellationToken: cancellationToken).ConfigureAwait(false);
            var functionNames = availableFunctions.Select(func => $"{func.PluginName}{this._templateFactory.NameDelimiter}{func.Name}");
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
        string? availableFunctions,
        CancellationToken cancellationToken)
    {
        var createPlanPrompt = this.ReadPrompt("CreatePlanPrompt.handlebars");
        var arguments = new KernelArguments()
            {
                { "functions", availableFunctions},
                { "goal", goal },
                { "nameDelimiter", this._templateFactory.NameDelimiter},
                { "insufficientFunctionsErrorMessage", InsufficientFunctionsError},
                { "allowLoops", this._options.AllowLoops },
                { "lastPlan", this._options.LastPlan },
                { "lastError", this._options.LastError }
            };

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
