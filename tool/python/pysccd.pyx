from libc.stdlib cimport malloc
from libc.string cimport strcpy, strlen

cdef extern from "../../cold.h":
    cdef int sccd_executor(int mode, char* in_path, char* out_path, \
    int n_cores, int row, int col, int method, \
    char* mask_path, double probability_threshold, \
    int min_days_conse, int output_mode, int verbose, \
    int training_type, int monitorwindow_lowerlim, int monitorwindow_upperlim, \
    int bandselection_bit, char* classification_config);

def py_sccd(mode, in_path, out_path, row, col, method, bandselection_bit, mask_path, probability_threshold=0.95, \
            min_days_conse=80, n_cores=1, output_mode=0, verbose=0, training_type=0, monitorwindow_lowerlim=0, \
            monitorwindow_upperlim=0, classification_config=b'None') -> int:
    ret = sccd_executor(mode, \
                        in_path, \
                        out_path, \
                        n_cores, \
                        row, \
                        col, \
                        method, \
                        mask_path, \
                        probability_threshold, \
                        min_days_conse, \
                        output_mode, \
                        verbose, \
                        training_type, \
                        monitorwindow_lowerlim, \
                        monitorwindow_upperlim, \
                        bandselection_bit, \
                        classification_config)
    return ret
