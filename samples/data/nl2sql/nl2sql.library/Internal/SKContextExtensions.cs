// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library.Internal;

using System.IO;
using Microsoft.SemanticKernel.Orchestration;

internal static class SKContextExtensions
{
    public static bool TryGetResult(this SKContext context, out string result, string? label = null, bool require = true)
    {
        result = string.Empty;

        if (context?.ErrorOccurred != false)
        {
            return false;
        }

        result = context.Result;

        if (!string.IsNullOrWhiteSpace(label))
        {
            result.TryGetValue(out result, label, require);
        }

        return true;
    }

    public static string GetResult(this SKContext context, string? label = null, bool require = true)
    {
        if (context == null)
        {
            return string.Empty;
        }

        if (!context.TryGetResult(out var result, label, require))
        {
            if (context.LastException != null)
            {
                throw new InvalidDataException("No result available due to an unexpected failure.", context.LastException);
            }

            throw new InvalidDataException(context.LastErrorDescription);
        }

        return result;
    }
}
