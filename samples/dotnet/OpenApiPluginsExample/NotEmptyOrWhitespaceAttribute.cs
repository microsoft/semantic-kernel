// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel.DataAnnotations;

namespace OpenApiPluginsExample;

/// <summary>
/// If the string is set, it must not be empty or whitespace.
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
