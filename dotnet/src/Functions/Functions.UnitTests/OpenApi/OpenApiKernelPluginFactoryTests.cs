// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using SemanticKernel.Functions.UnitTests.OpenApi.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;
public sealed class OpenApiKernelPluginFactoryTests
{
    /// <summary>
    /// OpenAPI function execution parameters.
    /// </summary>
    private readonly OpenApiFunctionExecutionParameters _executionParameters;

    /// <summary>
    /// OpenAPI document stream.
    /// </summary>
    private readonly Stream _openApiDocument;

    /// <summary>
    /// Creates an instance of a <see cref="OpenApiKernelExtensionsTests"/> class.
    /// </summary>
    public OpenApiKernelPluginFactoryTests()
    {
        this._executionParameters = new OpenApiFunctionExecutionParameters() { EnableDynamicPayload = false };

        this._openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV2_0.json");
    }

    [Fact]
    public async Task ItCanIncludeOpenApiOperationParameterTypesIntoFunctionParametersViewAsync()
    {
        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", this._openApiDocument, this._executionParameters);

        // Assert
        var setSecretFunction = plugin["SetSecret"];
        Assert.NotNull(setSecretFunction);

        var functionView = setSecretFunction.Metadata;
        Assert.NotNull(functionView);

        var secretNameParameter = functionView.Parameters.First(p => p.Name == "secret_name");
        Assert.NotNull(secretNameParameter.Schema);
        Assert.Equal("string", secretNameParameter.Schema!.RootElement.GetProperty("type").GetString());

        var apiVersionParameter = functionView.Parameters.First(p => p.Name == "api_version");
        Assert.Equal("string", apiVersionParameter.Schema!.RootElement.GetProperty("type").GetString());

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.NotNull(payloadParameter.Schema);
        Assert.Equal("object", payloadParameter.Schema!.RootElement.GetProperty("type").GetString());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItUsesServerUrlOverrideIfProvidedAsync(bool removeServersProperty)
    {
        // Arrange
        const string DocumentUri = "http://localhost:3001/openapi.json";
        const string ServerUrlOverride = "https://server-override.com/";

        var openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        if (removeServersProperty)
        {
            openApiDocument = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
            {
                doc.Remove("servers");
            });
        }

        using var messageHandlerStub = new HttpMessageHandlerStub(openApiDocument);
        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.HttpClient = httpClient;
        this._executionParameters.ServerUrlOverride = new Uri(ServerUrlOverride);

        var arguments = new KernelArguments
        {
            ["secret-name"] = "fake-secret-name",
            ["api-version"] = "7.0",
            ["X-API-Version"] = 6,
            ["payload"] = "fake-payload"
        };

        var kernel = new Kernel();

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", new Uri(DocumentUri), this._executionParameters);
        var setSecretFunction = plugin["SetSecret"];

        messageHandlerStub.ResetResponse();

        var result = await kernel.InvokeAsync(setSecretFunction, arguments);

        // Assert
        Assert.NotNull(messageHandlerStub.RequestUri);
        Assert.StartsWith(ServerUrlOverride, messageHandlerStub.RequestUri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData("documentV2_0.json")]
    [InlineData("documentV3_0.json")]
    public async Task ItUsesServerUrlFromOpenApiDocumentAsync(string documentFileName)
    {
        // Arrange
        const string DocumentUri = "http://localhost:3001/openapi.json";
        const string ServerUrlFromDocument = "https://my-key-vault.vault.azure.net/";

        var openApiDocument = ResourcePluginsProvider.LoadFromResource(documentFileName);

        using var messageHandlerStub = new HttpMessageHandlerStub(openApiDocument);
        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.HttpClient = httpClient;

        var arguments = new KernelArguments
        {
            ["secret-name"] = "fake-secret-name",
            ["api-version"] = "7.0",
            ["X-API-Version"] = 6,
            ["payload"] = "fake-payload"
        };

        var kernel = new Kernel();

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", new Uri(DocumentUri), this._executionParameters);
        var setSecretFunction = plugin["SetSecret"];

        messageHandlerStub.ResetResponse();

        var result = await kernel.InvokeAsync(setSecretFunction, arguments);

        // Assert
        Assert.NotNull(messageHandlerStub.RequestUri);
        Assert.StartsWith(ServerUrlFromDocument, messageHandlerStub.RequestUri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData("http://localhost:3001/openapi.json", "http://localhost:3001/", "documentV2_0.json")]
    [InlineData("http://localhost:3001/openapi.json", "http://localhost:3001/", "documentV3_0.json")]
    [InlineData("https://api.example.com/openapi.json", "https://api.example.com/", "documentV2_0.json")]
    [InlineData("https://api.example.com/openapi.json", "https://api.example.com/", "documentV3_0.json")]
    [SuppressMessage("Design", "CA1054:URI-like parameters should not be strings", Justification = "Required for test data.")]
    public async Task ItUsesOpenApiDocumentHostUrlWhenServerUrlIsNotProvidedAsync(string documentUri, string expectedServerUrl, string documentFileName)
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource(documentFileName);

        using var content = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
        {
            doc.Remove("servers");
            doc.Remove("host");
            doc.Remove("schemes");
        });

        using var messageHandlerStub = new HttpMessageHandlerStub(content);
        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.HttpClient = httpClient;

        var arguments = new KernelArguments
        {
            ["secret-name"] = "fake-secret-name",
            ["api-version"] = "7.0",
            ["X-API-Version"] = 6,
            ["payload"] = "fake-payload"
        };

        var kernel = new Kernel();

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", new Uri(documentUri), this._executionParameters);
        var setSecretFunction = plugin["SetSecret"];

        messageHandlerStub.ResetResponse();

        var result = await kernel.InvokeAsync(setSecretFunction, arguments);

        // Assert
        Assert.NotNull(messageHandlerStub.RequestUri);
        Assert.StartsWith(expectedServerUrl, messageHandlerStub.RequestUri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ItShouldRespectRunAsyncCancellationTokenOnExecutionAsync()
    {
        // Arrange
        using var messageHandlerStub = new HttpMessageHandlerStub();
        messageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.HttpClient = httpClient;

        var fakePlugin = new FakePlugin();

        using var registerCancellationToken = new System.Threading.CancellationTokenSource();
        using var executeCancellationToken = new System.Threading.CancellationTokenSource();

        var openApiPlugins = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", this._openApiDocument, this._executionParameters, registerCancellationToken.Token);

        var kernel = new Kernel();

        var arguments = new KernelArguments
        {
            { "secret-name", "fake-secret-name" },
            { "api-version", "fake-api-version" }
        };

        // Act
        registerCancellationToken.Cancel();
        var result = await kernel.InvokeAsync(openApiPlugins["GetSecret"], arguments, executeCancellationToken.Token);

        // Assert
        Assert.NotNull(result);

        var response = result.GetValue<RestApiOperationResponse>();

        //Check original response
        Assert.NotNull(response);
        Assert.Equal("fake-content", response.Content);
    }

    [Fact]
    public async Task ItShouldSanitizeOperationNameAsync()
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        using var content = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
        {
            doc["paths"]!["/secrets/{secret-name}"]!["get"]!["operationId"] = "issues/create-mile.stone";
        });

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", content, this._executionParameters);

        // Assert
        Assert.True(plugin.TryGetFunction("IssuesCreatemilestone", out var _));
    }

    [Fact]
    public async Task ItCanIncludeOpenApiDeleteAndPatchOperationsAsync()
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource("repair-service.json");

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("repairServicePlugin", openApiDocument, this._executionParameters);

        // Assert
        Assert.NotNull(plugin);
        var functionsMetadata = plugin.GetFunctionsMetadata();
        Assert.Equal(4, functionsMetadata.Count);
        AssertPayloadParameters(plugin, "updateRepair");
        AssertPayloadParameters(plugin, "deleteRepair");
    }

    [Theory]
    [InlineData("documentV2_0.json")]
    [InlineData("documentV3_0.json")]
    [InlineData("documentV3_1.yaml")]
    public async Task ItShouldReplicateMetadataToOperationAsync(string documentFileName)
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource(documentFileName);

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, this._executionParameters);

        // Assert Metadata Keys and Values
        Assert.True(plugin.TryGetFunction("OpenApiExtensions", out var function));
        var additionalProperties = function.Metadata.AdditionalProperties;
        Assert.Equal(6, additionalProperties.Count);

        Assert.Contains("method", additionalProperties.Keys);
        Assert.Contains("operation", additionalProperties.Keys);
        Assert.Contains("info", additionalProperties.Keys);
        Assert.Contains("security", additionalProperties.Keys);
        Assert.Contains("server-urls", additionalProperties.Keys);
        Assert.Contains("operation-extensions", additionalProperties.Keys);

        var operation = additionalProperties["operation"] as RestApiOperation;
        Assert.NotNull(operation);
        Assert.Equal("GET", additionalProperties["method"]);
        Assert.Equal("/api-with-open-api-extensions", operation.Path);
        var serverUrls = additionalProperties["server-urls"] as string[];
        Assert.NotNull(serverUrls);
        Assert.Equal(["https://my-key-vault.vault.azure.net"], serverUrls);
        var info = additionalProperties["info"] as RestApiInfo;
        Assert.NotNull(info);
        var security = additionalProperties["security"] as List<RestApiSecurityRequirement>;
        Assert.NotNull(security);

        // Assert Operation Extension keys
        var operationExtensions = additionalProperties["operation-extensions"] as Dictionary<string, object?>;
        Assert.NotNull(operationExtensions);
        Dictionary<string, object?> nonNullOperationExtensions = operationExtensions;

        Assert.Equal(8, nonNullOperationExtensions.Count);
        Assert.Contains("x-boolean-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-double-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-integer-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-string-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-date-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-datetime-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-array-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-object-extension", nonNullOperationExtensions.Keys);
    }

    [Fact]
    public async Task ItShouldFreezeOperationMetadataAsync()
    {
        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", this._openApiDocument, this._executionParameters);

        // Assert
        Assert.True(plugin.TryGetFunction("SetSecret", out var function));

        RestApiOperation additionalProperties = (RestApiOperation)function.Metadata.AdditionalProperties["operation"]!;

        // Assert that operation metadata is frozen
        var secretNameParameter = additionalProperties.Parameters.Single(p => p.Name == "secret-name");
        Assert.Throws<InvalidOperationException>(() => secretNameParameter.ArgumentName = "a new value");
    }

    [Fact]
    public async Task ItShouldHandleEmptyOperationNameAsync()
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        using var content = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
        {
            doc["paths"]!["/secrets/{secret-name}"]!["get"]!["operationId"] = "";
        });

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", content, this._executionParameters);

        // Assert
        Assert.Equal(8, plugin.Count());
        Assert.True(plugin.TryGetFunction("GetSecretsSecretname", out var _));
    }

    [Fact]
    public async Task ItShouldHandleNullOperationNameAsync()
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        using var content = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
        {
            doc["paths"]!["/secrets/{secret-name}"]!["get"]!.AsObject().Remove("operationId");
        });

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", content, this._executionParameters);

        // Assert
        Assert.Equal(8, plugin.Count());
        Assert.True(plugin.TryGetFunction("GetSecretsSecretname", out var _));
    }

    [Theory]
    [InlineData("string_parameter", typeof(string))]
    [InlineData("boolean_parameter", typeof(bool))]
    [InlineData("number_parameter", typeof(double))]
    [InlineData("float_parameter", typeof(float))]
    [InlineData("double_parameter", typeof(double))]
    [InlineData("integer_parameter", typeof(long))]
    [InlineData("int32_parameter", typeof(int))]
    [InlineData("int64_parameter", typeof(long))]
    public async Task ItShouldMapPropertiesOfPrimitiveDataTypeToKernelParameterMetadataAsync(string name, Type type)
    {
        // Arrange & Act
        this._executionParameters.EnableDynamicPayload = true;

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", this._openApiDocument, this._executionParameters);

        var parametersMetadata = plugin["TestParameterDataTypes"].Metadata.Parameters;

        // Assert
        var parameterMetadata = parametersMetadata.First(p => p.Name == name);

        Assert.Equal(type, parameterMetadata.ParameterType);
    }

    [Fact]
    public async Task ItShouldMapPropertiesOfObjectDataTypeToKernelParameterMetadataAsync()
    {
        // Arrange & Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", this._openApiDocument, this._executionParameters);

        var parametersMetadata = plugin["TestParameterDataTypes"].Metadata.Parameters;

        // Assert
        var parameterMetadata = parametersMetadata.First(p => p.Name == "payload");

        Assert.Equal(typeof(object), parameterMetadata.ParameterType);
    }

    [Fact]
    public async Task ItShouldUseCustomHttpResponseContentReaderAsync()
    {
        // Arrange
        using var messageHandlerStub = new HttpMessageHandlerStub(this._openApiDocument);
        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.HttpResponseContentReader = async (context, cancellationToken) => await context.Response.Content.ReadAsStreamAsync(cancellationToken);
        this._executionParameters.HttpClient = httpClient;

        var kernel = new Kernel();

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", new Uri("http://localhost:3001/openapi.json"), this._executionParameters);

        messageHandlerStub.ResetResponse();

        var arguments = new KernelArguments
        {
            ["secret-name"] = "fake-secret-name",
            ["api-version"] = "7.0",
            ["X-API-Version"] = 6
        };

        // Act
        var result = await kernel.InvokeAsync(plugin["GetSecret"], arguments);

        // Assert
        var response = result.GetValue<RestApiOperationResponse>();
        Assert.NotNull(response);

        Assert.IsAssignableFrom<Stream>(response.Content);
    }

    [Theory]
    [MemberData(nameof(GenerateSecurityMemberData))]
    public async Task ItAddSecurityMetadataToOperationAsync(string documentFileName, IDictionary<string, string[]> securityTypeMap)
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource(documentFileName);

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, this._executionParameters);

        // Assert Security Metadata Keys and Values
        foreach (var function in plugin)
        {
            var additionalProperties = function.Metadata.AdditionalProperties;
            Assert.Contains("operation", additionalProperties.Keys);

            var securityTypes = securityTypeMap[function.Name];

            var operation = additionalProperties["operation"] as RestApiOperation;
            Assert.NotNull(operation);
            Assert.NotNull(operation.SecurityRequirements);
            Assert.Equal(securityTypes.Length, operation.SecurityRequirements?.Count);
            foreach (var securityType in securityTypes)
            {
                Assert.Contains(operation.SecurityRequirements!, sr => sr.Keys.Any(k => k.SecuritySchemeType == securityType));
            }
        }
    }

    [Fact]
    public void ItCreatesPluginFromOpenApiSpecificationModel()
    {
        // Arrange
        var info = new RestApiInfo() { Description = "api-description", Title = "api-title", Version = "7.0" };

        var securityRequirements = new List<RestApiSecurityRequirement>
        {
            new(new Dictionary<RestApiSecurityScheme, IList<string>> { { new RestApiSecurityScheme(), new List<string>() } })
        };

        var operations = new List<RestApiOperation>
        {
            new (
                id: "operation1",
                servers: [],
                path: "path",
                method: HttpMethod.Get,
                description: "operation-description",
                parameters: [],
                responses: new Dictionary<string, RestApiExpectedResponse>(),
                securityRequirements: [],
                payload: null)
        };

        var specification = new RestApiSpecification(info, securityRequirements, operations);

        // Act
        var plugin = OpenApiKernelPluginFactory.CreateFromOpenApi("fakePlugin", specification, this._executionParameters);

        // Assert
        Assert.Single(plugin);
        Assert.Equal("api-description", plugin.Description);
        Assert.Equal("fakePlugin", plugin.Name);

        var function = plugin["operation1"];
        Assert.Equal("operation1", function.Name);
        Assert.Equal("operation-description", function.Description);
        Assert.Same(operations[0], function.Metadata.AdditionalProperties["operation"]);
    }

    [Fact]
    public async Task ItShouldResolveArgumentsByParameterNamesAsync()
    {
        // Arrange
        using var messageHandlerStub = new HttpMessageHandlerStub();
        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.EnableDynamicPayload = true;
        this._executionParameters.HttpClient = httpClient;

        var arguments = new KernelArguments
        {
            ["string_parameter"] = "fake-secret-name",
            ["boolean@parameter"] = true,
            ["integer+parameter"] = 6,
            ["float?parameter"] = 23.4f
        };

        var kernel = new Kernel();

        var openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, this._executionParameters);

        // Act
        var result = await kernel.InvokeAsync(plugin["TestParameterNamesSanitization"], arguments);

        // Assert path and query parameters added to the request uri
        Assert.NotNull(messageHandlerStub.RequestUri);
        Assert.Equal("https://my-key-vault.vault.azure.net/test-parameter-names-sanitization/fake-secret-name?boolean@parameter=true", messageHandlerStub.RequestUri.AbsoluteUri);

        // Assert header parameters added to the request
        Assert.Equal("6", messageHandlerStub.RequestHeaders!.GetValues("integer+parameter").First());

        // Assert payload parameters added to the request
        var messageContent = messageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);

        var deserializedPayload = await JsonNode.ParseAsync(new MemoryStream(messageContent));
        Assert.NotNull(deserializedPayload);

        Assert.Equal(23.4f, deserializedPayload["float?parameter"]!.GetValue<float>());
    }

    [Fact]
    public async Task ItShouldResolveArgumentsBySanitizedParameterNamesAsync()
    {
        // Arrange
        using var messageHandlerStub = new HttpMessageHandlerStub();
        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.EnableDynamicPayload = true;
        this._executionParameters.HttpClient = httpClient;

        var arguments = new KernelArguments
        {
            ["string_parameter"] = "fake-secret-name",  // Original parameter name - string-parameter
            ["boolean_parameter"] = true,               // Original parameter name - boolean@parameter
            ["integer_parameter"] = 6,                  // Original parameter name - integer+parameter
            ["float_parameter"] = 23.4f                 // Original parameter name - float?parameter
        };

        var kernel = new Kernel();

        var openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, this._executionParameters);

        // Act
        var result = await kernel.InvokeAsync(plugin["TestParameterNamesSanitization"], arguments);

        // Assert path and query parameters added to the request uri
        Assert.NotNull(messageHandlerStub.RequestUri);
        Assert.Equal("https://my-key-vault.vault.azure.net/test-parameter-names-sanitization/fake-secret-name?boolean@parameter=true", messageHandlerStub.RequestUri.AbsoluteUri);

        // Assert header parameters added to the request
        Assert.Equal("6", messageHandlerStub.RequestHeaders!.GetValues("integer+parameter").First());

        // Assert payload parameters added to the request
        var messageContent = messageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);

        var deserializedPayload = await JsonNode.ParseAsync(new MemoryStream(messageContent));
        Assert.NotNull(deserializedPayload);

        Assert.Equal(23.4f, deserializedPayload["float?parameter"]!.GetValue<float>());
    }

    [Fact]
    public async Task ItShouldPropagateRestApiOperationResponseFactoryToRunnerAsync()
    {
        // Arrange
        bool restApiOperationResponseFactoryIsInvoked = false;

        async Task<RestApiOperationResponse> RestApiOperationResponseFactory(RestApiOperationResponseFactoryContext context, CancellationToken cancellationToken)
        {
            restApiOperationResponseFactoryIsInvoked = true;

            return await context.InternalFactory(context, cancellationToken);
        }

        using var messageHandlerStub = new HttpMessageHandlerStub();
        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.HttpClient = httpClient;
        this._executionParameters.RestApiOperationResponseFactory = RestApiOperationResponseFactory;

        var openApiPlugins = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", this._openApiDocument, this._executionParameters);

        var kernel = new Kernel();

        var arguments = new KernelArguments
        {
            { "secret-name", "fake-secret-name" },
            { "api-version", "fake-api-version" }
        };

        // Act
        await kernel.InvokeAsync(openApiPlugins["GetSecret"], arguments);

        // Assert
        Assert.True(restApiOperationResponseFactoryIsInvoked);
    }

    [Fact]
    public async Task ItCanImportSpecifiedOperationsAsync()
    {
        // Arrange
        string[] operationsToInclude = ["GetSecret", "SetSecret"];

        this._executionParameters.OperationSelectionPredicate = (context) => operationsToInclude.Contains(context.Id);

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", this._openApiDocument, this._executionParameters);

        // Assert
        Assert.Equal(2, plugin.Count());
        Assert.Contains(plugin, p => p.Name == "GetSecret");
        Assert.Contains(plugin, p => p.Name == "SetSecret");
    }

    [Fact]
    public async Task ItCanFilterOutSpecifiedOperationsAsync()
    {
        // Arrange
        this._executionParameters.OperationsToExclude = ["GetSecret", "SetSecret"];

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", this._openApiDocument, this._executionParameters);

        // Assert
        Assert.True(plugin.Any());
        Assert.DoesNotContain(plugin, p => p.Name == "GetSecret");
        Assert.DoesNotContain(plugin, p => p.Name == "SetSecret");
    }

    /// <summary>
    /// Generate theory data for ItAddSecurityMetadataToOperationAsync
    /// </summary>
    public static TheoryData<string, IDictionary<string, string[]>> GenerateSecurityMemberData() =>
        new()
        {
            { "no-securityV3_0.json", new Dictionary<string, string[]>
                {
                    { "NoSecurity", Array.Empty<string>() },
                    { "Security", new[] { "ApiKey" } },
                    { "SecurityAndScope", new[] { "ApiKey" } }
                }},
            { "apikey-securityV3_0.json", new Dictionary<string, string[]>
                {
                    { "NoSecurity", Array.Empty<string>() },
                    { "Security", new[] { "ApiKey" } },
                    { "SecurityAndScope", new[] { "ApiKey" } }
                }},
            { "oauth-securityV3_0.json", new Dictionary<string, string[]>
                {
                    { "NoSecurity", Array.Empty<string>() },
                    { "Security", new[] { "OAuth2" } },
                    { "SecurityAndScope", new[] { "OAuth2" } }
                }}
        };

    [Fact]
    public async Task ItShouldCreateFunctionWithMultipartFormDataAsync()
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource("multipart-form-data.json");

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, this._executionParameters);

        // Assert
        Assert.False(plugin.TryGetFunction("createItem", out var _));
    }

    [Fact]
    public void Dispose()
    {
        this._openApiDocument.Dispose();
    }

    #region private ================================================================================

    private static void AssertPayloadParameters(KernelPlugin plugin, string functionName)
    {
        Assert.True(plugin.TryGetFunction(functionName, out var function));
        Assert.NotNull(function.Metadata.Parameters);
        Assert.Equal(2, function.Metadata.Parameters.Count);
        Assert.Equal("payload", function.Metadata.Parameters[0].Name);
        Assert.Equal("content_type", function.Metadata.Parameters[1].Name);
    }

    private sealed class FakePlugin
    {
        public string? ParameterValueFakeMethodCalledWith { get; private set; }

        [KernelFunction]
        public void DoFakeAction(string parameter)
        {
            this.ParameterValueFakeMethodCalledWith = parameter;
        }
    }

    #endregion
}
