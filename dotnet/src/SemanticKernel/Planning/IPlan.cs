// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning;

public interface IPlan
{
    string Goal { get; }

    ContextVariables State { get; }

    PlanStep Steps { get; }

    Task<IPlan> RunNextStepAsync(
        IKernel kernel,
        ContextVariables variables,
        CancellationToken cancellationToken = default);
}

public class PlanStep
{
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("selected_skill")]
    public string SelectedSkill { get; set; } = string.Empty;

    [JsonPropertyName("selected_function")]
    public string SelectedFunction { get; set; } = string.Empty;

    [JsonPropertyName("named_parameters")]
    public ContextVariables NamedParameters { get; set; } = new();

    [JsonPropertyName("output_key")]
    public string OutputKey { get; set; } = string.Empty;

    [JsonPropertyName("result_key")]
    public string ResultKey { get; set; } = string.Empty;

    [JsonPropertyName("children")]
    public IList<PlanStep> Children { get; } = new List<PlanStep>();
}
