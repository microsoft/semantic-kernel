// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

internal static class DynamicUtils
{
    internal static T? TryGetPropertyValue<T>(object obj, string propertyName, T? defaultValue = default)
    {
        if (obj is null)
        {
            return default;
        }

        var prop = obj.GetType().GetProperty(propertyName);
        if (prop == null)
        {
            return defaultValue;
        }

        try
        {
            return (T)prop.GetValue(obj, null);
        }
        catch
        {
            return defaultValue;
        }
    }
}
