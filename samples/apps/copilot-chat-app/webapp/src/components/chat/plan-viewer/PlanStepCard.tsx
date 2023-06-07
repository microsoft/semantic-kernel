import { Badge, Body1, Card, CardHeader, makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';
import { IPlan, IPlanInput } from '../../../libs/models/Plan';
import { CopilotChatTokens } from '../../../styles';
import { PlanStepInput } from './PlanStepInput';

const useClasses = makeStyles({
    card: {
        ...shorthands.margin('auto'),
        width: '700px',
        maxWidth: '100%',
    },
    header: {
        color: CopilotChatTokens.titleColor,
    },
    inputs: {
        ...shorthands.gap(tokens.spacingHorizontalS),
        display: 'flex',
        flexWrap: 'wrap',
    },
    bar: {
        ...shorthands.borderRadius(tokens.borderRadiusMedium),
        width: '4px',
        backgroundColor: CopilotChatTokens.titleColor,
    },
    flexRow: {
        display: 'flex',
        flexDirection: 'row',
    },
    flexColumn: {
        display: 'flex',
        flexDirection: 'column',
        marginLeft: tokens.spacingHorizontalS,
        marginTop: tokens.spacingVerticalXS,
        marginBottom: tokens.spacingVerticalXS,
        ...shorthands.gap(tokens.spacingHorizontalS),
    },
    singleLine: {
        ...shorthands.overflow('hidden'),
        lineHeight: '16px',
        display: '-webkit-box',
        WebkitLineClamp: 1,
        WebkitBoxOrient: 'vertical',
        width: '650px',
        fontSize: '12px',
    },
});

interface PlanStepCardProps {
    index: number;
    step: IPlan;
    setIsPlanDirty: React.Dispatch<React.SetStateAction<boolean>>;
    enableEdit: boolean;
}

export const PlanStepCard: React.FC<PlanStepCardProps> = ({ index, step, setIsPlanDirty, enableEdit }) => {
    const classes = useClasses();

    const numbersAsStrings = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
    const stepNumber = numbersAsStrings[index];

    return (
        <Card className={classes.card}>
            <div className={classes.flexRow}>
                <div className={classes.bar} />
                <div className={classes.flexColumn}>
                    <CardHeader
                        header={
                            <Body1>
                                <b className={classes.header}>Step {stepNumber} •</b> {step.skill}.{step.function}
                                <br />
                            </Body1>
                        }
                    />
                    {step.description && (
                        <div className={classes.singleLine}>
                            <Text weight="semibold">About: </Text> <Text>{step.description}</Text>
                        </div>
                    )}
                    {step.stepInputs.length > 0 && (
                        <div className={classes.inputs}>
                            <Text weight="semibold">Inputs: </Text>
                            {step.stepInputs.map((input: IPlanInput) => {
                                const onEditInput = (newValue: string) => {
                                    const inputIndex = step.stepInputs.findIndex(
                                        (element) => element.Key === input.Key,
                                    );
                                    step.stepInputs[inputIndex] = {
                                        Key: input.Key,
                                        Value: newValue,
                                    };
                                    setIsPlanDirty(true);
                                };
                                return (
                                    <PlanStepInput
                                        input={input}
                                        key={input.Key}
                                        onEdit={onEditInput}
                                        enableEdit={enableEdit}
                                    />
                                );
                            })}
                        </div>
                    )}
                    {step.stepOutputs.length > 0 && (
                        <div className={classes.inputs}>
                            <Text weight="semibold">Outputs: </Text>
                            {step.stepOutputs.map((output: string) => {
                                return (
                                    <Badge color="informative" shape="rounded" appearance="tint" key={output}>
                                        {output}
                                    </Badge>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </Card>
    );
};
