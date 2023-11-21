// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Planning.Handlebars.Models;
#pragma warning restore IDE0130

internal class HandlebarsParameterTypeMetadata
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("isComplexType")]
    public bool IsComplex { get; set; } = false;

    /// <summary>
    /// If this is a complex type, this will contain the properties of the complex type.
    /// </summary>
    [JsonPropertyName("properties")]
    public List<SKParameterMetadata> Properties { get; set; } = new();

    // Override the Equals method to compare the property values
    public override bool Equals(object obj)
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

    // A helper method to compare two lists of SKParameterMetadata
    private static bool ArePropertiesEqual(List<SKParameterMetadata> list1, List<SKParameterMetadata> list2)
    {
        // Check if the lists are null or have different lengths
        if (list1 == null || list2 == null || list1.Count != list2.Count)
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
        // Use a prime number to combine the hash codes of the properties
        int hash = 17;

        // Use the default string hash code for the Name property
        hash = (hash * 31) + (this.Name?.GetHashCode() ?? 0);

        // Use the default bool hash code for the IsComplex property
        hash = (hash * 31) + this.IsComplex.GetHashCode();

        // Use a helper method to compute the hash code of the Properties list
        hash = (hash * 31) + GetPropertiesHashCode(this.Properties);

        return hash;
    }

    // A helper method to compute the hash code of a list of SKParameterMetadata
    private static int GetPropertiesHashCode(List<SKParameterMetadata> list)
    {
        // Use a prime number to combine the hash codes of the elements
        int hash = 19;

        // Use the default SKParameterMetadata hash code for each element
        foreach (var item in list)
        {
            hash = (hash * 37) + GetPropertyHashCode(item);
        }

        return hash;
    }

    // A helper method to compute the hash code of a SKParameterMetadata object
    private static int GetPropertyHashCode(SKParameterMetadata property)
    {
        // Use a prime number to combine the hash codes of the elements
        int hash = 23;

        // Use the default string hash code for each element's name
        hash = (hash * 41) + (property?.Name.GetHashCode() ?? 0);

        // Use the default type hash code for each element's ParameterType
        hash = (hash * 41) + (property?.ParameterType?.GetHashCode() ?? 0);

        return hash;
    }
}
