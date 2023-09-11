// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Dynamic;

namespace Microsoft.SemanticKernel;

internal static class DynamicUtils
{
    internal static T? TryGetPropertyValue<T>(object obj, string propertyName, T? defaultValue = default)
    {
        if (obj is null)
        {
            return default;
        }

        var type = obj.GetType();
        if (type == typeof(ExpandoObject))
        {
            IDictionary<string, object> expandoDict = (ExpandoObject)obj;
            if (expandoDict.TryGetValue(propertyName, out var value))
            {
                return (T)value;
            }
            return defaultValue;
        }

        var prop = type.GetProperty(propertyName);
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
