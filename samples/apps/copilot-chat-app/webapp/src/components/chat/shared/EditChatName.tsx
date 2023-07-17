import { useMsal } from '@azure/msal-react';
import { Button } from '@fluentui/react-button';
import { makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { Input, InputOnChangeData } from '@fluentui/react-input';
import { useEffect, useState } from 'react';
import { AuthHelper } from '../../../libs/auth/AuthHelper';
import { AlertType } from '../../../libs/models/AlertType';
import { ChatService } from '../../../libs/services/ChatService';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { addAlert } from '../../../redux/features/app/appSlice';
import { editConversationTitle } from '../../../redux/features/conversations/conversationsSlice';
import { Breakpoints } from '../../../styles';
import { Checkmark20, Dismiss20 } from '../../shared/BundledIcons';

const useClasses = makeStyles({
    root: {
        width: '100%',
        ...Breakpoints.small({
            display: 'none',
        }),
    },
    buttons: {
        display: 'flex',
        alignSelf: 'end',
    },
    textButtons: {
        ...shorthands.gap(tokens.spacingVerticalS),
    },
});

interface IEditChatNameProps {
    name: string;
    chatId: string;
    exitEdits: () => void;
    textButtons?: boolean;
}

export const EditChatName: React.FC<IEditChatNameProps> = ({ name, chatId, exitEdits, textButtons }) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { instance, inProgress } = useMsal();
    const chatService = new ChatService(process.env.REACT_APP_BACKEND_URI as string);
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const chat = conversations[selectedId];

    const [title = '', setTitle] = useState<string | undefined>(name);

    useEffect(() => {
        if (selectedId !== chatId) exitEdits();
    }, [chatId, exitEdits, selectedId]);

    const onSaveTitleChange = async () => {
        if (name !== title) {
            await chatService.editChatAsync(
                chatId,
                title,
                chat.systemDescription,
                await AuthHelper.getSKaaSAccessToken(instance, inProgress),
            );
            dispatch(editConversationTitle({ id: chatId, newTitle: title }));
        }
        exitEdits();
    };

    const onClose = () => {
        setTitle(name);
        exitEdits();
    };

    const onTitleChange = (_ev: React.ChangeEvent<HTMLInputElement>, data: InputOnChangeData) => {
        setTitle(data.value);
    };

    const handleSave = () => {
        onSaveTitleChange().catch((e: any) => {
            const errorMessage = `Unable to retrieve chat to change title. Details: ${
                e instanceof Error ? e.message : String(e)
            }`;
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
        });
    };

    const handleKeyDown: React.KeyboardEventHandler<HTMLElement> = (event) => {
        if (event.key === 'Enter') {
            handleSave();
        }
    };
    return (
        <div
            className={classes.root}
            style={{
                display: 'flex',
                flexDirection: `${textButtons ? 'column' : 'row'}`,
                gap: `${textButtons ? tokens.spacingVerticalS : tokens.spacingVerticalNone}`,
            }}
        >
            <Input value={title} onChange={onTitleChange} id={title} onKeyDown={handleKeyDown} />
            {textButtons && (
                <div className={mergeClasses(classes.buttons, classes.textButtons)}>
                    <Button appearance="secondary" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button type="submit" appearance="primary" onClick={handleSave}>
                        Save
                    </Button>
                </div>
            )}
            {!textButtons && (
                <div className={classes.buttons}>
                    <Button icon={<Dismiss20 />} onClick={onClose} appearance="transparent" />
                    <Button icon={<Checkmark20 />} onClick={handleSave} appearance="transparent" />
                </div>
            )}
        </div>
    );
};
