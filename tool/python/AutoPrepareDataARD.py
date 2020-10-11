import tarfile
import os
from os import listdir
from os.path import isfile, join, isdir
import logging
import time
from osgeo import gdal_array
import parameter
import numpy as np
import numpy as geek
from datetime import datetime
import gdal
import click
import shutil
from pytz import timezone
from mpi4py import MPI
from fixed_thread_pool_executor import FixedThreadPoolExecutor
import multiprocessing
from math import floor, ceil

def mask_value(vector, val):
    """
    Build a boolean mask around a certain value in the vector.

    Args:
        vector: 1-d ndarray of values
        val: values to mask on
    Returns:
        1-d boolean ndarray
    """
    return vector == val

class Parameters(dict):
    def __init__(self, params):

        super(Parameters, self).__init__(params)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError('No such attribute: ' + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError('No such attribute: ' + name)

def qabitval_array(packedint_array, proc_params):
    """
    Institute a hierarchy of qa values that may be flagged in the bitpacked
    value.

    fill > cloud > shadow > snow > water > clear

    Args:
        packedint: int value to bit check
        proc_params: dictionary of processing parameters
    Returns:
        offset value to use
    """
    unpacked = np.full(packedint_array.shape, -9999)
    QA_FILL_unpacked = geek.bitwise_and(packedint_array, 1 << proc_params.QA_FILL)
    QA_CLOUD_unpacked = geek.bitwise_and(packedint_array, 1 << proc_params.QA_CLOUD)
    QA_SHADOW_unpacked = geek.bitwise_and(packedint_array, 1 << proc_params.QA_SHADOW)
    QA_SNOW_unpacked = geek.bitwise_and(packedint_array, 1 << proc_params.QA_SNOW)
    QA_WATER_unpacked = geek.bitwise_and(packedint_array, 1 << proc_params.QA_WATER)
    QA_CLEAR_unpacked = geek.bitwise_and(packedint_array, 1 << proc_params.QA_CLEAR)
    QA_CIRRUS1 = geek.bitwise_and(packedint_array, 1 << proc_params.QA_CIRRUS1)
    QA_CIRRUS2 = geek.bitwise_and(packedint_array, 1 << proc_params.QA_CIRRUS2)
    QA_OCCLUSION = geek.bitwise_and(packedint_array, 1 << proc_params.QA_OCCLUSION)

    unpacked[QA_OCCLUSION > 0] = proc_params.QA_CLEAR - 1
    unpacked[np.logical_and(QA_CIRRUS1 > 0, QA_CIRRUS2 > 0)] = proc_params.QA_CLEAR - 1
    unpacked[QA_CLEAR_unpacked > 0] = proc_params.QA_CLEAR - 1
    unpacked[QA_WATER_unpacked > 0] = proc_params.QA_WATER - 1
    unpacked[QA_SNOW_unpacked > 0] = proc_params.QA_SNOW - 1
    unpacked[QA_SHADOW_unpacked > 0] = proc_params.QA_SHADOW - 1
    unpacked[QA_CLOUD_unpacked > 0] = proc_params.QA_CLOUD - 1
    unpacked[QA_FILL_unpacked > 0] = 255
    return unpacked


def load_data(file_name, gdal_driver='GTiff'):
    '''
    Converts a GDAL compatable file into a numpy array and associated geodata.
    The rray is provided so you can run with your processing - the geodata consists of the geotransform and gdal dataset object
    if you're using an ENVI binary as input, this willr equire an associated .hdr file otherwise this will fail.
	This needs modifying if you're dealing with multiple bands.

	VARIABLES
	file_name : file name and path of your file

	RETURNS
	image array
	(geotransform, inDs)
    '''
    driver_t = gdal.GetDriverByName(gdal_driver) ## http://www.gdal.org/formats_list.html
    driver_t.Register()

    inDs = gdal.Open(file_name, gdal.GA_ReadOnly)
    # print(inDs)
    if inDs is None:
        print('Couldnt open this file {}'.format(file_name))
        sys.exit("Try again!")

    # Extract some info form the inDs
    geotransform = inDs.GetGeoTransform()

    # Get the data as a numpy array
    band = inDs.GetRasterBand(1)
    cols = inDs.RasterXSize
    rows = inDs.RasterYSize
    image_array = band.ReadAsArray(0, 0, cols, rows)

    return image_array, (geotransform, inDs)


def single_image_processing(tmp_path, source_dir, out_dir, folder, clear_threshold, width, height, band_count, image_count, total_image_count):

    # unzip SR
    if os.path.exists(os.path.join(tmp_path, folder)) is False:
        with tarfile.open(os.path.join(source_dir, folder+'.tar')) as tar_ref:
            try:
                tar_ref.extractall(os.path.join(tmp_path, folder))
            except:
                # logger.warning('Unzip fails for {}'.format(folder))
                print('Unzip fails for {}'.format(folder))

    # unzip BT
    if os.path.exists(os.path.join(source_dir, folder.replace("SR", "BT"))) is False:
        with tarfile.open(os.path.join(source_dir, folder.replace("SR", "BT")+'.tar')) as tar_ref:
            try:
                tar_ref.extractall(os.path.join(tmp_path, folder.replace("SR", "BT")))
            except:
                # logger.warning('Unzip fails for {}'.format(folder.replace("SR", "BT")))
                print('Unzip fails for {}'.format(folder.replace("SR", "BT")))


    driver = gdal.GetDriverByName('ENVI')
    if isdir(os.path.join(tmp_path, folder.replace("SR", "BT"))):
        try:
            QA_band = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                       "{}_PIXELQA.tif".format(folder[0:len(folder) - 3])))
        except ValueError as e:
            # logger.error('Cannot open QA band for {}: {}'.format(folder, e))
            print('Cannot open QA band for {}: {}'.format(folder, e))

        # convertQA = np.vectorize(qabitval)
        proc_params = Parameters(parameter.defaults)
        QA_band_unpacked = qabitval_array(QA_band, proc_params)
        clear_ratio = np.sum(np.logical_or(QA_band_unpacked == proc_params.QA_CLEAR - 1,
                                           QA_band_unpacked == proc_params.QA_WATER - 1)) / np.sum(QA_band_unpacked != proc_params.QA_FILL)
        if clear_ratio > clear_threshold:
            if folder[3] == '5':
                sensor = 'LT5'
            elif folder[3] == '7':
                sensor = 'LE7'
            elif folder[3] == '8':
                sensor = 'LC8'
            elif folder[3] == '4':
                sensor = 'LT4'
            else:
                print('Sensor is not correctly formated for the scene {}'.format(folder))

            col = folder[8:11]
            row = folder[11:14]
            year = folder[15:19]
            doy = datetime(int(year), int(folder[19:21]), int(folder[21:23])).strftime('%j')
            collection = "C{}".format(folder[35:36])
            version = folder[37:40]
            folder_name = sensor + col + row + year + doy + collection + version
            if not os.path.exists(os.path.join(out_dir, folder_name)):
                os.makedirs(os.path.join(out_dir, folder_name))

            file_name = folder_name + '_MTLstack'

            if sensor == 'LT5' or sensor == 'LE7' or sensor == 'LT4':
                try:
                    B1 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B1.tif".format(folder)))
                    B2 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B2.tif".format(folder)))
                    B3 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B3.tif".format(folder)))
                    B4 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B4.tif".format(folder)))
                    B5 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B5.tif".format(folder)))
                    B6 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B7.tif".format(folder)))
                    B7 = gdal_array.LoadFile(
                        os.path.join(os.path.join(tmp_path, "{}_BT".format(folder[0:len(folder) - 3])),
                                     "{}_BTB6.tif".format(folder[0:len(folder) - 3])))
                except ValueError as e:
                    # logger.error('Cannot open spectral bands for {}: {}'.format(folder, e))
                    print('Cannot open QA band for {}: {}'.format(folder, e))
            elif sensor == 'LC8':
                try:
                    B1 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B2.tif".format(folder)))
                    B2 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B3.tif".format(folder)))
                    B3 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B4.tif".format(folder)))
                    B4 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B5.tif".format(folder)))
                    B5 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B6.tif".format(folder)))
                    B6 = gdal_array.LoadFile(os.path.join(os.path.join(tmp_path, folder),
                                                          "{}B7.tif".format(folder)))
                    B7 = gdal_array.LoadFile(
                        os.path.join(os.path.join(tmp_path, "{}_BT".format(folder[0:len(folder) - 3])),
                                     "{}_BTB10.tif".format(folder[0:len(folder) - 3])))
                except ValueError as e:
                    # logger.error('Cannot open spectral bands for {}: {}'.format(folder, e))
                    print('Cannot open QA band for {}: {}'.format(folder, e))

            outDs = driver.Create(os.path.join(os.path.join(out_dir, folder_name), file_name), width, height,
                                  band_count,
                                  gdal.GDT_Int16, options=["INTERLEAVE=BIP"])
            outDs.GetRasterBand(1).WriteArray(B1)
            outDs.GetRasterBand(2).WriteArray(B2)
            outDs.GetRasterBand(3).WriteArray(B3)
            outDs.GetRasterBand(4).WriteArray(B4)
            outDs.GetRasterBand(5).WriteArray(B5)
            outDs.GetRasterBand(6).WriteArray(B6)
            outDs.GetRasterBand(7).WriteArray(B7)
            outDs.GetRasterBand(8).WriteArray(QA_band_unpacked)
            # print(os.path.join(os.path.join(tmp_path, folder), "{}B1.tif".format(folder)))
            srsdata, srsgeodata = load_data(os.path.join(os.path.join(tmp_path, folder), "{}B1.tif".format(folder)))
            original_geotransform, inDs = srsgeodata

            # srsgeodata[0][1] is resolution
            outDs.SetGeoTransform([original_geotransform[0], srsgeodata[0][1], 0.0, original_geotransform[3],
                                   0.0, -srsgeodata[0][1]])
            outDs.SetProjection(inDs.GetProjection())

            outDs.FlushCache()
            outDs = None
            # scene_list.append(folder_name)
        else:
            # logger.info('Not enough clear observations for {}'.format(folder[0:len(folder) - 3]))
            print('Not enough clear observations for {}'.format(folder[0:len(folder) - 3]))
    else:
        # logger.warning('Fail to locate BT folder for {}'.format(folder))
        print('Fail to locate BT folder for {}'.format(folder))

    # delete unzip folder
    shutil.rmtree(os.path.join(tmp_path, folder), ignore_errors=True)
    shutil.rmtree(os.path.join(tmp_path, folder.replace("SR", "BT")), ignore_errors=True)

    # logger.info("Finished processing {} th scene in total {} scene ".format(image_count, total_image_count))
    print("Finished processing {} th scene in total {} scene ".format(image_count, total_image_count))
    # time.sleep(0.1) # to reduce cpu usage

@click.command()
@click.option('--source_dir', type=str, default=None, help='the folder directory of Landsat tar files downloaded from USGS website')
@click.option('--out_dir', type=str, default=None, help='the folder directory for ENVI outputs')
@click.option('--threads_number', type=int, default=0, help='user-defined thread number')
@click.option('--parallel_mode', type=str, default='desktop', help='desktop or HPC')
@click.option('--clear_threshold', type=float, default=0.2, help='user-defined thread number')
def main(source_dir, out_dir, threads_number, parallel_mode, clear_threshold):
    source_dir = '/Users/coloury/Dropbox/transfer_landsat'
    out_dir = '/Users/coloury/sccd_test'
    if parallel_mode == 'desktop':
        tz = timezone('US/Eastern')
        logging.basicConfig(filename=os.path.join(os.getcwd(), 'AutoPrepareDataARD_{}.log'.format(datetime.
                                                                                                  fromtimestamp(
            time.time()).
                                                                                                  strftime(
            '%c').replace(" ", "_").
                                                                                                  replace(":", "-"))),
                            filemode='w+', level=logging.INFO)

        logger = logging.getLogger(__name__)

        tmp_path = os.path.join(out_dir, 'tmp')

        if os.path.exists(tmp_path) is False:
            os.mkdir(tmp_path)

        if threads_number == 0:
            threads_number = multiprocessing.cpu_count()
        else:
            threads_number = int(threads_number)

        print('The thread number to be paralleled is {}'.format(threads_number))

        folder_list = [f[0:len(f) - 4] for f in listdir(source_dir) if
                       (isfile(join(source_dir, f)) and f.endswith('.tar')
                        and f[len(f) - 6:len(f) - 4] == 'SR')]
        width = 5000
        height = 5000
        band_count = 8

        prepare_executor = FixedThreadPoolExecutor(size=threads_number)

        for count, folder in enumerate(folder_list):
            print("it is processing {} th scene in total {} scene ".format(count + 1, len(folder_list)))
            prepare_executor.submit(single_image_processing, tmp_path, source_dir, out_dir, folder, clear_threshold, width,
                                    height, band_count, count + 1, len(folder_list))

        # await all tile finished
        prepare_executor.drain()

        # await thread pool to stop
        prepare_executor.close()

        logger.info("Final report: finished preparation task ({})"
                    .format(datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')))

        # count_valid = len(scene_list)
        # logger.warning("Total processing scene number is {}; valid scene number is {}".format(count, count_valid))

        # remove tmp folder
        shutil.rmtree(tmp_path, ignore_errors=True)

    else: # for HPC mode
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        # query available cores/process number
        n_process = comm.Get_size()
        print('The core number to be paralleled is {}'.format(n_process))

        if rank == 0:
            tz = timezone('US/Eastern')
            logging.basicConfig(filename=os.path.join(os.getcwd(), 'out_AutoPrepareDataARD_{}.log'.format(datetime.
                                                                                                  fromtimestamp(time.time()).
                                                                                                  strftime('%c').replace(" ", "_").
                                                                                                  replace(":", "-"))), filemode='w+',
                                level=logging.INFO)

            # logger = logging.getLogger(__name__)
            # logger.info('AutoPrepareDataARD starts: {}'.format(datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')))
            print('AutoPrepareDataARD starts: {}'.format(datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')))

            tmp_path = os.path.join(out_dir, 'tmp')

            # select only _SR
            folder_list = [f[0:len(f)-4] for f in listdir(source_dir) if (isfile(join(source_dir, f)) and f.endswith('.tar')
                                                                         and f[len(f)-6:len(f)-4] == 'SR')]
            width = 5000
            height = 5000
            band_count = 8

            scene_per_process = ceil(len(folder_list) / n_process)
            # scene number for the last process is smaller than others
            scene_extra = scene_per_process * n_process - len(folder_list)

            # logger.info('The total process number is : {}'.format(n_process))
            # logger.info('scene number per process is : {}'.format(scene_per_process))
            # logger.info('extra scene number is : {}'.format(scene_extra))
            print('The total process number is : {}'.format(n_process))
            print('scene number per process is : {}'.format(scene_per_process))
            print('extra scene number is : {}'.format(scene_extra))
            # if tmp path exists, delete path
            if os.path.exists(tmp_path) is False:
                os.mkdir(tmp_path)
        else:
            # logger = None
            tmp_path = None
            folder_list = None
            width = None
            height = None
            band_count = None
            scene_per_process = None
            scene_extra = None

        # MPI broadcasting variables
        # comm.bcast(logger, root=0)
        tmp_path = comm.bcast(tmp_path, root=0)
        folder_list = comm.bcast(folder_list, root=0)
        width = int(comm.bcast(width, root=0))
        height = int(comm.bcast(height, root=0))
        band_count = int(comm.bcast(band_count, root=0))
        scene_per_process = int(comm.bcast(scene_per_process, root=0))
        scene_extra = int(comm.bcast(scene_extra, root=0))

        # for rank smaller scene_extra, we assigned scene_per_process-1 scenes per core
        if rank < scene_extra:
            for i in range((scene_per_process-1)*rank, (scene_per_process-1)*rank+scene_per_process-1):
                folder = folder_list[i]
                single_image_processing(tmp_path, source_dir, out_dir, folder, clear_threshold, width, height,
                                        band_count, i + 1, len(folder_list))
        else:  # for the last core
            for i in range((scene_per_process-1)*scene_extra+(rank-scene_extra)*scene_per_process,
                           (scene_per_process-1)*scene_extra+(rank-scene_extra)*scene_per_process+scene_per_process):
                folder = folder_list[i]
                single_image_processing(tmp_path, source_dir, out_dir, folder, clear_threshold, width, height,
                                        band_count, i + 1, len(folder_list))
        # logger.info("Final report: finished preparation task ({})"
        #             .format(datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')))

    # count_valid = len(scene_list)
    # logger.warning("Total processing scene number is {}; valid scene number is {}".format(count, count_valid))
    
    # remove tmp folder

    # scene_file = open(os.path.join(source_dir, "scene_list.txt"),"w+")
    # for L in scene_list:
    #     scene_file.writelines("{}\n".format(L))
    # scene_file.close()

if __name__ == '__main__':
    main()
