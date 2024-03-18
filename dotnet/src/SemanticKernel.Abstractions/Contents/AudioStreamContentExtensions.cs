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

        var originalPosition = content.Stream.Position;

        using var binaryReader = new BinaryReader(content.Stream, Encoding.Default, leaveOpen: true);
        var audioContent = new AudioContent(binaryReader.ReadBytes((int)content.Stream.Length));

        // reset to original position if seek is supported
        if (content.Stream.CanSeek)
        {
            content.Stream.Seek(originalPosition, SeekOrigin.Begin);
        }

        return audioContent;
    }
}
