// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for the AudioStreamContent class
/// </summary>
public static class AudioStreamContentExtensions
{
    /// <summary>
    /// Converts an AudioStreamContent to AudioContent by loading the stream data into memory.
    /// </summary>
    /// <returns>An AudioContent object from AudioStreamContent's stream</returns>
    public static AudioContent ToAudioContent(this AudioStreamContent content)
    {
        if (content is null) { throw new ArgumentNullException(nameof(content)); }

        byte[] bytes;
        using (var binaryReader = new BinaryReader(content.Stream))
        {
            bytes = binaryReader.ReadBytes((int)content.Stream.Length);
        }

        return new AudioContent(bytes);
    }
}
