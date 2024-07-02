// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.IO;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Core;

/// <summary>
/// Unit tests for <see cref="ClientResultExceptionExtensions"/> class.
/// </summary>
public sealed class ClientResultExceptionExtensionsTests
{
    [Fact]
    public void ToHttpOperationExceptionWithContentReturnsValidException()
    {
        // Arrange
        using var response = new FakeResponse("Response Content", 500);
        var exception = new ClientResultException(response);

        // Act
        var actualException = exception.ToHttpOperationException();

        // Assert
        Assert.IsType<HttpOperationException>(actualException);
        Assert.Equal(HttpStatusCode.InternalServerError, actualException.StatusCode);
        Assert.Equal("Response Content", actualException.ResponseContent);
        Assert.Same(exception, actualException.InnerException);
    }

    #region private

    private sealed class FakeResponse(string responseContent, int status) : PipelineResponse
    {
        private readonly string _responseContent = responseContent;
        public override BinaryData Content => BinaryData.FromString(this._responseContent);
        public override int Status { get; } = status;
        public override string ReasonPhrase => "Reason Phrase";
        public override Stream? ContentStream { get => null; set => throw new NotImplementedException(); }
        protected override PipelineResponseHeaders HeadersCore => throw new NotImplementedException();
        public override BinaryData BufferContent(CancellationToken cancellationToken = default) => new(this._responseContent);
        public override ValueTask<BinaryData> BufferContentAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override void Dispose() { }
    }

    #endregion
}
