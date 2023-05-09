// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable InconsistentNaming
public static class Utils
{
    // Function used to wrap long lines of text
    public static string WordWrap(string text, int maxLineLength)
    {
        var result = new StringBuilder();
        int i;
        var last = 0;
        var space = new[] { ' ', '\r', '\n', '\t' };
        do
        {
            i = last + maxLineLength > text.Length
                ? text.Length
                : (text.LastIndexOfAny(new[] { ' ', ',', '.', '?', '!', ':', ';', '-', '\n', '\r', '\t' }, Math.Min(text.Length - 1, last + maxLineLength)) + 1);
            if (i <= last) i = Math.Min(last + maxLineLength, text.Length);
            result.AppendLine(text.Substring(last, i - last).Trim(space));
            last = i;
        } while (i < text.Length);

        return result.ToString();
    }

    public static string ToPlanString(Microsoft.SemanticKernel.Planning.Plan originalPlan, string indent = " ")
    {
        string goalHeader = $"{indent}Goal: {originalPlan.Description}\n\n{indent}Steps:\n";

        string stepItems = string.Join("\n", originalPlan.Steps.Select(step =>
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
            else
            {
                string nestedSteps = ToPlanString(step, indent + indent);
                return nestedSteps;
            }
        }));

        return goalHeader + stepItems;
    }
}
