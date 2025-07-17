// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows.PowerFx;

internal static class TemplateExtensions
{
    public static string? Format(this RecalcEngine engine, IEnumerable<TemplateLine> template)
    {
        return string.Concat(template.Select(line => engine.Format(line)));
    }

    public static string? Format(this RecalcEngine engine, TemplateLine? line)
    {
        return string.Concat(line?.Segments.Select(segment => engine.Format(segment)) ?? [string.Empty]);
    }

    private static string? Format(this RecalcEngine engine, TemplateSegment segment)
    {
        if (segment is TextSegment textSegment)
        {
            return textSegment.Value;
        }

        if (segment is ExpressionSegment expressionSegment)
        {
            if (expressionSegment.Expression is not null)
            {
                if (expressionSegment.Expression.ExpressionText is not null)
                {
                    FormulaValue expressionValue = engine.Eval(expressionSegment.Expression.ExpressionText);
                    return expressionValue.Format();
                }
                if (expressionSegment.Expression.VariableReference is not null)
                {
                    FormulaValue expressionValue = engine.Eval(expressionSegment.Expression.VariableReference.ToString());
                    return expressionValue.Format();
                }
            }
        }

        throw new InvalidSegmentException($"Unsupported segment type: {segment.GetType().Name}");
    }
}
