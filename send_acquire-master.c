#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include "rp.h"
#include "rp_hw-profiles.h"

#define FILENAME_SIZE 100
#define FILEPATH_SIZE 200

int DECIM;
int BUFFER_SIZE;
int DELAY;
int LOOPS_NUMBER;
bool isLOCAL;

char *getFileNameOrPath(int type,bool isLocalAcq)
{
    time_t t = time(NULL);
    char date_time[FILENAME_SIZE];
    strftime(date_time, sizeof(date_time), "%Y_%m_%d_%H_%M_%S", localtime(&t));
    const char *path_local = "/tmp/";
    const char *path_remote = "/mnt/share/";
    const char *path = NULL;
    if(isLocalAcq == false){
        path = path_local;
    }
    else{
        path = path_remote;
    }

    printf("isLocal: %d\n", isLocalAcq);
    printf("path: %s\n", path);

    if (type == 1)
    {
        char *debugfile = malloc(FILENAME_SIZE * sizeof(char));
        sprintf(debugfile, "%sDEBUG_%s.txt",path, date_time);
        return debugfile;
    }
    else if (type == 2)
    {
        char *filepath = malloc(FILEPATH_SIZE * sizeof(char));
        sprintf(filepath, "%sCH1V_CH2V_%s.csv", path,date_time);
        return filepath;
    }

    return NULL;
}

void log_with_timestamp(FILE *fptr, const char *message) {
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    char time_str[20];
    
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", t);
    fprintf(fptr, "[%s] %s\n", time_str, message);
    fflush(fptr);
}

int Acquisition(int decim, int buffer_size, int delay,int loops_number, bool isLocal)
{
    clock_t start, end;
    double time_passed;

    FILE *fptr;
    FILE *data;
    char *debugLog = getFileNameOrPath(1,isLocal);
    char *filepath = getFileNameOrPath(2,isLocal);

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
        log_with_timestamp(fptr, "Rp api init failed! \n");
    }
    log_with_timestamp(fptr, "Rp api init success! \n");

    float *buff1 = (float *)malloc(buffer_size * sizeof(float));
    float *buff2 = (float *)malloc(buffer_size * sizeof(float));
    log_with_timestamp(fptr, "Buffer allocated\n");

    fprintf(fptr, "Decimation: %d\n", decim);
    fprintf(fptr, "Buffer size: %d\n", buffer_size);
    fprintf(fptr, "Delay: %d\n", delay);
    fprintf(fptr, "Loops number: %d\n", loops_number);


    rp_AcqReset();
    rp_AcqSetGain(RP_CH_1, RP_HIGH);
    rp_AcqSetGain(RP_CH_2, RP_HIGH);
    rp_SetEnableDaisyChainTrigSync(true);
    rp_SetEnableDiasyChainClockSync(true);
    rp_SetSourceTrigOutput(OUT_TR_ADC);
    rp_GenSetExtTriggerDebouncerUs(50000);
    rp_AcqSetDecimation(decim);
    log_with_timestamp(fptr, "Decimation set\n");

    
    rp_AcqSetTriggerDelay(delay);
    rp_AcqSetArmKeep(true);
    rp_AcqStart();
    log_with_timestamp(fptr, "Acquisition started\n");
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
    log_with_timestamp(fptr, "\n Buffer filled \n");
    uint32_t pos = 0;
    log_with_timestamp(stdout, "Reading signals \n");

    rp_AcqGetWritePointerAtTrig(&pos);
    start = clock();
    for (int loop = 0; loop < loops_number; loop++)
    {
        rp_AcqGetWritePointerAtTrig(&pos);

        rp_AcqGetDataV(RP_CH_1, &pos, &buffer_size, buff1);
        rp_AcqGetDataV(RP_CH_2, &pos, &buffer_size, buff2);

        log_with_timestamp(fptr, "\n Data acquired \n");
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
    log_with_timestamp(stdout, "\n Memory freed \n");

    fclose(fptr);
    fclose(data);
    free(filepath);
    free(debugLog);

    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 6)
    {
        fprintf(stderr, "Usage: %s <decimation> <buffer_size> <delay> <loops_number> <isLocal>\n", argv[0]);
        return 1;
    }

    DECIM = atoi(argv[1]);
    BUFFER_SIZE = atoi(argv[2]);
    DELAY = atoi(argv[3]);
    LOOPS_NUMBER = atoi(argv[4]);
    isLOCAL = (strcmp(argv[5], "True") == 0);

    return Acquisition(DECIM, BUFFER_SIZE, DELAY, LOOPS_NUMBER,isLOCAL);
}
