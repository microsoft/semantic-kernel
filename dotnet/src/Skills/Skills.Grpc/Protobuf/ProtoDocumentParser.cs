// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Google.Protobuf.Reflection;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Skills.Grpc.Model;
using ProtoBuf;

namespace Microsoft.SemanticKernel.Skills.Grpc.Protobuf;

/// <summary>
/// Parser for .proto definition documents.
/// </summary>
internal class ProtoDocumentParser
{
    /// <summary>
    /// Parses .proto document.
    /// </summary>
    /// <param name="protoDocument">The .proto document.</param>
    /// <param name="protoFileName">The .proto file logical name.</param>
    /// <returns>List of gRPC operations.</returns>
    public IList<GrpcOperation> Parse(Stream protoDocument, string protoFileName)
    {
        Verify.NotNull(protoDocument);
        Verify.NotNullOrWhiteSpace(protoFileName);

        using var textReader = new StreamReader(protoDocument);

        var descriptor = new FileDescriptorSet();
        descriptor.Add(protoFileName, source: textReader);
        descriptor.Process();

        var errors = descriptor.GetErrors();
        if (errors != null && errors.Length != 0)
        {
            throw new SKException($"Parsing of '{protoFileName}' .proto document has failed. Details: {string.Join(";", errors.AsEnumerable())}");
        }

        return this.GetGrpcOperations(descriptor.Files.Single());
    }

    /// <summary>
    /// Parses an .proto document and extracts gRPC operations.
    /// </summary>
    /// <param name="model">The .proto document model.</param>
    /// <returns>List of gRPC operations.</returns>
    private List<GrpcOperation> GetGrpcOperations(FileDescriptorProto model)
    {
        var operations = new List<GrpcOperation>();

        foreach (var service in model.Services)
        {
            foreach (var method in service.Methods)
            {
                var requestContract = this.CreateDataContract(model.MessageTypes, method.InputType, model.Package, method.Name);

                var responseContract = this.CreateDataContract(model.MessageTypes, method.OutputType, model.Package, method.Name);

                var operation = new GrpcOperation(service.Name, method.Name, requestContract, responseContract);
                operation.Package = model.Package;

                operations.Add(operation);
            }
        }

        return operations;
    }

    /// <summary>
    /// Creates gRPC operation data contract.
    /// </summary>
    /// <param name="allMessageTypes">Existing ,message types declared in .proto file.</param>
    /// <param name="messageTypeName">Message type to create the data contract for.</param>
    /// <param name="package">The .proto file 'package' specifier.</param>
    /// <param name="methodName">The method to create data contract for.</param>
    /// <returns>The operation data contract.</returns>
    private GrpcOperationDataContractType CreateDataContract(IList<DescriptorProto> allMessageTypes, string messageTypeName, string package, string methodName)
    {
        var fullTypeName = messageTypeName.TrimStart('.');

        var typeName = fullTypeName;

        if (!string.IsNullOrEmpty(package))
        {
            typeName = fullTypeName.Replace($"{package}.", "");
        }

        var messageType = allMessageTypes.SingleOrDefault(mt => mt.Name == fullTypeName || mt.Name == typeName);
        if (messageType == null)
        {
            throw new SKException($"No '{fullTypeName}' message type is found while resolving data contracts for the '{methodName}' method.");
        }

        var fields = this.GetDataContractFields(messageType.Fields);

        return new GrpcOperationDataContractType(fullTypeName, fields);
    }

    /// <summary>
    /// Returns data contract fields.
    /// </summary>
    /// <param name="fields">Message type fields.</param>
    /// <returns>The data contract fields.</returns>
    private List<GrpcOperationDataContractTypeFiled> GetDataContractFields(List<FieldDescriptorProto> fields)
    {
        var result = new List<GrpcOperationDataContractTypeFiled>();

        foreach (var field in fields)
        {
            var type = GetProtobufDataTypeName(field.type);

            result.Add(new GrpcOperationDataContractTypeFiled(field.Name, field.Number, type));
        }

        return result;
    }

    /// <summary>
    /// Returns protobuf data type name.
    /// </summary>
    /// <param name="type">Type descriptor.</param>
    /// <returns>The protobuf data type name.</returns>
    private static string GetProtobufDataTypeName(FieldDescriptorProto.Type type)
    {
        var fieldInfo = typeof(FieldDescriptorProto.Type).GetField(type.ToString());

        //Get protobuf type name from enum attribute - [global::ProtoBuf.ProtoEnum(Name = @"TYPE_DOUBLE")]
        var attribute = (ProtoEnumAttribute)Attribute.GetCustomAttribute(fieldInfo, typeof(ProtoEnumAttribute));

        if (attribute == null)
        {
            throw new SKException($"Impossible to find protobuf type name corresponding to '{type}' type.");
        }

        return attribute.Name;
    }
}
