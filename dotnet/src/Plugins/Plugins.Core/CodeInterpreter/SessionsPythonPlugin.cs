// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;

/// <summary>
/// A plugin for running Python code in an Azure Container Apps dynamic sessions code interpreter.
/// </summary>
public sealed partial class SessionsPythonPlugin
{
    private static readonly string s_assemblyVersion = typeof(Kernel).Assembly.GetName().Version!.ToString();
    private const string ApiVersion = "2024-10-02-preview";
    private readonly Uri _poolManagementEndpoint;
    private readonly SessionsPythonSettings _settings;
    private readonly Func<CancellationToken, Task<string>>? _authTokenProvider;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger _logger;

    /// <summary>
    /// Initializes a new instance of the SessionsPythonTool class.
    /// </summary>
    /// <param name="settings">The settings for the Python tool plugin.</param>
    /// <param name="httpClientFactory">The HTTP client factory.</param>
    /// <param name="authTokenProvider">Optional provider for auth token generation.</param>
    /// <param name="loggerFactory">The logger factory.</param>
    public SessionsPythonPlugin(
        SessionsPythonSettings settings,
        IHttpClientFactory httpClientFactory,
        Func<CancellationToken, Task<string>>? authTokenProvider = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(settings, nameof(settings));
        Verify.NotNull(httpClientFactory, nameof(httpClientFactory));
        Verify.NotNull(settings.Endpoint, nameof(settings.Endpoint));

        this._settings = settings;

        // Ensure the endpoint won't change by reference
        this._poolManagementEndpoint = GetBaseEndpoint(settings.Endpoint);

        this._authTokenProvider = authTokenProvider;
        this._httpClientFactory = httpClientFactory;
        this._logger = loggerFactory?.CreateLogger(typeof(SessionsPythonPlugin)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Executes the provided Python code.
    /// Start and end the code snippet with double quotes to define it as a string.
    /// Insert \n within the string wherever a new line should appear.
    /// Add spaces directly after \n sequences to replicate indentation.
    /// Use \"" to include double quotes within the code without ending the string.
    /// Keep everything in a single line; the \n sequences will represent line breaks
    /// when the string is processed or displayed.
    /// </summary>
    /// <param name="code"> The valid Python code to execute.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns> The result of the Python code execution. </returns>
    /// <exception cref="ArgumentNullException"></exception>
    /// <exception cref="HttpRequestException"></exception>
    [KernelFunction, Description("""
        Executes the provided Python code.
        Start and end the code snippet with double quotes to define it as a string.
        Insert \n within the string wherever a new line should appear.
        Add spaces directly after \n sequences to replicate indentation.
        Use \" to include double quotes within the code without ending the string.
        Keep everything in a single line; the \n sequences will represent line breaks
        when the string is processed or displayed.
        """)]
    public async Task<string> ExecuteCodeAsync(
        [Description("The valid Python code to execute.")] string code,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(code, nameof(code));

        if (this._settings.SanitizeInput)
        {
            code = SanitizeCodeInput(code);
        }

        this._logger.LogTrace("Executing Python code: {Code}", code);

        using var httpClient = this._httpClientFactory.CreateClient();

        var requestBody = new SessionsPythonCodeExecutionProperties(this._settings, code);

        using var content = new StringContent(JsonSerializer.Serialize(requestBody), Encoding.UTF8, "application/json");

        using var response = await this.SendAsync(httpClient, HttpMethod.Post, "executions", cancellationToken, content).ConfigureAwait(false);

        var responseContent = JsonSerializer.Deserialize<JsonElement>(await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false));

        var result = responseContent.GetProperty("result");

        return $"""
            Status:
            {responseContent.GetProperty("status").GetRawText()}
            Result:
            {result.GetProperty("executionResult").GetRawText()}
            Stdout:
            {result.GetProperty("stdout").GetRawText()}
            Stderr:
            {result.GetProperty("stderr").GetRawText()}
            """;
    }

    /// <summary>
    /// Uploads a file to the `/mnt/data` directory of the current session.
    /// </summary>
    /// <param name="remoteFileName">The name of the remote file, relative to `/mnt/data`.</param>
    /// <param name="localFilePath">The path to the file on the local machine.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The metadata of the uploaded file.</returns>
    /// <exception cref="ArgumentNullException"></exception>
    /// <exception cref="HttpRequestException"></exception>
    [KernelFunction, Description("Uploads a file to the `/mnt/data` directory of the current session.")]
    public async Task<SessionsRemoteFileMetadata> UploadFileAsync(
        [Description("The name of the remote file, relative to `/mnt/data`.")] string remoteFileName,
        [Description("The path to the file on the local machine.")] string localFilePath,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(remoteFileName, nameof(remoteFileName));
        Verify.NotNullOrWhiteSpace(localFilePath, nameof(localFilePath));

        this._logger.LogInformation("Uploading file: {LocalFilePath} to {RemoteFileName}", localFilePath, remoteFileName);

        using var httpClient = this._httpClientFactory.CreateClient();

        using var fileContent = new ByteArrayContent(File.ReadAllBytes(localFilePath));

        using var multipartFormDataContent = new MultipartFormDataContent()
        {
            { fileContent, "file", remoteFileName },
        };

        using var response = await this.SendAsync(httpClient, HttpMethod.Post, "files", cancellationToken, multipartFormDataContent).ConfigureAwait(false);

        var stringContent = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);

        return JsonSerializer.Deserialize<SessionsRemoteFileMetadata>(stringContent)!;
    }

    /// <summary>
    /// Downloads a file from the `/mnt/data` directory of the current session.
    /// </summary>
    /// <param name="remoteFileName">The name of the remote file to download, relative to `/mnt/data`.</param>
    /// <param name="localFilePath">The path to save the downloaded file to. If not provided won't save it in the disk.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The data of the downloaded file as byte array.</returns>
    [KernelFunction, Description("Downloads a file from the `/mnt/data` directory of the current session.")]
    public async Task<byte[]> DownloadFileAsync(
        [Description("The name of the remote file to download, relative to `/mnt/data`.")] string remoteFileName,
        [Description("The path to save the downloaded file to. If not provided won't save it in the disk.")] string? localFilePath = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(remoteFileName, nameof(remoteFileName));

        this._logger.LogTrace("Downloading file: {RemoteFileName} to {LocalFileName}", remoteFileName, localFilePath);

        using var httpClient = this._httpClientFactory.CreateClient();

        using var response = await this.SendAsync(httpClient, HttpMethod.Get, $"files/{Uri.EscapeDataString(remoteFileName)}/content", cancellationToken).ConfigureAwait(false);

        var fileContent = await response.Content.ReadAsByteArrayAndTranslateExceptionAsync(cancellationToken).ConfigureAwait(false);

        if (!string.IsNullOrWhiteSpace(localFilePath))
        {
            try
            {
                File.WriteAllBytes(localFilePath, fileContent);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException("Failed to write file to disk.", ex);
            }
        }

        return fileContent;
    }

    /// <summary>
    /// Lists all entities: files or directories in the `/mnt/data` directory of the current session.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The list of files in the session.</returns>
    [KernelFunction, Description("Lists all entities: files or directories in the `/mnt/data` directory of the current session.")]
    public async Task<IReadOnlyList<SessionsRemoteFileMetadata>> ListFilesAsync(CancellationToken cancellationToken = default)
    {
        this._logger.LogTrace("Listing files for Session ID: {SessionId}", this._settings.SessionId);

        using var httpClient = this._httpClientFactory.CreateClient();

        using var response = await this.SendAsync(httpClient, HttpMethod.Get, "files", cancellationToken).ConfigureAwait(false);

        var jsonElementResult = JsonSerializer.Deserialize<JsonElement>(await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false));

        var files = jsonElementResult.GetProperty("value");

        return files.Deserialize<SessionsRemoteFileMetadata[]>()!;
    }

    private static Uri GetBaseEndpoint(Uri endpoint)
    {
        if (endpoint.PathAndQuery.Contains("/python/execute"))
        {
            endpoint = new Uri(endpoint.ToString().Replace("/python/execute", ""));
        }

        if (!endpoint.PathAndQuery.EndsWith("/", StringComparison.InvariantCulture))
        {
            endpoint = new Uri(endpoint + "/");
        }

        return endpoint;
    }

    /// <summary>
    /// Sanitize input to the python REPL.
    /// Remove whitespace, backtick and "python" (if llm mistakes python console as terminal)
    /// </summary>
    /// <param name="code">The code to sanitize</param>
    /// <returns>The sanitized code</returns>
    private static string SanitizeCodeInput(string code)
    {
        // Remove leading whitespace and backticks and python (if llm mistakes python console as terminal)
        code = RemoveLeadingWhitespaceBackticksPython().Replace(code, "");

        // Remove trailing whitespace and backticks
        code = RemoveTrailingWhitespaceBackticks().Replace(code, "");

        return code;
    }

    /// <summary>
    /// Add headers to the HTTP request.
    /// </summary>
    /// <param name="request">The HTTP request to add headers to.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    private async Task AddHeadersAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        request.Headers.Add("User-Agent", $"{HttpHeaderConstant.Values.UserAgent}/{s_assemblyVersion} (Language=dotnet)");

        if (this._authTokenProvider is not null)
        {
            request.Headers.Add("Authorization", $"Bearer {(await this._authTokenProvider(cancellationToken).ConfigureAwait(false))}");
        }
    }

    /// <summary>
    /// Sends an HTTP request to the specified path with the specified method and content.
    /// </summary>
    /// <param name="httpClient">The HTTP client to use.</param>
    /// <param name="method">The HTTP method to use.</param>
    /// <param name="path">The path to send the request to.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <param name="httpContent">The content to send with the request.</param>
    /// <returns>The HTTP response message.</returns>
    private async Task<HttpResponseMessage> SendAsync(HttpClient httpClient, HttpMethod method, string path, CancellationToken cancellationToken, HttpContent? httpContent = null)
    {
        // The query string is the same for all operations
        var pathWithQueryString = $"{path}?identifier={this._settings.SessionId}&api-version={ApiVersion}";

        var uri = new Uri(this._poolManagementEndpoint, pathWithQueryString);

        // If a list of allowed domains has been provided, the host of the provided
        // uri is checked to verify it is in the allowed domain list.
        if (!this._settings.AllowedDomains?.Contains(uri.Host) ?? false)
        {
            throw new InvalidOperationException("Sending requests to the provided location is not allowed.");
        }

        using var request = new HttpRequestMessage(method, uri)
        {
            Content = httpContent,
        };

        await this.AddHeadersAsync(request, cancellationToken).ConfigureAwait(false);

        return await httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
    }

#if NET
    [GeneratedRegex(@"^(\s|`)*(?i:python)?\s*", RegexOptions.ExplicitCapture)]
    private static partial Regex RemoveLeadingWhitespaceBackticksPython();

    [GeneratedRegex(@"(\s|`)*$", RegexOptions.ExplicitCapture)]
    private static partial Regex RemoveTrailingWhitespaceBackticks();
#else
    private static Regex RemoveLeadingWhitespaceBackticksPython() => s_removeLeadingWhitespaceBackticksPython;
    private static readonly Regex s_removeLeadingWhitespaceBackticksPython = new(@"^(\s|`)*(?i:python)?\s*", RegexOptions.Compiled | RegexOptions.ExplicitCapture);

    private static Regex RemoveTrailingWhitespaceBackticks() => s_removeTrailingWhitespaceBackticks;
    private static readonly Regex s_removeTrailingWhitespaceBackticks = new(@"(\s|`)*$", RegexOptions.Compiled | RegexOptions.ExplicitCapture);
#endif
}
