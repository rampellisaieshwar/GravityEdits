export const formatDuration = (seconds: number): string => {
    const rounded = Math.round(seconds);
    if (rounded < 60) {
        return `${rounded}s`;
    }
    const minutes = Math.floor(rounded / 60);
    const remainingSeconds = rounded % 60;

    if (remainingSeconds === 0) {
        return `${minutes}m`;
    }
    return `${minutes}m ${remainingSeconds}s`;
};
