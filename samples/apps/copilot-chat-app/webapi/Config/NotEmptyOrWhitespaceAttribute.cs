// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using System.Reflection;

namespace SemanticKernel.Service.Config;

/// <summary>
/// If the other property is set to the expected value, then this property is required.
/// </summary>
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
internal sealed class NotEmptyOrWhitespaceAttribute : ValidationAttribute
{
    protected override ValidationResult? IsValid(object? value, ValidationContext validationContext)
    {
        if (value == null)
        {
            return ValidationResult.Success;
        }

        if (value is string s)
        {
            if (!string.IsNullOrWhiteSpace(s))
            {
                return ValidationResult.Success;
            }

            return new ValidationResult($"'{validationContext.MemberName}' cannot be empty or whitespace.");
        }

        return new ValidationResult($"'{validationContext.MemberName}' must be a string.");
    }
}
