// Copyright (c) Microsoft. All rights reserved.

namespace KernelHttpServer.Config;

internal static class Constants
{
    public static class SKHttpHeaders
    {
        public const string CompletionModel = "x-ms-sk-completion-model";
        public const string CompletionEndpoint = "x-ms-sk-completion-endpoint";
        public const string CompletionService = "x-ms-sk-completion-backend";
        public const string CompletionKey = "x-ms-sk-completion-key";

        public const string EmbeddingModel = "x-ms-sk-embedding-model";
        public const string EmbeddingEndpoint = "x-ms-sk-embedding-endpoint";
        public const string EmbeddingService = "x-ms-sk-embedding-backend";
        public const string EmbeddingKey = "x-ms-sk-embedding-key";

        public const string MSGraph = "x-ms-sk-msgraph";
    }
}
