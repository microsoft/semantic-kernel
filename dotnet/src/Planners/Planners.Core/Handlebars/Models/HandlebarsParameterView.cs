// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Planners.Handlebars.Models;

internal class HandlebarsParameterTypeView
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("isComplexType")]
    public bool IsComplexType { get; set; } = false;

    /// <summary>
    /// If this is a complex type, this will contain the properties of the complex type.
    /// </summary>
    [JsonPropertyName("properties")]
    public List<ParameterView> Properties { get; set; } = new();

    // Override the Equals method to compare the property values
    public override bool Equals(object obj)
    {
        // Check if the obj is null or of a different type
        if (obj == null || obj.GetType() != this.GetType())
        {
            return false;
        }

        // Cast the obj to HandlebarsParameterTypeView
        var other = (HandlebarsParameterTypeView)obj;

        // Compare the Name and IsComplexType properties
        if (this.Name != other.Name || this.IsComplexType != other.IsComplexType)
        {
            return false;
        }

        // Compare the Properties lists using a helper method
        return ArePropertiesEqual(this.Properties, other.Properties);
    }

    // A helper method to compare two lists of ParameterView
    private static bool ArePropertiesEqual(List<ParameterView> list1, List<ParameterView> list2)
    {
        // Check if the lists are null or have different lengths
        if (list1 == null || list2 == null || list1.Count != list2.Count)
        {
            return false;
        }

        // Compare the elements of the lists using the default ParameterView equality
        for (int i = 0; i < list1.Count; i++)
        {
            if (!list1[i].Equals(list2[i]))
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

        // Use the default bool hash code for the IsComplexType property
        hash = (hash * 31) + this.IsComplexType.GetHashCode();

        // Use a helper method to compute the hash code of the Properties list
        hash = (hash * 31) + GetPropertiesHashCode(this.Properties);

        return hash;
    }

    // A helper method to compute the hash code of a list of ParameterView
    private static int GetPropertiesHashCode(List<ParameterView> list)
    {
        // Use a prime number to combine the hash codes of the elements
        int hash = 19;

        // Use the default ParameterView hash code for each element
        foreach (var item in list)
        {
            hash = (hash * 37) + (item?.GetHashCode() ?? 0);
        }

        return hash;
    }
}
