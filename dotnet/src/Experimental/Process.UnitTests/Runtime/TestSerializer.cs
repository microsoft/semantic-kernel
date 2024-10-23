// Copyright (c) Microsoft. All rights reserved.
using System.IO;
using System.Runtime.Serialization;
using System.Text;
using System.Xml;

namespace SemanticKernel.Process.UnitTests.Runtime;

internal static class TestSerializer
{
    public static void Serialize<T>(this T obj, Stream stream)
    {
        DataContractSerializer serializer = new(typeof(T));
        using XmlDictionaryWriter writer = XmlDictionaryWriter.CreateTextWriter(stream, Encoding.Default, ownsStream: false);
        serializer.WriteObject(writer, obj);
        writer.Flush();
    }

    public static T? Deserialize<T>(this Stream stream)
    {
        DataContractSerializer serializer = new(typeof(T));
        stream.Position = 0;
        return (T?)serializer.ReadObject(stream);
    }
}
