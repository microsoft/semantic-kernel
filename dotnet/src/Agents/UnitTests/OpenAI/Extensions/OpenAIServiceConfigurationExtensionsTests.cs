// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.Agents.OpenAI.Extensions;
using OpenAI.Files;
using OpenAI.VectorStores;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Extensions;

/// <summary>
/// Unit testing of <see cref="OpenAIServiceConfigurationExtensions"/>.
/// </summary>
public class OpenAIServiceConfigurationExtensionsTests
{
    /// <summary>
    /// Verify <see cref="OpenAIServiceConfiguration"/> can produce a <see cref="FileClient"/>
    /// </summary>
    [Fact]
    public void OpenAIServiceConfigurationExtensionsCreateFileClientTest()
    {
        OpenAIServiceConfiguration configOpenAI = OpenAIServiceConfiguration.ForOpenAI("key", new Uri("https://localhost"));
        Assert.IsType<FileClient>(configOpenAI.CreateFileClient());

        OpenAIServiceConfiguration configAzure = OpenAIServiceConfiguration.ForAzureOpenAI("key", new Uri("https://localhost"));
        Assert.IsType<FileClient>(configOpenAI.CreateFileClient());
    }

    /// <summary>
    /// Verify <see cref="OpenAIServiceConfiguration"/> can produce a <see cref="VectorStoreClient"/>
    /// </summary>
    [Fact]
    public void OpenAIServiceConfigurationExtensionsCreateVectorStoreTest()
    {
        OpenAIServiceConfiguration configOpenAI = OpenAIServiceConfiguration.ForOpenAI("key", new Uri("https://localhost"));
        Assert.IsType<VectorStoreClient>(configOpenAI.CreateVectorStoreClient());

        OpenAIServiceConfiguration configAzure = OpenAIServiceConfiguration.ForAzureOpenAI("key", new Uri("https://localhost"));
        Assert.IsType<VectorStoreClient>(configOpenAI.CreateVectorStoreClient());
    }
}
