#include <string.h>
#include <stdarg.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/timeb.h>
#include <sys/time.h>
#include <omp.h>
#include <stdbool.h>
#include <unistd.h>
#include "defines.h"
#include "cold.h"
#include "const.h"
#include "utilities.h"
#include "2d_array.h"
#include "input.h"
#include "output.h"
#include "misc.h"
#include "s_ccd.h"

int main(int argc, char *argv[])
//int sccd_executor(
//    int mode,
//    char* in_path,
//    char* out_path,
//    int n_cores,
//    int row,
//    int col,
//    int METHOD,
//    char* mask_path,
//    double probability_threshold,
//    int min_days_conse,
//    int output_mode,
//    int verbose,
//    int training_type, /* for training process*/
//    int monitorwindow_lowerlin, /* for training process*/
//    int monitorwindow_upperlim, /* for training process*/
//    int bandselection_bit,
//    char* classification_config /* classification config file */
//)
{

    /* inputted argument, exe mode */
    int mode;                           /* CCD detection mode
                                        3: whole images; 1: pixel-based;
                                        2: scanline-based*/
    char in_path[MAX_STR_LEN];
    char out_path[MAX_STR_LEN];
    int n_cores;
    int row;
    int col;
    int METHOD;
    char mask_path[MAX_STR_LEN];
    int min_days_conse;
    double probability_threshold;
    int output_mode;
    bool verbose = TRUE;
    bool b_fastmode;
    bool b_outputCSV;           /* output point-based time series csv, only for debug   */
    int training_type; /* for training process*/
    int monitorwindow_lowerlin; /* for training process*/
    int monitorwindow_upperlim; /* for training process*/
    int bandselection_bit;
    char classification_config[MAX_STR_LEN];

    /* need to comment out for exe */
/*    bool b_fastmode;
    bool b_outputCSV; */          /* output point-based time series csv, only for debug   */
    if(output_mode % 10 == 1)
        b_fastmode = FALSE;
    else
        b_fastmode = TRUE;

    if(output_mode / 10 == 1)
        b_outputCSV = TRUE;
    else
        b_outputCSV = FALSE;
    /* need to comment out for exe */


    char pointTS_output_dir[MAX_STR_LEN]; /* output point-based time series csv, only for debug   */
    char scene_list_filename[] = "scene_list.txt"; /* file name containing list of input sceneIDs */
    FILE *fd, *fdoutput;
    char msg_str[MAX_STR_LEN];       /* Input data scene name                 */
    int i, j;                           /* Loop counters                         */
    char scene_list_directory[MAX_STR_LEN]; /* full directory of scene list*/
    int status;                      /* Return value from function call       */
    char FUNC_NAME[] = "main";       /* For printing error messages           */

    int *sdate;                      /* Pointer to list of acquisition dates  */
    char **scene_list;                /* 2-D array for list of scene IDs       */

    int num_scenes;                  /* Number of input scenes defined        */
    Input_meta_t *meta;              /* Structure for ENVI metadata hdr info  */
    char tmpstr[MAX_STR_LEN];        /* char string for text manipulation      */

    time_t now;                  /* For logging the start, stop, and some     */
    int result;

    short int **buf;                      /* This is the image bands buffer, valid pixel only*/
    int *valid_date_array;             /* Sdate array after cfmask filtering    */
    short int *fmask_buf;              /* fmask buf, valid pixels only*/
    short int *sensor_buf;
    FILE **fp_bip;                     /* Array of file pointers of BIP files    */
    char **valid_scene_list = NULL;    /* 2-D array for list of filtered        */
    int valid_scene_count = 0;         /* x/y location specified is not valid be-   */
    int num_fc;                        /* the number of functional curve        */
    char* in_filename;
    char* in_filename_tmp;
    char out_fullpath[MAX_STR_LEN];    /* the full path for storing pixel-based CCDC result */
    char out_filename[MAX_STR_LEN];
    char out_csvname[MAX_STR_LEN];

    Output_t_sccd*  s_rec_cg;                 /* S-CCDC outputted recorded  */
    Output_t*  rec_cg;                 /* CCDC outputted recorded  */
    int block_num;
    //block_num = (int)meta->lines / threads;
    long ms_start = getMicrotime();
    long ms_end;
    char states_output_dir[MAX_STR_LEN];
    FILE *sampleFile;
    int pixel_qa;
    const char sep = '/';
    int row_count = 0;
    char* csv_row;
    //int variable_count = 0;
    int n_focus_variable = 0;
    int n_total_variable = TOTAL_IMAGE_BANDS;
    int focus_blist[TOTAL_IMAGE_BANDS + TOTAL_INDICES] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    bool NDVI_INCLUDED = FALSE;
    bool NBR_INCLUDED = FALSE;
    bool RGI_INCLUDED = FALSE;
    bool TCTWETNESS_INCLUDED = FALSE;
    bool TCTGREENNESS_INCLUDED = FALSE;
    bool EVI_INCLUDED = FALSE;
    bool DI_INCLUDED = FALSE;
    bool NDMI_INCLUDED = FALSE;
//    double TCBRI;
//    double TCWET;
//    double TCGRE;
    bool b_landspecific_mode = FALSE;
//    char *xgboost_model_path[MAX_STR_LEN];
    char auxiliary_var_path[MAX_STR_LEN];
    short int auxval = 0;
    char maskval;
    int category;
//    BoosterHandle booster;
//    DMatrixHandle eval_dmats[] = {};

    /**************************************************************/
    /*                                                            */
    /*   record the start time of just the CDCD         */
    /*     algorithm.  Up until here, it has all just been        */
    /*     setting it up......                                    */
    /*                                                             */
    /**************************************************************/
    time (&now);                 /*     intermediate times.                   */
    snprintf (msg_str, sizeof(msg_str), "CCDC start_time=%s\n", ctime (&now));
    if (verbose == TRUE)
        LOG_MESSAGE (msg_str, FUNC_NAME);

    //printf("nonono");

    /**************************************************************/
    /*                                                            */
    /*   read CCD variable                                        */
    /*                                                            */
    /**************************************************************/
    /* need to recover for exe */
    result = get_variables(argc, argv, &mode, in_path, out_path, &n_cores,
                           &row, &col, &METHOD, mask_path, &probability_threshold,
                           &min_days_conse, &b_fastmode, &b_outputCSV, &training_type,
                           &monitorwindow_lowerlin, &monitorwindow_upperlim, &bandselection_bit,
                           &classification_config);
    /* need to recover for exe */

//    result = get_args(argc, argv, &mode, in_path, out_path, &n_cores, &row,
//                      &col, &METHOD, mask_path, &probability_threshold,
//                      &min_days_conse, &b_fastmode, &output_mode);

    if (METHOD == 3) /*the mode combining classification and change detection*/
    {
        // reset METHOD to be sccd, currently only support sccd
//        METHOD = 2;
//        b_landspecific_mode = TRUE;
//        status = get_classificationconfig(classification_config, xgboost_model_path, &specific_label, auxiliary_var_path);
//        if(status != SUCCESS)
//            RETURN_ERROR("Fails to retrieve info from classification_config file", FUNC_NAME, FAILURE);

//        DMatrixHandle eval_dmats[] = {};
//        safe_xgboost(XGBoosterCreate(eval_dmats, 0, &booster));
//        safe_xgboost(XGBoosterLoadModel(booster, xgboost_model_path));
    }
    else{
        // initialized an empty boost

//        DMatrixHandle eval_dmats[] = {};
//        safe_xgboost(XGBoosterCreate(eval_dmats, 0, &booster));
    }
    if (mode < 4)
    {
        sprintf(scene_list_directory, "%s/%s", in_path, scene_list_filename);


        if (access(scene_list_directory, F_OK) != 0) /* File does not exist */
        {
//            if (format == ENVI_FORMAT){
                status = create_scene_list(in_path, &num_scenes, scene_list_filename);
                if(status != SUCCESS)
                    RETURN_ERROR("Running create_scene_list file", FUNC_NAME, FAILURE);
//            }
//            else{
//                RETURN_ERROR("Couldn't find scene list file for tiff Landsat format", FUNC_NAME, FAILURE);
//            }

        }
        else
        {
            num_scenes = MAX_SCENE_LIST;
        }

        /**************************************************************/
        /*                                                            */
        /* Fill the scene list array with full path names.            */
        /*                                                            */
        /**************************************************************/
        fd = fopen(scene_list_directory, "r");
        if (fd == NULL)
        {
            RETURN_ERROR("Opening scene_list file", FUNC_NAME, FAILURE);
        }

        scene_list = (char **) allocate_2d_array (MAX_SCENE_LIST, ARD_STR_LEN,
                                                         sizeof (char));
        for (i = 0; i < num_scenes; i++)
        {
            if (fscanf(fd, "%s", tmpstr) == EOF)
                break;
            strcpy(scene_list[i], tmpstr);
        }

        num_scenes = i;

        fclose(fd);
    }
    else
        num_scenes = MAX_SCENE_LIST;

   // printf("num_scenes finished = %d\n", num_scenes);


    sdate = malloc(num_scenes * sizeof(int));

    if (sdate == NULL)
    {
        RETURN_ERROR("ERROR allocating sdate memory", FUNC_NAME, FAILURE);
    }

    /**************************************************************/
    /*                                                            */
    /* Now that we know the actual number of scenes, allocate     */
    /* memory for date array.                                     */
    /*                                                            */
    /**************************************************************/
    if (mode  < 4)
    {
        /**************************************************************/
        /*                                                            */
        /* Sort scene_list based on year & julian_day, then do the    */
        /* swath filter, but read it above first.                     */
        /*                                                            */
        /**************************************************************/
        //printf("sort started\n");
        status = sort_scene_based_on_year_doy_row(scene_list, num_scenes, sdate, 2);
        if (status != SUCCESS)
        {
            RETURN_ERROR ("Calling sort_scene_based_on_year_jday",
                          FUNC_NAME, FAILURE);
        }
    }
    //printf("sort finished\n");
    //save_scene_list(scene_list_directory, num_scenes, scene_list);
    meta = (Input_meta_t *)malloc(sizeof(Input_meta_t));

    if (mode < 4)
    {
//        if(format == ENVI_FORMAT){
            status = read_envi_header(in_path, scene_list[0], meta);
            if (status != SUCCESS)
            {
               RETURN_ERROR ("Calling read_envi_header",
                                  FUNC_NAME, FAILURE);
            }
//        }else if(format == TIFF_FORMAT){
//            status = read_tif_header(in_path, scene_list[0], meta);
//            if (status != SUCCESS)
//            {
//               RETURN_ERROR ("Calling read_envi_header",
//                                  FUNC_NAME, FAILURE);
//            }
//        }

    }
    //int bandselection_bit;

    for(i = 0; i < TOTAL_IMAGE_BANDS + TOTAL_INDICES; i++)
    {
        if (checkbit(bandselection_bit, i))
        {
            if(i > NDVI_INDEX - 1)
            {
                if (i == NDVI_INDEX)
                {
                    NDVI_INCLUDED = TRUE;
                    focus_blist[n_focus_variable] = n_total_variable;
                    n_total_variable = n_total_variable + 1;
                    n_focus_variable = n_focus_variable + 1;
                }
                else if (i == NBR_INDEX)
                {
                    NBR_INCLUDED = TRUE;
                    focus_blist[n_focus_variable] = n_total_variable;
                    n_total_variable = n_total_variable + 1;
                    n_focus_variable = n_focus_variable + 1;
                }
                else if (i == RGI_INDEX)
                {
                    RGI_INCLUDED =TRUE;
                    focus_blist[n_focus_variable] = n_total_variable;
                    n_total_variable = n_total_variable + 1;
                    n_focus_variable = n_focus_variable + 1;
                }
                else if (i == TCTWETNESS_INDEX)
                {
                    TCTWETNESS_INCLUDED = TRUE;
                    focus_blist[n_focus_variable] = n_total_variable;
                    n_total_variable = n_total_variable + 1;
                    n_focus_variable = n_focus_variable + 1;
                }
                else if (i == TCTGREENNESS_INDEX)
                {
                    TCTGREENNESS_INCLUDED = TRUE;
                    focus_blist[n_focus_variable] = n_total_variable;
                    n_total_variable = n_total_variable + 1;
                    n_focus_variable = n_focus_variable + 1;
                }
                else if (i == EVI_INDEX){
                    EVI_INCLUDED = TRUE;
                    focus_blist[n_focus_variable] = n_total_variable;
                    n_total_variable = n_total_variable + 1;
                    n_focus_variable = n_focus_variable + 1;
                }
                else if (i == DI_INDEX){
                    DI_INCLUDED = TRUE;
                    focus_blist[n_focus_variable] = n_total_variable;
                    n_total_variable = n_total_variable + 1;
                    n_focus_variable = n_focus_variable + 1;
                }
                else if (i == NDMI_INDEX)
                {
                    NDMI_INCLUDED = TRUE;
                    focus_blist[n_focus_variable] = n_total_variable;
                    n_total_variable = n_total_variable + 1;
                    n_focus_variable = n_focus_variable + 1;
                }
//                focus_blist[n_focus_variable] = n_total_variable;
//                n_total_variable = n_total_variable + 1;
            }
            else{
                focus_blist[n_focus_variable] = i;
                n_focus_variable = n_focus_variable + 1;
            }
            //n_focus_variable = n_focus_variable + 1;
        }
    }

    /* pixel-based detection */
    if(mode == 1)
    {
        // ms_start = getMicrotime();
        num_fc = 0;

        buf = (short int **) allocate_2d_array (TOTAL_IMAGE_BANDS, num_scenes, sizeof (short int));
        valid_scene_list = (char **) allocate_2d_array (num_scenes, MAX_STR_LEN,
                                             sizeof (char));

        valid_date_array = (int*) malloc(num_scenes * sizeof(int));
        fmask_buf = (short int *) malloc(num_scenes * sizeof(short int));
        sensor_buf = (short int *) malloc(num_scenes * sizeof(short int));
        /* temporally hard-coded*/

        fp_bip = (FILE **)malloc(num_scenes * sizeof (FILE*));
        if (fp_bip == NULL)
        {
            RETURN_ERROR ("Allocating fp_bip memory", FUNC_NAME, FAILURE);
        }

        /*******************************************************/
        /******************* meta data result path ************/
        /*****************************************************/
        /* save output meta data csv, e.g. "/home/su/Documents/Jupyter/source/LandsatARD/Plot23_coutput.csv";  */
        sprintf(out_filename, "spectral_%d_%d_obs.csv", row, col);
        sprintf(pointTS_output_dir, "%s/%s", out_path, out_filename);

        valid_scene_count = 0;

//        if(format == ENVI_FORMAT){
            for (i = 0; i < num_scenes; i++)
            {
                read_bip(in_path, scene_list, fp_bip, i,
                         row, col, meta->samples, sdate, buf, fmask_buf, sensor_buf,
                         &valid_scene_count, valid_scene_list, valid_date_array);
            }

            if(b_landspecific_mode == TRUE){
                 read_bip_auxval(auxiliary_var_path, row, col, meta->samples, &auxval);

                 read_bip_maskval(mask_path, row, col, meta->samples, &maskval);
            }
//        }else{
//            for (i = 0; i < num_scenes; i++)
//            {
//                read_tif(in_path, scene_list, fp_bip, i,
//                         row, col, meta->samples, sdate, buf, fmask_buf, sensor_buf,
//                         &valid_scene_count, valid_scene_list, valid_date_array);
//            }
//        }

        //printf("read bip finished\n");

        /*point_data output as csv*/
        if(b_outputCSV){
            fd = fopen(pointTS_output_dir, "w");
            // printf("pointTS_output_dir = %s\n", pointTS_output_dir);
            for (i = 0; i < valid_scene_count; i++)
            {
                fprintf(fd, "%i, %d, %d, %d, %d, %d, %d, %d, %d, %d\n", valid_date_array[i], (short int)buf[0][i],
                        (short int)buf[1][i], (short int)buf[2][i], (short int)buf[3][i], (short int)buf[4][i],
                        (short int)buf[5][i], (short int)buf[6][i], (short int)fmask_buf[i], (short int)sensor_buf[i]);

            }
            fclose(fd);
        }

        if (METHOD == SCCD)
        {
            sprintf(out_filename,  "record_change_%d_%d_sccd.dat", row, col);
            sprintf(out_fullpath, "%s/%s", out_path, out_filename);

            sprintf(out_filename, "StateRecords_%d_%d_B",row, col);
            sprintf(states_output_dir, "%s/%s", out_path, out_filename);
            //sprintf(out_filename, "StateRecords_%d_%d_B", row, col);
            //printf(states_output_dir, "%s/%s", out_path, out_filename);
            s_rec_cg = malloc(NUM_FC * sizeof(Output_t_sccd));
            if (b_landspecific_mode == TRUE){
                category = getlabelfromNLCD(maskval);
                for(i = 0; i < NUM_FC; i++){
                    if (i == 0)
                        s_rec_cg[i].land_type = category;
                    else
                        s_rec_cg[i].land_type = NA_VALUE;
                }
            }else{
                for(i = 0; i < NUM_FC; i++){
                        s_rec_cg[i].land_type = NA_VALUE;
                }
            }


            // printf("start sccd \n");
            result = sccd(buf, fmask_buf, valid_date_array, valid_scene_count, s_rec_cg, &num_fc,
                          meta->samples, col, row, b_fastmode, states_output_dir, probability_threshold,
                          min_days_conse, training_type, monitorwindow_lowerlin, monitorwindow_upperlim,
                          sensor_buf, n_focus_variable, n_total_variable, focus_blist, NDVI_INCLUDED, NBR_INCLUDED,
                          RGI_INCLUDED, TCTWETNESS_INCLUDED, TCTGREENNESS_INCLUDED, EVI_INCLUDED, DI_INCLUDED,
                          NDMI_INCLUDED, b_landspecific_mode, auxval);

            /**********************************************************/
            /****************** write binary header **********************/
            /**********************************************************/
            fdoutput= fopen(out_fullpath, "w");

            if (fdoutput == NULL)
            {
                RETURN_ERROR("Please provide correct path for binary output", FUNC_NAME, FAILURE);
            }
            for(i = 0; i < num_fc + 1; i++)
            {
                write_output_binary_sccd(fdoutput, s_rec_cg[i]);
                if(result != SUCCESS)
                     RETURN_ERROR("Binary data saving fails", FUNC_NAME, FAILURE);
            }

            fclose(fdoutput);

            free(s_rec_cg);
        }
        else if(METHOD == CCD)
        {
            sprintf(out_filename, "record_change_%d_%d_ccd.dat", row, col);
            sprintf(out_fullpath, "%s/%s", out_path, out_filename);

            rec_cg = malloc(NUM_FC * sizeof(Output_t));
            result = ccd(buf, fmask_buf, valid_date_array, valid_scene_count, rec_cg, &num_fc,
                         meta->samples, col, row, probability_threshold);

            /**********************************************************/
            /****************** write binary header **********************/
            /**********************************************************/
            fdoutput= fopen(out_fullpath, "w");
            // printf('%s\n', out_fullpath);
            if (fdoutput == NULL)
            {
                RETURN_ERROR("Please provide correct path for binary output", FUNC_NAME, FAILURE);
            }
            for(i = 0; i < num_fc; i++)
            {
                write_output_binary(fdoutput, rec_cg[i]);
            }

            fclose(fdoutput);

            free(rec_cg);
        }

        ms_end = getMicrotime();


        free_2d_array ((void **) buf);
        free((void **) fmask_buf);
        free((void **) sensor_buf);
        free_2d_array ((void **) valid_scene_list);
        free(fp_bip);
        free(valid_date_array);

    }
    /* scanline-based */
    else if(mode == 2)
    {
        ccd_scanline(row, in_path, scene_list, mask_path, meta->samples, num_scenes, sdate,
                     out_path, METHOD, probability_threshold, min_days_conse, training_type,
                     monitorwindow_lowerlin, monitorwindow_upperlim, n_focus_variable,
                     n_total_variable, focus_blist, NDVI_INCLUDED, NBR_INCLUDED, RGI_INCLUDED,
                     TCTWETNESS_INCLUDED, TCTGREENNESS_INCLUDED, EVI_INCLUDED, DI_INCLUDED,
                     NDMI_INCLUDED, b_landspecific_mode, auxiliary_var_path);
    }
    /* whole scene */
    else if (mode == 3)
    {

        /**************************************************************************/
        /*                   Parallel scanline processing                         */
        /**************************************************************************/

        omp_set_num_threads(n_cores);
        block_num = (int)(meta->samples/n_cores);
        int n_remain_line = meta->samples - block_num * n_cores;
        for (j = 0; j < block_num; j++)
        //for (j = 12; j < block_num; j ++)
        //for (j = 0; j < 598; j ++)
        {
            #pragma omp parallel
            {
                 int  tid;
                 /* Obtain and print thread id */
                 tid = omp_get_thread_num();
                 ccd_scanline(j * n_cores + tid + 1, in_path, scene_list, mask_path, meta->samples, num_scenes, sdate,
                              out_path, METHOD, probability_threshold, min_days_conse, training_type,
                              monitorwindow_lowerlin, monitorwindow_upperlim, n_focus_variable,
                              n_total_variable, focus_blist, NDVI_INCLUDED, NBR_INCLUDED, RGI_INCLUDED, TCTWETNESS_INCLUDED,
                              TCTGREENNESS_INCLUDED, EVI_INCLUDED, DI_INCLUDED, NDMI_INCLUDED, b_landspecific_mode, auxiliary_var_path);
                 if(result != SUCCESS)
                 {
                    printf("CCD procedure fails for ROW_%d! \n", j * n_cores + tid + 1);
                 }
                 else
                 {
                    printf("The row for %d processing is finished \n", j * n_cores + tid + 1);
                 }
                 //A barrier defines a point in the code where all active threads
                 //will stop until all threads have arrived at that point
            }  /* All threads join master thread and terminate */

        }

        /* processing remaining*/
        if (n_remain_line > 0)
        {
            omp_set_num_threads(n_remain_line);
            #pragma omp parallel
            {
                 int  tid;
                 /* Obtain and print thread id */
                 tid = omp_get_thread_num();
                 result = ccd_scanline(block_num * n_cores + tid + 1 , in_path, scene_list, mask_path, meta->samples,
                                       num_scenes, sdate, out_path, METHOD, probability_threshold, min_days_conse,
                                       training_type, monitorwindow_lowerlin, monitorwindow_upperlim, n_focus_variable,
                                       n_total_variable, focus_blist, NDVI_INCLUDED, NBR_INCLUDED, RGI_INCLUDED, TCTWETNESS_INCLUDED,
                                       TCTGREENNESS_INCLUDED, EVI_INCLUDED, DI_INCLUDED, NDMI_INCLUDED, b_landspecific_mode,
                                       auxiliary_var_path);
                 if(result != SUCCESS)
                 {
                      printf("CCD procedure fails for ROW_%d!", block_num * n_cores + tid + 1 );
                 }
                 else
                 {
                    printf("The row for %d processing is finished \n", block_num * n_cores + tid + 1 );
                 }
                 //A barrier defines a point in the code where all active threads
                 //will stop until all threads have arrived at that point
            }  /* All threads join master thread and terminate */
        }

     }

    else if (mode == 4)
    {
        sampleFile = fopen(in_path, "r");
        valid_date_array = malloc(MAX_SCENE_LIST * sizeof(int));
        fmask_buf = (short int *) malloc(MAX_SCENE_LIST * sizeof (short int));
        sensor_buf = (short int *) malloc(MAX_SCENE_LIST * sizeof (short int));
        csv_row = malloc(MAX_STR_LEN * sizeof(char));

        buf = (short int **) allocate_2d_array (TOTAL_IMAGE_BANDS, MAX_SCENE_LIST, sizeof (short int));
        while (fgets(csv_row, 255, sampleFile) != NULL)
        {
//            if(row_count != 0) // we skip first line because it is a header
//            {
                //convert_year_doy_to_ordinal(year, yearmonth2doy(year, month, day), &sdate_tmp);
                valid_date_array[valid_scene_count] = atoi(strtok(csv_row, ","));
                buf[0][valid_scene_count] = (short)atoi(strtok(NULL, ","));
                buf[1][valid_scene_count] = (short)atoi(strtok(NULL, ","));
                buf[2][valid_scene_count] = (short)atoi(strtok(NULL, ","));
                buf[3][valid_scene_count] = (short)atoi(strtok(NULL, ","));
                buf[4][valid_scene_count] = (short)atoi(strtok(NULL, ","));
                buf[5][valid_scene_count] = (short)atoi(strtok(NULL, ","));
                buf[6][valid_scene_count] = (short)atoi(strtok(NULL, ","));
                pixel_qa = atoi(strtok(NULL, ","));
                // need to bring it back for zhe zhu dataset
//                if (training_type == 1)
//                {
//                   fmask_buf[valid_scene_count] = (short)pixel_qa;
//                   sensor_buf[valid_scene_count] = (short)atoi(strtok(NULL, ","));
//                }
//                else
//                   fmask_buf[valid_scene_count] = (short)qabitval(pixel_qa);
                //fmask_buf[valid_scene_count] = (short)qabitval(pixel_qa);
                fmask_buf[valid_scene_count] = (short)pixel_qa;
                sensor_buf[valid_scene_count] = (short)atoi(strtok(NULL, ","));

                valid_scene_count++;
            // }
            row_count++;
        }

        quick_sort_buf_sensor(valid_date_array, buf, fmask_buf, sensor_buf, 0 , valid_scene_count-1);
//        sprintf(out_filename, "coutput_%d.csv", cur_plot_id);
        num_fc = 0;
        in_filename_tmp = strrchr(in_path, sep) + 1;
        //printf("in_filename_tmp is %s\n", in_filename_tmp);
        in_filename = (char *) malloc((strlen(in_filename_tmp) - 4 + 1) * sizeof (char));
        //memcpy(in_filename, in_filename_tmp, strlen(in_filename_tmp) - 4);
        substr(in_filename, in_filename_tmp, 0, strlen(in_filename_tmp) - 4);
        // important : terminate a string with 0
        //in_filename[strlen(in_filename)] = '\0';
        //printf("in_filename is %s\n", in_filename);
        sprintf(out_csvname, "%s%s", in_filename, "_obs.csv");
        sprintf(pointTS_output_dir, "%s/%s", out_path, out_csvname);
        //printf("pointTS_output_dir is %s\n", pointTS_output_dir);


        /* output csv for observation */
        if(b_outputCSV==TRUE){
            fd = fopen(pointTS_output_dir, "w");
            for (i = 0; i < valid_scene_count; i++)
            {
                fprintf(fd,"%i,", valid_date_array[i]);
                for (j = 0; j < TOTAL_IMAGE_BANDS; j++)
                    fprintf(fd, "%d, ", (short int)buf[j][i]);
                fprintf(fd, "%d, %d\n",  (short int)fmask_buf[i], (short int)sensor_buf[i]);

//                fprintf(fd, "%i, %d, %d, %d, %d, %d, %d, %d, %d, %d\n", valid_date_array[i],
//                        (short int)buf[0][i], (short int)buf[1][i], (short int)buf[2][i],
//                        (short int)buf[3][i], (short int)buf[4][i],
//                        (short int)buf[5][i], (short int)buf[6][i],
//                        (short int)fmask_buf[i], (short int)sensor_buf[i]);

            }
            fclose(fd);
        }
        // printf("reading finished \n");
        if (METHOD == SCCD)
        {

            /*******************************************************/
            /*                 define sccd result path            */
            /******************************************************/
                //sprintf(states_output_dir, "/home/su/Documents/Jupyter/source/LandsatARD/StateRecords_%d_%d_B", row_pos, col_pos);

            sprintf(out_filename, "%s%s", in_filename, "_sccd.dat");
            sprintf(out_fullpath, "%s/%s", out_path, out_filename);
            sprintf(out_filename, "%s%s", in_filename, "_StateRecords_B");
            sprintf(states_output_dir, "%s/%s", out_path, out_filename);

            s_rec_cg = malloc(NUM_FC * sizeof(Output_t_sccd));

//            result = sccd(buf, fmask_buf, valid_date_array, valid_scene_count, s_rec_cg, &num_fc,
//                         meta->samples, col, row, b_fastmode, states_output_dir, probability_threshold,
//                          min_days_conse, training_type, monitorwindow_lowerlin, monitorwindow_upperlim, sensor_buf,
//                          n_focus_variable, n_total_variable, focus_blist, NDVI_INCLUDED, NBR_INCLUDED,
//                          RGI_INCLUDED, TCTWETNESS_INCLUDED, TCTGREENNESS_INCLUDED, EVI_INCLUDED, DI_INCLUDED,
//                          NDMI_INCLUDED, booster, b_landspecific_mode, auxval);
            result = sccd(buf, fmask_buf, valid_date_array, valid_scene_count, s_rec_cg, &num_fc,
                         meta->samples, col, row, b_fastmode, states_output_dir, probability_threshold,
                          min_days_conse, training_type, monitorwindow_lowerlin, monitorwindow_upperlim, sensor_buf,
                          n_focus_variable, n_total_variable, focus_blist, NDVI_INCLUDED, NBR_INCLUDED,
                          RGI_INCLUDED, TCTWETNESS_INCLUDED, TCTGREENNESS_INCLUDED, EVI_INCLUDED, DI_INCLUDED,
                          NDMI_INCLUDED, b_landspecific_mode, auxval);
            for(i = 0; i < num_fc + 1; i++)
            {
                s_rec_cg[i].pos = 0;
            }
            /**********************************************************/
            /****************** write binary header **********************/
            /**********************************************************/
            fdoutput= fopen(out_fullpath, "w");

            if (fdoutput == NULL)
            {
                RETURN_ERROR("Please provide correct path for binary output", FUNC_NAME, FAILURE);
            }
            for(i = 0; i < num_fc + 1; i++)
            {
                result = write_output_binary_sccd(fdoutput, s_rec_cg[i]);
                if(result != SUCCESS)
                     RETURN_ERROR("Binary data saving fails", FUNC_NAME, FAILURE);
            }

            fclose(fdoutput);

            free(s_rec_cg);

        }
        else
        {

            sprintf(out_filename, "%s%s", in_filename, "_ccd.dat");
            sprintf(out_fullpath, "%s/%s", out_path, out_filename);

            rec_cg = malloc(NUM_FC * sizeof(Output_t));
            result = ccd(buf, fmask_buf, valid_date_array, valid_scene_count, rec_cg, &num_fc,
                         meta->samples, col, row, probability_threshold);
            for(i = 0; i < num_fc + 1; i++)
            {
                rec_cg[i].pos = 0;
            }
            //printf("processing finished \n");
            // printf("out_fullpath is %s\n", out_fullpath);
            fdoutput= fopen(out_fullpath, "w");
            if (fdoutput == NULL)
            {
                RETURN_ERROR("Please provide correct path for binary output", FUNC_NAME, FAILURE)
            }
            for(i = 0; i < num_fc; i++)
            {
                result = write_output_binary(fdoutput, rec_cg[i]);
                if(result != SUCCESS)
                     RETURN_ERROR("Binary data saving fails", FUNC_NAME, FAILURE);
            }

            fclose(fdoutput);

            free(rec_cg);
        }

        free((void *) in_filename);
        free((void *) csv_row);
        free_2d_array ((void **) buf);
        free((void *) fmask_buf);
        free((void *) sensor_buf);
        free((void *) valid_date_array);
        free(sdate);
        fclose(sampleFile);

    }

    ms_end = getMicrotime();
    snprintf (msg_str, sizeof(msg_str), "CCDC spent time (in ms)=%ld\n", ms_end - ms_start);
    if(verbose == TRUE)
        LOG_MESSAGE (msg_str, FUNC_NAME);


    time(&now);
    snprintf (msg_str, sizeof(msg_str), "CCDC end_time=%s\n", ctime (&now));
    if (verbose == TRUE)
        LOG_MESSAGE (msg_str, FUNC_NAME);
    //free(fp_bip);

    if (mode  < 4)
    {
        free_2d_array ((void **) scene_list);
    }
    free(meta);


    return SUCCESS;
}
