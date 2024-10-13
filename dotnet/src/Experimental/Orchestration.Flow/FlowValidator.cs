// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> main
=======
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> head
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
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
<<<<<<< HEAD
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

/// <summary>
/// The flow validator
/// </summary>
public class FlowValidator : IFlowValidator
{
    /// <inheritdoc/>
    public void Validate(Flow flow)
    {
        Verify.NotNullOrWhiteSpace(flow.Goal, nameof(flow.Goal));

        this.ValidateNonEmpty(flow);
        this.ValidatePartialOrder(flow);
        this.ValidateReferenceStep(flow);
        this.ValidateStartingMessage(flow);
        this.ValidatePassthroughVariables(flow);
    }

    private void ValidateStartingMessage(Flow flow)
    {
        foreach (var step in flow.Steps)
        {
            if (step.CompletionType is CompletionType.Optional or CompletionType.ZeroOrMore
                && string.IsNullOrEmpty(step.StartingMessage))
            {
                throw new ArgumentException(
                    $"Missing starting message for step={step.Goal} with completion type={step.CompletionType}");
            }
        }
    }

    private void ValidateNonEmpty(Flow flow)
    {
        if (flow.Steps.Count == 0)
        {
            throw new ArgumentException("Flow must contain at least one flow step.");
        }
    }

    private void ValidatePartialOrder(Flow flow)
    {
        try
        {
            var sorted = flow.SortSteps();
        }
        catch (Exception ex)
        {
            throw new ArgumentException("Flow steps must be a partial order set.", ex);
        }
    }

    private void ValidateReferenceStep(Flow flow)
    {
        var steps = flow.Steps
            .Select(step => step as ReferenceFlowStep)
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            .Where(step => step is not null);
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
            .Where(step => step is not null);
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
            .Where(step => step is not null);
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
            .Where(step => step is not null);
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
            .Where(step => step is not null);
=======
            .Where(step => step != null);
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        foreach (var step in steps)
        {
            Verify.NotNullOrWhiteSpace(step!.FlowName);

            if (step.Requires.Any())
            {
                throw new ArgumentException("Reference flow step cannot have any direct requirements.");
            }

            if (step.Provides.Any())
            {
                throw new ArgumentException("Reference flow step cannot have any direct provides.");
            }

            if (step.Plugins?.Count != 0)
            {
                throw new ArgumentException("Reference flow step cannot have any direct plugins.");
            }
        }
    }

    private void ValidatePassthroughVariables(Flow flow)
    {
        foreach (var step in flow.Steps)
        {
            if (step.CompletionType != CompletionType.AtLeastOnce
                && step.CompletionType != CompletionType.ZeroOrMore
                && step.Passthrough.Any())
            {
                throw new ArgumentException(
                    $"step={step.Goal} with completion type={step.CompletionType} cannot have passthrough variables as that is only applicable for the AtLeastOnce or ZeroOrMore completion types");
            }
        }
    }
}
