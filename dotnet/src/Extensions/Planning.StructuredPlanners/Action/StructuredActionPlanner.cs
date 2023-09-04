// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Action;

using System;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Diagnostics;
using Extensions.Logging;
using Extensions.Logging.Abstractions;
using Orchestration;
using SkillDefinition;


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

        _plannerFunction = kernel.CreateFunctionCall(
            skillName: SkillName,
            promptTemplate: promptTemplate,
            callFunctionsAutomatically: false,
            targetFunction: ActionPlan,
            maxTokens: 1024, temperature: 0.0);

        kernel.ImportSkill(this, SkillName);
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
        SKContext result = await _plannerFunction.InvokeAsync(_context, cancellationToken: cancellationToken).ConfigureAwait(false);
        ActionFunctionCall? response = result.ToFunctionCallResult<ActionFunctionCall>();

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
                        },
                        Required = new[] { "rationale", "function", "parameters" }
                    }
                },
                Required = new[] { "action" }
            },
            new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase })
    };
}
