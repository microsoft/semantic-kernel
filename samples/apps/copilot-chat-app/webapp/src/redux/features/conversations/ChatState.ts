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
    botResponseStatus: string | undefined;
    userDataLoaded: boolean;
    memoryBalance: number;
    // HACK. Since the client insert user input without waiting for the id from the backend. We hack the solution to create a temporary id = userid + timestamp. If the message id is presented, it means it's under content moderation analysis.
    moderatingMessages?: string[];
}
