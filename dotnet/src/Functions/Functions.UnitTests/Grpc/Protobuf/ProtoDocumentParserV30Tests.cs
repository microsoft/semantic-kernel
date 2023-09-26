// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Linq;
using Microsoft.SemanticKernel.Functions.Grpc.Protobuf;
using SemanticKernel.Functions.UnitTests.Grpc.Protobuf.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Grpc.Protobuf;

public sealed class ProtoDocumentParserV30Tests
{
    /// <summary>
    /// System under test - an instance of ProtoDocumentParser class.
    /// </summary>
    private readonly ProtoDocumentParser _sut;

    /// <summary>
    /// .proto document stream.
    /// </summary>
    private readonly Stream _protoDocument;

    /// <summary>
    /// Creates an instance of a <see cref="ProtoDocumentParserV30Tests"/> class.
    /// </summary>
    public ProtoDocumentParserV30Tests()
    {
        this._protoDocument = ResourcePluginsProvider.LoadFromResource("protoV3.proto");

        this._sut = new ProtoDocumentParser();
    }

    [Fact]
    public void ShouldCreateOperationsForAllServicesInProtoDocument()
    {
        // Act
        var operations = this._sut.Parse(this._protoDocument, "fake_name");

        // Assert
        Assert.NotNull(operations);
        Assert.Equal(2, operations.Count);

        var greeterServiceOperations = operations.Where(o => o.ServiceName == "Greeter");
        Assert.NotNull(greeterServiceOperations);
        Assert.Contains(greeterServiceOperations, o => o.Name == "SayHello");

        var farewellerServiceOperations = operations.Where(o => o.ServiceName == "Fareweller");
        Assert.NotNull(farewellerServiceOperations);
        Assert.Contains(farewellerServiceOperations, o => o.Name == "SayGoodbye");
    }

    [Fact]
    public void ShouldParseSimpleOperationRequestDataContract()
    {
        // Act
        var operations = this._sut.Parse(this._protoDocument, "fake_name");

        // Assert
        Assert.NotNull(operations);

        var greeterServiceOperations = operations.Where(o => o.ServiceName == "Greeter");
        Assert.NotNull(greeterServiceOperations);

        var sayHelloOperation = greeterServiceOperations.SingleOrDefault(o => o.Name == "SayHello");
        Assert.NotNull(sayHelloOperation);

        var request = sayHelloOperation.Request;
        Assert.NotNull(request);

        Assert.Equal("greet.HelloRequest", request.Name);
        Assert.NotNull(request.Fields);

        var nameField = request.Fields.SingleOrDefault(f => f.Name == "name");
        Assert.NotNull(nameField);

        Assert.Equal(1, nameField.Number);
        Assert.Equal("TYPE_STRING", nameField.TypeName);
    }

    [Fact]
    public void ShouldParseSimpleOperationResponseDataContract()
    {
        // Act
        var operations = this._sut.Parse(this._protoDocument, "fake_name");

        // Assert
        Assert.NotNull(operations);

        var greeterServiceOperations = operations.Where(o => o.ServiceName == "Greeter");
        Assert.NotNull(greeterServiceOperations);

        var sayHelloOperation = greeterServiceOperations.SingleOrDefault(o => o.Name == "SayHello");
        Assert.NotNull(sayHelloOperation);

        var response = sayHelloOperation.Response;
        Assert.NotNull(response);

        Assert.Equal("greet.HelloReply", response.Name);
        Assert.NotNull(response.Fields);

        var messageField = response.Fields.SingleOrDefault(f => f.Name == "message");
        Assert.NotNull(messageField);

        Assert.Equal(1, messageField.Number);
        Assert.Equal("TYPE_STRING", messageField.TypeName);
    }
}
