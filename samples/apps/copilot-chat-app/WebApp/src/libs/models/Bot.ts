// Copyright (c) Microsoft. All rights reserved.

import { ChatMessage } from './ChatMessage';

export interface Bot {
    ChatHistory: ChatMessage[];
    Embeddings: any[]; // TODO: type this
}
