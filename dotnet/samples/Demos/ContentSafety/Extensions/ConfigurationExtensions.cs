// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ContentSafety.Extensions;

public static class ConfigurationExtensions
{
    public static TOptions GetValid<TOptions>(this IConfigurationRoot configurationRoot, string sectionName)
    {
        var options = configurationRoot.GetSection(sectionName).Get<TOptions>()!;

        Validator.ValidateObject(options, new(options));

        return options;
    }
}
