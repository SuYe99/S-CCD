#ifndef CCD_H
#define CCD_H
#include <stdbool.h>
#include "output.h"
// #include <xgboost/c_api.h>

int preprocessing
(
    short int** buf,            /* I/O:  pixel-based time series  */
    short int* fmask_buf,        /* I:   mask time series  */
    int *valid_num_scenes, /* I/O: * number of scenes after cfmask counts and  */
    int *id_range,
    int *clear_sum,      /* I/O: Total number of clear cfmask pixels          */
    int *water_sum,      /* I/O: counter for cfmask water pixels.             */
    int *shadow_sum,     /* I/O: counter for cfmask shadow pixels.            */
    int *sn_sum,         /* I/O: Total number of snow cfmask pixels           */
    int *cloud_sum      /* I/O: counter for cfmask cloud pixels.             */
);

int ccd
(
    short int **buf,            /* I/O:  pixel-based time series           */
    short int *fmask_buf,       /* I:  mask-based time series              */
    int *valid_date_array,      /* I: valid date time series               */
    int valid_num_scenes,       /* I: number of valid scenes under cfmask fill counts  */
    Output_t *rec_cg,           /* O: outputted structure for CCDC results    */
    int *num_fc,                /* O: number of fitting curves                       */
    int num_samples,            /* I: column number per scanline                    */
    int col_pos,                /* I: column position of current processing pixel   */
    int row_pos,                /* I:raw position of current processing pixel */
    double probability_threshold
);


int stand_procedure
(
    int num_scenes,             /* I:  number of scenes  */
    int *date_array,            /* I: valid date time series  */
    short int **buf,            /* I:  pixel-based time series  */
    short int *fmask_buf,       /* I:  mask-based time series  */
    int *id_range,
    Output_t *rec_cg,            /* O: CCDC result as recorded */
    int *num_curve,                   /* Intialize NUM of Functional Curves    */
    double probability_threshold
);

int inefficientobs_procedure
(
    int num_scenes,             /* I:  number of scenes  */
    int *date_array,            /* I: valid date time series  */
    short int **buf,            /* I:  pixel-based time series  */
    short int *fmask_buf,       /* I:  mask-based time series  */
    int *id_range,              /* I:  ids to check valid values  */
    double sn_pct,               /* I:  mask-based time series  */
    Output_t *rec_cg,           /* O: outputed records for CCDC results */
    int *num_curve                   /* O: Intialize NUM of Functional Curves    */
);

//int main(int argc, char *argv[]);
extern int sccd_executor(
    int mode,
    char* in_path,
    char* out_path,
    int n_cores,
    int row,
    int col,
    int METHOD,
    char* mask_path,
    double probability_threshold,
    int min_days_conse,
    int output_mode,
    int verbose,
    int training_type, /* for training process*/
    int monitorwindow_lowerlin, /* for training process*/
    int monitorwindow_upperlim, /* for training process*/
    int bandselection_bit,
    char* classification_config
);

#endif // CCD_H
