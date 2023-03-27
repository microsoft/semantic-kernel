// Copyright (c) Microsoft. All rights reserved.

import { ChatMessage } from '../../../libs/models/ChatMessage';
import { ChatUser } from '../../../libs/models/ChatUser';
import { mockMessages } from '../../../mock-data';

export interface ChatState {
    id: string | undefined;
    audience: ChatUser[];
    messages: ChatMessage[];
    botTypingTimestamp: number;
}

export const initialState: ChatState = {
    id: undefined,
    audience: [],
    // TODO: revert to actual initial state
    messages: mockMessages,
    botTypingTimestamp: 0,
};

export const initialBotMessage = (name: string) => {
    return {
        timestamp: new Date().getTime(),
        sender: 'bot',
        content: `Hi ${name}, nice to meet you! How can I help you today? Type in a message.`
    }
};