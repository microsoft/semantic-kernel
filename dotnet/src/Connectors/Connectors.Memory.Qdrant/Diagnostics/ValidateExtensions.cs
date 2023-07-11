// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics;

internal static class ValidateExtensions
{
    public static void Validate(IValidatable target)
    {
        target.Validate();
    }

    public static void Validate(params IValidatable[] targets)
    {
        foreach (var t in targets ?? Enumerable.Empty<IValidatable>())
        {
            Validate(t);
        }
    }

    public static void ValidateRequired(this IValidatable item, string arg)
    {
        Verify.NotNull(item, arg);
        item.Validate();
    }

    public static void ValidateRequired(this object item, string arg)
    {
        if (item is IValidatable v)
        {
            v.ValidateRequired(arg);
        }
        else
        {
            Verify.NotNull(item, arg);
        }
    }

    public static void ValidateRequired(this string item, string arg)
    {
        Verify.NotNullOrEmpty(item, arg);
    }

    public static void ValidateOptional(this IValidatable item, string arg)
    {
        if (item == null)
        {
            return;
        }

        item.ValidateRequired(arg);
    }

    [SuppressMessage("Design", "CA1031:Modify to catch a more specific allowed exception type, or rethrow exception",
        Justification = "Does not throw an exception by design.")]
    public static bool IsValid(this IValidatable target)
    {
        try
        {
            target.ValidateRequired("target");
            return true;
        }
        catch
        {
        }

        return false;
    }

    public static void ValidateRequired<T>(this IEnumerable<T> list, string arg)
    {
        Verify.NotNull(list, nameof(list));
        foreach (T item in list)
        {
            item?.ValidateRequired(arg);
        }
    }
}
