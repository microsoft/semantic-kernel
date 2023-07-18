// Copyright (c) Microsoft. All rights reserved.

using System.Linq;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Extension methods for <see cref="Plan"/> type.
/// </summary>
public static class PlanExtensions
{
    /// <summary>
    /// Constructs string representation of <see cref="Plan"/> without sensitive data.
    /// </summary>
    /// <param name="plan">Instance of <see cref="Plan"/> for string construction.</param>
    /// <param name="indent">Optional indentation.</param>
    public static string ToSafePlanString(this Plan plan, string indent = " ")
    {
        string planString = string.Join("\n", plan.Steps.Select(step =>
        {
            if (step.Steps.Count == 0)
            {
                string skillName = step.SkillName;
                string stepName = step.Name;

                return $"{indent}{indent}- {string.Join(".", skillName, stepName)}";
            }

            return step.ToSafePlanString(indent + indent);
        }));

        return planString;
    }

    /// <summary>
    /// Constructs string representation of <see cref="Plan"/>.
    /// </summary>
    /// <param name="plan">Instance of <see cref="Plan"/> for string construction.</param>
    /// <param name="indent">Optional indentation.</param>
    public static string ToPlanString(this Plan plan, string indent = " ")
    {
        string planString = string.Join("\n", plan.Steps.Select(step =>
        {
            if (step.Steps.Count == 0)
            {
                string skillName = step.SkillName;
                string stepName = step.Name;

                string parameters = string.Join(" ", step.Parameters.Select(param => $"{param.Key}='{param.Value}'"));
                if (!string.IsNullOrEmpty(parameters))
                {
                    parameters = $" {parameters}";
                }

                string? outputs = step.Outputs.FirstOrDefault();
                if (!string.IsNullOrEmpty(outputs))
                {
                    outputs = $" => {outputs}";
                }

                return $"{indent}{indent}- {string.Join(".", skillName, stepName)}{parameters}{outputs}";
            }

            return step.ToPlanString(indent + indent);
        }));

        return planString;
    }
}
