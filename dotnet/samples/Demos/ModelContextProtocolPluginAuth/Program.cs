// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Net;
using System.Text;
using System.Web;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ModelContextProtocol.Client;

var config = new ConfigurationBuilder()
    .AddUserSecrets<Program>()
    .AddEnvironmentVariables()
    .Build();

if (config["OpenAI:ApiKey"] is not { } apiKey)
{
    Console.Error.WriteLine("Please provide a valid OpenAI:ApiKey to run this sample. See the associated README.md for more details.");
    return;
}

// We can customize a shared HttpClient with a custom handler if desired
using var sharedHandler = new SocketsHttpHandler
{
    PooledConnectionLifetime = TimeSpan.FromMinutes(2),
    PooledConnectionIdleTimeout = TimeSpan.FromMinutes(1)
};
using var httpClient = new HttpClient(sharedHandler);

var consoleLoggerFactory = LoggerFactory.Create(builder =>
{
    builder.AddConsole();
});

// Create streamable HTTP client transport for the MCP server
var serverUrl = "http://localhost:7071/";
var transport = new HttpClientTransport(new()
{
    Endpoint = new Uri(serverUrl),
    Name = "Secure Weather Client",
    OAuth = new()
    {
        ClientId = "ProtectedMcpClient",
        RedirectUri = new Uri("http://localhost:1179/callback"),
        AuthorizationRedirectDelegate = HandleAuthorizationUrlAsync,
    }
}, httpClient, consoleLoggerFactory);

// Create an MCPClient for the protected MCP server
await using var mcpClient = await McpClient.CreateAsync(transport, loggerFactory: consoleLoggerFactory);

// Retrieve the list of tools available on the GitHub server
var tools = await mcpClient.ListToolsAsync().ConfigureAwait(false);
foreach (var tool in tools)
{
    Console.WriteLine($"{tool.Name}: {tool.Description}");
}

// Prepare and build kernel with the MCP tools as Kernel functions
var builder = Kernel.CreateBuilder();
builder.Services
    .AddLogging(c => c.AddDebug().SetMinimumLevel(Microsoft.Extensions.Logging.LogLevel.Trace))
    .AddOpenAIChatCompletion(
        modelId: config["OpenAI:ChatModelId"] ?? "gpt-4o-mini",
        apiKey: apiKey);
Kernel kernel = builder.Build();
kernel.Plugins.AddFromFunctions("WeatherApi", tools.Select(aiFunction => aiFunction.AsKernelFunction()));

// Enable automatic function calling
OpenAIPromptExecutionSettings executionSettings = new()
{
    Temperature = 0,
    FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
};

// Test using weather tools
var prompt = "Get current weather alerts for New York?";
var result = await kernel.InvokePromptAsync(prompt, new(executionSettings)).ConfigureAwait(false);
Console.WriteLine($"\n\n{prompt}\n{result}");

// Define the agent
ChatCompletionAgent agent = new()
{
    Instructions = "Answer questions about weather alerts for US states.",
    Name = "WeatherAgent",
    Kernel = kernel,
    Arguments = new KernelArguments(executionSettings),
};

// Respond to user input, invoking functions where appropriate.
ChatMessageContent response = await agent.InvokeAsync("Get the current weather alerts for Washington?").FirstAsync();
Console.WriteLine($"\n\nResponse from WeatherAgent:\n{response.Content}");

/// <summary>
/// Handles the OAuth authorization URL by starting a local HTTP server and opening a browser.
/// This implementation demonstrates how SDK consumers can provide their own authorization flow.
/// </summary>
/// <param name="authorizationUrl">The authorization URL to open in the browser.</param>
/// <param name="redirectUri">The redirect URI where the authorization code will be sent.</param>
/// <param name="cancellationToken">The cancellation token.</param>
/// <returns>The authorization code extracted from the callback, or null if the operation failed.</returns>
static async Task<string?> HandleAuthorizationUrlAsync(Uri authorizationUrl, Uri redirectUri, CancellationToken cancellationToken)
{
    Console.WriteLine("Starting OAuth authorization flow...");
    Console.WriteLine($"Opening browser to: {authorizationUrl}");

    var listenerPrefix = redirectUri.GetLeftPart(UriPartial.Authority);
    if (!listenerPrefix.EndsWith("/", StringComparison.InvariantCultureIgnoreCase))
    {
        listenerPrefix += "/";
    }

    using var listener = new HttpListener();
    listener.Prefixes.Add(listenerPrefix);

    try
    {
        listener.Start();
        Console.WriteLine($"Listening for OAuth callback on: {listenerPrefix}");

        OpenBrowser(authorizationUrl);

        var context = await listener.GetContextAsync();
        var query = HttpUtility.ParseQueryString(context.Request.Url?.Query ?? string.Empty);
        var code = query["code"];
        var error = query["error"];

        string responseHtml = "<html><body><h1>Authentication complete</h1><p>You can close this window now.</p></body></html>";
        byte[] buffer = Encoding.UTF8.GetBytes(responseHtml);
        context.Response.ContentLength64 = buffer.Length;
        context.Response.ContentType = "text/html";
        context.Response.OutputStream.Write(buffer, 0, buffer.Length);
        context.Response.Close();

        if (!string.IsNullOrEmpty(error))
        {
            Console.WriteLine($"Auth error: {error}");
            return null;
        }

        if (string.IsNullOrEmpty(code))
        {
            Console.WriteLine("No authorization code received");
            return null;
        }

        Console.WriteLine("Authorization code received successfully.");
        return code;
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Error getting auth code: {ex.Message}");
        return null;
    }
    finally
    {
        if (listener.IsListening)
        {
            listener.Stop();
        }
    }
}

/// <summary>
/// Opens the specified URL in the default browser.
/// </summary>
/// <param name="url">The URL to open.</param>
static void OpenBrowser(Uri url)
{
    try
    {
        var psi = new ProcessStartInfo
        {
            FileName = url.ToString(),
            UseShellExecute = true
        };
        Process.Start(psi);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Error opening browser. {ex.Message}");
        Console.WriteLine($"Please manually open this URL: {url}");
    }
}
