// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.OpenAI;

/// <summary>
/// Available in .Net8:
/// https://learn.microsoft.com/en-us/dotnet/api/system.text.json.jsonnamingpolicy.snakecaselower?view=net-8.0#system-text-json-jsonnamingpolicy-snakecaselower
/// </summary>
internal sealed class SnakeCaseJsonNamingPolicy : JsonNamingPolicy
{
    public readonly static SnakeCaseJsonNamingPolicy Instance = new();

    private SnakeCaseJsonNamingPolicy() { }

    public override string ConvertName(string name)
    {
        static IEnumerable<char> ToSnakeCase(CharEnumerator e)
        {
            if (!e.MoveNext()) { yield break; }
            var wasLower = char.IsLower(e.Current);
            yield return char.ToLower(e.Current, CultureInfo.InvariantCulture);
            while (e.MoveNext())
            {
                var isLower = char.IsLower(e.Current);
                if (wasLower && !isLower)
                {
                    yield return '_';
                }

                wasLower = isLower;

                yield return char.ToLower(e.Current, CultureInfo.InvariantCulture);
            }
        }

        var newName = new string(ToSnakeCase(name.GetEnumerator()).ToArray());

        return newName;
    }
}
