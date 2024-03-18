// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text;

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

        var stream = Stream.Synchronized(content.Stream);
        using var binaryReader = new BinaryReader(stream, Encoding.Default, leaveOpen: true);
        AudioContent audioContent = new(binaryReader.ReadBytes((int)stream.Length));

        // reset to 0 position if seek is supported
        if (stream.CanSeek)
        {
            stream.Seek(0, SeekOrigin.Begin);
        }

        return audioContent;
    }
}
