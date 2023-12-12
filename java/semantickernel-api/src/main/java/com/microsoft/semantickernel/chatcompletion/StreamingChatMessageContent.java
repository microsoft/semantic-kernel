package com.microsoft.semantickernel.chatcompletion;

import com.microsoft.semantickernel.orchestration.StreamingContent;

public class StreamingChatMessageContent extends StreamingContent<ChatMessageContent> {

    public StreamingChatMessageContent(ChatMessageContent content) {
        super(content);
    }
}
