import { Button } from '@fluentui/react-button';
import { makeStyles } from '@fluentui/react-components';
import { Tooltip } from '@fluentui/react-tooltip';
import React, { useCallback, useState } from 'react';
import { useChat } from '../../../libs/useChat';
import { useFile } from '../../../libs/useFile';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { FeatureKeys } from '../../../redux/features/app/AppState';
import { Breakpoints } from '../../../styles';
import { ArrowDownload16, Edit, Share20 } from '../../shared/BundledIcons';
import { InvitationCreateDialog } from '../invitation-dialog/InvitationCreateDialog';
import { DeleteChatDialog } from './dialogs/DeleteChatDialog';

const useClasses = makeStyles({
    root: {
        display: 'contents',
        ...Breakpoints.small({
            display: 'none',
        }),
    },
});

interface IListItemActionsProps {
    chatId: string;
    chatName: string;
    onEditTitleClick: () => void;
}

export const ListItemActions: React.FC<IListItemActionsProps> = ({ chatId, chatName, onEditTitleClick }) => {
    const classes = useClasses();
    const { features } = useAppSelector((state: RootState) => state.app);

    const chat = useChat();
    const { downloadFile } = useFile();
    const [isGettingInvitationId, setIsGettingInvitationId] = useState(false);

    const onDownloadBotClick = useCallback(() => {
        // TODO: Add a loading indicator
        void chat.downloadBot(chatId).then((content) => {
            downloadFile(
                `chat-history-${chatName}-${new Date().toISOString()}.json`,
                JSON.stringify(content),
                'text/json',
            );
        });
    }, [chat, chatId, chatName, downloadFile]);

    return (
        <div className={classes.root}>
            <Tooltip content={'Edit chat name'} relationship="label">
                <Button icon={<Edit />} appearance="transparent" aria-label="Edit" onClick={onEditTitleClick} />
            </Tooltip>
            <Tooltip content={'Download chat session'} relationship="label">
                <Button
                    disabled={!features[FeatureKeys.BotAsDocs].enabled}
                    icon={<ArrowDownload16 />}
                    appearance="transparent"
                    aria-label="Edit"
                    onClick={onDownloadBotClick}
                />
            </Tooltip>
            <Tooltip content={'Share live chat code'} relationship="label">
                <Button
                    disabled={!features[FeatureKeys.MultiUserChat].enabled}
                    icon={<Share20 />}
                    appearance="transparent"
                    aria-label="Edit"
                    onClick={() => setIsGettingInvitationId(true)}
                />
            </Tooltip>
            <DeleteChatDialog chatId={chatId} chatName={chatName} />
            {isGettingInvitationId && (
                <InvitationCreateDialog
                    onCancel={() => {
                        setIsGettingInvitationId(false);
                    }}
                    chatId={chatId}
                />
            )}
        </div>
    );
};
