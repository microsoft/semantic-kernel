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
import { ShieldTask16Regular } from '@fluentui/react-icons';
import { FC, useState } from 'react';
import { Constants } from '../../../Constants';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { FeatureKeys } from '../../../redux/features/app/AppState';
import { setSelectedConversation } from '../../../redux/features/conversations/conversationsSlice';
import { Breakpoints } from '../../../styles';
import { timestampToDateString } from '../../utils/TextUtils';
import { EditChatName } from '../shared/EditChatName';
import { ListItemActions } from './ListItemActions';

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
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        marginLeft: tokens.spacingHorizontalXS,
        ...Breakpoints.small({
            display: 'none',
        }),
        alignSelf: 'center',
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
        ...shorthands.overflow('hidden'),
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
    },
    protectedIcon: {
        color: '#6BB700',
        verticalAlign: 'text-bottom',
        marginLeft: '4px',
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
    const { features } = useAppSelector((state: RootState) => state.app);

    const showPreview = !features[FeatureKeys.SimplifiedExperience].show && preview;
    const showActions = features[FeatureKeys.SimplifiedExperience].show && isSelected;

    const [editingTitle, setEditingTitle] = useState(false);

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
                    <Persona
                        avatar={{ image: { src: botProfilePicture } }}
                        presence={
                            !features[FeatureKeys.SimplifiedExperience].show ? { status: 'available' } : undefined
                        }
                    />
                    {editingTitle ? (
                        <EditChatName name={header} chatId={id} exitEdits={() => setEditingTitle(false)} />
                    ) : (
                        <>
                            <div className={classes.body}>
                                <div className={classes.header}>
                                    <Text className={classes.title}>
                                        {header}
                                        {features[FeatureKeys.AzureContentSafety].show && (
                                            <ShieldTask16Regular className={classes.protectedIcon} />
                                        )}
                                    </Text>
                                    {!features[FeatureKeys.SimplifiedExperience].show && (
                                        <Text className={classes.timestamp} size={300}>
                                            {time}
                                        </Text>
                                    )}
                                </div>
                                {showPreview && (
                                    <>
                                        {
                                            <Text
                                                id={`message-preview-${id}`}
                                                size={200}
                                                className={classes.previewText}
                                            >
                                                {preview}
                                            </Text>
                                        }
                                    </>
                                )}
                            </div>
                            {showActions && (
                                <ListItemActions
                                    chatId={id}
                                    chatName={header}
                                    onEditTitleClick={() => setEditingTitle(true)}
                                />
                            )}
                        </>
                    )}
                </div>
            </PopoverTrigger>
            <PopoverSurface className={classes.popoverSurface}>
                <Text weight="bold">{Constants.bot.profile.fullName}</Text>
                <Text>{time}</Text>
            </PopoverSurface>
        </Popover>
    );
};
