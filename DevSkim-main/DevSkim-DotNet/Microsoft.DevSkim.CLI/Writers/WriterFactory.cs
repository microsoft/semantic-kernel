// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using System;
using System.IO;

namespace Microsoft.DevSkim.CLI.Writers
{
    public class WriterFactory
    {
        public static Writer GetWriter(string writerName, string format, TextWriter output, string? outputPath = null, GitInformation? gitInformation = null)
        {
            if (string.IsNullOrEmpty(writerName))
            {
                writerName = "_dummy";
            }

            switch (writerName.ToLowerInvariant())
            {
                case "_dummy":
                    return new DummyWriter();

                case "json":
                    return new JsonWriter(format, output);

                case "text":
                    return new SimpleTextWriter(format, output);

                case "sarif":
                    return new SarifWriter(output, outputPath, gitInformation);

                default:
                    throw new Exception("wrong output");
            }
        }
    }

    public record GitInformation
    {
        public Uri? RepositoryUri { get; set; }
        public string CommitHash { get; set; } = string.Empty;
        public string Branch { get; set; } = string.Empty;
    }
}