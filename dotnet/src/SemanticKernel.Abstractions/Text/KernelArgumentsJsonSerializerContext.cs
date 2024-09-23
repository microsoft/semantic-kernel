// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(KernelArguments))]
[JsonSerializable(typeof(uint?))]
[JsonSerializable(typeof(int?))]
[JsonSerializable(typeof(long?))]
[JsonSerializable(typeof(string))]
[JsonSerializable(typeof(bool?))]
[JsonSerializable(typeof(float?))]
[JsonSerializable(typeof(double?))]
[JsonSerializable(typeof(decimal?))]
[JsonSerializable(typeof(DateTime?))]
[JsonSerializable(typeof(DateTimeOffset?))]
[JsonSerializable(typeof(TimeSpan?))]
[JsonSerializable(typeof(Guid?))]
internal sealed partial class KernelArgumentsJsonSerializerContext : JsonSerializerContext
{
}
