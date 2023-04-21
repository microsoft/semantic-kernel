// Copyright (c) Microsoft. All rights reserved.

import { BaseService } from './BaseService';
import { Bot } from '../models/Bot';

export class BotService extends BaseService {
    public exportAsync = async (
        chatId: string,
        accessToken: string,
        connectorAccessToken?: string,
    ): Promise<any> => {
        const result = await this.getResponseAsync<any>(
            {
                commandPath: `bot/export/${chatId}`,
                method: 'GET',
            },
            accessToken,
            connectorAccessToken,
        );
        return result;
    };

    public importAsync = async (
        bot: Bot,
        userId: string,
        accessToken: string,
        connectorAccessToken?: string,
    ): Promise<any> => {
        // TODO: return type
        const result = await this.getResponseAsync<any>(
            {
                commandPath: `bot/import?userId=${userId}`,
                method: 'Post',
                body: bot,
            },
            accessToken,
            connectorAccessToken,
        );
        return result;
    };
}
