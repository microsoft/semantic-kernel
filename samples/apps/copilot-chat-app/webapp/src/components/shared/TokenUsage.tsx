import {
    Body2,
    Button,
    Divider,
    makeStyles,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    shorthands,
    Text,
    tokens,
} from '@fluentui/react-components';
import { Info16 } from './BundledIcons';

const useClasses = makeStyles({
    horizontal: {
        display: 'flex',
        ...shorthands.gap(tokens.spacingVerticalSNudge),
        alignItems: 'center',
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.gap(tokens.spacingHorizontalS),
        paddingBottom: tokens.spacingHorizontalM,
    },
    popover: {
        width: '300px',
    },
    header: {
        marginBlockEnd: tokens.spacingHorizontalM,
    },
});

interface ITokenUsage {
    promptUsage: number;
    dependencyUsage: number;
    sessionTotal?: boolean;
}

export const TokenUsage: React.FC<ITokenUsage> = ({ sessionTotal, promptUsage, dependencyUsage }) => {
    // Necessary conversion due to type coercion issues
    promptUsage = Number(promptUsage);
    dependencyUsage = Number(dependencyUsage);

    const showBarChart = promptUsage > 0 || dependencyUsage > 0;

    const classes = useClasses();
    const maxWidth = 500;
    const totalUsage = Number(promptUsage) + Number(dependencyUsage);
    const promptPercentage = promptUsage / totalUsage;
    const dependencyPercentage = dependencyUsage / totalUsage;

    const promptWidth = promptPercentage * maxWidth;
    const dependencyWidth = dependencyPercentage * maxWidth;

    return (
        <>
            <h3 className={classes.header}>
                Token Usage
                <Popover withArrow>
                    <PopoverTrigger disableButtonEnhancement>
                        <Button icon={<Info16 />} appearance="transparent" />
                    </PopoverTrigger>
                    <PopoverSurface className={classes.popover}>
                        <Text>
                            Prompt token usage is the number of tokens used in the bot generation prompt. Dependency
                            token usage is the number of tokens used in dependency prompts called to construct the bot
                            generation prompt.
                        </Text>
                    </PopoverSurface>
                </Popover>
            </h3>
            <div className={classes.content}>
                {showBarChart ? (
                    <>
                        {sessionTotal && <Text>Total token usage for current session</Text>}
                        <div className={classes.horizontal} style={{ gap: tokens.spacingHorizontalXXS }}>
                            <div
                                style={{
                                    backgroundColor: tokens.colorNeutralForeground2BrandHover,
                                    height: '10px',
                                    width: `${promptWidth}px`,
                                }}
                            />
                            <div
                                style={{
                                    backgroundColor: tokens.colorPaletteRedBackground2,
                                    height: '10px',
                                    width: `${dependencyWidth}px`,
                                }}
                            />
                        </div>
                        <div className={classes.horizontal}>
                            <div
                                style={{
                                    backgroundColor: tokens.colorNeutralForeground2BrandHover,
                                    height: '10px',
                                    width: `10px`,
                                }}
                            />
                            <Text>
                                Prompt {'('}
                                {promptUsage}
                                {')'}
                            </Text>
                            <div
                                style={{
                                    backgroundColor: tokens.colorPaletteRedBackground2,
                                    height: '10px',
                                    width: `10px`,
                                }}
                            />
                            <Text>
                                Dependency {'('}
                                {dependencyUsage}
                                {')'}
                            </Text>
                        </div>
                    </>
                ) : (
                    <Body2>
                        {sessionTotal
                            ? 'No tokens have been used in this session yet.'
                            : 'Unable to determine tokens used in this prompt.'}
                    </Body2>
                )}
            </div>

            <Divider />
        </>
    );
};
