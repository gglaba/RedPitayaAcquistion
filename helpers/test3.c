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
if (!logFile || !dataFile) {
    fprintf(stderr, "Failed to create output files.\n");
    return 1;
}

// init
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

// Acquisition configuration (must be set before rp_AcqStart)
rp_AcqReset();
rp_AcqSetGain(RP_CH_1, RP_HIGH);
rp_AcqSetGain(RP_CH_2, RP_HIGH);

// If using daisy-chain / sync
rp_SetEnableDaisyChainTrigSync(true);
rp_SetEnableDiasyChainClockSync(true);
rp_SetSourceTrigOutput(OUT_TR_ADC);

rp_AcqSetDecimation(decim);
rp_AcqSetTriggerDelay(0);
rp_AcqSetArmKeep(true);

// Start acquisition (continuous ring buffer). Use NOW for continuous.
rp_AcqSetTriggerSrc(RP_TRIG_SRC_NOW);
if (rp_AcqStart() != RP_OK) {
    log_with_timestamp(logFile, "rp_AcqStart failed.");
    rp_Release();
    return 1;
}

// compute sampling frequency and buffer time
double Fs = 125e6 / (double)decim;
double chunk_time_sec = (double)buffer_size / Fs;
if (chunk_time_sec < 0.00001) chunk_time_sec = 0.00001; // safety
unsigned int sleep_between_checks_us = (unsigned int)(chunk_time_sec * 1e6 / 2.0); // check halfway
if (sleep_between_checks_us < 500) sleep_between_checks_us = 500;

fprintf(logFile, "Fs: %.2f Hz | Chunk size: %u | chunk time: %.6f s\n", Fs, buffer_size, chunk_time_sec);

// Allocate buffers: use fBuffer from API if available, otherwise malloc
float *buff1 = (float*)malloc(buffer_size * sizeof(float));
float *buff2 = (float*)malloc(buffer_size * sizeof(float));
float *interleaved = (float*)malloc(buffer_size * 2 * sizeof(float));
if (!buff1 || !buff2 || !interleaved) {
    log_with_timestamp(logFile, "Buffer allocation failed.");
    rp_Release();
    return 1;
}

uint32_t total_samples = loops * buffer_size;
uint32_t samples_captured = 0;

// For robust reading use GetOldestDataV which returns the oldest contiguous block (OS >= 2.00)
// Fallback: use GetDataV with computed start position if necessary.
while (samples_captured < total_samples) {
    // Wait for buffer to fill at least buffer_size samples
    bool fillState = false;
    rp_AcqGetBufferFillState(&fillState);
    if (!fillState) {
        // If not enough to fill whole buffer, sleep less aggressively
        usleep(sleep_between_checks_us);
        // also check control file periodically
        if ((samples_captured % (buffer_size*10)) == 0) {
            if (check_control_signal(logFile, dataPath, logPath)) break;
        }
        continue;
    }

    // Get how many samples are currently available in the buffer (write pointer)
    uint32_t wp = 0;
    if (rp_AcqGetWritePointer(&wp) != RP_OK) {
        log_with_timestamp(logFile, "Failed to get write pointer.");
        usleep(sleep_between_checks_us);
        continue;
    }

    // rp_AcqGetOldestDataV will return up to buffer_size samples from the oldest data in buffer
    uint32_t size = buffer_size;
    if (rp_AcqGetOldestDataV(RP_CH_1, &size, buff1) != RP_OK) {
        log_with_timestamp(logFile, "rp_AcqGetOldestDataV CH1 failed.");
        usleep(sleep_between_checks_us);
        continue;
    }
    uint32_t size2 = size;
    if (rp_AcqGetOldestDataV(RP_CH_2, &size2, buff2) != RP_OK || size2 != size) {
        log_with_timestamp(logFile, "rp_AcqGetOldestDataV CH2 mismatch or failed.");
        usleep(sleep_between_checks_us);
        continue;
    }

    // Interleave and write
    for (uint32_t j = 0; j < size; ++j) {
        interleaved[2*j] = buff1[j];
        interleaved[2*j + 1] = buff2[j];
    }

    fwrite(interleaved, sizeof(float), size * 2, dataFile);
    fflush(dataFile);

    samples_captured += size;
    char msg[128];
    snprintf(msg, sizeof(msg), "Captured %u / %u samples (%.2f%%)", samples_captured, total_samples, 100.0 * samples_captured / total_samples);
    log_with_timestamp(logFile, msg);

    // check control signal
    if (check_control_signal(logFile, dataPath, logPath)) {
        break;
    }

    // small sleep to let hardware refill
    usleep(sleep_between_checks_us);
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