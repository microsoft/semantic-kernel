// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Class used to copy and export data about parameters for planner and related scenarios.
/// </summary>
/// <param name="Name">Parameter name. The name must be alphanumeric (underscore is the only special char allowed).</param>
/// <param name="Description">Parameter description</param>
/// <param name="DefaultValue">Default parameter value, if not provided</param>
/// <param name="Type">Parameter type.</param>
/// <param name="IsRequired">Whether the parameter is required.</param>
public sealed record ParameterView(
    string Name,
    string? Description = null,
    string? DefaultValue = null,
    ParameterViewType? Type = null,
    bool? IsRequired = null);
