// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;
using DevLab.JmesPath;

namespace Microsoft.SemanticKernel.Process;
internal class ProcessStateManager
{
    private readonly Type? _stateType;
    private object? _instance;

    public ProcessStateManager(Type? stateType, object? initialState = null)
    {
        this._stateType = stateType;
        this._instance = initialState;

        if (initialState is null && stateType is not null)
        {
            // Create an instance of the state type if not provided
            this._instance = Activator.CreateInstance(stateType);
        }
    }

    public async Task ReduceAsync(Func<Type, object?, Task<object?>> func)
    {
        Verify.NotNull(func);
        if (this._stateType is null)
        {
            throw new KernelException("State type is not defined.");
        }

        this._instance = await func(this._stateType, this._instance).ConfigureAwait(false);
    }
}

internal static class JMESPathConditionEvaluator
{
    public static bool EvaluateCondition(object? data, string jmesPathExpression)
    {
        if (data == null || string.IsNullOrEmpty(jmesPathExpression))
        {
            return false;
        }

        JmesPath _jmesPath = new();
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            // Convert your state object to a JSON string
            string jsonState = JsonSerializer.Serialize(data);

            // Evaluate the JMESPath expression
            string result = _jmesPath.Transform(jsonState, jmesPathExpression);

            // Parse the result
            if (string.IsNullOrEmpty(result) || result == "null")
            {
                return false;
            }

            // Handle different result types
            if (result == "true" || result == "\"true\"")
            {
                return true;
            }

            if (result == "false" || result == "\"false\"")
            {
                return false;
            }

            // If the result is a number, check if it's non-zero
            if (double.TryParse(result.Trim('"'), out double numericResult))
            {
                return numericResult != 0;
            }

            // If it's a non-empty array or object, consider it true
            using JsonDocument doc = JsonDocument.Parse(result);
            JsonElement root = doc.RootElement;

            switch (root.ValueKind)
            {
                case JsonValueKind.Array:
                    return root.GetArrayLength() > 0;
                case JsonValueKind.Object:
                    // Check if object has any properties
                    using (var enumerator = root.EnumerateObject())
                    {
                        return enumerator.MoveNext(); // True if there's at least one property
                    }
                case JsonValueKind.String:
                    return !string.IsNullOrEmpty(root.GetString());
                default:
                    return true; // Any other non-null value is considered true
            }
        }
        catch (Exception ex)
        {
            // Log the exception if needed
            Console.WriteLine($"Error evaluating JMESPath expression: {ex.Message}");
            return false;
        }
#pragma warning restore CA1031 // Do not catch general exception types
    }
}

internal static class ConditionEvaluator
{
    public static bool EvaluateCondition(object? data, ConditionExpression expression)
    {
        if (data == null || expression == null)
        {
            return false;
        }

        // Get the property value using reflection
        var propertyValue = GetPropertyValue(data, expression.Path);

        // If property doesn't exist, the condition is false
        if (propertyValue == null)
        {
            return false;
        }

        // Convert the target value to the same type as the property
        var typedValue = ConvertValue(expression.Value, propertyValue.GetType());

        // Evaluate based on the operator
        return EvaluateWithOperator(propertyValue, expression.Operator, typedValue);
    }

    private static object? GetPropertyValue(object data, string path)
    {
        // Handle nested properties with dot notation (e.g., "User.Address.City")
        var properties = path.Split('.');
        object? current = data;

        foreach (var property in properties)
        {
            if (current == null)
            {
                return null;
            }

            // Get property info using reflection
            var propertyInfo = current.GetType().GetProperty(property);
            if (propertyInfo == null)
            {
                return null;
            }

            // Get the value
            current = propertyInfo.GetValue(current);
        }

        return current;
    }

    private static object? ConvertValue(object value, Type targetType)
    {
        if (value == null)
        {
            return null;
        }

        // Handle numeric conversions which are common in comparison operations
        if (targetType.IsNumeric() && value is IConvertible)
        {
            return Convert.ChangeType(value, targetType);
        }

        return value;
    }

    private static bool EvaluateWithOperator(object left, ConditionOperator op, object? right)
    {
        // Special case for null values
        if (left == null && right == null)
        {
            return op == ConditionOperator.Equal;
        }

        if (left == null || right == null)
        {
            return op == ConditionOperator.NotEqual;
        }

        // If both values are comparable
        if (left is IComparable comparable)
        {
            int comparisonResult = comparable.CompareTo(right);

            switch (op)
            {
                case ConditionOperator.Equal: return comparisonResult == 0;
                case ConditionOperator.NotEqual: return comparisonResult != 0;
                case ConditionOperator.GreaterThan: return comparisonResult > 0;
                case ConditionOperator.GreaterThanOrEqual: return comparisonResult >= 0;
                case ConditionOperator.LessThan: return comparisonResult < 0;
                case ConditionOperator.LessThanOrEqual: return comparisonResult <= 0;
                default: throw new NotSupportedException($"Operator {op} is not supported.");
            }
        }

        // Fallback to simple equality
        return left.Equals(right);
    }
}

// Extension method to check if a type is numeric
internal static class TypeExtensions
{
    public static bool IsNumeric(this Type type)
    {
        if (type == null)
        {
            return false;
        }

        switch (Type.GetTypeCode(type))
        {
            case TypeCode.Byte:
            case TypeCode.Decimal:
            case TypeCode.Double:
            case TypeCode.Int16:
            case TypeCode.Int32:
            case TypeCode.Int64:
            case TypeCode.SByte:
            case TypeCode.Single:
            case TypeCode.UInt16:
            case TypeCode.UInt32:
            case TypeCode.UInt64:
                return true;
            default:
                return false;
        }
    }
}
