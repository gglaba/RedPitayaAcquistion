#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include "rp.h"

#define WAVEFORM1 RP_WAVEFORM_SQUARE
#define WAVEFORM2 RP_WAVEFORM_SINE
#define FREQ 1000000
#define FILENAME_SIZE 100
#define FILEPATH_SIZE 200

int DECIM;
int BUFFER_SIZE;
int DELAY;
bool isLOCAL;

bool generateSignals() {
    rp_GenReset();
    rp_GenSynchronise();

    rp_GenWaveform(RP_CH_1, WAVEFORM1);
    rp_GenFreq(RP_CH_1, FREQ);
    rp_GenAmp(RP_CH_1, 0.5);

    rp_GenWaveform(RP_CH_2, WAVEFORM2);
    rp_GenFreq(RP_CH_2, FREQ);
    rp_GenAmp(RP_CH_2, 0.5);

    rp_GenOutEnableSync(true);
    return (rp_GenSynchronise() == RP_OK);
}

char *getFileNameOrPath(int type, bool isLocalAcq) {
    time_t t = time(NULL);
    char date_time[FILENAME_SIZE];
    strftime(date_time, sizeof(date_time), "%Y_%m_%d_%H_%M_%S", localtime(&t));
    const char *path = isLocalAcq ? "/mnt/share/" : "/tmp/";

    char *result = malloc(FILEPATH_SIZE * sizeof(char));
    if (type == 1)
        sprintf(result, "%sDEBUG_%s.txt", path, date_time);
    else
        sprintf(result, "%sCH1V_CH2V_%s.csv", path, date_time);
    return result;
}

void log_with_timestamp(FILE *fptr, const char *message) {
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    char time_str[20];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", t);
    fprintf(fptr, "[%s] %s\n", time_str, message);
    fflush(fptr);
}

int Acquisition(int decim, int buffer_size, int delay, bool isLocal) {
    FILE *fptr, *data;
    char *debugLog = getFileNameOrPath(1, isLocal);
    char *filepath = getFileNameOrPath(2, isLocal);
    fptr = fopen(debugLog, "w+");
    data = fopen(filepath, "w+");

    if (!fptr || !data) {
        fprintf(stderr, "Error creating log/data files.\n");
        return 1;
    }
    fprintf(data, "CH1V,CH2V\n");

    if (rp_Init() != RP_OK) {
        log_with_timestamp(fptr, "rp_Init failed");
        return 1;
    }
    log_with_timestamp(fptr, "rp_Init success");

    float *buff1 = malloc(buffer_size * sizeof(float));
    float *buff2 = malloc(buffer_size * sizeof(float));

    rp_AcqReset();
    rp_AcqSetGain(RP_CH_1, RP_HIGH);
    rp_AcqSetGain(RP_CH_2, RP_HIGH);

    // ✅ Daisy chain configuration
    rp_SetEnableDaisyChainTrigSync(true);
    rp_SetEnableDiasyChainClockSync(true);
    rp_SetSourceTrigOutput(OUT_TR_ADC);
    rp_GenSetExtTriggerDebouncerUs(50000);

    rp_AcqSetDecimation(decim);
    rp_AcqSetTriggerDelay(delay);
    rp_AcqSetArmKeep(false); // Only arm once per loop

    int sample_rate = 125000000 / decim;
    int total_samples = 10 * sample_rate;
    int loops = (total_samples + buffer_size - 1) / buffer_size;

    fprintf(fptr, "Sample rate: %d Hz\n", sample_rate);
    fprintf(fptr, "Loops needed: %d\n", loops);

    for (int loop = 0; loop < loops; loop++) {
        rp_AcqStart();
        usleep(100000);

        rp_AcqSetTriggerSrc(RP_TRIG_SRC_NOW);
        rp_acq_trig_state_t state;
        do {
            rp_AcqGetTriggerState(&state);
        } while (state != RP_TRIG_STATE_TRIGGERED);

        bool fillState = false;
        while (!fillState) {
            rp_AcqGetBufferFillState(&fillState);
        }

        uint32_t pos = 0;
        rp_AcqGetWritePointerAtTrig(&pos);

        uint32_t size = buffer_size;
        rp_AcqGetDataV(RP_CH_1, &pos, &size, buff1);
        rp_AcqGetDataV(RP_CH_2, &pos, &size, buff2);

        for (uint32_t i = 0; i < size; i++) {
            fprintf(data, "%f,%f\n", buff1[i], buff2[i]);
        }

        log_with_timestamp(fptr, "One loop data acquired");
    }

    rp_Release();
    free(buff1);
    free(buff2);
    fclose(fptr);
    fclose(data);
    free(filepath);
    free(debugLog);

    return 0;
}

int main(int argc, char **argv) {
    if (argc < 5) {
        fprintf(stderr, "Usage: %s <decimation> <buffer_size> <delay> <isLocal>\n", argv[0]);
        return 1;
    }

    DECIM = atoi(argv[1]);
    BUFFER_SIZE = atoi(argv[2]);
    DELAY = atoi(argv[3]);
    isLOCAL = (strcmp(argv[4], "True") == 0);

    return Acquisition(DECIM, BUFFER_SIZE, DELAY, isLOCAL);
}
