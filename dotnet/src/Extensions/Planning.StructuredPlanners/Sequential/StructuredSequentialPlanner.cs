// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Structured.Sequential;

using System;
using System.Collections.Generic;
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
///  Sequential planner that uses the OpenAI chat completion function calling API to generate a step by step plan to fulfill a goal.
/// </summary>
public class StructuredSequentialPlanner : IStructuredPlanner
{
    /// <summary>
    ///  Initializes a new instance of the <see cref="StructuredSequentialPlanner"/> class.
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="config"></param>
    /// <param name="prompt"></param>
    /// <param name="loggerFactory"></param>
    public StructuredSequentialPlanner(
        IKernel kernel,
        StructuredPlannerConfig? config = null,
        string? prompt = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(kernel);

        _logger = loggerFactory is not null ? loggerFactory.CreateLogger(nameof(StructuredSequentialPlanner)) : NullLogger.Instance;

        Config = config ?? new StructuredPlannerConfig();

        Config.ExcludedSkills.Add(RestrictedSkillName);

        var promptTemplate = prompt ?? EmbeddedResource.Read("Prompts.Sequential.skprompt.txt");

        if (string.IsNullOrEmpty(promptTemplate))
        {
            throw new SKException("The prompt template is empty");
        }

        _plannerFunction = kernel.CreateFunctionCall(
            skillName: RestrictedSkillName,
            promptTemplate: promptTemplate,
            callFunctionsAutomatically: false,
            targetFunction: SequentialPlan,
            maxTokens: Config.MaxTokens, temperature: 0.0);
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
        List<SequentialFunctionCallResult>? functionCalls = result.ToFunctionCallResult<List<SequentialFunctionCallResult>>();

        if (functionCalls is null)
        {
            throw new SKException("The planner failed to generate a response");
        }

        var plan = functionCalls.ToPlan(goal, skillCollection);
        return plan;
    }


    private StructuredPlannerConfig Config { get; }
    private readonly SKContext _context;
    private readonly ISKFunction _plannerFunction;
    private readonly ILogger _logger;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedSkillName = "SequentialPlanner_Excluded";

    private static FunctionDefinition SequentialPlan => new()
    {
        Name = "submitPlan",
        Description = "Given a request or command or goal generate a step by step plan to fulfill the request using functions.",
        Parameters = BinaryData.FromObjectAsJson(
            new
            {
                Type = "object",
                Properties = new
                {
                    Plan = new
                    {
                        Type = "array",
                        Description = "Plan data structure",
                        Items = new
                        {
                            Type = "object",
                            Description = "A function call in the plan",
                            Properties = new
                            {
                                Rationale = new
                                {
                                    Type = "string",
                                    Description = "The rationale for choosing the function"
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
                                        Description = "Parameter name-value pair",
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
                                },
                                SetContextVariable = new
                                {
                                    Type = "string",
                                    Description = "Optional. The context variable to set the output of the function to"
                                },
                                AppendToResult = new
                                {
                                    Type = "string",
                                    Description = "Optional. Indicates whether to append the output of the function to the final result of the plan"
                                }
                            },
                            Required = new[] { "function", "rationale", "parameters" }
                        }
                    }
                },
                Required = new[] { "plan" }
            },
            new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase })
    };
}
