// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using Azure;
using Azure.Core;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.AzureSdk;

/// <summary>
/// Unit tests for <see cref="RequestFailedExceptionExtensions"/> class.
/// </summary>
public sealed class RequestFailedExceptionExtensionsTests
{
    [Theory]
    [InlineData(0, null)]
    [InlineData(500, HttpStatusCode.InternalServerError)]
    public void ToHttpOperationExceptionWithStatusReturnsValidException(int responseStatus, HttpStatusCode? httpStatusCode)
    {
        // Arrange
        var exception = new RequestFailedException(responseStatus, "Error Message");

        // Act
        var actualException = exception.ToHttpOperationException();

        // Assert
        Assert.IsType<HttpOperationException>(actualException);
        Assert.Equal(httpStatusCode, actualException.StatusCode);
        Assert.Equal("Error Message", actualException.Message);
        Assert.Same(exception, actualException.InnerException);
    }

    [Fact]
    public void ToHttpOperationExceptionWithContentReturnsValidException()
    {
        // Arrange
        using var response = new FakeResponse("Response Content", 500);
        var exception = new RequestFailedException(response);

        // Act
        var actualException = exception.ToHttpOperationException();

        // Assert
        Assert.IsType<HttpOperationException>(actualException);
        Assert.Equal(HttpStatusCode.InternalServerError, actualException.StatusCode);
        Assert.Equal("Response Content", actualException.ResponseContent);
        Assert.Same(exception, actualException.InnerException);
    }

    #region private

    private sealed class FakeResponse(string responseContent, int status) : Response
    {
        private readonly string _responseContent = responseContent;
        private readonly int _status = status;
        private readonly IEnumerable<HttpHeader> _headers = new List<HttpHeader>();

        public override BinaryData Content => BinaryData.FromString(this._responseContent);
        public override int Status => this._status;
        public override string ReasonPhrase => "Reason Phrase";
        public override Stream? ContentStream { get => null; set => throw new NotImplementedException(); }
        public override string ClientRequestId { get => "Client Request Id"; set => throw new NotImplementedException(); }

        public override void Dispose() { }
        protected override bool ContainsHeader(string name) => throw new NotImplementedException();
        protected override IEnumerable<HttpHeader> EnumerateHeaders() => this._headers;
#pragma warning disable CS8765 // Nullability of type of parameter doesn't match overridden member (possibly because of nullability attributes).
        protected override bool TryGetHeader(string name, out string? value) => throw new NotImplementedException();
        protected override bool TryGetHeaderValues(string name, out IEnumerable<string>? values) => throw new NotImplementedException();
#pragma warning restore CS8765 // Nullability of type of parameter doesn't match overridden member (possibly because of nullability attributes).
    }

    #endregion
}
