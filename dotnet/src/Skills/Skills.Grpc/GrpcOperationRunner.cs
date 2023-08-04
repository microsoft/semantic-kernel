// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Net.Http;
using System.Reflection;
using System.Reflection.Emit;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using Grpc.Net.Client;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Skills.Grpc.Model;
using ProtoBuf;

namespace Microsoft.SemanticKernel.Skills.Grpc;

/// <summary>
/// Runs gRPC operation runner.
/// </summary>
internal class GrpcOperationRunner
{
    /// <summary>
    /// An instance of the HttpClient class.
    /// </summary>
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Creates an instance of a <see cref="GrpcOperationRunner"/> class.
    /// </summary>
    /// <param name="httpClient">An instance of the HttpClient class.</param>
    public GrpcOperationRunner(HttpClient httpClient)
    {
        this._httpClient = httpClient;
    }

    /// <summary>
    /// Runs a gRPC operation.
    /// </summary>
    /// <param name="operation">The operation to run.</param>
    /// <param name="arguments">The operation arguments.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the operation run.</returns>
    public async Task<JsonObject> RunAsync(GrpcOperation operation, IDictionary<string, string> arguments, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(operation);
        Verify.NotNull(arguments);

        var address = this.GetAddress(operation, arguments);

        var channelOptions = new GrpcChannelOptions { HttpClient = this._httpClient, DisposeHttpClient = false };

        using (var channel = GrpcChannel.ForAddress(address, channelOptions))
        {
            var requestType = BuildGrpcOperationDataContractType(operation.Request);

            var responseType = BuildGrpcOperationDataContractType(operation.Response);

            var method = new Method<object, object>
            (
                MethodType.Unary,
                operation.FullServiceName,
                operation.Name,
                this.CreateMarshaller<object>(requestType),
                this.CreateMarshaller<object>(responseType)
            );

            var invoker = channel.CreateCallInvoker();

            var request = this.GenerateOperationRequest(operation, requestType, arguments);

            var response = await invoker.AsyncUnaryCall(method, null, new CallOptions(cancellationToken: cancellationToken), request).ConfigureAwait(false);

            return ConvertResponse(response, responseType);
        }
    }

    /// <summary>
    /// Converts gRPC response.
    /// </summary>
    /// <param name="response">The response to convert.</param>
    /// <param name="responseType">The response type info.</param>
    /// <returns>The converted response.</returns>
    private static JsonObject ConvertResponse(object response, Type responseType)
    {
        var content = JsonSerializer.Serialize(response, responseType, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });

        //First iteration allowing to associate additional metadata with the returned content.
        var result = new JsonObject();
        result.Add("content", content);
        result.Add("contentType", "application/json; charset=utf-8");
        return result;
    }

    /// <summary>
    /// Returns address of a channel that provides connection to a gRPC server.
    /// </summary>
    /// <param name="operation">The gRPC operation.</param>
    /// <param name="arguments">The gRPC operation arguments.</param>
    /// <returns>The channel address.</returns>
    private string GetAddress(GrpcOperation operation, IDictionary<string, string> arguments)
    {
        if (!arguments.TryGetValue(GrpcOperation.AddressArgumentName, out string? address))
        {
            address = operation.Address;
        }

        if (string.IsNullOrEmpty(address))
        {
            throw new SKException($"No address provided for the '{operation.Name}' gRPC operation.");
        }

        return address!;
    }

    /// <summary>
    /// Creates a marshaller - a typed abstraction for gRPC message serialization and deserialization.
    /// </summary>
    /// <param name="contractType">The message contract data type.</param>
    /// <returns>The marshaller.</returns>
    private Marshaller<T> CreateMarshaller<T>(Type contractType)
    {
        byte[] Serialize(T instance)
        {
            using var memoryStream = new MemoryStream();

            Serializer.NonGeneric.Serialize(memoryStream, instance);

            return memoryStream.ToArray();
        }

        T Deserialize(byte[] source)
        {
            using var memoryStream = new MemoryStream(source);

            return (T)Serializer.NonGeneric.Deserialize(contractType, memoryStream);
        }

        return Marshallers.Create((instance) => Serialize(instance), (bytes) => Deserialize(bytes));
    }

    /// <summary>
    /// Creates a gRPC operation request.
    /// </summary>
    /// <param name="operation">The gRPC operation.</param>
    /// <param name="type">The operation request data type.</param>
    /// <param name="arguments">The operation arguments.</param>
    /// <returns>The operation request instance.</returns>
    private object GenerateOperationRequest(GrpcOperation operation, Type type, IDictionary<string, string> arguments)
    {
        //Getting 'payload' argument to by used as gRPC request message
        if (!arguments.TryGetValue(GrpcOperation.PayloadArgumentName, out var payload))
        {
            throw new SKException($"No '{GrpcOperation.PayloadArgumentName}' argument representing gRPC request message is found for the '{operation.Name}' gRPC operation.");
        }

        //Deserializing JSON payload to gRPC request message
        var instance = JsonSerializer.Deserialize(payload, type, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
        if (instance == null)
        {
            throw new SKException($"Impossible to create gRPC request message for the '{operation.Name}' gRPC operation.");
        }

        return instance;
    }

    /// <summary>
    /// Builds gRPC operation data contract type.
    /// </summary>
    /// <param name="dataContractMetadata">The data contract type metadata.</param>
    /// <returns>.NET type representing the data contract type.</returns>
    private static TypeInfo BuildGrpcOperationDataContractType(GrpcOperationDataContractType dataContractMetadata)
    {
        var assemblyName = new AssemblyName($"{dataContractMetadata.Name}Assembly");

        var assemblyBuilder = AssemblyBuilder.DefineDynamicAssembly(assemblyName, AssemblyBuilderAccess.Run);

        var moduleBuilder = assemblyBuilder.DefineDynamicModule($"{dataContractMetadata.Name}Module");

        var typeBuilder = moduleBuilder.DefineType(dataContractMetadata.Name, TypeAttributes.Public | TypeAttributes.Sealed | TypeAttributes.Class);

        //Creating and adding a .NET property for each data contract filed
        foreach (var field in dataContractMetadata.Fields)
        {
            var fieldName = field.Name;
            var propertyName = CultureInfo.InvariantCulture.TextInfo.ToTitleCase(field.Name);

            var propertyType = GetNetType(field.TypeName);

            //Creating a private backing field for the property
            var fieldBuilder = typeBuilder.DefineField(fieldName + "_", propertyType, FieldAttributes.Private);
            var propertyBuilder = typeBuilder.DefineProperty(propertyName, PropertyAttributes.None, propertyType, null);

            //Creating the property get method and binding it to the private filed
            var getterBuilder = typeBuilder.DefineMethod("get_" + propertyName, MethodAttributes.Public | MethodAttributes.SpecialName | MethodAttributes.HideBySig, propertyType, Type.EmptyTypes);
            var getterIl = getterBuilder.GetILGenerator();
            getterIl.Emit(OpCodes.Ldarg_0);
            getterIl.Emit(OpCodes.Ldfld, fieldBuilder);
            getterIl.Emit(OpCodes.Ret);

            //Creating the property set method and binding it to the private filed
            var setterBuilder = typeBuilder.DefineMethod("set_" + propertyName, MethodAttributes.Public | MethodAttributes.SpecialName | MethodAttributes.HideBySig, null, new[] { propertyType });
            var setterIl = setterBuilder.GetILGenerator();
            setterIl.Emit(OpCodes.Ldarg_0);
            setterIl.Emit(OpCodes.Ldarg_1);
            setterIl.Emit(OpCodes.Stfld, fieldBuilder);
            setterIl.Emit(OpCodes.Ret);

            //Registering the property get and set methods.
            propertyBuilder.SetGetMethod(getterBuilder);
            propertyBuilder.SetSetMethod(setterBuilder);

            //Add ProtoMember attribute to the data contract with tag/number
            var dataMemberAttributeBuilder = new CustomAttributeBuilder(typeof(ProtoMemberAttribute).GetConstructor(new[] { typeof(int) }), new object[] { field.Number });
            propertyBuilder.SetCustomAttribute(dataMemberAttributeBuilder);
        }

        //Add ProtoContract attribute to the data contract
        var dataContractAttributeBuilder = new CustomAttributeBuilder(typeof(ProtoContractAttribute).GetConstructor(Type.EmptyTypes), Array.Empty<object>());
        typeBuilder.SetCustomAttribute(dataContractAttributeBuilder);

        var type = typeBuilder.CreateTypeInfo();
        if (type == null)
        {
            throw new SKException($"Impossible to create type for '{dataContractMetadata.Name}' data contract.");
        }

        return type;
    }

    /// <summary>
    /// Returns .net type that corresponds to protobuf data type name.
    /// </summary>
    /// <param name="type">The protobuf data type name.</param>
    /// <returns>The .net type.</returns>
    private static Type GetNetType(string type)
    {
        switch (type)
        {
            case "TYPE_DOUBLE":
                return typeof(double);
            case "TYPE_FLOAT":
                return typeof(float);
            case "TYPE_INT64":
                return typeof(long);
            case "TYPE_UINT64":
                return typeof(ulong);
            case "TYPE_INT32":
                return typeof(int);
            case "TYPE_FIXED64":
                return typeof(ulong);
            case "TYPE_FIXED32":
                return typeof(uint);
            case "TYPE_BOOL":
                return typeof(bool);
            case "TYPE_STRING":
                return typeof(string);
            case "TYPE_BYTES":
                return typeof(byte[]);
            case "TYPE_UINT32":
                return typeof(uint);
            case "TYPE_SFIXED32":
                return typeof(int);
            case "TYPE_SFIXED64":
                return typeof(long);
            case "TYPE_SINT32":
                return typeof(int);
            case "TYPE_SINT64":
                return typeof(long);
            default:
                throw new ArgumentException($"Unknown type {type}", nameof(type));
        }
    }
}
