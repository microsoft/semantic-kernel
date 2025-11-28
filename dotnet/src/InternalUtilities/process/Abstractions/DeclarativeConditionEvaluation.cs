// Copyright (c) Microsoft. All rights reserved.
using System;
using System.IO;
using System.Text.Json;
using DevLab.JmesPath;

namespace Microsoft.SemanticKernel.Process.Internal;

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
            if (result is "true" or "\"true\"")
            {
                return true;
            }

            if (result is "false" or "\"false\"")
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

    /// <summary>
    /// Evaluates a JMESPath expression on a state object and returns the result as a string.
    /// </summary>
    /// <param name="data">The state object to evaluate against</param>
    /// <param name="jmesPathExpression">The JMESPath expression</param>
    /// <returns>The string result, or null if the result is null or cannot be converted to a string</returns>
    public static string? EvaluateToString(object data, string jmesPathExpression)
    {
        if (data == null || string.IsNullOrEmpty(jmesPathExpression))
        {
            return null;
        }

        JmesPath _jmesPath = new();

#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            // Convert your state object to a JSON string
            string jsonState = JsonSerializer.Serialize(data);

            // Evaluate the JMESPath expression
            string result = _jmesPath.Transform(jsonState, jmesPathExpression);

            // Handle different result scenarios
            if (string.IsNullOrEmpty(result) || result == "null")
            {
                return null;
            }

            // Parse the result to handle string escape sequences properly
            using JsonDocument doc = JsonDocument.Parse(result);
            JsonElement root = doc.RootElement;

            // Check if the result is a JSON string
            if (root.ValueKind == JsonValueKind.String)
            {
                // Return the string value without quotes
                return root.GetString();
            }
            // For non-string results, convert to string representation
            return root.ToString();
        }
        catch (Exception ex)
        {
            // Log the exception if needed
            Console.WriteLine($"Error evaluating JMESPath expression: {ex.Message}");
            return null;
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

internal static class JMESUpdate
{
    public static JsonDocument UpdateState(JsonDocument document, string path, StateUpdateOperations operation, object? value = null)
    {
        if (document == null)
        {
            throw new ArgumentNullException(nameof(document));
        }

        if (string.IsNullOrEmpty(path))
        {
            throw new ArgumentException("Path cannot be null or empty", nameof(path));
        }

        try
        {
            // Clone the document for immutability
            using var memoryStream = new MemoryStream();
            using (var jsonWriter = new Utf8JsonWriter(memoryStream))
            {
                UpdateJsonElement(document.RootElement, jsonWriter, path.Split('.'), 0, operation, value);
                jsonWriter.Flush();
            }

            memoryStream.Position = 0;
            return JsonDocument.Parse(memoryStream);
        }
        catch (JsonException ex)
        {
            throw new InvalidOperationException($"JSON processing error: {ex.Message}", ex);
        }
        catch (IOException ex)
        {
            throw new InvalidOperationException($"I/O error during JSON update: {ex.Message}", ex);
        }
        catch (ArgumentOutOfRangeException ex)
        {
            throw new ArgumentException($"Invalid path: {ex.Message}", ex);
        }
    }

    private static void UpdateJsonElement(JsonElement element, Utf8JsonWriter writer, string[] pathParts, int depth, StateUpdateOperations operation, object? value)
    {
        // If we're at the target element
        if (depth == pathParts.Length)
        {
            PerformOperation(element, writer, operation, value);
            return;
        }

        // If we're at an intermediate level
        switch (element.ValueKind)
        {
            case JsonValueKind.Object:
                writer.WriteStartObject();

                foreach (var property in element.EnumerateObject())
                {
                    if (property.Name == pathParts[depth])
                    {
                        writer.WritePropertyName(property.Name);
                        UpdateJsonElement(property.Value, writer, pathParts, depth + 1, operation, value);
                    }
                    else
                    {
                        property.WriteTo(writer);
                    }
                }

                writer.WriteEndObject();
                break;

            case JsonValueKind.Array:
                writer.WriteStartArray();

                // Check if the path part is a valid array index
                if (int.TryParse(pathParts[depth], out int index) && index < element.GetArrayLength())
                {
                    int i = 0;
                    foreach (var item in element.EnumerateArray())
                    {
                        if (i == index)
                        {
                            UpdateJsonElement(item, writer, pathParts, depth + 1, operation, value);
                        }
                        else
                        {
                            item.WriteTo(writer);
                        }
                        i++;
                    }
                }
                else
                {
                    // If the index is invalid, just copy the array unchanged
                    foreach (var item in element.EnumerateArray())
                    {
                        item.WriteTo(writer);
                    }
                }

                writer.WriteEndArray();
                break;

            default:
                // We've reached a leaf node before the full path was traversed
                // Just write the current value and return
                element.WriteTo(writer);
                break;
        }
    }

    private static void PerformOperation(JsonElement element, Utf8JsonWriter writer, StateUpdateOperations operation, object? value)
    {
        try
        {
            switch (operation)
            {
                case StateUpdateOperations.Set:
                    WriteValue(writer, value);
                    break;

                case StateUpdateOperations.Increment:
                    if (element.ValueKind != JsonValueKind.Number)
                    {
                        throw new InvalidOperationException("Cannot increment non-numeric value at the specified path");
                    }

                    if (element.TryGetInt32(out int intValue))
                    {
                        int incrementBy = value != null ? Convert.ToInt32(value) : 1;
                        writer.WriteNumberValue(intValue + incrementBy);
                    }
                    else if (element.TryGetDouble(out double doubleValue))
                    {
                        double incrementBy = value != null ? Convert.ToDouble(value) : 1.0;
                        writer.WriteNumberValue(doubleValue + incrementBy);
                    }
                    break;

                case StateUpdateOperations.Decrement:
                    if (element.ValueKind != JsonValueKind.Number)
                    {
                        throw new InvalidOperationException("Cannot decrement non-numeric value at the specified path");
                    }

                    if (element.TryGetInt32(out int intVal))
                    {
                        int decrementBy = value != null ? Convert.ToInt32(value) : 1;
                        writer.WriteNumberValue(intVal - decrementBy);
                    }
                    else if (element.TryGetDouble(out double doubleVal))
                    {
                        double decrementBy = value != null ? Convert.ToDouble(value) : 1.0;
                        writer.WriteNumberValue(doubleVal - decrementBy);
                    }
                    break;

                default:
                    throw new NotSupportedException($"Operation {operation} is not supported");
            }
        }
        catch (FormatException ex)
        {
            throw new ArgumentException($"Value format error: {ex.Message}", ex);
        }
        catch (OverflowException ex)
        {
            throw new ArgumentException($"Numeric overflow during operation: {ex.Message}", ex);
        }
    }

    private static void WriteValue(Utf8JsonWriter writer, object? value)
    {
        if (value == null)
        {
            writer.WriteNullValue();
            return;
        }

        switch (value)
        {
            case string strValue:
                writer.WriteStringValue(strValue);
                break;
            case int intValue:
                writer.WriteNumberValue(intValue);
                break;
            case long longValue:
                writer.WriteNumberValue(longValue);
                break;
            case double doubleValue:
                writer.WriteNumberValue(doubleValue);
                break;
            case decimal decimalValue:
                writer.WriteNumberValue(decimalValue);
                break;
            case bool boolValue:
                writer.WriteBooleanValue(boolValue);
                break;
            case DateTime dateTimeValue:
                writer.WriteStringValue(dateTimeValue);
                break;
            default:
                // For complex objects, serialize them to JSON
                var json = JsonSerializer.Serialize(value);
                using (var doc = JsonDocument.Parse(json))
                {
                    doc.RootElement.WriteTo(writer);
                }
                break;
        }
    }
}
