// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

/// <summary>
/// These samples show different ways OpenAPI document can be transformed to change its various aspects before creating a plugin out of it.
/// The transformations can be useful if the original OpenAPI document can't be consumed as is.
/// </summary>
public sealed class OpenApiPlugin_Customization : BaseTest
{
    private readonly Kernel _kernel;
    private readonly ITestOutputHelper _output;
    private readonly HttpClient _httpClient;

    public OpenApiPlugin_Customization(ITestOutputHelper output) : base(output)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        this._kernel = builder.Build();

        this._output = output;

        void RequestDataHandler(string requestData)
        {
            this._output.WriteLine("Request payload");
            this._output.WriteLine(requestData);
        }

        // Create HTTP client with a stub handler to log the request data
        this._httpClient = new(new StubHttpHandler(RequestDataHandler));
    }

    /// <summary>
    /// This sample demonstrates how to assign argument names to parameters and variables that have the same name.
    /// For example, in this sample, there are multiple parameters named 'id' in the 'getProductFromCart' operation.
    ///   * Region of the API in the server variable.
    ///   * User ID in the path.
    ///   * Subscription ID in the query string.
    ///   * Session ID in the header.
    /// </summary>
    [Fact]
    public async Task HandleOpenApiDocumentHavingTwoParametersWithSameNameButRelatedToDifferentEntitiesAsync()
    {
        OpenApiDocumentParser parser = new();

        using StreamReader sr = File.OpenText("Resources/Plugins/ProductsPlugin/openapi.json");

        // Register the custom HTTP client with the stub handler
        OpenApiFunctionExecutionParameters executionParameters = new() { HttpClient = this._httpClient };

        // Parse the OpenAPI document
        RestApiSpecification specification = await parser.ParseAsync(sr.BaseStream);

        // Get the 'getProductFromCart' operation
        RestApiOperation getProductFromCartOperation = specification.Operations.Single(o => o.Id == "getProductFromCart");

        // Set the 'region' argument name to the 'id' server variable that represents the region of the API
        RestApiServerVariable idServerVariable = getProductFromCartOperation.Servers[0].Variables["id"];
        idServerVariable.ArgumentName = "region";

        // Set the 'userId' argument name to the 'id' path parameter that represents the user ID
        RestApiParameter idPathParameter = getProductFromCartOperation.Parameters.Single(p => p.Location == RestApiParameterLocation.Path && p.Name == "id");
        idPathParameter.ArgumentName = "userId";

        // Set the 'subscriptionId' argument name to the 'id' query string parameter that represents the subscription ID
        RestApiParameter idQueryStringParameter = getProductFromCartOperation.Parameters.Single(p => p.Location == RestApiParameterLocation.Query && p.Name == "id");
        idQueryStringParameter.ArgumentName = "subscriptionId";

        // Set the 'sessionId' argument name to the 'id' header parameter that represents the session ID
        RestApiParameter sessionIdHeaderParameter = getProductFromCartOperation.Parameters.Single(p => p.Location == RestApiParameterLocation.Header && p.Name == "id");
        sessionIdHeaderParameter.ArgumentName = "sessionId";

        // Import the transformed OpenAPI plugin specification
        KernelPlugin plugin = this._kernel.ImportPluginFromOpenApi("Products_Plugin", specification, new OpenApiFunctionExecutionParameters(this._httpClient));

        // Create arguments for the 'addProductToCart' operation using the new argument names defined earlier.
        // Internally these will be mapped to the correct entity when invoking the Open API endpoint.
        KernelArguments arguments = new()
        {
            ["region"] = "en",
            ["subscriptionId"] = "subscription-12345",
            ["userId"] = "user-12345",
            ["sessionId"] = "session-12345",
        };

        // Invoke the 'addProductToCart' function
        await this._kernel.InvokeAsync(plugin["getProductFromCart"], arguments);

        // The REST API request details
        // {  
        //     "RequestUri": "https://api.example.com:443/eu/users/user-12345/cart?id=subscription-12345",  
        //     "Method": "Get", 
        //     "Headers": {  
        //         "id": ["session-12345"]  
        //     }  
        // }  
    }

    private sealed class StubHttpHandler : DelegatingHandler
    {
        private readonly Action<string> _requestHandler;
        private readonly JsonSerializerOptions _options;

        public StubHttpHandler(Action<string> requestHandler) : base()
        {
            this._requestHandler = requestHandler;
            this._options = new JsonSerializerOptions { WriteIndented = true };
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var requestData = new Dictionary<string, object>
            {
                { "RequestUri", request.RequestUri! },
                { "Method", request.Method },
                { "Headers", request.Headers.ToDictionary(h => h.Key, h => h.Value) },
            };

            this._requestHandler(JsonSerializer.Serialize(requestData, this._options));

            return new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent("Success", System.Text.Encoding.UTF8, "application/json")
            };
        }
    }

    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);
        this._httpClient.Dispose();
    }
}
