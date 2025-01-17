#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include "rp.h"
#include "rp_hw-profiles.h"

#define WAVEFORM1 RP_WAVEFORM_SQUARE
#define WAVEFORM2 RP_WAVEFORM_SINE
#define FILENAME_SIZE 100
#define FILEPATH_SIZE 200
#define FREQ 1000000

int DECIM = 1; // Default values
int BUFFER_SIZE = 16384;
int DELAY = 0;
int LOOPS_NUMBER = 64;
double TRIG_LVL = 

bool generateSignals()
{
    /* Reset Generation and */
    rp_GenReset();

    /* Generation */
    rp_GenSynchronise();

    rp_GenWaveform(RP_CH_1, WAVEFORM1);
    if(rp_GenFreq(RP_CH_1, FREQ) != RP_OK){
        fprintf(stdout,"Problem with generating at this freq! \n");
        return false;
    }
    rp_GenAmp(RP_CH_1, 0.5);

    rp_GenWaveform(RP_CH_2, WAVEFORM2);
    rp_GenFreq(RP_CH_2, FREQ);
    rp_GenAmp(RP_CH_2, 0.5);

    rp_GenOutEnableSync(true);
    if (rp_GenSynchronise() != RP_OK)
    {
        return false;
    }
    return true;
}

char *getFileNameOrPath(int type)
{
    time_t t = time(NULL);
    char date_time[FILENAME_SIZE];
    strftime(date_time, sizeof(date_time), "%Y_%m_%d_%H_%M_%S", localtime(&t));

    if (type == 1)
    {
        char *debugfile = malloc(FILENAME_SIZE * sizeof(char));
        sprintf(debugfile, "/tmp/DEBUG_%s.txt", date_time);
        return debugfile;
    }
    else if (type == 2)
    {
        char *filepath = malloc(FILEPATH_SIZE * sizeof(char));
        sprintf(filepath, "/tmp/CH1V_CH2V_%s.csv", date_time);
        return filepath;
    }

    return NULL;
}

int Acquisition(int decim, int buffer_size, int delay)
{
    clock_t start, end;
    double time_passed;

    FILE *fptr;
    FILE *data;
    char *debugLog = getFileNameOrPath(1);
    char *filepath = getFileNameOrPath(2);

    fptr = fopen(debugLog, "w+");

    if (filepath != NULL)
    {
        data = fopen(filepath, "w+");
    }
    if (fptr == NULL || data == NULL)
    {
        fprintf(stdout, "One of the files was not created \n");
        exit(1);
    }
    fprintf(data, "CH1V,CH2V\n");

    if (rp_Init() != RP_OK)
    {
        fprintf(fptr, "Rp api init failed! \n");
    }
    fprintf(fptr, "Rp api init success! \n");

    if (generateSignals() == false)
    {
        fprintf(fptr, "Signal generation failed");
        return -1;
    }
    fprintf(fptr, "Signals generated");

    float *buff1 = (float *)malloc(buffer_size * sizeof(float));
    float *buff2 = (float *)malloc(buffer_size * sizeof(float));
    fprintf(fptr, "Buffer allocated\n");

    rp_AcqReset();
    rp_SetEnableDaisyChainTrigSync(true);
    rp_SetEnableDiasyChainClockSync(true);
    rp_SetSourceTrigOutput(OUT_TR_ADC);
    rp_GenSetExtTriggerDebouncerUs(50000);
    rp_AcqSetDecimation(decim);
    rp_AcqSetTriggerLevel(RP_CH_1, 1.0);
    rp_AcqSetTriggerLevel(RP_CH_2, 1.0);
    fprintf(fptr, "Decimation set\n");
    
    rp_AcqSetTriggerDelay(delay);
    rp_AcqSetArmKeep(true);
    rp_AcqStart();
    fprintf(fptr, "Acquisition started\n");
    sleep(0.2);

    rp_AcqSetTriggerSrc(RP_TRIG_SRC_NOW);
    rp_acq_trig_state_t state = RP_TRIG_STATE_TRIGGERED;
    while (1)
    {
        rp_AcqGetTriggerState(&state);
        if (state == RP_TRIG_STATE_TRIGGERED)
        {
            fprintf(fptr, "\n ACQUSITION TRIGGERED \n");
            break;
        }
    }

    bool fillState = false;
    while (!fillState)
    {
        rp_AcqGetBufferFillState(&fillState);
    }
    fprintf(fptr, "\n Buffer filled \n");
    uint32_t pos = 0;
    fprintf(stdout, "Reading signals \n");

    rp_AcqGetWritePointerAtTrig(&pos);
    start = clock();
    for (int loop = 0; loop < LOOPS_NUMBER; loop++)
    {
        rp_AcqGetWritePointerAtTrig(&pos);

        rp_AcqGetDataV(RP_CH_1, &pos, &buffer_size, buff1);
        rp_AcqGetDataV(RP_CH_2, &pos, &buffer_size, buff2);

        fprintf(fptr, "\n Data acquired \n");
        for (int i = 0; i < buffer_size; i++)
        {
            fprintf(data, "%f,%f\n", buff1[i], buff2[i]);
        }
    }
    end = clock();

    time_passed = ((double)(end - start)) / CLOCKS_PER_SEC;
    fprintf(fptr, "\n Acquisition time: %f \n", time_passed);

    fflush(fptr);
    fflush(data);
    free(buff1);
    free(buff2);

    rp_Release();
    fprintf(stdout, "\n Memory freed \n");

    fclose(fptr);
    fclose(data);
    free(filepath);
    free(debugLog);

    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 5)
    {
        fprintf(stderr, "Usage: %s <decimation> <buffer_size> <delay> <loops_number>\n", argv[0]);
        return 1;
    }

    DECIM = atoi(argv[1]);
    BUFFER_SIZE = atoi(argv[2]);
    DELAY = atoi(argv[3]);
    LOOPS_NUMBER = atoi(argv[4]);

    return Acquisition(DECIM, BUFFER_SIZE, DELAY, LOOPS_NUMBER);
}
