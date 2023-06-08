// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Planning;

namespace SemanticKernel.Service.CopilotChat.Models;

/// <summary>
/// Information about a single proposed plan.
/// </summary>
public class ProposedPlan
{
    /// <summary>
    /// Plan object to be approved or invoked.
    /// </summary>
    [JsonPropertyName("proposedPlan")]
    public Plan Plan { get; set; }

    /// <summary>
    /// Indicates whether plan is Action (single-step) or Sequential (multi-step)
    /// </summary>
    public string Type { get; set; }

    /// <summary>
    /// State of plan: Approved, Rejected, or ApprovalRequired
    /// </summary>
    public string State { get; set; }

    /// <summary>
    /// Unique Id tied to response saved in chat history
    /// </summary>
    public string? MessageId { get; set; }

    /// <summary>
    /// Indicates whether user made edits to the plan before approval
    /// </summary>
    public Boolean Modified { get; set; }

    /// <summary>
    /// Create a new proposed plan.
    /// </summary>
    /// <param name="plan">Proposed plan object</param>
    public ProposedPlan(Plan plan, string type, string state, string? messageId = null, Boolean modified = false)
    {
        this.Plan = plan;
        this.Type = type;
        this.State = state;
        this.MessageId = messageId;
        this.Modified = false;
    }
}
