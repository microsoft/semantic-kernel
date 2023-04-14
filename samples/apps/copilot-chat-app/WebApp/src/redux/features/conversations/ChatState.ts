// Copyright (c) Microsoft. All rights reserved.

import { ChatMessage } from '../../../libs/models/ChatMessage';
import { ChatUser } from '../../../libs/models/ChatUser';

export interface ChatState {
    id: string;
    title: string;
    audience: ChatUser[];
    messages: ChatMessage[];
    botTypingTimestamp: number;
    botProfilePicture: string;
}