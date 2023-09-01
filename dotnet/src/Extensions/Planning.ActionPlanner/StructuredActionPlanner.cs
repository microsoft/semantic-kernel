// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Action;

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using AI.ChatCompletion;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.AzureSdk.FunctionCalling;
using Diagnostics;
using Extensions.Logging;
using Extensions.Logging.Abstractions;
using Orchestration;
using SkillDefinition;
using TemplateEngine.Prompt;


/// <summary>
///  Action planner that uses the OpenAI chat completion function calling API to select the best action to take.
/// </summary>
public class StructuredActionPlanner : IActionPlanner
{
    private const string SkillName = "this";


    /// <summary>
    ///  Initializes a new instance of the <see cref="StructuredActionPlanner"/> class.
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="prompt"></param>
    /// <param name="loggerFactory"></param>
    public StructuredActionPlanner(
        IKernel kernel,
        string? prompt = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(kernel);

        _logger = loggerFactory is not null ? loggerFactory.CreateLogger(nameof(ActionPlanner)) : NullLogger.Instance;

        var promptTemplate = prompt ?? PromptTemplate;

        _plannerFunction = kernel.CreateSemanticFunction(
            skillName: SkillName,
            promptTemplate: promptTemplate,
            maxTokens: 1024);

        kernel.ImportSkill(this, SkillName);

        _chatCompletion = kernel.GetService<IChatCompletion>();
        _context = kernel.CreateNewContext();
    }


    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }

        // temporary solution until deeper integration with the kernel
        _context.Variables.Update(goal);
        var templateEngine = new PromptTemplateEngine();
        var prompt = await templateEngine.RenderAsync(PromptTemplate, _context, cancellationToken).ConfigureAwait(false);

        var openAIChatCompletion = (IOpenAIChatCompletion)_chatCompletion;

        var chatHistory = openAIChatCompletion.CreateNewChat(prompt);

        List<FunctionDefinition> functionDefinitions = _context.Skills.GetFunctionDefinitions(new[] { SkillName }).ToList();
        // the intended functionCall must always be included in the list of function definitions
        functionDefinitions.Add(ActionPlan);
        var response = await openAIChatCompletion.GenerateResponseAsync<ActionPlanCall>(
            chatHistory,
            new ChatRequestSettings()
                { Temperature = 0.2, MaxTokens = 512 },
            ActionPlan, functionDefinitions.ToArray(), cancellationToken: cancellationToken).ConfigureAwait(false);

        if (response is null)
        {
            throw new SKException("The planner failed to generate a response");
        }

        if (!_context.Skills.TryGetFunction(response, out var function))
        {
            throw new SKException($"The function {response.Function} is not available");
        }

        Plan plan = new(goal, function!);
        plan.Steps[0].Parameters = response.FunctionParameters();

        return plan;
    }


    // Planner semantic function
    private readonly ISKFunction _plannerFunction;

    // Context used to access the list of functions in the kernel
    private readonly SKContext _context;
    private readonly ILogger _logger;

    private readonly IChatCompletion _chatCompletion;

    private const string PromptTemplate = "Decide the best action to take to achieve the user's goal." +
                                          "\nGoal: {{ $input }}";

    private static FunctionDefinition ActionPlan => new()
    {
        Name = "takeAction",
        Description = "decide the best action to take to achieve the user's goal",
        Parameters = BinaryData.FromObjectAsJson(
            new
            {
                Type = "object",
                Properties = new
                {
                    Action = new
                    {
                        Type = "object",
                        Description = "Action data structure",
                        Properties = new
                        {
                            Rationale = new
                            {
                                Type = "string",
                                Description = "the rationale for the action"
                            },
                            Function = new
                            {
                                Type = "string",
                                Description = "Name of the function chosen"
                            },
                            Parameters = new
                            {
                                Type = "array",
                                Description = "Parameter values",
                                Items = new
                                {
                                    Type = "object",
                                    Description = "Parameter value",
                                    Properties = new
                                    {
                                        Name = new
                                        {
                                            Type = "string",
                                            Description = "Parameter name"
                                        },
                                        Value = new
                                        {
                                            Type = "string",
                                            Description = "Parameter value"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase })
    };
}
