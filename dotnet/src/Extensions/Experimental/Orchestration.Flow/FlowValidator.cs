// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130

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
            .Where(step => step != null);

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

            if (step.Skills?.Count != 0)
            {
                throw new ArgumentException("Reference flow step cannot have any direct skills.");
            }
        }
    }
}
