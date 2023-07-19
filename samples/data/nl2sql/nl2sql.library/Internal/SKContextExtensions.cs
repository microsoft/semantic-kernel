// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library.Internal;

using System;
using System.IO;
using Microsoft.SemanticKernel.Orchestration;

internal static class SKContextExtensions
{
    public static string GetResult(this SKContext context, string? label = null)
    {
        if (context == null)
        {
            return string.Empty;
        }

        if (context.ErrorOccurred)
        {
            if (context.LastException != null)
            {
                throw new InvalidDataException("No result available due to an unexpected failure.", context.LastException);
            }

            throw new InvalidDataException(context.LastErrorDescription);
        }

        var result = context.Result;

        if (!string.IsNullOrWhiteSpace(label))
        {
            // Trim out label, if present.
            int index = result.IndexOf($"{label}:", StringComparison.OrdinalIgnoreCase);
            if (index > -1)
            {
                result = result.Substring(index + label.Length + 1);
            }
        }

        return result;
    }
}
