// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using RepoUtils;
using Xunit.Abstractions;

namespace Examples;

public abstract class BaseTest
{
    protected ITestOutputHelper Output { get; }

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
            .AddUserSecrets<Env>()
            .Build();

        TestConfiguration.Initialize(configRoot);
    }

    /// <summary>
    /// This method can be substituted by Console.WriteLine when used in Console apps.
    /// </summary>
    /// <param name="target">Target object to write</param>
    protected void WriteLine(object? target = null)
    {
        this.Output.WriteLine(target ?? string.Empty);
    }

    /// <summary>
    /// Current interface ITestOutputHelper does not have a Write method. This extension method adds it to make it analogous to Console.Write when used in Console apps.
    /// </summary>
    /// <param name="target">Target object to write</param>
    protected void Write(object? target = null)
    {
        this.Output.WriteLine(target ?? string.Empty);
    }
}
