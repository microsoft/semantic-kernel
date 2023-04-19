import { useAccount, useMsal } from '@azure/msal-react';
import { Constants } from '../Constants';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';
import { addAlert } from '../redux/features/app/appSlice';
import { ChatState } from '../redux/features/conversations/ChatState';
import { Conversations } from '../redux/features/conversations/ConversationsState';
import {
    addConversation,
    incrementBotProfilePictureIndex,
    setConversations,
    setSelectedConversation,
    updateConversation,
} from '../redux/features/conversations/conversationsSlice';
import { AuthHelper } from './auth/AuthHelper';
import { AlertType } from './models/AlertType';
import { AuthorRoles, ChatMessage } from './models/ChatMessage';
import { ChatUser } from './models/ChatUser';
import { IAsk } from './semantic-kernel/model/Ask';
import { IAskResult, Variables } from './semantic-kernel/model/AskResult';
import { useSemanticKernel } from './semantic-kernel/useSemanticKernel';
// import { useConnectors } from './connectors/useConnectors'; // ConnectorTokenExample

export const useChat = () => {
    const dispatch = useAppDispatch();
    const { instance, accounts } = useMsal();
    const account = useAccount(accounts[0] || {});
    const sk = useSemanticKernel(process.env.REACT_APP_BACKEND_URI as string);
    const { botProfilePictureIndex } = useAppSelector((state: RootState) => state.conversations);
    
    // const connectors = useConnectors(); // ConnectorTokenExample

    const botProfilePictures: string[] = [
        '/assets/bot-icon-1.png',
        '/assets/bot-icon-2.png',
        '/assets/bot-icon-3.png',
        '/assets/bot-icon-4.png',
        '/assets/bot-icon-5.png',
    ];

    const loggedInUser: ChatUser = {
        id: account?.homeAccountId || '',
        fullName: account?.name || '',
        emailAddress: account?.username || '',
        photo: undefined, // TODO: Make call to Graph /me endpoint to load photo
        online: true,
        lastTypingTimestamp: 0,
    };

    const getAudienceMemberForId = (id: string, chatId: string, audience: ChatUser[]) => {
        if (id === `${chatId}-bot` || id.toLocaleLowerCase() === 'bot') return Constants.bot.profile;
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

    const createChat = async () => {
        const chatTitle = `SK Chatbot @ ${new Date().toLocaleString()}`;
        try {
            var ask: IAsk = {
                input: chatTitle,
                variables: [
                    { key: 'userId', value: account!.homeAccountId! },
                    { key: 'userName', value: account!.name! },
                ],
            };

            await sk.invokeAsync(
                ask,
                'ChatHistorySkill',
                'CreateChat',
                await AuthHelper.getSKaaSAccessToken(instance)).then(async (result: IAskResult) => {
                const newChatId = result.value;
                const initialBotMessage = getVariableValue(result.variables, 'initialBotMessage');

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
            const errorMessage = `Unable to create new chat. Details: ${e.message ?? e}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        }
    };

    const getResponse = async (value: string, chatId: string) => {
        const ask = {
            input: value,
            variables: [
                {
                    key: 'userId',
                    value: account?.homeAccountId!
                },
                {
                    key: 'userName',
                    value: account?.name!
                },
                {
                    key: 'chatId',
                    value: chatId
                }
            ]
        };
        try {
            var result = await sk.invokeAsync(ask, 'ChatSkill', 'Chat', await AuthHelper.getSKaaSAccessToken(instance));
            // var result = await connectors.invokeSkillWithGraphToken(ask, {ConnectorSkill}, {ConnectorFunction}); // ConnectorTokenExample

            const messageResult = {
                timestamp: new Date().getTime(),
                userName: 'bot',
                userId: 'bot',
                content: result.value,
                authorRole: AuthorRoles.Bot,
            };
            dispatch(updateConversation({ message: messageResult, chatId: chatId }));
        } catch (e: any) {
            const errorMessage = `Unable to generate bot response. Details: ${e.message ?? e}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        }
    };

    const loadChats = async () => {
        try {
            const ask = { input: account!.homeAccountId! };
            var result = await sk.invokeAsync(
                ask,
                'ChatHistorySkill',
                'GetAllChats',
                await AuthHelper.getSKaaSAccessToken(instance)
            );

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
                        'ChatHistorySkill',
                        'GetAllChatMessages',
                        await AuthHelper.getSKaaSAccessToken(instance)
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
                            return null;
                        });

                    conversations[chat.id] = {
                        id: chat.id,
                        title: chat.title,
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
            return true;
        } catch (e: any) {
            const errorMessage = `Unable to load chats. Details: ${e.message ?? e}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
            return false;
        }
    };

    return {
        getAudienceMemberForId,
        createChat,
        loadChats,
        getResponse,
    };
};
