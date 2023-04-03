import { useAccount } from "@azure/msal-react";
import debug from "debug";
import { Constants } from "../Constants";
import { useAppDispatch, useAppSelector } from "../redux/app/hooks";
import { RootState } from "../redux/app/store";
import { ChatState, initialBotMessage } from "../redux/features/chat/ChatState";
import { addConversation, setSelectedConversation, updateConversation } from "../redux/features/conversations/conversationsSlice";
import { ChatUser } from "./models/ChatUser";
import { useSemanticKernel } from "./semantic-kernel/useSemanticKernel";

const log = debug(Constants.debug.root).extend('use-chat');

export const useChat = () => {
    const { audience } = useAppSelector((state: RootState) => state.chat);
    const dispatch = useAppDispatch();
    const account = useAccount();
    const sk = useSemanticKernel(import.meta.env.VITE_REACT_APP_BACKEND_URI as string);
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);

    const botProfilePictures : string[] = [
        '/assets/bot-icon-1.png',
        '/assets/bot-icon-2.png',
        '/assets/bot-icon-3.png',
        '/assets/bot-icon-4.png',
        '/assets/bot-icon-5.png',
    ];

    const getAudienceMemberForId = (id: string) =>
    {
        if (id === 'bot') return Constants.bot.profile;
        return audience.find((member) => member.id === id);
    };

    // TODO: handle error case of missing account information
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
        }
        dispatch(addConversation(newChat));
        dispatch(setSelectedConversation(name));
        return name;
    };

    const getResponse = async (value: string, chatId: string) => {
        const ask = { input: value, variables: [{ key: 'audience', value: account?.name ?? 'Unknown User' }] };
        try {
            var result = await sk.invokeAsync(ask, 'ChatSkill', 'Chat');
            const messageResult = {
                timestamp: new Date().getTime(),
                sender: 'bot',
                content: result.value,
            };
            dispatch(updateConversation({ message: messageResult, chatId: chatId }));
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    return {
        getAudienceMemberForId,
        createChat,
        getResponse
    };
}