import { Button } from '@fluentui/react-button';
import { makeStyles } from '@fluentui/react-components';
import { ArrowDownload16Regular, Delete16Regular, EditRegular, Share20Regular } from '@fluentui/react-icons';
import { Tooltip } from '@fluentui/react-tooltip';
import React, { useCallback, useState } from 'react';
import { useChat } from '../../../libs/useChat';
import { useFile } from '../../../libs/useFile';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { FeatureKeys } from '../../../redux/features/app/AppState';
import { Breakpoints } from '../../../styles';
import { InvitationCreateDialog } from '../invitation-dialog/InvitationCreateDialog';

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
    chatTitle: string;
    onEditTitleClick: () => void;
}

export const ListItemActions: React.FC<IListItemActionsProps> = ({ chatId, chatTitle, onEditTitleClick }) => {
    const classes = useClasses();
    const { features } = useAppSelector((state: RootState) => state.app);

    const chat = useChat();
    const { downloadFile } = useFile();
    const [isGettingInvitationId, setIsGettingInvitationId] = useState(false);

    const onDownloadBotClick = useCallback(() => {
        // TODO: Add a loading indicator
        void chat.downloadBot(chatId).then((content) => {
            downloadFile(
                `chat-history-${chatTitle}-${new Date().toISOString()}.json`,
                JSON.stringify(content),
                'text/json',
            );
        });
    }, [chat, chatId, chatTitle, downloadFile]);

    return (
        <div className={classes.root}>
            <Tooltip content={'Edit chat name'} relationship="label">
                <Button icon={<EditRegular />} appearance="transparent" aria-label="Edit" onClick={onEditTitleClick} />
            </Tooltip>
            <Tooltip content={'Download chat session'} relationship="label">
                <Button
                    disabled={!features[FeatureKeys.BotAsDocs].enabled}
                    icon={<ArrowDownload16Regular />}
                    appearance="transparent"
                    aria-label="Edit"
                    onClick={onDownloadBotClick}
                />
            </Tooltip>
            <Tooltip content={'Share live chat code'} relationship="label">
                <Button
                    disabled={!features[FeatureKeys.MultiUserChat].enabled}
                    icon={<Share20Regular />}
                    appearance="transparent"
                    aria-label="Edit"
                    onClick={() => setIsGettingInvitationId(true)}
                />
            </Tooltip>
            <Tooltip content={'Delete chat session (show alert with ok/cancel)'} relationship="label">
                <Button icon={<Delete16Regular />} appearance="transparent" aria-label="Edit" />
            </Tooltip>
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
