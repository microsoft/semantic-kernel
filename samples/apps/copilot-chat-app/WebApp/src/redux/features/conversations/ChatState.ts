// Copyright (c) Microsoft. All rights reserved.

import { ChatMessage } from '../../../libs/models/ChatMessage';
import { ChatUser } from '../../../libs/models/ChatUser';

export interface ChatState {
    id: string | undefined;
    audience: ChatUser[];
    messages: ChatMessage[];
    botTypingTimestamp: number;
    botProfilePicture: string;
}

export const initialBotMessage = (name: string) => {
    return {
        timestamp: new Date().getTime(),
        sender: 'bot',
        content: `Hi ${name}, nice to meet you! How can I help you today? Type in a message.`
    }
};

export const initialChatName = `SK Chatbot @ ${new Date().toLocaleString()}`;

export const initialState: ChatState = {
    id: initialChatName,
    audience: [],
    messages: [initialBotMessage('there')],
    botTypingTimestamp: 0,
    botProfilePicture: '/assets/bot-icon-1.png',
};