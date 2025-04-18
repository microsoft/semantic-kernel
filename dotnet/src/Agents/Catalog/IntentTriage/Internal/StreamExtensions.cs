// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.IntentTriage.Internal;

internal static partial class StreamExtensions
{
    [GeneratedRegex(@"\$\{([^}]+)\}")]
    private static partial Regex SpecParameterBindingExpression();

    public static async ValueTask<string> BindParametersAsync(this Stream resourceStream, Dictionary<string, string> parameters, CancellationToken cancellationToken)
    {
        using StreamReader reader = new(resourceStream);
        string apispec = await reader.ReadToEndAsync(cancellationToken);
        return SpecParameterBindingExpression().Replace(
            apispec,
            match =>
            {
                string key = match.Groups[1].Value;
                return parameters.TryGetValue(key, out string? value) ? value : match.Value;
            });
    }
}
