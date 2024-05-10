// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

internal sealed class HandlebarsParameterTypeMetadata
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("isComplexType")]
    public bool IsComplex { get; set; } = false;

    /// <summary>
    /// If this is a complex type, this will contain the properties of the complex type.
    /// </summary>
    [JsonPropertyName("properties")]
    public List<KernelParameterMetadata> Properties { get; set; } = [];

    // Override the Equals method to compare the property values
    public override bool Equals(object? obj)
    {
        // Check to make sure the object is the expected type
        if (obj is not HandlebarsParameterTypeMetadata other)
        {
            return false;
        }

        // Compare the Name and IsComplex properties
        if (this.Name != other.Name || this.IsComplex != other.IsComplex)
        {
            return false;
        }

        // Compare the Properties lists using a helper method
        return ArePropertiesEqual(this.Properties, other.Properties);
    }

    // A helper method to compare two lists of KernelParameterMetadata
    private static bool ArePropertiesEqual(List<KernelParameterMetadata> list1, List<KernelParameterMetadata> list2)
    {
        // Check if the lists are null or have different lengths
        if (list1 is null || list2 is null || list1.Count != list2.Count)
        {
            return false;
        }

        // Compare the elements of the lists by comparing the Name and ParameterType properties
        for (int i = 0; i < list1.Count; i++)
        {
            if (!list1[i].Name.Equals(list2[i].Name, System.StringComparison.Ordinal) || !list1[i].ParameterType!.Equals(list2[i].ParameterType))
            {
                return false;
            }
        }

        // If all elements are equal, return true
        return true;
    }

    // Override the GetHashCode method to generate a hash code based on the property values
    public override int GetHashCode()
    {
        HashCode hash = default;
        hash.Add(this.Name);
        hash.Add(this.IsComplex);
        foreach (var item in this.Properties)
        {
            // Combine the Name and ParameterType properties into one hash code
            hash.Add(
                HashCode.Combine(item.Name, item.ParameterType)
            );
        }

        return hash.ToHashCode();
    }
}
