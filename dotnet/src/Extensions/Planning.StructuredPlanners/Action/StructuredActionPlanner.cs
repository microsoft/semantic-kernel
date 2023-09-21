// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Structured.Action;

using System;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Diagnostics;
using Extensions;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Orchestration;


/// <summary>
///  Action planner that uses the OpenAI chat completion function calling API to select the best action to take.
/// </summary>
public class StructuredActionPlanner : IStructuredPlanner
{

    /// <summary>
    ///  Initializes a new instance of the <see cref="StructuredActionPlanner"/> class.
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="config"></param>
    /// <param name="prompt"></param>
    /// <param name="loggerFactory"></param>
    public StructuredActionPlanner(
        IKernel kernel,
        StructuredPlannerConfig? config = null,
        string? prompt = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(kernel);

        _logger = loggerFactory is not null ? loggerFactory.CreateLogger(nameof(StructuredActionPlanner)) : NullLogger.Instance;

        Config = config ?? new StructuredPlannerConfig();
        Config.ExcludedSkills.Add(SkillName);

        if (!string.IsNullOrEmpty(prompt))
        {
            _promptTemplate = prompt!;
        }

        _plannerFunction = kernel.CreateFunctionCall(
            skillName: SkillName,
            promptTemplate: _promptTemplate,
            callFunctionsAutomatically: false,
            targetFunction: ActionPlan,
            maxTokens: 1024, temperature: 0.0);

        _context = kernel.CreateNewContext();
    }


    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }
        _context.Variables.Update(goal);

        FunctionCollection skillCollection = await _context.GetSkillCollection(Config, goal).ConfigureAwait(false);

        _plannerFunction.SetDefaultFunctionCollection(skillCollection);

        SKContext? result = await _plannerFunction.InvokeAsync(_context, cancellationToken: cancellationToken).ConfigureAwait(false);
        ActionFunctionCall? response = result.ToFunctionCallResult<ActionFunctionCall>();

        if (response is null)
        {
            throw new SKException("The planner failed to generate a response");
        }

        if (!_context.Functions.TryGetFunction(response, out ISKFunction? function))
        {
            throw new SKException($"The function {response.Function} is not available");
        }

        Plan plan = new(goal, function!);
        plan.Steps[0].Parameters = response.FunctionParameters();

        return plan;
    }


    private StructuredPlannerConfig Config { get; }

    // Context used to access the list of functions in the kernel
    private readonly SKContext _context;
    private readonly ILogger _logger;

    // Planner semantic function
    private readonly ISKFunction _plannerFunction;
    private const string SkillName = "this";

    private readonly string _promptTemplate = "Decide the best action to take to achieve the user's goal." +
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
