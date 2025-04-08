#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include <stdbool.h>
#include "rp.h"

#define FILENAME_SIZE 100
#define FILEPATH_SIZE 200
#define MAX_BUFFER_SIZE 16384

char *getFileNameOrPath(int type, bool isLocal) {
    time_t t = time(NULL);
    char date_time[FILENAME_SIZE];
    strftime(date_time, sizeof(date_time), "%Y_%m_%d_%H_%M_%S", localtime(&t));

    const char *path = isLocal ? "/mnt/share/" : "/tmp/";

    char *filename = malloc(FILEPATH_SIZE);
    if (type == 1)
        snprintf(filename, FILEPATH_SIZE, "%sDEBUG_%s.txt", path, date_time);
    else
        snprintf(filename, FILEPATH_SIZE, "%sCH1V_CH2V_%s.csv", path, date_time);
    return filename;
}

void log_with_timestamp(FILE *fptr, const char *message) {
    time_t now = time(NULL);
    char time_str[20];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", localtime(&now));
    fprintf(fptr, "[%s] %s\n", time_str, message);
    fflush(fptr);
}

bool check_control_signal(FILE *log, const char *filepath, const char *debugLog) {
    FILE *ctrl = fopen("/tmp/acq_control.txt", "r");
    if (!ctrl) return false;
    char cmd[16];
    if (fgets(cmd, sizeof(cmd), ctrl)) {
        if (strncmp(cmd, "STOP", 4) == 0) {
            log_with_timestamp(log, "STOP");
            fclose(ctrl);
            return true;
        } else if (strncmp(cmd, "ABORT", 5) == 0) {
            log_with_timestamp(log, "ABORT");
            fclose(ctrl);
            remove(filepath);
            remove(debugLog);
            exit(0);
        }
    }
    fclose(ctrl);
    return false;
}

int Acquisition(int decim, uint32_t buffer_size, int delay, int loops, bool isLocal) {
    if (buffer_size > MAX_BUFFER_SIZE) buffer_size = MAX_BUFFER_SIZE;

    FILE *logFile, *dataFile;
    char *logPath = getFileNameOrPath(1, isLocal);
    char *dataPath = getFileNameOrPath(2, isLocal);

    logFile = fopen(logPath, "w+");
    dataFile = fopen(dataPath, "w+");

    FILE *ctrl = fopen("/tmp/acq_control.txt", "w");
    if (ctrl) {
       fprintf(ctrl, "RUN");
       fclose(ctrl);}

    if (!logFile || !dataFile) {
        fprintf(stderr, "Failed to create output files.\n");
        exit(1);
    }

    if (rp_Init() != RP_OK) {
        log_with_timestamp(logFile, "Red Pitaya init failed.");
        exit(1);
    }
    log_with_timestamp(logFile, "Red Pitaya init successful.");

    float *buff1 = malloc(buffer_size * sizeof(float));
    float *buff2 = malloc(buffer_size * sizeof(float));

    if (!buff1 || !buff2) {
        log_with_timestamp(logFile, "Buffer allocation failed.");
        exit(1);
    }

    rp_AcqReset();
    rp_AcqSetGain(RP_CH_1, RP_HIGH);
    rp_AcqSetGain(RP_CH_2, RP_HIGH);

    rp_SetEnableDaisyChainTrigSync(true);
    rp_SetEnableDiasyChainClockSync(true);

    rp_AcqSetDecimation(decim);
    rp_AcqSetTriggerDelay(0);
    rp_AcqSetArmKeep(true);
    rp_AcqSetTriggerSrc(RP_TRIG_SRC_EXT_PE);  // Wait for external trigger from master

    double Fs = 125e6 / (double)decim;
    double expected_time = (double)buffer_size / Fs;

    fprintf(logFile, "Fs: %.2f Hz | Buffer: %u samples | Wait: %.3f s | Loops: %d\n",
            Fs, buffer_size, expected_time, loops);
    fprintf(dataFile, "CH1V,CH2V\n");

    for (int i = 0; i < loops; i++) {
        rp_AcqStart();

        // Wait for trigger from master
        rp_acq_trig_state_t state = RP_TRIG_STATE_WAITING;
        while (state != RP_TRIG_STATE_TRIGGERED) {
            rp_AcqGetTriggerState(&state);
        }

        usleep(expected_time * 1e6);  // Wait for data to fill buffer

        uint32_t pos;
        rp_AcqGetWritePointer(&pos);
        uint32_t start = (pos + MAX_BUFFER_SIZE - buffer_size) % MAX_BUFFER_SIZE;
        uint32_t size = buffer_size;

        if (rp_AcqGetDataV(RP_CH_1, start, &size, buff1) != RP_OK ||
            rp_AcqGetDataV(RP_CH_2, start, &size, buff2) != RP_OK) {
            log_with_timestamp(logFile, "Data acquisition failed.");
            continue;
        }

        for (uint32_t j = 0; j < size; j++) {
            fprintf(dataFile, "%f,%f\n", buff1[j], buff2[j]);
        }

        fprintf(logFile, "Loop %d completed\n", i + 1);
        usleep(delay * 1000);  // Optional delay
        if (check_control_signal(logFile, dataPath, logPath)) break;
    }

    free(buff1);
    free(buff2);
    rp_Release();

    fclose(logFile);
    fclose(dataFile);
    free(logPath);
    free(dataPath);

    return 0;
}

int main(int argc, char **argv) {
    if (argc < 6) {
        fprintf(stderr, "Usage: %s <decimation> <buffer_size> <delay_ms> <loops> <isLocal>\n", argv[0]);
        return 1;
    }

    int decim = atoi(argv[1]);
    uint32_t buffer_size = atoi(argv[2]);
    int delay = atoi(argv[3]);
    int loops = atoi(argv[4]);
    bool isLocal = (strcmp(argv[5], "True") == 0);

    // Reset control file before starting
    FILE *ctrl = fopen("/tmp/acq_control.txt", "w");
    if (ctrl) {
        fprintf(ctrl, "RUN");
        fclose(ctrl);
    }

    return Acquisition(decim, buffer_size, delay, loops, isLocal);
}
