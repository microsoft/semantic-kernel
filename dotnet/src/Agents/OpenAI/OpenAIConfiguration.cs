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
        AzureOpenAIKey,
        AzureOpenAICredential,
        OpenAI,
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="endpoint"></param>
    /// <param name="apiKey"></param>
    /// <param name="httpClient"></param>
    /// <returns></returns>
    public static OpenAIConfiguration ForAzureOpenAI(Uri endpoint, string apiKey, HttpClient? httpClient = null) =>
        // %%% VERIFY
        new()
        {
            ApiKey = apiKey,
            Endpoint = endpoint,
            HttpClient = httpClient,
            Type = OpenAIConfigurationType.AzureOpenAIKey,
        };

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="endpoint"></param>
    /// <param name="credentials"></param>
    /// <param name="httpClient"></param>
    /// <returns></returns>
    public static OpenAIConfiguration ForAzureOpenAI(Uri endpoint, TokenCredential credentials, HttpClient? httpClient = null) =>
        // %%% VERIFY
        new()
        {
            Credentials = credentials,
            Endpoint = endpoint,
            HttpClient = httpClient,
            Type = OpenAIConfigurationType.AzureOpenAICredential,
        };

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="endpoint"></param>
    /// <param name="apiKey"></param>
    /// <param name="httpClient"></param>
    /// <returns></returns>
    public static OpenAIConfiguration ForOpenAI(Uri endpoint, string apiKey, HttpClient? httpClient = null) =>
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
    /// <param name="endpoint"></param>
    /// <param name="apiKey"></param>
    /// <param name="organizationId"></param>
    /// <param name="httpClient"></param>
    /// <returns></returns>
    public static OpenAIConfiguration ForOpenAI(Uri endpoint, string apiKey, string organizationId, HttpClient? httpClient = null) =>
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
    internal TokenCredential? Credentials { get; init; }
    internal Uri? Endpoint { get; init; }
    internal HttpClient? HttpClient { get; init; }
    internal string? OrganizationId { get; init; }
    internal OpenAIConfigurationType Type { get; init; }
}
