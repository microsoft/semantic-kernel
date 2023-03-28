import { useAccount } from "@azure/msal-react";
import debug from "debug";
import { Constants } from "../Constants";
import { useAppDispatch, useAppSelector } from "../redux/app/hooks";
import { RootState } from "../redux/app/store";
import { addMessage, setChat } from "../redux/features/chat/chatSlice";
import { ChatState, initialBotMessage } from "../redux/features/chat/ChatState";
import { addConversation, setSelectedConversation } from "../redux/features/conversations/conversationsSlice";
import { MicrosoftGraph } from './MicrosoftGraph';
import { ChatMessage } from "./models/ChatMessage";
import { ChatUser } from "./models/ChatUser";

const log = debug(Constants.debug.root).extend('use-chat');

export const useChat = () => {
    const { audience, messages } = useAppSelector((state: RootState) => state.chat);
    const { conversations } = useAppSelector((state: RootState) => state.conversations);
    const dispatch = useAppDispatch();
    const account = useAccount();

    const getAudienceMemberForId = (id: string) =>
    {
        if (id === 'bot') return Constants.bot.profile;
        return audience.find((member) => member.id === id);
    };

    const addMessageToHistory = async (message: ChatMessage) => {
        dispatch(addMessage(message));
    };

    // TODO: handle error case of missing account information
    const createChat = async () => {
        const name = `SK Chatbot @ ${new Date().toLocaleString()}`;
        const user: ChatUser = {
            id: account?.homeAccountId ?? '',
            fullName: account?.name ?? 'Unknown User',
            emailAddress: account?.username ?? '',
            photo: await MicrosoftGraph.getMyPhotoAsync(),
            online: true,
            lastTypingTimestamp: 0,
        };
        const newChat: ChatState = {
            id: name,
            messages: [initialBotMessage(account?.name ?? 'there')],
            audience: [user],
            botTypingTimestamp: 0
        }
        dispatch(addConversation(newChat));
        // Pass in new chat payload to account for 
        // race condition between parallel dispatches
        // Will remove this once we support async fetch from SK
        setSelectedChat(name, newChat);
        return name;
    };

    const setSelectedChat = (id: string, chatPayload?: ChatState) => {
        dispatch(setSelectedConversation(id));
        dispatch(setChat(conversations[id] ?? chatPayload));
    }

    return {
        addMessageToHistory,
        getAudienceMemberForId,
        setSelectedChat,
        createChat
    };
}