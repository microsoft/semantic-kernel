// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Sequential;

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Diagnostics;
using Orchestration;
using SkillDefinition;


/// <summary>
///  Sequential planner that uses the OpenAI chat completion function calling API to generate a step by step plan to fulfill a goal.
/// </summary>
public class StructuredSequentialPlanner : ISequentialPlanner
{
    /// <summary>
    ///  Initializes a new instance of the <see cref="StructuredSequentialPlanner"/> class.
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="config"></param>
    /// <param name="prompt"></param>
    public StructuredSequentialPlanner(
        IKernel kernel,
        SequentialPlannerConfig? config = null,
        string? prompt = null)
    {
        Verify.NotNull(kernel);
        _kernel = kernel;
        Config = config ?? new SequentialPlannerConfig();

        Config.ExcludedSkills.Add(RestrictedSkillName);

        _promptTemplate = prompt ?? EmbeddedResource.Read("structuredPrompt.txt");

        if (string.IsNullOrEmpty(_promptTemplate))
        {
            throw new Exception("The prompt template is empty");
        }
    }


    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }

        _context = _kernel.CreateNewContext();
        _context.Variables.Update(goal);
        List<FunctionDefinition> relevantFunctionDefinitions = await _context.GetFunctionDefinitions(goal, Config, cancellationToken).ConfigureAwait(false);

        _functionFlowFunction = _kernel.CreateFunctionCall(
            skillName: RestrictedSkillName,
            promptTemplate: _promptTemplate,
            callFunctionsAutomatically: false,
            targetFunction: SequentialPlan,
            callableFunctions: relevantFunctionDefinitions,
            maxTokens: Config.MaxTokens ?? 1024, temperature: 0.0);

        SKContext? result = await _functionFlowFunction.InvokeAsync(_context, cancellationToken: cancellationToken).ConfigureAwait(false);
        List<SequentialPlanCall>? functionCalls = result.ToFunctionCallResult<List<SequentialPlanCall>>();

        if (functionCalls is null)
        {
            throw new SKException("The planner failed to generate a response");
        }

        var plan = functionCalls.ToPlan(goal, _context.Skills);
        Console.WriteLine(plan.ToPlanString());
        return plan;
    }


    private SequentialPlannerConfig Config { get; }

    private SKContext? _context;
    private readonly IKernel _kernel;

    /// <summary>
    /// the function flow semantic function, which takes a goal and creates an xml plan that can be executed
    /// </summary>
    private ISKFunction? _functionFlowFunction;

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

    private readonly string _promptTemplate;
}
