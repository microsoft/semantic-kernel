import { useAccount } from '@azure/msal-react';
import { Constants } from '../Constants';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';
import { addAlert } from '../redux/features/app/appSlice';
import { ChatState, initialBotMessage } from '../redux/features/conversations/ChatState';
import {
    addConversation,
    setSelectedConversation,
    updateConversation,
} from '../redux/features/conversations/conversationsSlice';
import { AlertType } from './models/AlertType';
import { ChatUser } from './models/ChatUser';
import { useSemanticKernel } from './semantic-kernel/useSemanticKernel';
// import { useConnectors } from './connectors/useConnectors'; // ConnectorTokenExample

export const useChat = () => {
    const dispatch = useAppDispatch();
    const account = useAccount();
    const sk = useSemanticKernel(process.env.REACT_APP_BACKEND_URI as string);
    const { conversations } = useAppSelector((state: RootState) => state.conversations);
    // const connectors = useConnectors(); // ConnectorTokenExample

    const botProfilePictures: string[] = [
        '/assets/bot-icon-1.png',
        '/assets/bot-icon-2.png',
        '/assets/bot-icon-3.png',
        '/assets/bot-icon-4.png',
        '/assets/bot-icon-5.png',
    ];

    const getAudienceMemberForId = (id: string, chatId: string, audience: ChatUser[]) => {
        if (id === `${chatId}-bot` || id.toLocaleLowerCase() === 'bot') return Constants.bot.profile;
        return audience.find((member) => member.id === id);
    };

    const createChat = async () => {
        const name = `SK Chatbot @ ${new Date().toLocaleString()}`;
        const user: ChatUser = {
            id: account?.homeAccountId ?? '',
            fullName: account?.name ?? 'Unknown User',
            emailAddress: account?.username ?? '',
            photo: undefined,
            online: true,
            lastTypingTimestamp: 0,
        };

        const botProfilePictureIndex = Object.keys(conversations).length % botProfilePictures.length;
        const newChat: ChatState = {
            id: name,
            messages: [initialBotMessage(account?.name ?? 'there')],
            audience: [user],
            botTypingTimestamp: 0,
            botProfilePicture: botProfilePictures.at(botProfilePictureIndex) ?? '/assets/bot-icon-1.png',
        };
        dispatch(addConversation(newChat));
        dispatch(setSelectedConversation(name));
        return name;
    };

    const getResponse = async (value: string, chatId: string) => {
        const ask = { input: value, variables: [{ key: 'audience', value: account?.name ?? 'Unknown User' }] };
        try {
            var result = await sk.invokeAsync(ask, 'ChatSkill', 'Chat');
            // var result = await connectors.invokeSkillWithGraphToken(ask, {ConnectorSkill}, {ConnectorFunction}); // ConnectorTokenExample

            const messageResult = {
                timestamp: new Date().getTime(),
                sender: 'bot',
                content: result.value,
            };
            dispatch(updateConversation({ message: messageResult, chatId: chatId }));
        } catch (e: any) {
            const errorMessage = `Unable to generate bot response. Details: ${e.message ?? e}`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        }
    };

    return {
        getAudienceMemberForId,
        createChat,
        getResponse,
    };
};
