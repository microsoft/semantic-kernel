// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Configuration;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using RepoUtils;
using Xunit.Abstractions;

namespace Examples;

public abstract class BaseTest
{
    /// <summary>
    /// Flag to force usage of OpenAI configuration if both <see cref="TestConfiguration.OpenAI"/>
    /// and <see cref="TestConfiguration.AzureOpenAI"/> are defined.
    /// If 'false', Azure takes precedence.
    /// </summary>
    protected virtual bool ForceOpenAI { get; } = false;

    protected ITestOutputHelper Output { get; }

    protected ILoggerFactory LoggerFactory { get; }

    protected string GetApiKey()
    {
        if (string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint) || this.ForceOpenAI)
        {
            return TestConfiguration.OpenAI.ApiKey;
        }

        return TestConfiguration.AzureOpenAI.ApiKey;
    }

    protected Kernel CreateKernelWithChatCompletion(KernelPlugin? plugin = null)
    {
        var builder = Kernel.CreateBuilder();

        if (string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint) || this.ForceOpenAI)
        {
            builder.AddOpenAIChatCompletion(
                TestConfiguration.OpenAI.ChatModelId,
                TestConfiguration.OpenAI.ApiKey);
        }
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);
        }

        if (plugin != null)
        {
            builder.Plugins.Add(plugin);
        }

        return builder.Build();
    }

    protected BaseTest(ITestOutputHelper output)
    {
        this.Output = output;
        this.LoggerFactory = new XunitLogger(output);

        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddJsonFile("appsettings.Development.json", true)
            .AddEnvironmentVariables()
            .AddUserSecrets(Assembly.GetExecutingAssembly())
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
