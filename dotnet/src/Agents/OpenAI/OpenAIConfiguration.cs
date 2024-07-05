// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net.Http;
using Azure.Core;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Configuration for OpenAI services.
/// </summary>
public sealed class OpenAIConfiguration
{
    internal enum OpenAIConfigurationType
    {
        AzureOpenAI,
        OpenAI,
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="apiKey"></param>
    /// <param name="endpoint"></param>
    /// <param name="httpClient"></param>
    /// <returns></returns>
    public static OpenAIConfiguration ForAzureOpenAI(string apiKey, Uri endpoint, HttpClient? httpClient = null) =>
        // %%% VERIFY
        new()
        {
            ApiKey = apiKey,
            Endpoint = endpoint,
            HttpClient = httpClient,
            Type = OpenAIConfigurationType.AzureOpenAI,
        };

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="credential"></param>
    /// <param name="endpoint"></param>
    /// <param name="httpClient"></param>
    /// <returns></returns>
    public static OpenAIConfiguration ForAzureOpenAI(TokenCredential credential, Uri endpoint, HttpClient? httpClient = null) =>
        // %%% VERIFY
        new()
        {
            Credential = credential,
            Endpoint = endpoint,
            HttpClient = httpClient,
            Type = OpenAIConfigurationType.AzureOpenAI,
        };

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="apiKey"></param>
    /// <param name="endpoint"></param>
    /// <param name="httpClient"></param>
    /// <returns></returns>
    public static OpenAIConfiguration ForOpenAI(string apiKey, Uri? endpoint = null, HttpClient? httpClient = null) =>
        // %%% VERIFY
        new()
        {
            ApiKey = apiKey,
            Endpoint = endpoint,
            HttpClient = httpClient,
            Type = OpenAIConfigurationType.OpenAI,
        };

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="apiKey"></param>
    /// <param name="organizationId"></param>
    /// <param name="endpoint"></param>
    /// <param name="httpClient"></param>
    /// <returns></returns>
    public static OpenAIConfiguration ForOpenAI(string apiKey, string organizationId, Uri? endpoint = null, HttpClient? httpClient = null) =>
        // %%% VERIFY
        new()
        {
            ApiKey = apiKey,
            Endpoint = endpoint,
            HttpClient = httpClient,
            OrganizationId = organizationId,
            Type = OpenAIConfigurationType.OpenAI,
        };

    internal string? ApiKey { get; init; }
    internal TokenCredential? Credential { get; init; }
    internal Uri? Endpoint { get; init; }
    internal HttpClient? HttpClient { get; init; }
    internal string? OrganizationId { get; init; }
    internal OpenAIConfigurationType Type { get; init; }
}
