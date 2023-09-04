// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel.Orchestration;

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Extensions.Logging;
using Memory;
using Planning;
using Planning.Structured;
using Planning.Structured.Extensions;
using Planning.Structured.Sequential;
using SkillDefinition;

#pragma warning restore IDE0130


public static class StructuredPlannerExtensions
{
    internal const string PlannerMemoryCollectionName = "Planning.SKFunctionsManual";

    internal const string PlanSKFunctionsAreRemembered = "Planning.SKFunctionsAreRemembered";


    /// <summary>
    /// Returns a string containing the manual for all available functions.
    /// </summary>
    /// <param name="context">The SKContext to get the functions manual for.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="config">The planner skill config.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A string containing the manual for all available functions.</returns>
    public static async Task<string> GetFunctionsManualAsync(
        this SKContext context,
        string? semanticQuery = null,
        StructuredPlannerConfig? config = null,
        CancellationToken cancellationToken = default)
    {
        config ??= new StructuredPlannerConfig();

        // Use configured function provider if available, otherwise use the default SKContext function provider.
        FunctionsView functions = config.GetAvailableFunctionsAsync is null
            ? await context.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken).ConfigureAwait(false)
            : await config.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken).ConfigureAwait(false);

        return functions.ToManualString();
    }


    /// <summary>
    ///  Gets a list of functions that are available to the user based on the semantic query and the excluded skills and functions.
    /// </summary>
    /// <param name="context"></param>
    /// <param name="semanticQuery"></param>
    /// <param name="config"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static async Task<List<FunctionDefinition>> GetFunctionDefinitions(
        this SKContext context,
        string? semanticQuery = null,
        StructuredPlannerConfig? config = null,
        CancellationToken cancellationToken = default)
    {
        config ??= new StructuredPlannerConfig();

        // Use configured function provider if available, otherwise use the default SKContext function provider.
        FunctionsView functions = config.GetAvailableFunctionsAsync is null
            ? await context.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken).ConfigureAwait(false)
            : await config.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken).ConfigureAwait(false);

        return functions.ToFunctionDefinitions().ToList();
    }


    /// <summary>
    /// Returns a list of functions that are available to the user based on the semantic query and the excluded skills and functions.
    /// </summary>
    /// <param name="context">The SKContext</param>
    /// <param name="config">The planner config.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A list of functions that are available to the user based on the semantic query and the excluded skills and functions.</returns>
    public static async Task<FunctionsView> GetAvailableFunctionsAsync(
        this SKContext context,
        StructuredPlannerConfig config,
        string? semanticQuery = null,
        CancellationToken cancellationToken = default)
    {
        var functionsView = context.Skills.GetFunctionsView();

        List<FunctionView> availableFunctions = functionsView.SemanticFunctions
            .Concat(functionsView.NativeFunctions)
            .SelectMany(x => x.Value)
            .Where(s => !config.ExcludedSkills.Contains(s.SkillName) && !config.ExcludedFunctions.Contains(s.Name))
            .ToList();

        List<FunctionView>? result = null;

        if (string.IsNullOrEmpty(semanticQuery) || config.Memory is NullMemory || config.RelevancyThreshold is null)
        {
            // If no semantic query is provided, return all available functions.
            // If a Memory provider has not been registered, return all available functions.
            result = availableFunctions;
        }
        else
        {
            result = new List<FunctionView>();

            // Remember functions in memory so that they can be searched.
            await RememberFunctionsAsync(context, config.Memory, availableFunctions, cancellationToken).ConfigureAwait(false);

            // Search for functions that match the semantic query.
            IAsyncEnumerable<MemoryQueryResult> memories = config.Memory.SearchAsync(
                PlannerMemoryCollectionName,
                semanticQuery!,
                config.MaxRelevantFunctions,
                config.RelevancyThreshold.Value,
                cancellationToken: cancellationToken);

            // Add functions that were found in the search results.
            result.AddRange(await GetRelevantFunctionsAsync(context, availableFunctions, memories, cancellationToken).ConfigureAwait(false));

            // Add any missing functions that were included but not found in the search results.
            IEnumerable<FunctionView> missingFunctions = config.IncludedFunctions
                .Except(result.Select(x => x.Name))
                .Join(availableFunctions, f => f, af => af.Name, (_, af) => af);

            result.AddRange(missingFunctions);
        }

        functionsView = new FunctionsView();
        IOrderedEnumerable<FunctionView> functions = result
            .OrderBy(x => x.SkillName)
            .ThenBy(x => x.Name);

        foreach (FunctionView functionView in functions)
        {
            functionsView.AddFunction(functionView);
        }
        return functionsView;
    }


    private static async Task<IEnumerable<FunctionView>> GetRelevantFunctionsAsync(
        SKContext context,
        IEnumerable<FunctionView> availableFunctions,
        IAsyncEnumerable<MemoryQueryResult> memories,
        CancellationToken cancellationToken = default)
    {
        ILogger? logger = null;
        ConcurrentBag<FunctionView> relevantFunctions = new ConcurrentBag<FunctionView>();

        await foreach (var memoryEntry in memories.WithCancellation(cancellationToken))
        {
            var function = availableFunctions.FirstOrDefault(x => x.ToFullyQualifiedName() == memoryEntry.Metadata.Id);

            if (function != null)
            {
                logger ??= context.LoggerFactory.CreateLogger(typeof(SKContext));

                if (logger.IsEnabled(LogLevel.Debug))
                {
                    logger.LogDebug("Found relevant function. Relevance Score: {0}, Function: {1}", memoryEntry.Relevance, function.ToFullyQualifiedName());
                }

                relevantFunctions.Add(function);
            }
        }

        return relevantFunctions;
    }


    /// <summary>
    /// Saves all available functions to memory.
    /// </summary>
    /// <param name="context">The SKContext to save the functions to.</param>
    /// <param name="memory">The memory provided to store the functions to.</param>
    /// <param name="availableFunctions">The available functions to save.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    internal static async Task RememberFunctionsAsync(
        SKContext context,
        ISemanticTextMemory memory,
        List<FunctionView> availableFunctions,
        CancellationToken cancellationToken = default)
    {
        // Check if the functions have already been saved to memory.
        if (context.Variables.ContainsKey(PlanSKFunctionsAreRemembered))
        {
            return;
        }

        foreach (var function in availableFunctions)
        {
            var functionName = function.ToFullyQualifiedName();
            var key = functionName;
            var description = string.IsNullOrEmpty(function.Description) ? functionName : function.Description;
            var textToEmbed = function.ToEmbeddingString();

            // It'd be nice if there were a saveIfNotExists method on the memory interface
            var memoryEntry = await memory.GetAsync(PlannerMemoryCollectionName, key, false,
                cancellationToken).ConfigureAwait(false);

            if (memoryEntry == null)
            {
                // TODO It'd be nice if the minRelevanceScore could be a parameter for each item that was saved to memory
                // As folks may want to tune their functions to be more or less relevant.
                // Memory now supports these such strategies.
                await memory.SaveInformationAsync(PlannerMemoryCollectionName, textToEmbed, key, description,
                    string.Empty, cancellationToken).ConfigureAwait(false);
            }
        }

        // Set a flag to indicate that the functions have been saved to memory.
        context.Variables.Set(PlanSKFunctionsAreRemembered, "true");
    }


    internal static async Task RememberFunctionsAsync(
        IKernel context,
        ISemanticTextMemory memory,
        List<FunctionView> availableFunctions,
        CancellationToken cancellationToken = default)
    {
        // Check if the functions have already been saved to memory.

        foreach (var function in availableFunctions)
        {
            var functionName = function.ToFullyQualifiedName();
            var key = functionName;
            var description = string.IsNullOrEmpty(function.Description) ? functionName : function.Description;
            var textToEmbed = function.ToEmbeddingString();

            // It'd be nice if there were a saveIfNotExists method on the memory interface
            var memoryEntry = await memory.GetAsync(PlannerMemoryCollectionName, key, false,
                cancellationToken).ConfigureAwait(false);

            if (memoryEntry == null)
            {
                // TODO It'd be nice if the minRelevanceScore could be a parameter for each item that was saved to memory
                // As folks may want to tune their functions to be more or less relevant.
                // Memory now supports these such strategies.
                await memory.SaveInformationAsync(PlannerMemoryCollectionName, textToEmbed, key, description,
                    string.Empty, cancellationToken).ConfigureAwait(false);
            }
        }
    }


    public static Plan ToPlan(this IEnumerable<SequentialPlanCall> functionCalls, string goal, IReadOnlySkillCollection skillCollection)
    {
        // Initialize Plan with goal
        var plan = new Plan(goal);

        List<SequentialPlanCall> functions = functionCalls.ToList();

        if (functions.Count == 0)
        {
            Console.WriteLine("No functions found");
            return plan;
        }

        // Process each functionCall
        foreach (var functionCall in functions)
        {
            skillCollection.TryGetFunction(functionCall, out var skillFunction);

            if (skillFunction is not null)
            {
                var planStep = new Plan(skillFunction);

                var functionVariables = new ContextVariables();

                foreach (var parameter in functionCall.Parameters)
                {
                    functionVariables.Set(parameter.Name, parameter.Value);
                }

                List<string> functionOutputs = new();

                if (!string.IsNullOrEmpty(functionCall.SetContextVariable))
                {
                    functionOutputs.Add(functionCall.SetContextVariable!);
                }

                List<string> functionResults = new();

                if (!string.IsNullOrEmpty(functionCall.AppendToResult))
                {
                    functionOutputs.Add(functionCall.AppendToResult!);
                    functionResults.Add(functionCall.AppendToResult!);
                }

                planStep.Outputs = functionOutputs;
                planStep.Parameters = functionVariables;

                foreach (var result in functionResults)
                {
                    plan.Outputs.Add(result);
                }

                plan.AddSteps(planStep);
            }
            else
            {
                throw new Exception($"Function '{functionCall.Function}' not found.");
            }
        }

        return plan;
    }
}
