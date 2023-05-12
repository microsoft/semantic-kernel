// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import {
    Button,
    Input,
    InputOnChangeData,
    Label,
    makeStyles,
    Persona,
    shorthands,
    tokens,
    Tooltip,
} from '@fluentui/react-components';
import { EditRegular, Save24Regular } from '@fluentui/react-icons';
import React, { useEffect, useState } from 'react';
import { AuthHelper } from '../../libs/auth/AuthHelper';
import { AlertType } from '../../libs/models/AlertType';
import { ChatService } from '../../libs/services/ChatService';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { addAlert } from '../../redux/features/app/appSlice';
import { editConversationTitle } from '../../redux/features/conversations/conversationsSlice';
import { ChatRoom } from './ChatRoom';
import { ShareBotMenu } from './ShareBotMenu';

const useClasses = makeStyles({
    root: {
        height: '100%',
        display: 'grid',
        gridTemplateColumns: '1fr',
        gridTemplateRows: 'auto 1fr',
        gridTemplateAreas: "'header' 'content'",
        width: '-webkit-fill-available',
        backgroundColor: '#F5F5F5',
        boxShadow: 'rgb(0 0 0 / 25%) 0 0.2rem 0.4rem -0.075rem',
    },
    header: {
        ...shorthands.gridArea('header'),
        backgroundColor: tokens.colorNeutralBackground4,
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        ...shorthands.borderBottom('1px', 'solid', 'rgb(0 0 0 / 10%)'),
    },
    headerContent: {
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
        display: 'grid',
        gridTemplateColumns: '1fr auto',
        gridTemplateRows: '1fr',
        gridTemplateAreas: "'title controls'",
        boxSizing: 'border-box',
        width: '100%',
    },
    title: {
        ...shorthands.gridArea('title'),
        ...shorthands.gap(tokens.spacingHorizontalM),
        alignItems: 'center',
        display: 'flex',
        flexDirection: 'row',
    },
    controls: {
        ...shorthands.gridArea('controls'),
        ...shorthands.gap(tokens.spacingHorizontalM),
        alignItems: 'right',
        display: 'flex',
        flexDirection: 'row',
    },
    content: {
        ...shorthands.gridArea('content'),
        overflowY: 'auto',
    },
    contentOuter: {
        height: '100%',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
    },
    contentInner: {
        width: '100%',
    },
});

export const ChatWindow: React.FC = () => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const chatName = conversations[selectedId].title;
    const [title, setTitle] = useState<string | undefined>(selectedId ?? undefined);
    const [isEditing, setIsEditing] = useState<boolean>(false);
    const { instance } = useMsal();

    const chatService = new ChatService(process.env.REACT_APP_BACKEND_URI as string);

    const onEdit = async () => {
        if (isEditing) {
            if (chatName !== title) {
                try {
                    await chatService.editChatAsync(
                        conversations[selectedId].id,
                        title!,
                        await AuthHelper.getSKaaSAccessToken(instance),
                    );

                    dispatch(editConversationTitle({ id: selectedId ?? '', newTitle: title ?? '' }));
                } catch (e: any) {
                    const errorMessage = `Unable to retrieve chat to change title. Details: ${e.message ?? e}`;
                    dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
                }
            }
        }
        setIsEditing(!isEditing);
    };

    const onTitleChange = (_ev: React.ChangeEvent<HTMLInputElement>, data: InputOnChangeData) => {
        setTitle(data.value);
    };

    useEffect(() => {
        setTitle(chatName);
        setIsEditing(false);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedId]);

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <div className={classes.headerContent}>
                    <div className={classes.title}>
                        <Persona
                            key={'SK Bot'}
                            size="medium"
                            avatar={{ image: { src: conversations[selectedId].botProfilePicture }}}
                            presence={{ status: 'available' }}
                        />
                        {isEditing ? (
                            <Input value={title} onChange={onTitleChange} id={title} />
                        ) : (
                            <Label size="large" weight="semibold">
                                {chatName}
                            </Label>
                        )}
                        <Tooltip content={isEditing ? "Save conversation name" : "Edit conversation name"} relationship="label">
                            <Button
                                icon={isEditing ? <Save24Regular /> : <EditRegular />}
                                appearance="transparent"
                                onClick={onEdit}
                                disabled={title === undefined || !title}
                            />
                        </Tooltip>
                    </div>
                    <div className={classes.controls}>
                        <ShareBotMenu chatId={selectedId} chatTitle={title || ''} />
                    </div>
                </div>
            </div>
            <div className={classes.content}>
                <div className={classes.contentOuter}>
                    <div className={classes.contentInner}>
                        <ChatRoom />
                    </div>
                </div>
            </div>
        </div>
    );
};
