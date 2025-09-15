// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

/// <summary>
/// Sample shows how to register the <see cref="RestApiOperationResponseFactory"/> to transform existing or create new <see cref="RestApiOperationResponse"/>.
/// </summary>
public sealed class OpenApiPlugin_RestApiOperationResponseFactory(ITestOutputHelper output) : BaseTest(output)
{
    private readonly HttpClient _httpClient = new(new StubHttpHandler(InterceptRequestAndCustomizeResponseAsync));

    [Fact]
    public async Task IncludeResponseHeadersToOperationResponseAsync()
    {
        Kernel kernel = new();

        // Register the operation response factory and the custom HTTP client
        OpenApiFunctionExecutionParameters executionParameters = new()
        {
            RestApiOperationResponseFactory = IncludeHeadersIntoRestApiOperationResponseAsync,
            HttpClient = this._httpClient
        };

        // Create OpenAPI plugin
        KernelPlugin plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("RepairService", "Resources/Plugins/RepairServicePlugin/repair-service.json", executionParameters);

        // Create arguments for a new repair
        KernelArguments arguments = new()
        {
            ["title"] = "The Case of the Broken Gizmo",
            ["description"] = "It's broken. Send help!",
            ["assignedTo"] = "Tech Magician"
        };

        // Create the repair
        FunctionResult createResult = await plugin["createRepair"].InvokeAsync(kernel, arguments);

        // Get operation response that was modified
        RestApiOperationResponse response = createResult.GetValue<RestApiOperationResponse>()!;

        // Display the 'repair-id' header value
        Console.WriteLine(response.Headers!["repair-id"].First());
    }

    /// <summary>
    /// A custom factory to transform the operation response.
    /// </summary>
    /// <param name="context">The context for the <see cref="RestApiOperationResponseFactory"/>.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The transformed operation response.</returns>
    private static async Task<RestApiOperationResponse> IncludeHeadersIntoRestApiOperationResponseAsync(RestApiOperationResponseFactoryContext context, CancellationToken cancellationToken)
    {
        // Create the response using the internal factory
        RestApiOperationResponse response = await context.InternalFactory(context, cancellationToken);

        // Obtain the 'repair-id' header value from the HTTP response and include it in the operation response only for the 'createRepair' operation
        if (context.Operation.Id == "createRepair" && context.Response.Headers.TryGetValues("repair-id", out IEnumerable<string>? values))
        {
            response.Headers ??= new Dictionary<string, IEnumerable<string>>();
            response.Headers["repair-id"] = values;
        }

        // Include the request options in the operation response
        if (context.Request.Options is not null)
        {
            response.Data ??= new Dictionary<string, object?>();
            response.Data["http.request.options"] = context.Request.Options;
        }

        // Return the modified response that will be returned to the caller
        return response;
    }

    /// <summary>
    /// A custom HTTP handler to intercept HTTP requests and return custom responses.
    /// </summary>
    /// <param name="request">The original HTTP request.</param>
    /// <returns>The custom HTTP response.</returns>
    private static async Task<HttpResponseMessage> InterceptRequestAndCustomizeResponseAsync(HttpRequestMessage request)
    {
        // Return a mock response that includes the 'repair-id' header for the 'createRepair' operation
        if (request.RequestUri!.AbsolutePath == "/repairs" && request.Method == HttpMethod.Post)
        {
            return new HttpResponseMessage(HttpStatusCode.Created)
            {
                Content = new StringContent("Success", Encoding.UTF8, "application/json"),
                Headers =
                {
                    { "repair-id", "repair-12345" }
                }
            };
        }

        return new HttpResponseMessage(HttpStatusCode.NoContent);
    }

    private sealed class StubHttpHandler(Func<HttpRequestMessage, Task<HttpResponseMessage>> requestHandler) : DelegatingHandler()
    {
        private readonly Func<HttpRequestMessage, Task<HttpResponseMessage>> _requestHandler = requestHandler;

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            return await this._requestHandler(request);
        }
    }

    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);
        this._httpClient.Dispose();
    }
}
