// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Skills.OpenAPI.OpenApi;
using SemanticKernel.Skills.UnitTests.OpenAPI.TestSkills;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.OpenAPI.Extensions;
public sealed class KernelOpenApiExtensionsTests : IDisposable
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
    /// Creates an instance of a <see cref="KernelOpenApiExtensionsTests"/> class.
    /// </summary>
    public KernelOpenApiExtensionsTests()
    {
        this.kernel = KernelBuilder.Create();

        this._openApiDocument = ResourceSkillsProvider.LoadFromResource("documentV2_0.json");

        this._sut = new OpenApiDocumentParser();
    }

    [Fact]
    public async Task ItCanIncludeOpenApiOperationParameterTypesIntoFunctionParametersViewAsync()
    {
        //Act
        var skill = await this.kernel.RegisterOpenApiSkillAsync(this._openApiDocument, "fakeSkill");

        //Assert
        var setSecretFunction = skill["SetSecret"];
        Assert.NotNull(setSecretFunction);

        var functionView = setSecretFunction.Describe();
        Assert.NotNull(functionView);

        var secretNameParameter = functionView.Parameters.First(p => p.Name == "secret_name");
        Assert.Equal("string", secretNameParameter.Type);

        var apiVersionParameter = functionView.Parameters.First(p => p.Name == "api_version");
        Assert.Equal("string", apiVersionParameter.Type);

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.Equal("object", payloadParameter.Type);
    }

    public void Dispose()
    {
        this._openApiDocument.Dispose();
    }
}
