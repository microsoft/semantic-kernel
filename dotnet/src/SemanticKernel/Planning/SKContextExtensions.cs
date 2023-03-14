// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Orchestration.Extensions;
using Microsoft.SemanticKernel.SkillDefinition;
using static Microsoft.SemanticKernel.CoreSkills.PlannerSkill;

namespace Microsoft.SemanticKernel.Planning;

internal static class SKContextExtensions
{
    internal const string MemoryCollectionName = "Planning.SKFunctionsManual";

    /// <summary>
    /// Returns a string containing the manual for all available functions.
    /// </summary>
    /// <param name="context">The SKContext to get the functions manual for.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="config">The planner skill config.</param>
    /// <returns>A string containing the manual for all available functions.</returns>
    internal static async Task<string> GetFunctionsManualAsync(
        this SKContext context,
        string? semanticQuery = null,
        PlannerSkillConfig? config = null)
    {
        config ??= new PlannerSkillConfig();
        var functions = await context.GetAvailableFunctionsAsync(config, semanticQuery);

        return string.Join("\n\n", functions.Select(x => x.ToManualString()));
    }

    /// <summary>
    /// Returns a list of functions that are available to the user based on the semantic query and the excluded skills and functions.
    /// </summary>
    /// <param name="context">The SKContext</param>
    /// <param name="config">The planner skill config.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <returns>A list of functions that are available to the user based on the semantic query and the excluded skills and functions.</returns>
    internal static async Task<List<FunctionView>?> GetAvailableFunctionsAsync(
        this SKContext context,
        PlannerSkillConfig config,
        string? semanticQuery = null)
    {
        var excludedSkills = config.ExcludedSkills ?? new();
        var excludedFunctions = config.ExcludedFunctions ?? new();
        var includedFunctions = config.IncludedFunctions ?? new();

        context.ThrowIfSkillCollectionNotSet();

        var functionsView = context.Skills!.GetFunctionsView();

        var availableFunctions = functionsView.SemanticFunctions
            .Concat(functionsView.NativeFunctions)
            .SelectMany(x => x.Value)
            .Where(s => !excludedSkills.Contains(s.SkillName) && !excludedFunctions.Contains(s.Name))
            .ToList();

        List<FunctionView> result = availableFunctions;
        if (!string.IsNullOrEmpty(semanticQuery))
        {
            // If a Memory provider has not been registered, do not filter the functions.
            if (context.Memory is not NullMemory)
            {
                // catalog functions to memory
                foreach (var function in availableFunctions)
                {
                    var functionName = function.ToFunctionName();
                    var key = string.IsNullOrEmpty(function.Description) ? functionName : function.Description;

                    // It'd be nice if there were a saveIfNotExists method on the memory interface
                    var memoryEntry = await context.Memory.GetAsync(MemoryCollectionName, key, context.CancellationToken);
                    if (memoryEntry == null)
                    {
                        // TODO It'd be nice if the minRelevanceScore could be a parameter for each item that was saved to memory
                        // As folks may want to tune their functions to be more or less relevant.
                        await context.Memory.SaveInformationAsync(MemoryCollectionName, key, functionName, function.ToManualString(),
                            context.CancellationToken);
                    }
                }

                var memories = context.Memory.SearchAsync(MemoryCollectionName, semanticQuery, config.MaxFunctions, config.RelevancyThreshold,
                    context.CancellationToken);

                result = new List<FunctionView>();
                await foreach (var memoryEntry in memories)
                {
                    var function = availableFunctions.Find(x => x.ToFunctionName() == memoryEntry.Id);
                    if (function != null)
                    {
                        context.Log.LogDebug("Found relevant function. Relevance Score: {0}, Function: {1}", memoryEntry.Relevance, function.ToFunctionName());
                        result.Add(function);
                    }
                }

                foreach (var function in includedFunctions)
                {
                    if (!result.Any(x => x.Name == function))
                    {
                        var functionView = availableFunctions.Find(x => x.Name == function);
                        if (functionView != null)
                        {
                            result.Add(functionView);
                        }
                    }
                }
            }
        }

        return result;
    }

    /// <summary>
    /// Gets the planner skill config from the SKContext.
    /// </summary>
    /// <param name="context">The SKContext to get the planner skill config from.</param>
    /// <returns>The planner skill config.</returns>
    internal static PlannerSkillConfig GetPlannerSkillConfig(this SKContext context)
    {
        var config = new PlannerSkillConfig();

        if (context.Variables.Get(Parameters.RelevancyThreshold, out var threshold) && double.TryParse(threshold, out var parsedValue))
        {
            config.RelevancyThreshold = parsedValue;
        }

        if (context.Variables.Get(Parameters.MaxFunctions, out var maxFunctions) && int.TryParse(maxFunctions, out var parsedMaxFunctions))
        {
            config.MaxFunctions = parsedMaxFunctions;
        }

        if (context.Variables.Get(Parameters.ExcludedFunctions, out var excludedFunctions))
        {
            var excludedFunctionsList = excludedFunctions.Split(',').Select(x => x.Trim()).ToList();

            // Excluded functions and excluded skills from context.Variables should be additive to the default excluded functions and skills.
            config.ExcludedFunctions = config.ExcludedFunctions.Union(excludedFunctionsList).ToList();
        }

        if (context.Variables.Get(Parameters.ExcludedSkills, out var excludedSkills))
        {
            var excludedSkillsList = excludedSkills.Split(',').Select(x => x.Trim()).ToList();

            // Excluded functions and excluded skills from context.Variables should be additive to the default excluded functions and skills.
            config.ExcludedSkills = config.ExcludedSkills.Union(excludedSkillsList).ToList();
        }

        if (context.Variables.Get(Parameters.IncludedFunctions, out var includedFunctions))
        {
            var includedFunctionsList = includedFunctions.Split(',').Select(x => x.Trim()).ToList();

            // Included functions from context.Variables should not override the default excluded functions.
            var includedFunctionsListMinusExcludedFunctionsList = includedFunctionsList.Except(config.ExcludedFunctions).ToList();
            config.IncludedFunctions = includedFunctionsListMinusExcludedFunctionsList;
        }

        return config;
    }
}
