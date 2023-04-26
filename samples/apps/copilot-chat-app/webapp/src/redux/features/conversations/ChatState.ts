// Copyright (c) Microsoft. All rights reserved.

import { ChatMessages } from '../../../libs/models/ChatMessage';
import { ChatUser } from '../../../libs/models/ChatUser';

export interface ChatState {
    id: string;
    title: string;
    audience: ChatUser[];
    messages: ChatMessages;
    botTypingTimestamp: number;
    botProfilePicture: string;
}