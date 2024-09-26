// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using System.Text.Json.Serialization;

namespace Models;
public class NewCustomerForm
{
    [JsonPropertyName("userFirstName")]
    public string UserFirstName { get; set; } = "";

    [JsonPropertyName("userLastName")]
    public string UserLastName { get; set; } = "";

    [JsonPropertyName("userDateOfBirth")]
    public string UserDateOfBirth { get; set; } = "";

    [JsonPropertyName("userState")]
    public string UserState { get; set; } = "";

    [JsonPropertyName("userPhoneNumber")]
    public string UserPhoneNumber { get; set; } = "";

    [JsonPropertyName("userId")]
    public string UserId { get; set; } = "";

    [JsonPropertyName("userEmail")]
    public string UserEmail { get; set; } = "";

    public NewCustomerForm CopyWithDefaultValues(string defaultStringValue = "Unanswered")
    {
        NewCustomerForm copy = new();
        PropertyInfo[] properties = typeof(NewCustomerForm).GetProperties();

        foreach (PropertyInfo property in properties)
        {
            // Get the value of the property  
            string? value = property.GetValue(this) as string;

            // Check if the value is an empty string  
            if (string.IsNullOrEmpty(value))
            {
                property.SetValue(copy, defaultStringValue);
            }
            else
            {
                property.SetValue(copy, value);
            }
        }

        return copy;
    }

    public bool IsFormCompleted()
    {
        return !string.IsNullOrEmpty(UserFirstName) &&
            !string.IsNullOrEmpty(UserLastName) &&
            !string.IsNullOrEmpty(UserId) &&
            !string.IsNullOrEmpty(UserDateOfBirth) &&
            !string.IsNullOrEmpty(UserState) &&
            !string.IsNullOrEmpty(UserEmail) &&
            !string.IsNullOrEmpty(UserPhoneNumber);
    }
}
