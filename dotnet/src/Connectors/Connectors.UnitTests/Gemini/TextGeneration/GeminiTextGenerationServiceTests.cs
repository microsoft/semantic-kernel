#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.IO;
using System.Net.Http;

namespace SemanticKernel.Connectors.UnitTests.Gemini.TextGeneration;

public class GeminiTextGenerationServiceTests
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public GeminiTextGenerationServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText("./Gemini/TextGeneration/TestData/completion_one_response.json"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }
}
