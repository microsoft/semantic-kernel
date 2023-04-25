// Copyright (c) Microsoft. All rights reserved.

import { BaseService } from './BaseService';
import { Bot } from '../models/Bot';

export class BotService extends BaseService {
    public downloadAsync = async (chatId: string, accessToken: string, connectorAccessToken?: string): Promise<any> => {
        const result = await this.getResponseAsync<any>(
            {
                commandPath: `bot/download/${chatId}`,
                method: 'GET',
            },
            accessToken,
            connectorAccessToken,
        );
        return result;
    };

    public uploadAsync = async (
        bot: Bot,
        userId: string,
        accessToken: string,
        connectorAccessToken?: string,
    ): Promise<any> => {
        // TODO: return type
        const result = await this.getResponseAsync<any>(
            {
                commandPath: `bot/upload?userId=${userId}`,
                method: 'Post',
                body: bot,
            },
            accessToken,
            connectorAccessToken,
        );
        return result;
    };
}
