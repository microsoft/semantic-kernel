// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace Plugins;

public sealed class StaticTextPlugin
{
    [SKFunction, Description("Change all string chars to uppercase")]
    public static string Uppercase([Description("Text to uppercase")] string input) =>
        input.ToUpperInvariant();

    [SKFunction, Description("Append the day variable")]
    public static string AppendDay(
        [Description("Text to append to")] string input,
        [Description("Value of the day to append")] string day) =>
        input + day;
}
