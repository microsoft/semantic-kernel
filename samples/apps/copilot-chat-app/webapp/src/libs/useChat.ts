// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { Constants } from '../Constants';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';
import { addAlert, updateTokenUsage } from '../redux/features/app/appSlice';
import { ChatState } from '../redux/features/conversations/ChatState';
import { Conversations } from '../redux/features/conversations/ConversationsState';
import {
    addConversation,
    setConversations,
    setSelectedConversation,
} from '../redux/features/conversations/conversationsSlice';
import { Plugin } from '../redux/features/plugins/PluginsState';
import { AuthHelper } from './auth/AuthHelper';
import { AlertType } from './models/AlertType';
import { Bot } from './models/Bot';
import { ChatMessageType } from './models/ChatMessage';
import { IChatSession } from './models/ChatSession';
import { IChatUser } from './models/ChatUser';
import { IAskVariables } from './semantic-kernel/model/Ask';
import { BotService } from './services/BotService';
import { ChatService } from './services/ChatService';
import { DocumentImportService } from './services/DocumentImportService';

import botIcon1 from '../assets/bot-icons/bot-icon-1.png';
import botIcon2 from '../assets/bot-icons/bot-icon-2.png';
import botIcon3 from '../assets/bot-icons/bot-icon-3.png';
import botIcon4 from '../assets/bot-icons/bot-icon-4.png';
import botIcon5 from '../assets/bot-icons/bot-icon-5.png';

export interface GetResponseOptions {
    messageType: ChatMessageType;
    value: string;
    chatId: string;
    contextVariables?: IAskVariables[];
}

export const useChat = () => {
    const dispatch = useAppDispatch();
    const { instance, inProgress } = useMsal();
    const { conversations } = useAppSelector((state: RootState) => state.conversations);
    const { activeUserInfo } = useAppSelector((state: RootState) => state.app);

    const botService = new BotService(process.env.REACT_APP_BACKEND_URI as string);
    const chatService = new ChatService(process.env.REACT_APP_BACKEND_URI as string);
    const documentImportService = new DocumentImportService(process.env.REACT_APP_BACKEND_URI as string);

    const botProfilePictures: string[] = [botIcon1, botIcon2, botIcon3, botIcon4, botIcon5];

    const userId = activeUserInfo?.id ?? '';
    const fullName = activeUserInfo?.username ?? '';
    const emailAddress = activeUserInfo?.email ?? '';
    const loggedInUser: IChatUser = {
        id: userId,
        fullName,
        emailAddress,
        photo: undefined, // TODO: Make call to Graph /me endpoint to load photo
        online: true,
        isTyping: false,
    };

    const { plugins } = useAppSelector((state: RootState) => state.plugins);

    const getChatUserById = (id: string, chatId: string, users: IChatUser[]) => {
        if (id === `${chatId}-bot` || id.toLocaleLowerCase() === 'bot') return Constants.bot.profile;
        return users.find((user) => user.id === id);
    };

    const createChat = async () => {
        const chatTitle = `Copilot @ ${new Date().toLocaleString()}`;
        const accessToken = await AuthHelper.getSKaaSAccessToken(instance, inProgress);
        try {
            await chatService.createChatAsync(userId, chatTitle, accessToken).then(async (result: IChatSession) => {
                const chatMessages = await chatService.getChatMessagesAsync(result.id, 0, 1, accessToken);

                const newChat: ChatState = {
                    id: result.id,
                    title: result.title,
                    systemDescription: result.systemDescription,
                    messages: chatMessages,
                    users: [loggedInUser],
                    botProfilePicture: getBotProfilePicture(Object.keys(conversations).length),
                    input: '',
                    botResponseStatus: undefined,
                    userDataLoaded: false,
                    memoryBalance: result.memoryBalance,
                };

                dispatch(addConversation(newChat));
                return newChat.id;
            });
        } catch (e: any) {
            const errorMessage = `Unable to create new chat. Details: ${getErrorDetails(e)}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        }
    };

    const getResponse = async ({ messageType, value, chatId, contextVariables }: GetResponseOptions) => {
        const ask = {
            input: value,
            variables: [
                {
                    key: 'userId',
                    value: userId,
                },
                {
                    key: 'userName',
                    value: fullName,
                },
                {
                    key: 'chatId',
                    value: chatId,
                },
                {
                    key: 'messageType',
                    value: messageType.toString(),
                },
            ],
        };

        if (contextVariables) {
            ask.variables.push(...contextVariables);
        }

        try {
            const askResult = await chatService.getBotResponseAsync(
                ask,
                await AuthHelper.getSKaaSAccessToken(instance, inProgress),
                getEnabledPlugins(),
            );

            const promptTokenUsage = askResult.variables.find((v) => v.key === 'promptTokenUsage')?.value;
            const dependencyTokenUsage = askResult.variables.find((v) => v.key === 'dependencyTokenUsage')?.value;

            dispatch(
                updateTokenUsage({
                    prompt: promptTokenUsage ? parseInt(promptTokenUsage) : 0,
                    dependency: dependencyTokenUsage ? parseInt(dependencyTokenUsage) : 0,
                }),
            );
        } catch (e: any) {
            const errorMessage = `Unable to generate bot response. Details: ${getErrorDetails(e)}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        }
    };

    const loadChats = async () => {
        const accessToken = await AuthHelper.getSKaaSAccessToken(instance, inProgress);
        try {
            const chatSessions = await chatService.getAllChatsAsync(userId, accessToken);

            if (chatSessions.length > 0) {
                const loadedConversations: Conversations = {};
                for (const chatSession of chatSessions) {
                    const chatMessages = await chatService.getChatMessagesAsync(chatSession.id, 0, 100, accessToken);

                    const chatUsers = await chatService.getAllChatParticipantsAsync(chatSession.id, accessToken);

                    loadedConversations[chatSession.id] = {
                        id: chatSession.id,
                        title: chatSession.title,
                        systemDescription: chatSession.systemDescription,
                        users: chatUsers,
                        messages: chatMessages,
                        botProfilePicture: getBotProfilePicture(Object.keys(loadedConversations).length),
                        input: '',
                        botResponseStatus: undefined,
                        userDataLoaded: false,
                        memoryBalance: chatSession.memoryBalance,
                    };
                }

                dispatch(setConversations(loadedConversations));
                dispatch(setSelectedConversation(chatSessions[0].id));
            } else {
                // No chats exist, create first chat window
                await createChat();
            }

            return true;
        } catch (e: any) {
            const errorMessage = `Unable to load chats. Details: ${getErrorDetails(e)}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));

            return false;
        }
    };

    const downloadBot = async (chatId: string) => {
        try {
            return await botService.downloadAsync(chatId, await AuthHelper.getSKaaSAccessToken(instance, inProgress));
        } catch (e: any) {
            const errorMessage = `Unable to download the bot. Details: ${getErrorDetails(e)}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        }

        return undefined;
    };

    const uploadBot = async (bot: Bot) => {
        const accessToken = await AuthHelper.getSKaaSAccessToken(instance, inProgress);
        botService
            .uploadAsync(bot, userId, accessToken)
            .then(async (chatSession: IChatSession) => {
                const chatMessages = await chatService.getChatMessagesAsync(chatSession.id, 0, 100, accessToken);

                const newChat = {
                    id: chatSession.id,
                    title: chatSession.title,
                    users: [loggedInUser],
                    messages: chatMessages,
                    botProfilePicture: getBotProfilePicture(Object.keys(conversations).length),
                    botResponseStatus: undefined,
                };

                dispatch(addConversation(newChat));
            })
            .catch((e: any) => {
                const errorMessage = `Unable to upload the bot. Details: ${getErrorDetails(e)}`;
                dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
            });
    };

    const getBotProfilePicture = (index: number): string => {
        return botProfilePictures[index % botProfilePictures.length];
    };

    const getChatMemorySources = async (chatId: string) => {
        try {
            return await chatService.getChatMemorySourcesAsync(
                chatId,
                await AuthHelper.getSKaaSAccessToken(instance, inProgress),
            );
        } catch (e: any) {
            const errorMessage = `Unable to get chat files. Details: ${getErrorDetails(e)}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        }

        return [];
    };

    const getSemanticMemories = async (chatId: string, memoryName: string) => {
        try {
            return await chatService.getSemanticMemoriesAsync(
                chatId,
                memoryName,
                await AuthHelper.getSKaaSAccessToken(instance, inProgress),
            );
        } catch (e: any) {
            const errorMessage = `Unable to get semantic memories. Details: ${getErrorDetails(e)}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        }

        return [];
    };

    const importDocument = async (chatId: string, files: File[]) => {
        try {
            await documentImportService.importDocumentAsync(
                userId,
                fullName,
                chatId,
                files,
                await AuthHelper.getSKaaSAccessToken(instance, inProgress),
            );
        } catch (e: any) {
            const errorMessage = `Failed to upload document. Details: ${getErrorDetails(e)}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        }
    };

    /*
     * Once enabled, each plugin will have a custom dedicated header in every Semantic Kernel request
     * containing respective auth information (i.e., token, encoded client info, etc.)
     * that the server can use to authenticate to the downstream APIs
     */
    const getEnabledPlugins = () => {
        return Object.values<Plugin>(plugins).filter((plugin) => plugin.enabled);
    };

    const joinChat = async (chatId: string) => {
        const accessToken = await AuthHelper.getSKaaSAccessToken(instance, inProgress);
        try {
            await chatService.joinChatAsync(userId, chatId, accessToken).then(async (result: IChatSession) => {
                // Get chat messages
                const chatMessages = await chatService.getChatMessagesAsync(result.id, 0, 100, accessToken);

                // Get chat users
                const chatUsers = await chatService.getAllChatParticipantsAsync(result.id, accessToken);

                const newChat: ChatState = {
                    id: result.id,
                    title: result.title,
                    systemDescription: result.systemDescription,
                    messages: chatMessages,
                    users: chatUsers,
                    botProfilePicture: getBotProfilePicture(Object.keys(conversations).length),
                    input: '',
                    botResponseStatus: undefined,
                    userDataLoaded: false,
                    memoryBalance: result.memoryBalance,
                };

                dispatch(addConversation(newChat));
            });
        } catch (e: any) {
            const errorMessage = `Error joining chat ${chatId}. Details: ${getErrorDetails(e)}`;
            return { success: false, message: errorMessage };
        }

        return { success: true, message: '' };
    };

    const editChat = async (
        chatId: string,
        title: string,
        syetemDescription: string,
        memoryBalance: number,
    ) => {
        const accessToken = await AuthHelper.getSKaaSAccessToken(instance, inProgress);
        try {
            await chatService.editChatAsync(
                chatId,
                title,
                syetemDescription,
                memoryBalance,
                accessToken
            );
        } catch (e: any) {
            const errorMessage = `Error editing chat ${chatId}. Details: ${getErrorDetails(e)}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        }
    };

    return {
        getChatUserById,
        createChat,
        loadChats,
        getResponse,
        downloadBot,
        uploadBot,
        getChatMemorySources,
        getSemanticMemories,
        importDocument,
        joinChat,
        editChat,
    };
};

function getErrorDetails(e: any) {
    return e instanceof Error ? e.message : String(e);
}
