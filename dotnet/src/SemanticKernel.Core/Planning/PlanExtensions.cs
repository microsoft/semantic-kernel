// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.Extensions.Logging;

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
                string pluginName = step.PluginName;
                string stepName = step.Name;

                return $"{indent}{indent}- {string.Join(".", pluginName, stepName)}";
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
                string pluginName = step.PluginName;
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

                return $"{indent}{indent}- {string.Join(".", pluginName, stepName)}{parameters}{outputs}";
            }

            return step.ToPlanString(indent + indent);
        }));

        return planString;
    }

    /// <summary>
    /// Returns decorated instance of <see cref="IPlan"/> with enabled instrumentation.
    /// </summary>
    /// <param name="plan">Instance of <see cref="IPlan"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public static IPlan WithInstrumentation(this IPlan plan, ILoggerFactory? loggerFactory = null)
    {
        return new InstrumentedPlan(plan, loggerFactory);
    }
}
