// Copyright (c) Microsoft. All rights reserved.

import { ChatMessages } from './ChatMessage';

export interface Bot {
    Schema: { Name: string; Version: number };
    Configurations: { EmbeddingAIService: string; EmbeddingDeploymentOrModelId: string };
    ChatTitle: string;
    ChatHistory: ChatMessages;
    Embeddings: any[]; // TODO: type this
}
