// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Sequential;

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using AI.ChatCompletion;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.AzureSdk.FunctionCalling;
using Connectors.AI.OpenAI.ChatCompletion;
using Diagnostics;
using Orchestration;
using SkillDefinition;
using TemplateEngine.Prompt;


public class StructuredSequentialPlanner : ISequentialPlanner
{
    // private readonly string _promptTemplate = string.Empty;


    public StructuredSequentialPlanner(
        IKernel kernel,
        SequentialPlannerConfig? config = null,
        string? prompt = null)
    {
        Verify.NotNull(kernel);
        Config = config ?? new SequentialPlannerConfig();

        Config.ExcludedSkills.Add(RestrictedSkillName);

        // _promptTemplate = prompt ?? EmbeddedResource.Read("structuredprompt.txt");

        // this._functionFlowFunction = kernel.CreateSemanticFunction(
        //     promptTemplate,
        //     skillName: RestrictedSkillName,
        //     description: "Given a request or command or goal generate a step by step plan to " +
        //                  "fulfill the request using functions. This ability is also known as decision making and function flow",
        //     maxTokens: this.Config.MaxTokens ?? 1024,
        //     temperature: 0.0);

        _context = kernel.CreateNewContext();
        _chatCompletion = kernel.GetService<IChatCompletion>();
    }


    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }

        List<FunctionDefinition> relevantFunctionDefinitions = await _context.GetFunctionDefinitions(goal, Config, cancellationToken).ConfigureAwait(false);

        relevantFunctionDefinitions.Add(SequentialPlan);
        _context.Variables.Update(goal);

        var templateEngine = new PromptTemplateEngine();
        var prompt = await templateEngine.RenderAsync(PromptTemplate, _context, cancellationToken).ConfigureAwait(false);
        Console.WriteLine(prompt);
        var openAIChatCompletion = (OpenAIChatCompletion)_chatCompletion;

        var chatHistory = openAIChatCompletion.CreateNewChat(prompt);

        List<SKFunctionCall>? functionCalls = await openAIChatCompletion.GenerateResponseAsync<List<SKFunctionCall>>(
            chatHistory,
            new ChatRequestSettings()
                { Temperature = 0.2, MaxTokens = 1024 },
            SequentialPlan, relevantFunctionDefinitions.ToArray(), cancellationToken: cancellationToken).ConfigureAwait(false);

        if (functionCalls is null)
        {
            throw new SKException("The planner failed to generate a response");
        }

        Plan plan = functionCalls.ToPlan(goal, _context.Skills);
        Console.WriteLine(plan.ToPlanString());
        return plan;
    }


    private SequentialPlannerConfig Config { get; }

    private readonly SKContext _context;

    private readonly IChatCompletion _chatCompletion;

    /// <summary>
    /// the function flow semantic function, which takes a goal and creates an xml plan that can be executed
    /// </summary>
    private readonly ISKFunction _functionFlowFunction;

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

    private const string PromptTemplate = @"Create a step-by-step plan to satisfy the goal given, with the available functions.

To create a plan, follow these steps:
0. The plan should be as short as possible.
1. From a 'goal' property create a 'plan' property as a series of 'functionCalls'.
2. A plan has 'INPUT' available in context variables by default.
3. Only add functions to the plan that exist in the list of functions provided.
4. Only use functions that are required for the given goal.
5. Make sure each function call in the plan ends with a valid JSON object.
6. Always output valid JSON that can be parsed by a JSON parser.
7. If a plan cannot be created with the functions provided, return an empty plan array.

A function call in plan takes the form of a JSON object:
{
    ""rationale"": ""... reason for taking step ..."",
    ""function"": ""FullyQualifiedFunctionName"",
    ""parameters"": [
        {""name"": ""parameter1"", ""value"": ""value1""},
        {""name"": ""parameter2"", ""value"": ""value2""}
        // ... more parameters
    ],
    ""setContextVariable"": ""UNIQUE_VARIABLE_KEY"",    // optional
    ""appendToResult"": ""RESULT__UNIQUE_RESULT_KEY""    // optional
}

The 'setContextVariable' and 'appendToResult' properties are optional and used to save the 'output' of the function.

Use a '$' to reference a context variable in a parameter value, e.g. when `INPUT='world'` the parameter value 'Hello $INPUT' will evaluate to `Hello world`.

Functions do not have access to the context variables of other functions. Do not attempt to use context variables as arrays or objects. Instead, use available functions to extract specific elements or properties from context variables.

Goal: {{$input}}

Begin!";
}
