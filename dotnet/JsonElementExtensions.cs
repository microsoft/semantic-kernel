// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Extension methods to convert a JsonElement to an Expando
/// </summary>
internal static class JsonElementExtensions
{
    // Method to convert a JsonElement to an Expando object
    static ExpandoObject ToExpando(JsonElement jsonElement)
    {
        // Create a new Expando object
        ExpandoObject expando = new ExpandoObject();

        // Get the dictionary of the Expando object
        IDictionary<string, object> expandoDict = expando;

        // Iterate over the properties and values of the JsonElement
        foreach (JsonProperty property in jsonElement.EnumerateObject())
        {
            // Get the property name and value
            string name = property.Name;
            JsonElement value = property.Value;

            // Check the value type and add it to the Expando object accordingly
            switch (value.ValueKind)
            {
                case JsonValueKind.Object:
                    // If the value is an object, recursively convert it to an Expando object
                    expandoDict.Add(name, JsonElementToExpando(value));
                    break;
                case JsonValueKind.Array:
                    // If the value is an array, convert it to a list of objects
                    List<object> list = new List<object>();
                    foreach (JsonElement element in value.EnumerateArray())
                    {
                        // If the element is an object, recursively convert it to an Expando object
                        if (element.ValueKind == JsonValueKind.Object)
                        {
                            list.Add(ToExpando(element));
                        }
                        else
                        {
                            // Otherwise, add the element value directly
                            list.Add(element.GetValue());
                        }
                    }
                    expandoDict.Add(name, list);
                    break;
                default:
                    // For other value types, add the value directly
                    expandoDict.Add(name, value.GetValue());
                    break;
            }
        }

        // Return the Expando object
        return expando;
    }

    // Extension method to get the value of a JsonElement based on its type
    public static object GetValue(this JsonElement jsonElement)
    {
        switch (jsonElement.ValueKind)
        {
            case JsonValueKind.String:
                return jsonElement.GetString();
            case JsonValueKind.Number:
                return jsonElement.GetDouble();
            case JsonValueKind.True:
                return true;
            case JsonValueKind.False:
                return false;
            case JsonValueKind.Null:
                return null;
            default:
                throw new InvalidOperationException($"Unsupported value kind: {jsonElement.ValueKind}");
        }
    }
}
