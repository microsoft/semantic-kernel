// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Http;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;



namespace Microsoft.SemanticKernel.Plugins.Web.QP;

public static class ProcessExtensions
{
    /// <summary>
    /// Provides an awaitable task that completes when the process exits.
    /// </summary>
    public static Task WaitForExitAsync(this Process process, CancellationToken cancellationToken = default)
    {
        if (process.HasExited)
            return Task.CompletedTask;

        var tcs = new TaskCompletionSource<object?>(TaskCreationOptions.RunContinuationsAsynchronously);

        void Handler(object? s, EventArgs e) => tcs.TrySetResult(null);

        process.EnableRaisingEvents = true;
        process.Exited += Handler;

        if (cancellationToken != default)
        {
            cancellationToken.Register(() =>
            {
                tcs.TrySetCanceled(cancellationToken);
            });
        }

        return tcs.Task;
    }
}
/// <summary>
/// Connector for the QP (Quest Perplexity) search engine.
/// </summary>
public sealed class QPConnector : IWebSearchEngineConnector
{
    private readonly string _apiKey;

    private readonly HttpClient _httpClient;

    private readonly Uri? _uri = null;

    private const string DefaultUri = "https://api.bing.microsoft.com/v7.0/search?q";

    /// <summary>
    /// Initializes a new instance of the <see cref="QPConnector"/> class.
    /// </summary>
    /// <param name="apiKey">The API key for the QP search engine.</param>
    public QPConnector(string apiKey)
    {
        this._apiKey = apiKey;
        //this._uri = uri ?? new Uri(DefaultUri);
    }
    public static List<WebPage> ExtractUrls(JObject root)
    {
        var urls = new List<WebPage>();

        // 1. Get the array
        if (root["m_documentList"] is JArray docs)
        {
            // 2. Iterate each element
            foreach (JToken doc in docs)
            {
                WebPage webPage = new WebPage();
                // 3. Drill into m_url → m_URL
                string? url = doc["Url"]?["m_URL"]?.Value<string>();
                string? title = doc["Title"]?.Value<string>();
                string? snippet = doc["Snippet"]?.Value<string>();
                if (!string.IsNullOrEmpty(url) && !string.IsNullOrEmpty(snippet))
                {
                    webPage.Name = title;
                    webPage.Url = url;
                    webPage.Snippet = snippet;
                    Console.WriteLine("MCPTool response: {0}, {1}", url, title);
                    urls.Add(webPage);
                }
            }
        }

        return urls;
    }

    public async Task<List<WebPage>> GetUrpResponseAsync(string query,
        int count = 1,
        int offset = 0,
         CancellationToken cancellationToken = default)
    {
        string toolDir = @"..\urpmcp\";
        string command = toolDir + "UrpMcpTool.exe";
       string arguments = "simple " + "\"" + query + "\" " + count.ToString();

        Console.WriteLine("MCPTool command: {0}, {1}", command, arguments);

        var psi = new ProcessStartInfo
        {
            FileName = toolDir + command,
            Arguments = arguments,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        using var proc = new Process { StartInfo = psi, EnableRaisingEvents = true };
        

        bool debug = false;
        string outputfilename = "";
        if (debug)
        {
            outputfilename = "a9e7f02ed8989e65287777f5ffac85f3.json";
        }
        else
        {
            proc.Start();

            // Kick off both reads
            Task<string> stdOutTask = proc.StandardOutput.ReadToEndAsync();
            Task<string> stdErrTask = proc.StandardError.ReadToEndAsync();

            // Await process exit
            await proc.WaitForExitAsync().ConfigureAwait(false);

            string stdout = await stdOutTask.ConfigureAwait(false);
            string stderr = await stdErrTask.ConfigureAwait(false);
            outputfilename = stdout.TrimEnd(new[] { '\r', '\n', ' '});
            if (proc.ExitCode != 0 || !outputfilename.EndsWith("json"))
            {
                // You can choose to throw, or return an error JSON instead:
                throw new InvalidOperationException(
                    $"Command failed (exit code {proc.ExitCode}): {stderr}");
            }
        }
        string path = outputfilename;
        string jsoncontent = File.ReadAllText(path);
        // Try parse the raw output as JSON; if that fails, keep it as a string
        JToken parsedOutput;
        try
        {
            parsedOutput = JToken.Parse(jsoncontent);
        }
        catch (JsonReaderException)
        {
            parsedOutput = "";
        }

        var obj = parsedOutput as JObject;
        return ExtractUrls(obj);
    }

    /// <summary>
    /// Performs a web search using the QP search engine.
    /// </summary>
    /// <param name="query">The search query.</param>
    /// <param name="count">The number of results to return.</param>
    /// <param name="offset">The number of results to skip.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>A list of web search results.</returns>
    public async Task<IEnumerable<T>> SearchAsync<T>(
        string query,
        int count = 1,
        int offset = 0,
        CancellationToken cancellationToken = default)
    {
        count = 20;
        List<WebPage> pages = await GetUrpResponseAsync(query, count, offset).ConfigureAwait(false);
        List<T>? returnValues = null;
        if (pages is not null)
        {
            if (typeof(T) == typeof(string))
            {

                List<string> jsonList = pages.Select(p => System.Text.Json.JsonSerializer.Serialize(p, new JsonSerializerOptions
                {
                    // optional: make JSON more human‑readable
                    WriteIndented = false
                })).ToList();
                returnValues = jsonList as List<T>;
            }
            else if (typeof(T) == typeof(WebPage))
            {
                
                returnValues = pages as List<T>;
            }
            else
            {
                throw new NotSupportedException($"Type {typeof(T)} is not supported.");
            }
        }

        return
            returnValues is null ? [] :
            returnValues.Count <= count ? returnValues :
            returnValues.Take(count);
    }

    private async Task<HttpResponseMessage> SendGetRequestAsync(Uri uri, CancellationToken cancellationToken = default)
    {
        using var httpRequestMessage = new HttpRequestMessage(HttpMethod.Get, uri);
        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }
}
