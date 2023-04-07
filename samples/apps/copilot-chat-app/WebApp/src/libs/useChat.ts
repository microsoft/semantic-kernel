import { useAccount } from '@azure/msal-react';
import { Constants } from '../Constants';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';
import { ChatState } from '../redux/features/conversations/ChatState';
import {
    addConversation,
    incrementBotProfilePictureIndex,
    setConversations,
    setSelectedConversation,
    updateConversation
} from '../redux/features/conversations/conversationsSlice';
import { Conversations } from '../redux/features/conversations/ConversationsState';
import { ChatMessage } from './models/ChatMessage';
import { ChatUser } from './models/ChatUser';
import { IAsk } from './semantic-kernel/model/Ask';
import { IAskResult, Variables } from './semantic-kernel/model/AskResult';
import { useSemanticKernel } from './semantic-kernel/useSemanticKernel';

export const useChat = () => {
    const dispatch = useAppDispatch();
    const account = useAccount();
    const sk = useSemanticKernel(process.env.REACT_APP_BACKEND_URI as string);
    const { botProfilePictureIndex } = useAppSelector((state: RootState) => state.conversations);

    const botProfilePictures: string[] = [
        '/assets/bot-icon-1.png',
        '/assets/bot-icon-2.png',
        '/assets/bot-icon-3.png',
        '/assets/bot-icon-4.png',
        '/assets/bot-icon-5.png',
    ];

    const loggedInUser: ChatUser = {
        id: account!.homeAccountId,
        fullName: account!.name!,
        emailAddress: account!.username,
        photo: undefined, // TODO: Make call to Graph /me endpoint to load photo
        online: true,
        lastTypingTimestamp: 0,
    };

    // TODO: Verify consistent 'sender' field -- is it name or ID?
    const getAudienceMemberForId = (id: string, botId: string, audience: ChatUser[]) => {
        if (id === `${botId}-bot` || id === 'Bot') return Constants.bot.profile;
        return audience.find((member) => member.id === id);
    };

    const getVariableValue = (variables: Variables, key: string): string | undefined => {
        for (const idx in variables) {
            if (variables[idx].key === key) {
                return variables[idx].value;
            }
        }
        // End of array, did not find expected variable.
        throw new Error(`Could not find valid ${key} variable in context.`);
    };

    const registerLoggedInUser = async () => {
        try {
            var ask: IAsk = {
                input: account!.homeAccountId!,
                variables: [
                    { key: 'name', value: account!.name! },
                    { key: 'email', value: account!.username },
                ],
            };

            await sk.invokeAsync(ask, 'ChatMemorySkill', 'CreateUser');
        } catch (e: any) {
            const userFoundRegEx = new RegExp(/Error.+User\s[\d\w.\-]+\salready\sexists\./g);
            const userFound = userFoundRegEx.test(e.message);
            if (!userFound) {
                alert('[RegisterUser] Unable to register logged in user. Details:\n' + e);
            }
        }
    };

    const createChat = async () => {
        const chatTitle = `SK Chatbot @ ${new Date().toLocaleString()}`;
        try {
            var ask: IAsk = {
                input: chatTitle,
                variables: [{ key: 'userId', value: account!.homeAccountId! }],
            };

            await sk.invokeAsync(ask, 'ChatMemorySkill', 'CreateChat').then(async (result: IAskResult) => {
                const newChatId = result.value;
                const initialBotMessage = getVariableValue(result.variables, 'initialBotMessage');

                // TODO: hook up chat object once Tao makes change to return Chat object
                const newChat: ChatState = {
                    id: newChatId,
                    title: chatTitle,
                    messages: [JSON.parse(initialBotMessage!)],
                    audience: [loggedInUser],
                    botTypingTimestamp: 0,
                    botProfilePicture: botProfilePictures.at(botProfilePictureIndex) ?? '/assets/bot-icon-1.png',
                };

                dispatch(incrementBotProfilePictureIndex());
                dispatch(addConversation(newChat));
                dispatch(setSelectedConversation(newChatId));

                return newChatId;
            });
        } catch (e: any) {
            alert('[CreateChat] Unable to create new chat. Details:\n' + e);
        }
    };

    const getResponse = async (value: string, chatId: string) => {
        const ask = {
            input: value,
            variables: [
                { key: 'userId', value: account!.homeAccountId! },
                { key: 'chatId', value: chatId },
            ],
        };
        try {
            var result = await sk.invokeAsync(ask, 'ChatSkill', 'Chat');
            const messageResult = {
                timestamp: new Date().getTime(),
                sender: getVariableValue(result.variables, 'userId')!,
                content: result.value,
            };
            dispatch(updateConversation({ message: messageResult, chatId: chatId }));
        } catch (e) {
            alert('[GetResponse] Error getting bot response.\n\nDetails:\n' + e);
        }
    };

    const loadChats = async () => {
        try {
            const ask = { input: account!.homeAccountId! };
            await sk.invokeAsync(ask, 'ChatMemorySkill', 'GetAllChats').then(async (result) => {
                const chats = JSON.parse(result.value);
                if (Object.keys(chats).length > 0) {
                    const conversations: Conversations = {};
                    for (const index in chats) {
                        const chat = chats[index];
                        const loadMessagesAsk = {
                            input: chat.id,
                            variables: [
                                { key: 'startIdx', value: '0' },
                                { key: 'count', value: '100' },
                            ],
                        };
                        const messageResult = await sk.invokeAsync(
                            loadMessagesAsk,
                            'ChatMemorySkill',
                            'GetAllChatMessages',
                        );

                        const messages = JSON.parse(messageResult.value);

                        // Messages are returned with most recent message at index 0 and oldest messge at the last index,
                        // so we need to reverse the order for render
                        const orderedMessages: ChatMessage[] = [];
                        Object.keys(messages)
                            .reverse()
                            .map((key) => {
                                const chatMessage = messages[key];
                                orderedMessages.push(chatMessage);
                            });

                        conversations[chat.id] = {
                            id: chat.id,
                            title: chat.Title,
                            audience: [loggedInUser],
                            messages: orderedMessages,
                            botTypingTimestamp: 0,
                            botProfilePicture: botProfilePictures[botProfilePictureIndex],
                        };
                        dispatch(incrementBotProfilePictureIndex());
                    }

                    dispatch(setConversations(conversations));
                    dispatch(setSelectedConversation(chats[0].id));
                } else {
                    // No chats exist, create first chat window
                    await createChat();
                }
            });
        } catch (e) {
            alert('Unable to load chats. \n\nDetails:\n' + e);
        }
    };

    return {
        registerLoggedInUser,
        getAudienceMemberForId,
        createChat,
        getResponse,
        loadChats,
    };
};