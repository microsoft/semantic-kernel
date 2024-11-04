// Copyright (c) Microsoft. All rights reserved.
using System;
using System.IO;
using System.Runtime.Serialization;
using System.Text;
using System.Xml;

namespace SemanticKernel.Process.Dapr.Runtime.UnitTests;

internal static class TestSerializer
{
    public static void Serialize<T>(this T obj, Stream stream) where T : class
    {
        DataContractSerializer serializer = new(obj.GetType());
        using XmlDictionaryWriter writer = XmlDictionaryWriter.CreateTextWriter(stream, Encoding.Default, ownsStream: false);
        serializer.WriteObject(writer, obj);
        writer.Flush();
    }

    public static T? Deserialize<T>(this Stream stream, Type type)
    {
        DataContractSerializer serializer = new(type);
        stream.Position = 0;
        return (T?)serializer.ReadObject(stream);
    }
}
