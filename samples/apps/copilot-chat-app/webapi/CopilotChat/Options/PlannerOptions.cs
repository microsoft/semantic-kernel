// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel.DataAnnotations;
using SemanticKernel.Service.CopilotChat.Models;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Configuration options for the planner.
/// </summary>
public class PlannerOptions
{
    public const string PropertyName = "Planner";

    /// <summary>
    /// Define if the planner must be Sequential or not.
    /// </summary>
    [Required]
    public PlanType Type { get; set; } = PlanType.Action;

    /// <summary>
    /// The minimum relevancy score for a function to be considered during plan creation
    /// when using SequentialPlanner
    /// </summary>
    public double? RelevancyThreshold { get; set; } = null;
}
