// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using RepoUtils;
using Xunit.Abstractions;

namespace Examples;

public abstract class BaseTest
{
    protected readonly ITestOutputHelper _output;

    protected BaseTest(ITestOutputHelper output)
    {
        this._output = output;
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
}
