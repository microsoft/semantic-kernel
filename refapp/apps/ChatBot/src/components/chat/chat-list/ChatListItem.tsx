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
        height: '4.8rem',
        minWidth: '90%'
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
        height: '1.2rem',
        lineHeight: '20px',
        flexGrow: '1',
        justifyContent: 'space-between',
        ...shorthands.overflow('hidden'),
        textOverflow: 'ellipsis',
    },
    timestamp: {
        flexShrink: 0,
        fontSize: 'small',
        maxWidth: '6rem',
        marginTop: '0',
        marginBottom: 'auto',
        marginLeft: '0.8rem'
    },
    preview: {
        ...shorthands.overflow('hidden'),
        whiteSpace: 'nowrap',
        display: 'block',
        flexGrow: 1,
        lineHeight: "16px",
        height: "16px",
        textOverflow: 'ellipsis',
    }
});

interface IChatListItemProps {
    id: string;
    header: string;
    timestamp: string;
    preview: string;
}

// TODO: populate Avatar
export const ChatListItem: FC<IChatListItemProps> = ({ id, header, timestamp, preview }) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();

    const onClick = (_ev: any) => {
        dispatch(setSelectedConversation(id));
    };

    return (
        <div className={classes.root} onClick={onClick }>
            <Avatar />
            <div className={classes.body}>
                <div className={classes.header}>
                    <Text style={{color: 'var(--colorNeutralForeground1)'}}> {header} </Text>
                    {timestamp && (
                        <Text className={classes.timestamp} size={300} >
                            {timestamp}
                        </Text>
                    )}
                </div>
                {preview && (
                    <div className={classes.preview} >
                        {<Text id={`message-preview-${id}`} size={200}>{preview}</Text>}
                    </div>
                )}
            </div>
        </div>
    );
}