// Copyright (c) Microsoft. All rights reserved.

import { Bot } from '../models/Bot';
import { IChatSession } from '../models/ChatSession';
import { BaseService } from './BaseService';

export class BotService extends BaseService {
    public downloadAsync = async (chatId: string, accessToken: string) => {
        const result = await this.getResponseAsync<object>(
            {
                commandPath: `bot/download/${chatId}`,
                method: 'GET',
            },
            accessToken,
        );

        return result;
    };

    public uploadAsync = async (bot: Bot, userId: string, accessToken: string) => {
        // TODO: return type
        const result = await this.getResponseAsync<IChatSession>(
            {
                commandPath: `bot/upload?userId=${userId}`,
                method: 'Post',
                body: bot,
            },
            accessToken,
        );

        return result;
    };
}
