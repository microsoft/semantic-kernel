// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using Azure.Core;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Extensions for rerouting URIs for Azure AI Agents and Workflows.
/// </summary>
internal static class FoundryWorkflowHelperExtensions
{
    /// <summary>
    /// Reroutes the specified URI for workflow or agent endpoints, updating the API version and path as needed.
    /// </summary>
    /// <param name="uri">The original URI.</param>
    /// <param name="apiVersion">The API version to use.</param>
    /// <param name="isWorkflow">Indicates if the URI should be rewritten for a workflow.</param>
    /// <returns>The rerouted <see cref="Uri"/>.</returns>
    public static Uri Reroute(this Uri uri, string apiVersion, bool isWorkflow)
    {
        UriBuilder uriBuilder = new(uri);

        // Check if URI contains "run" and body contains assistant_id starting with "wf_"
        bool isRunOrAgentPath =
           uri.ToString().Contains("runs", StringComparison.OrdinalIgnoreCase) ||
           uri.AbsolutePath.EndsWith("/agents", StringComparison.OrdinalIgnoreCase);

        bool isWorkflowInstance =
            uri.AbsolutePath.Contains("/wf_agent");

        bool shouldRewriteToWorkflow =
            (isRunOrAgentPath && isWorkflow) || isWorkflowInstance;

        if (shouldRewriteToWorkflow)
        {
            // 1RP
            if (uriBuilder.Host.EndsWith("services.ai.azure.com", StringComparison.OrdinalIgnoreCase))
            {
                var items = new ArrayList(uriBuilder.Path.Split(['/'], options: StringSplitOptions.RemoveEmptyEntries));
                if (items.Count > 3)
                {
                    items.Insert(3, "workflows");
                }

                uriBuilder.Path = string.Join("/", items.ToArray());
            }
            else
            {
                // Non-1RP (Machine Learning RP)
                uriBuilder.Path = Regex.Replace(uriBuilder.Path, "/agents/v1.0", "/workflows/v1.0", RegexOptions.IgnoreCase);
            }
        }

        // Remove the "/openai" request URI infix, if present
        uriBuilder.Path = Regex.Replace(uriBuilder.Path, "/openai", string.Empty);

        // Substitute the Azure AI Agents api-version where the default AOAI one is
        uriBuilder.Query = Regex.Replace(uriBuilder.Query, "api-version=[^&]*", $"api-version={apiVersion}");

        // Ensure file search citation result content is always requested on run steps
        if (!uriBuilder.Query.Contains("include[]"))
        {
            uriBuilder.Query += "&include[]=step_details.tool_calls[*].file_search.results[*].content";
        }

        return uriBuilder.Uri;
    }

    /// <summary>
    /// Determines whether the <see cref="RequestContent"/> contains a workflow pattern.
    /// </summary>
    /// <param name="content">The request content.</param>
    /// <returns><c>true</c> if the content contains a workflow pattern; otherwise, <c>false</c>.</returns>
    public static bool IsWorkflow(this RequestContent content)
    {
        return IsWorkflowInternal(content, (c, s) => c?.WriteTo(s, default));
    }

    /// <summary>
    /// Determines whether the <see cref="System.ClientModel.BinaryContent"/> contains a workflow pattern.
    /// </summary>
    /// <param name="content">The binary content.</param>
    /// <returns><c>true</c> if the content contains a workflow pattern; otherwise, <c>false</c>.</returns>
    public static bool IsWorkflow(this System.ClientModel.BinaryContent content)
    {
        return IsWorkflowInternal(content, (c, s) => c?.WriteTo(s, default));
    }

    private static bool IsWorkflowInternal<T>(T content, Action<T, Stream> writeToStream)
    {
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            using var stream = new MemoryStream();
            writeToStream(content, stream);
            return StreamContainsWorkflowPattern(stream, @"""assistant_id"":""wf_", @"""workflow_version");
        }
        catch
        {
            // ignore
        }
#pragma warning restore CA1031 // Do not catch general exception types
        return false;
    }

    private static bool StreamContainsWorkflowPattern(Stream stream, params string[] bodies)
    {
        var patterns = bodies.Select(b => Encoding.UTF8.GetBytes(b)).ToArray();
        stream.Position = 0;
        int b;
        var matchIndexes = new int[patterns.Length];
        while ((b = stream.ReadByte()) != -1)
        {
            for (int i = 0; i < patterns.Length; i++)
            {
                if (b == patterns[i][matchIndexes[i]])
                {
                    matchIndexes[i]++;
                    if (matchIndexes[i] == patterns[i].Length)
                    {
                        return true;
                    }
                }
                else
                {
                    matchIndexes[i] = (b == patterns[i][0]) ? 1 : 0;
                }
            }
        }
        return false;
    }

    private static bool Contains(this string source, string value, StringComparison comparison)
    {
#if NETCOREAPP3_0_OR_GREATER
        return source.Contains(value, comparison);
#else
        return source.IndexOf(value, comparison) >= 0;
#endif
    }
}
