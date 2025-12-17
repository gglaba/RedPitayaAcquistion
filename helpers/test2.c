#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <sys/time.h>
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
        snprintf(filename, FILEPATH_SIZE, "%sCH1V_CH2V_%s.bin", path, date_time);
    return filename;
}

bool generateSignals() {
    // Make sure API initialized elsewhere or here:
    if (rp_Init() != RP_OK) {
        return false;
    }

    // Reset generator
    if (rp_GenReset() != RP_OK) {
        return false;
    }

    // Optional: set explicit continuous mode for both channels
    if (rp_GenMode(RP_CH_2, RP_GEN_MODE_CONTINUOUS) != RP_OK) return false;

    // Configure CH2
    if (rp_GenWaveform(RP_CH_2, RP_WAVEFORM_SINE) != RP_OK) return false;
    if (rp_GenFreq(RP_CH_2, 10000.0) != RP_OK) return false;
    if (rp_GenAmp(RP_CH_2, 4.0) != RP_OK) return false;
    if (rp_GenTriggerSource(RP_CH_2, RP_GEN_TRIG_SRC_INTERNAL) != RP_OK) return false;


    if (rp_GenOutEnable(RP_CH_2) != RP_OK) return false;

    return true;
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
        fclose(ctrl);
        if (strncmp(cmd, "STOP", 4) == 0) {
            log_with_timestamp(log, "STOP received.");
            return true;
        } else if (strncmp(cmd, "ABORT", 5) == 0) {
            log_with_timestamp(log, "ABORT received.");
            remove(filepath);
            remove(debugLog);
            return true;  // ABORT now means "stop and clean up in main"
        }
    }
    //fclose(ctrl);
    return false;
}

uint64_t current_time_ms() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)(tv.tv_sec * 1000 + tv.tv_usec / 1000);
}

int Acquisition(int decim, uint32_t buffer_size, int delay, int loops, bool isLocal) {
    if (buffer_size > MAX_BUFFER_SIZE) buffer_size = MAX_BUFFER_SIZE;

    char *logPath = getFileNameOrPath(1, isLocal);
    char *dataPath = getFileNameOrPath(2, isLocal);
    FILE *logFile = fopen(logPath, "w+");
    FILE *dataFile = fopen(dataPath, "wb");

    FILE *ctrl = fopen("/tmp/acq_control.txt", "w");
    if (ctrl) {
        fprintf(ctrl, "RUN");
        fclose(ctrl);
    }

    if (!logFile || !dataFile) {
        fprintf(stderr, "Failed to create output files.\n");
        return 1;
    }

    if (rp_Init() != RP_OK) {
        log_with_timestamp(logFile, "Red Pitaya init failed.");
        return 1;
    }

    if (!generateSignals()) {
        log_with_timestamp(logFile, "Signal generation failed.");
        rp_Release();
        return 1;
    }

    log_with_timestamp(logFile, "Red Pitaya initialized.");

    rp_AcqReset();
    rp_AcqSetGain(RP_CH_1, RP_HIGH);
    rp_AcqSetGain(RP_CH_2, RP_HIGH);
    rp_SetEnableDaisyChainTrigSync(true);
    rp_SetEnableDiasyChainClockSync(true);
    rp_SetSourceTrigOutput(OUT_TR_ADC);
    rp_AcqSetDecimation(decim);
    rp_AcqSetTriggerDelay(0);
    rp_AcqSetArmKeep(true);

    rp_AcqSetTriggerSrc(RP_TRIG_SRC_NOW);  // Edge-triggered
rp_AcqStart();
double Fs = 125e6 / (double)decim;
double wait_sec = (double)buffer_size / Fs;
unsigned int wait_us = (unsigned int)(wait_sec * 1e6);

if (wait_us < 1000) wait_us = 1000;

usleep(wait_us);

    fprintf(logFile, "Fs: %.2f Hz | Chunk size: %d | Loops: %d\n", Fs, buffer_size, loops);

    float *buff1 = malloc(buffer_size * sizeof(float));
    float *buff2 = malloc(buffer_size * sizeof(float));
    float *interleaved = malloc(buffer_size * 2 * sizeof(float));

    uint32_t total_samples = loops * buffer_size;
    uint32_t samples_captured = 0;
    uint32_t last_pos = 0;

    uint64_t last_check_time = current_time_ms();

    while (samples_captured < total_samples) {
        uint32_t wp;
        if (rp_AcqGetWritePointer(&wp) != RP_OK) {
            log_with_timestamp(logFile, "Failed to get write pointer.");
            continue;
        }

        uint32_t diff = (wp - last_pos + MAX_BUFFER_SIZE) % MAX_BUFFER_SIZE;
        char buf[100];
        snprintf(buf, sizeof(buf), "WP: %u, Last: %u, Diff: %u", wp, last_pos, diff);
        log_with_timestamp(logFile, buf);

        uint64_t now = current_time_ms();

        if (diff >= buffer_size || (now - last_check_time > 100 && diff > 0)) {
            uint32_t size = (diff >= buffer_size) ? buffer_size : diff;
            uint32_t start = last_pos;

            if (rp_AcqGetDataV(RP_CH_1, start, &size, buff1) != RP_OK ||
                rp_AcqGetDataV(RP_CH_2, start, &size, buff2) != RP_OK) {
                log_with_timestamp(logFile, "Data acquisition failed.");
                continue;
            }

            for (uint32_t j = 0; j < size; j++) {
                interleaved[2 * j]     = buff1[j];
                interleaved[2 * j + 1] = buff2[j];
            }

            fwrite(interleaved, sizeof(float), size * 2, dataFile);
            fflush(dataFile);

            last_pos = (last_pos + size) % MAX_BUFFER_SIZE;
            samples_captured += size;

            fprintf(logFile, "Written %u samples (%.1f%%)\n", samples_captured, 100.0 * samples_captured / total_samples);
            fflush(logFile);

            if (check_control_signal(logFile, dataPath, logPath)) {
    break;
}

            last_check_time = now;
        }

        usleep(100);
    }

    log_with_timestamp(logFile, "Acquisition completed.");
    free(buff1);
    free(buff2);
    free(interleaved);
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
    int delay = atoi(argv[3]);  // ignored in continuous mode
    int loops = atoi(argv[4]);
    bool isLocal = (strcmp(argv[5], "True") == 0);

    return Acquisition(decim, buffer_size, delay, loops, isLocal);
}