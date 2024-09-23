// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(KernelArguments))]
[JsonSerializable(typeof(byte?))]
[JsonSerializable(typeof(sbyte?))]
[JsonSerializable(typeof(short?))]
[JsonSerializable(typeof(ushort?))]
[JsonSerializable(typeof(int?))]
[JsonSerializable(typeof(uint?))]
[JsonSerializable(typeof(long?))]
[JsonSerializable(typeof(ulong?))]
[JsonSerializable(typeof(char?))]
[JsonSerializable(typeof(double?))]
[JsonSerializable(typeof(float?))]
[JsonSerializable(typeof(bool?))]
[JsonSerializable(typeof(decimal?))]
[JsonSerializable(typeof(string))]
[JsonSerializable(typeof(DateTime?))]
[JsonSerializable(typeof(DateTimeOffset?))]
[JsonSerializable(typeof(TimeSpan?))]
[JsonSerializable(typeof(Guid?))]
[JsonSerializable(typeof(Uri))]

internal sealed partial class KernelArgumentsJsonSerializerContext : JsonSerializerContext
{
}
