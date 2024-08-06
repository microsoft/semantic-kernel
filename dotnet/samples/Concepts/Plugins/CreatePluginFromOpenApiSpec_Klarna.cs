// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

public class CreatePluginFromOpenApiSpec_Klarna(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This sample shows how to invoke an OpenApi plugin.
    /// </summary>
    /// <remarks>
    /// You must provide the plugin name and a URI to the Open API manifest before running this sample.
    /// </remarks>
    [Fact(Skip = "Run it only after filling the template below")]
    public async Task InvokeOpenApiPluginAsync()
    {
        Kernel kernel = new();

        // This HTTP client is optional. SK will fallback to a default internal one if omitted.
        using HttpClient httpClient = new();

        // Import an Open AI plugin via URI
        var plugin = await kernel.ImportPluginFromOpenApiAsync("<plugin name>", new Uri("<OpenApi-plugin>"), new OpenApiFunctionExecutionParameters(httpClient));

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var arguments = new KernelArguments { ["<parameter-name>"] = "<parameter-value>" };

        // Run
        var functionResult = await kernel.InvokeAsync(plugin["<function-name>"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine($"Function execution result: {result?.Content}");
    }

    /// <summary>
    /// This sample shows how to invoke the Klarna Get Products function as an OpenAPI plugin.
    /// </summary>
    [Fact]
    public async Task InvokeKlarnaGetProductsAsOpenApiPluginAsync()
    {
        Kernel kernel = new();

        var plugin = await kernel.ImportPluginFromOpenApiAsync("Klarna", new Uri("https://www.klarna.com/us/shopping/public/openai/v0/api-docs/"));

        var arguments = new KernelArguments
        {
            ["q"] = "Laptop",      // Category or product that needs to be searched for.
            ["size"] = "3",        // Number of products to return
            ["budget"] = "200",    // Maximum price of the matching product in local currency
            ["countryCode"] = "US" // ISO 3166 country code with 2 characters based on the user location.
        };
        // Currently, only US, GB, DE, SE and DK are supported.

        var functionResult = await kernel.InvokeAsync(plugin["productsUsingGET"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine($"Function execution result: {result?.Content}");
    }

    /// <summary>
    /// This sample shows how to use a delegating handler when invoking an OpenAPI function.
    /// </summary>
    /// <remarks>
    /// An instances of <see cref="OpenApiKernelFunctionContext"/> will be set in the `HttpRequestMessage.Options` (for .NET 5.0 or higher) or
    /// in the `HttpRequestMessage.Properties` dictionary (for .NET Standard) with the key `KernelFunctionContextKey`.
    /// The <see cref="OpenApiKernelFunctionContext"/> contains the <see cref="Kernel"/>, <see cref="KernelFunction"/> and <see cref="KernelArguments"/>.
    /// </remarks>
    [Fact]
    public async Task UseDelegatingHandlerWhenInvokingAnOpenApiFunctionAsync()
    {
        using var httpHandler = new HttpClientHandler();
        using var customHandler = new CustomHandler(httpHandler);
        using HttpClient httpClient = new(customHandler);

        Kernel kernel = new();

        var plugin = await kernel.ImportPluginFromOpenApiAsync("Klarna", new Uri("https://www.klarna.com/us/shopping/public/openai/v0/api-docs/"), new OpenApiFunctionExecutionParameters(httpClient));

        var arguments = new KernelArguments
        {
            ["q"] = "Laptop",      // Category or product that needs to be searched for.
            ["size"] = "3",        // Number of products to return
            ["budget"] = "200",    // Maximum price of the matching product in local currency
            ["countryCode"] = "US" // ISO 3166 country code with 2 characters based on the user location.
        };
        // Currently, only US, GB, DE, SE and DK are supported.

        var functionResult = await kernel.InvokeAsync(plugin["productsUsingGET"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine($"Function execution result: {result?.Content}");
    }

    /// <summary>
    /// Custom delegating handler to modify the <see cref="HttpRequestMessage"/> before sending it.
    /// </summary>
    private sealed class CustomHandler(HttpMessageHandler innerHandler) : DelegatingHandler(innerHandler)
    {
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
#if NET5_0_OR_GREATER
            request.Options.TryGetValue(OpenApiKernelFunctionContext.KernelFunctionContextKey, out var functionContext);
#else
            request.Properties.TryGetValue(OpenApiKernelFunctionContext.KernelFunctionContextKey, out var functionContext);
#endif
            // Function context is only set when the Plugin is invoked via the Kernel
            if (functionContext is not null)
            {
                // Modify the HttpRequestMessage
                request.Headers.Add("Kernel-Function-Name", functionContext?.Function?.Name);
            }

            // Call the next handler in the pipeline
            return await base.SendAsync(request, cancellationToken);
        }
    }
}
