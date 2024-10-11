// Copyright (c) Microsoft. All rights reserved.

namespace AotCompatibility.TestApp;

/// <summary>
/// This application is created in accordance with the instructions in the blog post at https://devblogs.microsoft.com/dotnet/creating-aot-compatible-libraries to ensure that
/// all Native-AOT-related warnings missed by the Roslyn analyzers are caught by the AOT compiler used in this application.
/// </summary>
internal static class Program
{
    private static void Main(string[] args)
    {
        Console.WriteLine("Hello, World!");
    }
}
