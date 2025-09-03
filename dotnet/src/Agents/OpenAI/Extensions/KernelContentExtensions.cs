// Copyright (c) Microsoft. All rights reserved.

using System;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Extensons methods for <see cref="KernelContent"/>.
/// </summary>
internal static class KernelContentExtensions
{
    internal static ResponseContentPart ToResponseContentPart(this KernelContent content)
    {
        return content switch
        {
            TextContent textContent => textContent.ToResponseContentPart(),
            ImageContent imageContent => imageContent.ToResponseContentPart(),
            BinaryContent binaryContent => binaryContent.ToResponseContentPart(),
            FileReferenceContent fileReferenceContent => fileReferenceContent.ToResponseContentPart(),
            _ => throw new NotSupportedException($"Unsupported content type {content.GetType().Name}. Cannot convert to {nameof(ResponseContentPart)}.")
        };
    }

    internal static ResponseContentPart ToResponseContentPart(this TextContent content)
    {
        return ResponseContentPart.CreateInputTextPart(content.Text);
    }

    internal static ResponseContentPart ToResponseContentPart(this ImageContent content)
    {
        return content.Uri is not null
            ? ResponseContentPart.CreateInputImagePart(content.Uri)
            : content.Data is not null
            ? ResponseContentPart.CreateInputImagePart(new BinaryData(content.Data), content.MimeType)
            : throw new NotSupportedException("ImageContent cannot be converted to ResponseContentPart. Only ImageContent with a uri or binary data is supported.");
    }

    internal static ResponseContentPart ToResponseContentPart(this BinaryContent content)
    {
        return content.Data is not null
            ? ResponseContentPart.CreateInputFilePart(new BinaryData(content.Data), content.MimeType, Guid.NewGuid().ToString())
            : throw new NotSupportedException("AudioContent cannot be converted to ResponseContentPart. Only AudioContent with binary data is supported.");
    }

    internal static ResponseContentPart ToResponseContentPart(this FileReferenceContent content)
    {
        return content.FileId is not null
            ? ResponseContentPart.CreateInputFilePart(content.FileId)
            : throw new NotSupportedException("FileReferenceContent cannot be converted to ResponseContentPart. Only FileReferenceContent with a file id is supported.");
    }
}
