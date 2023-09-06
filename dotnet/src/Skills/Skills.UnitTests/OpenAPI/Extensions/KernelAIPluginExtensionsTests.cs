// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Skills.OpenAPI.OpenApi;
using SemanticKernel.Skills.UnitTests.OpenAPI.TestSkills;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.OpenAPI.Extensions;

public sealed class KernelAIPluginExtensionsTests : IDisposable
{
    /// <summary>
    /// System under test - an instance of OpenApiDocumentParser class.
    /// </summary>
    private readonly OpenApiDocumentParser _sut;

    /// <summary>
    /// OpenAPI document stream.
    /// </summary>
    private readonly Stream _openApiDocument;

    /// <summary>
    /// Kernel instance.
    /// </summary>
    private IKernel kernel;

    /// <summary>
    /// Creates an instance of a <see cref="KernelAIPluginExtensionsTests"/> class.
    /// </summary>
    public KernelAIPluginExtensionsTests()
    {
        this.kernel = KernelBuilder.Create();

        this._openApiDocument = ResourceSkillsProvider.LoadFromResource("documentV2_0.json");

        this._sut = new OpenApiDocumentParser();
    }

    [Fact]
    public async Task ItCanIncludeOpenApiOperationParameterTypesIntoFunctionParametersViewAsync()
    {
        //Act
        var skill = await this.kernel.ImportAIPluginAsync("fakeSkill", this._openApiDocument);

        //Assert
        var setSecretFunction = skill["SetSecret"];
        Assert.NotNull(setSecretFunction);

        var functionView = setSecretFunction.Describe();
        Assert.NotNull(functionView);

        var secretNameParameter = functionView.Parameters.First(p => p.Name == "secret_name");
        Assert.Equal(ParameterViewType.String, secretNameParameter.Type);

        var apiVersionParameter = functionView.Parameters.First(p => p.Name == "api_version");
        Assert.Equal("string", apiVersionParameter?.Type?.ToString());

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.Equal(ParameterViewType.Object, payloadParameter.Type);
    }

    [Theory]
    [InlineData("http://localhost:3001/openapi.json", "http://localhost:3001/")]
    [InlineData("https://api.example.com/openapi.json", "https://api.example.com/")]
    [SuppressMessage("Design", "CA1054:URI-like parameters should not be strings", Justification = "Required for test data.")]
    public async Task ItUsesOpenApiDocumentHostUrlWhenServerUrlIsNotProvidedAsync(string documentUri, string expectedServerUrl)
    {
        // Arrange
        var openApiDocument = ResourceSkillsProvider.LoadFromResource("documentV3_0.json");

        using var content = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
        {
            doc.Remove("servers");
        });

        using var expectedHttpResponseMessage = new HttpResponseMessage { Content = new StreamContent(content) };
        using var httpClient = new HttpClient(OpenApiTestHelper.GetHttpClientHandlerMock(expectedHttpResponseMessage));

        var executionParameters = new OpenApiSkillExecutionParameters { HttpClient = httpClient };

        // Act
        var skill = await this.kernel.ImportAIPluginAsync("fakeSkill", new Uri(documentUri), executionParameters);

        // Assert
        var setSecretFunction = skill["SetSecret"];
        Assert.NotNull(setSecretFunction);

        var functionView = setSecretFunction.Describe();
        Assert.NotNull(functionView);

        var serverUrlParameter = functionView.Parameters.First(p => p.Name == "server_url");
        Assert.Equal(expectedServerUrl, serverUrlParameter.DefaultValue);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItUsesServerUrlOverrideIfProvidedAsync(bool removeServersProperty)
    {
        // Arrange
        const string DocumentUri = "http://localhost:3001/openapi.json";
        const string ServerUrlOverride = "https://server-override.com/";

        var openApiDocument = ResourceSkillsProvider.LoadFromResource("documentV3_0.json");

        if (removeServersProperty)
        {
            openApiDocument = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
            {
                doc.Remove("servers");
            });
        }

        using var expectedHttpResponseMessage = new HttpResponseMessage { Content = new StreamContent(openApiDocument) };
        using var httpClient = new HttpClient(OpenApiTestHelper.GetHttpClientHandlerMock(expectedHttpResponseMessage));

        var executionParameters = new OpenApiSkillExecutionParameters { HttpClient = httpClient, ServerUrlOverride = new Uri(ServerUrlOverride) };

        // Act
        var skill = await this.kernel.ImportAIPluginAsync("fakeSkill", new Uri(DocumentUri), executionParameters);

        // Assert
        var setSecretFunction = skill["SetSecret"];
        Assert.NotNull(setSecretFunction);

        var functionView = setSecretFunction.Describe();
        Assert.NotNull(functionView);

        var serverUrlParameter = functionView.Parameters.First(p => p.Name == "server_url");
        Assert.Equal(ServerUrlOverride, serverUrlParameter.DefaultValue);
    }

    public void Dispose()
    {
        this._openApiDocument.Dispose();
    }
}
