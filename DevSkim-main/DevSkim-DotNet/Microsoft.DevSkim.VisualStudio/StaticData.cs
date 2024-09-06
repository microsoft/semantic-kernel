namespace Microsoft.DevSkim.VisualStudio
{
    using Microsoft.DevSkim.LanguageProtoInterop;
    using System;
    using System.Collections.Concurrent;
    using System.Collections.Generic;

    internal static class StaticData
    {
        // Maps file name to a dictionary of file versions to a deduplicated set of CodeFixMappings
        internal static ConcurrentDictionary<Uri, ConcurrentDictionary<int, ConcurrentDictionary<CodeFixMapping, bool>>> FileToCodeFixMap { get; } = new();
    }
}
