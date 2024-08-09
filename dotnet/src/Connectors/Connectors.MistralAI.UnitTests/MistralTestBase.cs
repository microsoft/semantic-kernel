// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.MistralAI.UnitTests;
public abstract class MistralTestBase : IDisposable
{
    protected AssertingDelegatingHandler? DelegatingHandler { get; set; }
    protected HttpClient? HttpClient { get; set; }

    protected string GetTestResponseAsString(string fileName)
    {
        return File.ReadAllText($"./TestData/{fileName}");
    }
    protected byte[] GetTestResponseAsBytes(string fileName)
    {
        return File.ReadAllBytes($"./TestData/{fileName}");
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposed)
        {
            if (disposing)
            {
                this.DelegatingHandler?.Dispose();
                this.HttpClient?.Dispose();
            }

            this._disposed = true;
        }
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    #region private
    private bool _disposed = false;

    private static HttpRequestHeaders GetDefaultRequestHeaders(string key, bool stream)
    {
#pragma warning disable CA2000 // Dispose objects before losing scope
        var requestHeaders = new HttpRequestMessage().Headers;
#pragma warning restore CA2000 // Dispose objects before losing scope
        requestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        requestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(MistralClient)));
        requestHeaders.Add("Accept", stream ? "text/event-stream" : "application/json");
        requestHeaders.Add("Authorization", $"Bearer {key}");

        return requestHeaders;
    }
    #endregion

    public sealed class AssertingDelegatingHandler : DelegatingHandler
    {
        public Uri RequestUri { get; init; }
        public HttpMethod Method { get; init; } = HttpMethod.Post;
        public HttpRequestHeaders RequestHeaders { get; init; } = GetDefaultRequestHeaders("key", false);
        public HttpResponseMessage ResponseMessage { get; private set; } = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        public string? RequestContent { get; private set; } = null;
        public int SendAsyncCallCount { get; private set; } = 0;

        private readonly string[]? _responseStringArray;
        private readonly byte[][]? _responseBytesArray;

        internal AssertingDelegatingHandler(string requestUri, params string[] responseStringArray)
        {
            this.RequestUri = new Uri(requestUri);
            this.RequestHeaders = GetDefaultRequestHeaders("key", false);
            this._responseStringArray = responseStringArray;
        }

        internal AssertingDelegatingHandler(string requestUri, bool stream = true, params byte[][] responseBytesArray)
        {
            this.RequestUri = new Uri(requestUri);
            this.RequestHeaders = GetDefaultRequestHeaders("key", stream);
            this._responseBytesArray = responseBytesArray;
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            Assert.Equal(this.RequestUri, request.RequestUri);
            Assert.Equal(this.Method, request.Method);
            Assert.Equal(this.RequestHeaders, request.Headers);

            this.RequestContent = await request.Content!.ReadAsStringAsync(cancellationToken);

            if (this._responseStringArray is not null)
            {
                var index = this.SendAsyncCallCount % this._responseStringArray.Length;
                this.ResponseMessage = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
                {
                    Content = new StringContent(this._responseStringArray[index], System.Text.Encoding.UTF8, "application/json")
                };
            }
            if (this._responseBytesArray is not null)
            {
                var index = this.SendAsyncCallCount % this._responseBytesArray.Length;
                this.ResponseMessage = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
                {
                    Content = new StreamContent(new MemoryStream(this._responseBytesArray[index]))
                };
            }
            this.SendAsyncCallCount++;

            return await Task.FromResult(this.ResponseMessage);
        }
    }
}
