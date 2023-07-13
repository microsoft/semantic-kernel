// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Planning.Action;

/// <summary>
/// Plan data structure returned by the basic planner semantic function
/// </summary>
internal sealed class ActionPlanResponse
{
    public sealed class PlanData
    {
        /// <summary>
        /// Rationale given by the LLM for choosing the function
        /// </summary>
        public string Rationale { get; set; } = string.Empty;

        /// <summary>
        /// Name of the function chosen
        /// </summary>
        public string Function { get; set; } = string.Empty;

        /// <summary>
        /// Parameter values
        /// </summary>
        public Dictionary<string, object> Parameters { get; set; } = new();
    }

    /// <summary>
    /// Plan information
    /// </summary>
    public PlanData Plan { get; set; } = new();
}
