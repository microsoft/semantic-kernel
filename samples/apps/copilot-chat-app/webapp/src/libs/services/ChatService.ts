// Copyright (c) Microsoft. All rights reserved.

import { Plugin } from '../../redux/features/plugins/PluginsState';
import { ChatMemorySource } from '../models/ChatMemorySource';
import { IChatMessage } from '../models/ChatMessage';
import { IChatParticipant } from '../models/ChatParticipant';
import { IChatSession } from '../models/ChatSession';
import { IChatUser } from '../models/ChatUser';
import { IAsk, IAskVariables } from '../semantic-kernel/model/Ask';
import { IAskResult } from '../semantic-kernel/model/AskResult';
import { BaseService } from './BaseService';

export class ChatService extends BaseService {
    public createChatAsync = async (userId: string, title: string, accessToken: string): Promise<IChatSession> => {
        const body = {
            userId,
            title,
        };

        const result = await this.getResponseAsync<IChatSession>(
            {
                commandPath: 'chatSession/create',
                method: 'POST',
                body,
            },
            accessToken,
        );

        return result;
    };

    public getChatAsync = async (chatId: string, accessToken: string): Promise<IChatSession> => {
        const result = await this.getResponseAsync<IChatSession>(
            {
                commandPath: `chatSession/getChat/${chatId}`,
                method: 'GET',
            },
            accessToken,
        );

        return result;
    };

    public getAllChatsAsync = async (userId: string, accessToken: string): Promise<IChatSession[]> => {
        const result = await this.getResponseAsync<IChatSession[]>(
            {
                commandPath: `chatSession/getAllChats/${userId}`,
                method: 'GET',
            },
            accessToken,
        );
        return result;
    };

    public getChatMessagesAsync = async (
        chatId: string,
        startIdx: number,
        count: number,
        accessToken: string,
    ): Promise<IChatMessage[]> => {
        const result = await this.getResponseAsync<IChatMessage[]>(
            {
                commandPath: `chatSession/getChatMessages/${chatId}?startIdx=${startIdx}&count=${count}`,
                method: 'GET',
            },
            accessToken,
        );

        // Messages are returned with most recent message at index 0 and oldest message at the last index,
        // so we need to reverse the order for render
        return result.reverse();
    };

    public editChatAsync = async (chatId: string, title: string, accessToken: string): Promise<any> => {
        const body: IChatSession = {
            id: chatId,
            title,
        };

        const result = await this.getResponseAsync<IChatSession>(
            {
                commandPath: 'chatSession/edit',
                method: 'POST',
                body,
            },
            accessToken,
        );

        return result;
    };

    public getBotResponseAsync = async (
        ask: IAsk,
        accessToken: string,
        enabledPlugins?: Plugin[],
    ): Promise<IAskResult> => {
        // If skill requires any additional api properties, append to context
        if (enabledPlugins && enabledPlugins.length > 0) {
            const openApiSkillVariables: IAskVariables[] = [];

            for (const plugin of enabledPlugins) {
                if (plugin.apiProperties) {
                    const apiProperties = plugin.apiProperties;

                    for (const property in apiProperties) {
                        const propertyDetails = apiProperties[property];

                        if (propertyDetails.required && !propertyDetails.value) {
                            throw new Error(`Missing required property ${property} for ${plugin.name} skill.`);
                        }

                        if (propertyDetails.value) {
                            openApiSkillVariables.push({
                                key: `${property}`,
                                value: propertyDetails.value,
                            });
                        }
                    }
                }
            }

            ask.variables = ask.variables ? ask.variables.concat(openApiSkillVariables) : openApiSkillVariables;
        }

        const result = await this.getResponseAsync<IAskResult>(
            {
                commandPath: 'chat',
                method: 'POST',
                body: ask,
            },
            accessToken,
            enabledPlugins,
        );

        return result;
    };

    public joinChatAsync = async (userId: string, chatId: string, accessToken: string): Promise<IChatSession> => {
        const body: IChatParticipant = {
            userId,
            chatId,
        };

        await this.getResponseAsync<any>(
            {
                commandPath: 'chatParticipant/join',
                method: 'POST',
                body,
            },
            accessToken,
        );

        return await this.getChatAsync(chatId, accessToken);
    };

    public getChatMemorySourcesAsync = async (chatId: string, accessToken: string): Promise<ChatMemorySource[]> => {
        const result = await this.getResponseAsync<ChatMemorySource[]>(
            {
                commandPath: `chatSession/${chatId}/sources`,
                method: 'GET',
            },
            accessToken,
        );

        return result;
    };

    public getAllChatParticipantsAsync = async (chatId: string, accessToken: string): Promise<IChatUser[]> => {
        const result = await this.getResponseAsync<IChatParticipant[]>(
            {
                commandPath: `chatParticipant/getAllParticipants/${chatId}`,
                method: 'GET',
            },
            accessToken,
        );

        const chatUsers = result.map<IChatUser>((participant) => ({
            id: participant.userId,
            online: false,
            fullName: '', // The user's full name is not returned from the server
            emailAddress: '', // The user's email address is not returned from the server
            isTyping: false,
            photo: '',
        }));

        return chatUsers;
    };
}
