// Copyright (c) Microsoft. All rights reserved.

import { SKBotAudienceMember } from '../semantic-kernel/bot-agent/models/SKBotAudienceMember';

export interface ChatUser extends SKBotAudienceMember {
    lastTypingTimestamp: number;
}
