import { Avatar, makeStyles, shorthands, Text } from '@fluentui/react-components';
import { FC } from 'react';
import { useAppDispatch } from '../../../redux/app/hooks';
import { setSelectedConversation } from '../../../redux/features/conversations/conversationsSlice';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        paddingTop: '0.8rem',
        paddingBottom: '0.8rem',
        paddingRight: '1rem',
        minWidth: '90%',
    },
    avatar: {
        flexShrink: '0',
        minWidth: '3.2rem'
    },
    body: {
        display: 'flex',
        flexDirection: 'column',
        minWidth: '0',
        flexGrow: '1',
        lineHeight: '1.6rem',
        paddingLeft: '0.8rem',
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        maxHeight: '1.2rem',
        lineHeight: '20px',
        flexGrow: '1',
        justifyContent: 'space-between',
    },
    timestamp: {
        flexShrink: 0,
        fontSize: 'small',
        maxWidth: '6rem',
        marginTop: '0',
        marginBottom: 'auto',
        marginLeft: '0.8rem'
    },
    title: {
        ...shorthands.overflow('hidden'),
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        minWidth: '4rem'
    },
    preview: {
        marginTop: '0.2rem',
        lineHeight: '16px',
    },
    previewText: {
        display: 'block',
        ...shorthands.overflow('hidden'),
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
    },
});

interface IChatListItemProps {
    id: string;
    header: string;
    timestamp: string;
    preview: string;
    botProfilePicture: string;
}

// TODO: populate Avatar
export const ChatListItem: FC<IChatListItemProps> = ({ id, header, timestamp, preview, botProfilePicture }) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();

    const onClick = (_ev: any) => {
        dispatch(setSelectedConversation(id));
    };

    return (
        <div className={classes.root} onClick={onClick}>
            <Avatar image={{ src: botProfilePicture }}/>
            <div className={classes.body}>
                <div className={classes.header}>
                    <Text className={classes.title} style={{ color: 'var(--colorNeutralForeground1)' }}>
                        {header}
                    </Text>
                    {timestamp && (
                        <Text className={classes.timestamp} size={300}>
                            {timestamp}
                        </Text>
                    )}
                </div>
                {preview && (
                    <div className={classes.preview}>
                        {
                            <Text id={`message-preview-${id}`} size={200} className={classes.previewText}>
                                {preview}
                            </Text>
                        }
                    </div>
                )}
            </div>
        </div>
    );
};