import {
    makeStyles,
    mergeClasses,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    shorthands,
    Text,
    tokens,
} from '@fluentui/react-components';
import { FC } from 'react';
import { Constants } from '../../../Constants';
import { useAppDispatch } from '../../../redux/app/hooks';
import { setSelectedConversation } from '../../../redux/features/conversations/conversationsSlice';
import { Breakpoints } from '../../../styles';
import { timestampToDateString } from '../../utils/TextUtils';

const useClasses = makeStyles({
    root: {
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'row',
        width: '100%',
        ...Breakpoints.small({
            justifyContent: 'center',
        }),
        cursor: 'pointer',
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalXL),
    },
    avatar: {
        flexShrink: 0,
        width: '32px',
    },
    body: {
        minWidth: 0,
        display: 'flex',
        flexDirection: 'column',
        marginLeft: tokens.spacingHorizontalXS,
        ...Breakpoints.small({
            display: 'none',
        }),
    },
    header: {
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    title: {
        ...shorthands.overflow('hidden'),
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        fontSize: tokens.fontSizeBase300,
        color: tokens.colorNeutralForeground1,
        lineHeight: tokens.lineHeightBase200,
    },
    timestamp: {
        flexShrink: 0,
        marginLeft: tokens.spacingHorizontalM,
        fontSize: tokens.fontSizeBase200,
        color: tokens.colorNeutralForeground2,
        lineHeight: tokens.lineHeightBase200,
    },
    previewText: {
        display: 'block',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        lineHeight: tokens.lineHeightBase100,
        color: tokens.colorNeutralForeground2,
        ...shorthands.overflow('hidden')
    },
    popoverSurface: {
        display: 'none',
        ...Breakpoints.small({
            display: 'flex',
            flexDirection: 'column',
        }),
    },
    selected: {
        backgroundColor: tokens.colorNeutralBackground1,
    }
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
                <div className={mergeClasses(classes.root, isSelected && classes.selected)} onClick={onClick}>
                    <Persona avatar={{ image: { src: botProfilePicture } }} presence={{ status: 'available' }} />
                    <div className={classes.body}>
                        <div className={classes.header}>
                            <Text className={classes.title}>
                                {header}
                            </Text>
                            <Text className={classes.timestamp} size={300}>
                                {time}
                            </Text>
                        </div>
                        {preview && (
                            <>
                                {
                                    <Text id={`message-preview-${id}`} size={200} className={classes.previewText}>
                                        {preview}
                                    </Text>
                                }
                            </>
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
