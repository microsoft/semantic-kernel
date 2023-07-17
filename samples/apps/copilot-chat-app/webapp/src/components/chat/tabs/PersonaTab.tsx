// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { AuthHelper } from '../../../libs/auth/AuthHelper';
import { ChatService } from '../../../libs/services/ChatService';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { editConversationSystemDescription } from '../../../redux/features/conversations/conversationsSlice';
import { MemoryBiasSlider } from '../persona/MemoryBiasSlider';
import { PromptEditor } from '../persona/PromptEditor';
import { TabView } from './TabView';

export const PersonaTab: React.FC = () => {
    const { instance, inProgress } = useMsal();
    const dispatch = useAppDispatch();

    const chatService = new ChatService(process.env.REACT_APP_BACKEND_URI as string);
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const chat = conversations[selectedId];

    return (
        <TabView title="Persona" learnMoreDescription="personas" learnMoreLink=" https://aka.ms/sk-intro-to-personas ">
            <PromptEditor
                title="Meta Prompt"
                prompt={chat.systemDescription}
                isEditable={true}
                info="The prompt that defines the chat bot's persona."
                modificationHandler={async (newSystemDescription: string) => {
                    chatService
                        .editChatAsync(
                            chat.id,
                            chat.title,
                            newSystemDescription,
                            await AuthHelper.getSKaaSAccessToken(instance, inProgress),
                        )
                        .finally(() => {
                            dispatch(
                                editConversationSystemDescription({
                                    id: chat.id,
                                    newSystemDescription: newSystemDescription,
                                }),
                            );
                        });
                }}
            />
            <PromptEditor
                title="Short Term Memory"
                prompt="Extract information for a short period of time, such as a few seconds or minutes. It should be useful for performing complex cognitive tasks that require attention, concentration, or mental calculation."
                isEditable={false}
                info="We maintain a summary of the most recent N chat exchanges."
            />
            <PromptEditor
                title="Long Term Memory"
                prompt="Extract information that is encoded and consolidated from other memory types, such as working memory or sensory memory. It should be useful for maintaining and recalling one's personal identity, history, and knowledge over time."
                isEditable={false}
                info="We maintain a summary of the least recent N chat exchanges."
            />
            <MemoryBiasSlider />
        </TabView>
    );
};
