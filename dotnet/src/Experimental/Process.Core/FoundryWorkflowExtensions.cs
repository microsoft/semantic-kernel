// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Azure.Core;
using Azure.Core.Pipeline;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Extensions for managing Foundry Workflows
/// </summary>
public static class FoundryWorkflowExtensions
{
    /// <summary>
    /// Publishes a workflow using a <see cref="ClientPipeline"/> and a <see cref="FoundryProcessBuilder{T}"/>.
    /// </summary>
    /// <typeparam name="T">The process state type.</typeparam>
    /// <param name="pipeline">The client pipeline.</param>
    /// <param name="process">The process builder.</param>
    /// <returns>The published <see cref="Workflow"/>.</returns>
    public static async Task<Workflow> PublishWorkflowAsync<T>(this ClientPipeline pipeline, FoundryProcessBuilder<T> process) where T : class, new()
    {
        // Send the request
        using var message = pipeline.CreateMessage();
        var payload = await process.ToJsonAsync().ConfigureAwait(false);
        message.Request.Method = "POST";
        message.Request.Uri = new Uri("https://localhost/agents");
        message.Request.Content = System.ClientModel.BinaryContent.Create(new MemoryStream(Encoding.UTF8.GetBytes(payload)));
        message.Request.Headers.Add("Content-Type", "application/json");

        await pipeline.SendAsync(message).ConfigureAwait(false);

        if (message.Response?.Status < 200 || message.Response?.Status >= 300)
        {
            var errorContent = await message.Response.Content.AsJsonAsync().ConfigureAwait(false);

            throw new KernelException($"Error publishing workflow: {errorContent}");
        }

        var responseJson = await message.Response!.Content.AsJsonAsync().ConfigureAwait(false) ?? string.Empty;

        using var doc = JsonDocument.Parse(responseJson);
        var workflowId = doc.RootElement.GetProperty("id").GetString() ?? string.Empty;

        return new Workflow() { Id = workflowId };
    }

    /// <summary>
    /// Publishes a workflow using an <see cref="HttpPipeline"/> and a <see cref="FoundryProcessBuilder{T}"/>.
    /// </summary>
    /// <typeparam name="T">The process state type.</typeparam>
    /// <param name="pipeline">The HTTP pipeline.</param>
    /// <param name="process">The process builder.</param>
    /// <returns>The published <see cref="Workflow"/>.</returns>
    public static async Task<Workflow> PublishWorkflowAsync<T>(this HttpPipeline pipeline, FoundryProcessBuilder<T> process) where T : class, new()
    {
        // Send the request
        using var message = pipeline.CreateMessage();
        message.Request.Method = RequestMethod.Post;
        message.Request.Uri.Reset(new Uri("https://localhost/agents"));
        message.Request.Content = RequestContent.Create(new MemoryStream(Encoding.UTF8.GetBytes(await process.ToJsonAsync().ConfigureAwait(false))));
        message.Request.Headers.Add("Content-Type", "application/json");

        await pipeline.SendAsync(message, default).ConfigureAwait(false);

        if (message.Response?.Status < 200 || message.Response?.Status >= 300)
        {
            var errorContent = await message.Response.Content.AsJsonAsync().ConfigureAwait(false);

            throw new KernelException($"Error publishing workflow: {errorContent}");
        }

        var responseJson = await message.Response!.Content.AsJsonAsync().ConfigureAwait(false) ?? string.Empty;

        using var doc = JsonDocument.Parse(responseJson);
        var workflowId = doc.RootElement.GetProperty("id").GetString() ?? string.Empty;

        Console.WriteLine($"Creating workflow {workflowId}...");

        return new Workflow() { Id = workflowId };
    }

    /// <summary>
    /// Deletes a workflow using a <see cref="ClientPipeline"/>.
    /// </summary>
    /// <param name="pipeline">The client pipeline.</param>
    /// <param name="workflow">The workflow to delete.</param>
    public static async Task DeleteWorkflowAsync(this ClientPipeline pipeline, Workflow workflow)
    {
        // Send the request
        using var message = pipeline.CreateMessage();
        message.Request.Method = "DELETE";
        message.Request.Uri = new Uri($"https://localhost/agents/{workflow.Id}");

        await pipeline.SendAsync(message).ConfigureAwait(false);

        if (message.Response?.Status < 200 || message.Response?.Status >= 300)
        {
            throw new KernelException($"Failed to delete workflow: {message.Response?.Status} {message.Response?.ReasonPhrase}");
        }
    }

    /// <summary>
    /// Deletes a workflow using an <see cref="HttpPipeline"/>.
    /// </summary>
    /// <param name="pipeline">The HTTP pipeline.</param>
    /// <param name="workflow">The workflow to delete.</param>
    public static async Task DeleteWorkflowAsync(this HttpPipeline pipeline, Workflow workflow)
    {
        // Send the request
        using var message = pipeline.CreateMessage();
        message.Request.Method = RequestMethod.Delete;
        message.Request.Uri.Reset(new Uri($"https://localhost/agents/{workflow.Id}"));

        await pipeline.SendAsync(message, default).ConfigureAwait(false);

        if (message.Response?.Status < 200 || message.Response?.Status >= 300)
        {
            throw new KernelException($"Failed to delete workflow: {message.Response?.Status} {message.Response?.ReasonPhrase}");
        }
    }

    /// <summary>
    /// Reads the <see cref="BinaryData"/> as a JSON string asynchronously.
    /// </summary>
    /// <param name="data">The binary data.</param>
    /// <returns>The JSON string.</returns>
    public static async Task<string> AsJsonAsync(this BinaryData data)
    {
        if (data == null || data.Length == 0)
        {
            return string.Empty;
        }

        using var reader = new StreamReader(data.ToStream(), Encoding.UTF8);

        return await reader.ReadToEndAsync().ConfigureAwait(false);
    }
}
