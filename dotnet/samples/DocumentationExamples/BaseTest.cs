// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.Configuration;
using Xunit.Abstractions;

namespace Examples;

public abstract class BaseTest
{
    protected ITestOutputHelper Output { get; }

    protected List<string> SimulatedInputText = new();
    protected int SimulatedInputTextIndex = 0;

    protected BaseTest(ITestOutputHelper output)
    {
        this.Output = output;
        LoadUserSecrets();
    }

    private static void LoadUserSecrets()
    {
        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddJsonFile("appsettings.Development.json", true)
            .AddEnvironmentVariables()
            .AddUserSecrets<TestConfiguration>()
            .Build();

        TestConfiguration.Initialize(configRoot);
    }

    /// <summary>
    /// This method can be substituted by Console.WriteLine when used in Console apps.
    /// </summary>
    /// <param name="target">Target object to write</param>
    protected void WriteLine(object? target = null)
    {
        this.Output.WriteLine(target?.ToString() ?? string.Empty);
    }

    /// <summary>
    /// Current interface ITestOutputHelper does not have a Write method. This extension method adds it to make it analogous to Console.Write when used in Console apps.
    /// </summary>
    /// <param name="target">Target object to write</param>
    protected void Write(object? target = null)
    {
        this.Output.WriteLine(target?.ToString() ?? string.Empty);
    }

    /// <summary>
    /// Simulates reading input strings from a user for the purpose of running tests.
    /// </summary>
    /// <returns>A simulate user input string, if available. Null otherwise.</returns>
    protected string? ReadLine()
    {
        if (SimulatedInputTextIndex < SimulatedInputText.Count)
        {
            return SimulatedInputText[SimulatedInputTextIndex++];
        }

        return null;
    }
}
