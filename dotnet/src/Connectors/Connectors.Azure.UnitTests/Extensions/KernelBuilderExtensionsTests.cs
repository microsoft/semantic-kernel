// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Connectors.Azure.UnitTests;

/// <summary>
/// Unit tests of <see cref="AzureKernelBuilderExtensions"/>.
/// </summary>
public class AzureKernelBuilderExtensionsTests
{
    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        // Arrange
        // Act - Assert no exception occurs
        Kernel targetKernel = Kernel.CreateBuilder()
           .AddAzureChatCompletion("depl", new Uri("https://url"), "key", "azure")
           .Build();

        Assert.NotNull(targetKernel.GetRequiredService<IChatCompletionService>("azure"));
    }

    [Fact]
    public void ItCanOverwriteServices()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        builder.Services.AddAzureChatCompletion("dep", new Uri("https://localhost"), "key", serviceId: "one");
        builder.Services.AddAzureChatCompletion("dep", new Uri("https://localhost"), "key", serviceId: "one");

        // Act - Assert no exception occurs
        builder.Build();
    }
}
