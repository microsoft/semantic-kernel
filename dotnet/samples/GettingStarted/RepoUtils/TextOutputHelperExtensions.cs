// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;

namespace Examples;

public static class TextOutputHelperExtensions
{
    public static void WriteLine(this ITestOutputHelper testOutputHelper, object target)
    {
        testOutputHelper.WriteLine(target.ToString());
    }

    public static void WriteLine(this ITestOutputHelper testOutputHelper)
    {
        testOutputHelper.WriteLine(string.Empty);
    }

    public static void Write(this ITestOutputHelper testOutputHelper)
    {
        testOutputHelper.WriteLine(string.Empty);
    }

    /// <summary>
    /// Current interface ITestOutputHelper does not have a Write method. This extension method adds it to make it analogous to Console.Write when used in Console apps.
    /// </summary>
    /// <param name="testOutputHelper">TestOutputHelper</param>
    /// <param name="target">Target object to write</param>
    public static void Write(this ITestOutputHelper testOutputHelper, object target)
    {
        testOutputHelper.WriteLine(target.ToString());
    }
}
