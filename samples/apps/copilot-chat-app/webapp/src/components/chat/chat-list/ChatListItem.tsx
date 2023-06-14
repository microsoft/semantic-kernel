import {
    makeStyles,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    shorthands,
    Text,
} from '@fluentui/react-components';
import { FC } from 'react';
import { Constants } from '../../../Constants';
import { useAppDispatch } from '../../../redux/app/hooks';
import { setSelectedConversation } from '../../../redux/features/conversations/conversationsSlice';
import { Breakpoints } from '../../../styles';
import { timestampToDateString } from '../../utils/TextUtils';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        paddingTop: '0.8rem',
        paddingBottom: '0.8rem',
        paddingRight: '1rem',
        width: '93%',
        ...Breakpoints.small({
            justifyContent: 'center',
        }),
    },
    avatar: {
        flexShrink: '0',
        minWidth: '3.2rem',
    },
    body: {
        display: 'flex',
        flexDirection: 'column',
        minWidth: '0',
        flexGrow: '1',
        lineHeight: '1.6rem',
        paddingLeft: '0.8rem',
        ...Breakpoints.small({
            display: 'none',
        }),
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
        marginLeft: '0.8rem',
    },
    title: {
        ...shorthands.overflow('hidden'),
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        minWidth: '4rem',
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
    popoverSurface: {
        display: 'none',
        ...Breakpoints.small({
            display: 'flex',
            flexDirection: 'column',
        }),
    },
});

interface IChatListItemProps {
    id: string;
    header: string;
    timestamp: number;
    preview: string;
    botProfilePicture: string;
    isSelected: boolean;
}

export const ChatListItem: FC<IChatListItemProps> = ({
    id,
    header,
    timestamp,
    preview,
    botProfilePicture,
    isSelected,
}) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();

    const onClick = (_ev: any) => {
        dispatch(setSelectedConversation(id));
    };

    const time = timestampToDateString(timestamp);
    return (
        <Popover
            openOnHover={!isSelected}
            mouseLeaveDelay={0}
            positioning={{
                position: 'after',
                autoSize: 'width',
            }}
        >
            <PopoverTrigger disableButtonEnhancement>
                <div className={classes.root} onClick={onClick}>
                    <Persona avatar={{ image: { src: botProfilePicture } }} presence={{ status: 'available' }} />
                    <div className={classes.body}>
                        <div className={classes.header}>
                            <Text className={classes.title} style={{ color: 'var(--colorNeutralForeground1)' }}>
                                {header}
                            </Text>
                            <Text className={classes.timestamp} size={300}>
                                {time}
                            </Text>
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
            </PopoverTrigger>
            <PopoverSurface className={classes.popoverSurface}>
                <Text weight="bold">{Constants.bot.profile.fullName}</Text>
                <Text>{time}</Text>
            </PopoverSurface>
        </Popover>
    );
};
