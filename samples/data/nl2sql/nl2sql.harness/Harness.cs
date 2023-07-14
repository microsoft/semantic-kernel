// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Harness;

using System.Reflection;
using Microsoft.Extensions.Configuration;

internal static class Harness
{
    public static IConfiguration Configuration { get; } = CreateConfiguration();

    private static IConfiguration CreateConfiguration()
    {
        return
            new ConfigurationBuilder()
                .AddEnvironmentVariables()
                .AddUserSecrets(Assembly.GetExecutingAssembly())
                .Build();
    }
}
