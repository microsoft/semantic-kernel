// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130 // Namespace does not match folder structure
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

/// <summary>
/// Extension methods for <see cref="Flow"/>.
/// </summary>
public static class FlowExtensions
{
    internal static List<FlowStep> SortSteps(this Flow flow)
    {
        var sortedSteps = new List<FlowStep>();
        var remainingSteps = new List<FlowStep>(flow.Steps);

        while (remainingSteps.Count > 0)
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            var independentStep = remainingSteps.FirstOrDefault(step => !remainingSteps.Any(step.DependsOn)) ??
                throw new KernelException("The plan contains circular dependencies.");
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            var independentStep = remainingSteps.FirstOrDefault(step => !remainingSteps.Any(step.DependsOn)) ??
                throw new KernelException("The plan contains circular dependencies.");
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            var independentStep = remainingSteps.FirstOrDefault(step => !remainingSteps.Any(step.DependsOn)) ??
                throw new KernelException("The plan contains circular dependencies.");
=======
            var independentStep = remainingSteps.FirstOrDefault(step => !remainingSteps.Any(step.DependsOn));

            if (independentStep is null)
            {
                throw new SKException("The plan contains circular dependencies.");
            }
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

            sortedSteps.Add(independentStep);
            remainingSteps.Remove(independentStep);
        }

        return sortedSteps;
    }

    /// <summary>
    /// Hydrate the reference steps in the flow.
    /// </summary>
    /// <param name="flow">the flow</param>
    /// <param name="flowRepository">the flow repository</param>
    /// <returns>The flow with hydrated steps</returns>
    /// <exception cref="ArgumentException">if referenced flow cannot be found in the repository</exception>
    public static async Task<Flow> BuildReferenceAsync(this Flow flow, IFlowCatalog flowRepository)
    {
        var referenceSteps = flow.Steps.OfType<ReferenceFlowStep>().ToList();

        foreach (var step in referenceSteps)
        {
            flow.Steps.Remove(step);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            var referencedFlow = await flowRepository.GetFlowAsync(step.FlowName).ConfigureAwait(false) ??
                throw new ArgumentException($"Referenced flow {step.FlowName} is not found");
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            var referencedFlow = await flowRepository.GetFlowAsync(step.FlowName).ConfigureAwait(false) ??
                throw new ArgumentException($"Referenced flow {step.FlowName} is not found");
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            var referencedFlow = await flowRepository.GetFlowAsync(step.FlowName).ConfigureAwait(false) ??
                throw new ArgumentException($"Referenced flow {step.FlowName} is not found");
=======
            var referencedFlow = await flowRepository.GetFlowAsync(step.FlowName).ConfigureAwait(false);
            if (referencedFlow is null)
            {
                throw new ArgumentException($"Referenced flow {step.FlowName} is not found");
            }
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

            referencedFlow.CompletionType = step.CompletionType;
            referencedFlow.AddPassthrough(step.Passthrough.ToArray());
            referencedFlow.StartingMessage = step.StartingMessage;
            referencedFlow.TransitionMessage = step.TransitionMessage;

            foreach (var referencedFlowStep in referencedFlow.Steps)
            {
                referencedFlowStep.AddPassthrough(step.Passthrough.ToArray(), isReferencedFlow: true);
            }

            flow.Steps.Add(referencedFlow);
        }

        return flow;
    }
}
