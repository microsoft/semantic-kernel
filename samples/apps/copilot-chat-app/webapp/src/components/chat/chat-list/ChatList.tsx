import {
    Button,
    Dialog,
    Label,
    makeStyles,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    shorthands,
    Text,
    Tooltip,
} from '@fluentui/react-components';
import { Tree, TreeItem } from '@fluentui/react-components/unstable';

import { ArrowUploadRegular, BotAdd20Regular } from '@fluentui/react-icons';
import { FC, useCallback, useState } from 'react';
import { useChat } from '../../../libs/useChat';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { BotUploader } from '../../BotUploader';
import { ChatListItem } from './ChatListItem';
import { useFile } from '../../../libs/useFile';
import { Bot } from '../../../libs/models/Bot';

const useClasses = makeStyles({
    root: {
        width: '25%',
        minHeight: '100%',
        overflowX: 'hidden',
        overflowY: 'auto',
        scrollbarWidth: 'thin',
        backgroundColor: '#F0F0F0',
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginRight: '1em',
        marginLeft: '1em',
        alignItems: 'center',
        height: '4.8em',
        '& controls': {
            ...shorthands.gap('10px'),
            display: 'flex',
        },
    },
    label: {
        marginLeft: '1em',
    },
});

export const ChatList: FC = () => {
    const classes = useClasses();
    const { conversations, selectedId } = useAppSelector((state: RootState) => state.conversations);
    const chat = useChat();
    const fileHandler = useFile();

    const [uploadDialogOpen, setUploadDialogOpen] = useState(false);

    const onAddChat = () => {
        chat.createChat();
    };

    const onUpload = useCallback(
        (file: File) => {
            fileHandler.loadFile<Bot>(file, chat.importBot);
            setUploadDialogOpen(false);
        },
        [fileHandler, chat, setUploadDialogOpen],
    );

    return (
        <>
            <div className={classes.root}>
                <div className={classes.header}>
                    <Text weight="bold" size={500}>
                        Conversations
                    </Text>
                    <Menu>
                        <MenuTrigger disableButtonEnhancement>
                            <Tooltip content="Add Bot" relationship="label">
                                <Button icon={<BotAdd20Regular />} appearance="transparent" />
                            </Tooltip>
                        </MenuTrigger>
                        <MenuPopover>
                            <MenuList>
                                <MenuItem icon={<BotAdd20Regular />} onClick={onAddChat}>
                                    Add a new Bot
                                </MenuItem>
                                <MenuItem icon={<ArrowUploadRegular />}>
                                    <div onClick={() => setUploadDialogOpen(true)}>Upload a Bot</div>
                                </MenuItem>
                            </MenuList>
                        </MenuPopover>
                    </Menu>
                    <Dialog open={uploadDialogOpen} onOpenChange={(_event, data) => setUploadDialogOpen(data.open)}>
                        <BotUploader onUpload={onUpload} />
                    </Dialog>
                </div>
                <Label className={classes.label}>Your Bot</Label>
                <Tree aria-label={'chat list'}>
                    {Object.keys(conversations).map((id) => {
                        const convo = conversations[id];
                        const messages = convo.messages;
                        const lastMessage = convo.messages.length - 1;
                        return (
                            <TreeItem
                                key={id}
                                leaf
                                style={
                                    id === selectedId
                                        ? { background: 'var(--colorNeutralBackground1Selected)' }
                                        : undefined
                                }
                            >
                                <ChatListItem
                                    id={id}
                                    header={convo.title}
                                    timestamp={new Date(messages[lastMessage].timestamp).toLocaleTimeString([], {
                                        hour: '2-digit',
                                        minute: '2-digit',
                                    })}
                                    preview={
                                        messages.length > 0 ? messages[lastMessage].content : 'Click to start the chat'
                                    }
                                    botProfilePicture={convo.botProfilePicture}
                                />
                            </TreeItem>
                        );
                    })}
                </Tree>
            </div>
        </>
    );
};
