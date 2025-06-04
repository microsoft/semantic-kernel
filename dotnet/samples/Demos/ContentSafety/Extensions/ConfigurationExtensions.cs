// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ContentSafety.Extensions;

/// <summary>
/// Class with extension methods for app configuration.
/// </summary>
public static class ConfigurationExtensions
{
    /// <summary>
    /// Returns <typeparamref name="TOptions"/> if it's valid or throws <see cref="ValidationException"/>.
    /// </summary>
    public static TOptions GetValid<TOptions>(this IConfigurationRoot configurationRoot, string sectionName)
    {
        var options = configurationRoot.GetSection(sectionName).Get<TOptions>()!;

        Validator.ValidateObject(options, new(options));

        return options;
    }
}
