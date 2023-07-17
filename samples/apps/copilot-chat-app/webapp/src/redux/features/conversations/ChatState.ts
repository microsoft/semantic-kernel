// Copyright (c) Microsoft. All rights reserved.

import { IChatMessage } from '../../../libs/models/ChatMessage';
import { IChatUser } from '../../../libs/models/ChatUser';

export interface ChatState {
    id: string;
    title: string;
    systemDescription: string;
    users: IChatUser[];
    messages: IChatMessage[];
    botProfilePicture: string;
    lastUpdatedTimestamp?: number;
    input: string;
    isBotTyping: boolean;
    userDataLoaded: boolean;
}
