"""
Python 3 script for downloading Landsat ARD in HPC
    download_m2m('/path/to/downloads', username='user1234', dataset='ARD_TILE',
                 products='TOA,BT,SR,PQA', threads=40,
                 fields={'Region': 'CU', 'Spacecraft': 'LANDSAT_8'})
original script: https://gist.github.com/jakebrinkmann/c3bc9ec04c3a171028b9882bcdbe759d#file-readme-md
Author: Su Ye

"""
import requests, json, os, sys, getpass, urllib3, time, logging
from argparse import ArgumentParser
import configparser
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# from mpi4py import MPI
from fixed_thread_pool_executor import FixedThreadPoolExecutor


def message(msg, stop=False):
    stdout = sys.stderr
    if isinstance(msg, list):
        msg = '\n'.join(msg)
    if stop:
        msg = '\n' + msg + '\n'
    stdout.write(msg)
    stdout.flush()
    if stop:
        exit(1)


class EarthExplorer(object):
    """  Web-Service interface for EarthExplorer JSON Machine-to-Machine API  """
    def __init__(self, version='1.4.1'):
        self.baseurl = 'https://earthexplorer.usgs.gov/inventory/json/v/%s/' % version

    def _api(self, endpoint='login', body=None):
        body = {'jsonRequest': json.dumps(body)} if body else {}
        r = requests.post(self.baseurl+endpoint, data=body)
        r.raise_for_status()
        dat = r.json()
        if dat.get('error'):
            message(': '.join([dat.get('errorCode'), dat.get('error')]), stop=True)
        return dat

    @classmethod
    def login(cls, username, password=None):
        if password is None:
            password = getpass.getpass('Password (%s): ' % username)
        payload = {'username': username, 'password': password}
        return cls()._api('login', payload).get('data')

    @classmethod
    def search(cls, **kwargs):
        return cls()._api('search', kwargs).get('data')

    @classmethod
    def idlookup(cls, **kwargs):
        return cls()._api('idlookup', kwargs).get('data')

    @classmethod
    def metadata(cls, **kwargs):
        return cls()._api('metadata', kwargs).get('data')

    @classmethod
    def download(cls, **kwargs):
        return cls()._api('download', kwargs).get('data')

    @classmethod
    def downloadoptions(cls, **kwargs):
        return cls()._api('downloadoptions', kwargs).get('data')

    @classmethod
    def datasets(cls, **kwargs):
        return cls()._api('datasets', kwargs).get('data')

    @classmethod
    def datasetfields(cls, **kwargs):
        return cls()._api('datasetfields', kwargs).get('data')

    @classmethod
    def additionalCriteriaValues(cls, api_key, dataset, filters):
        """ Attempts to build a complex search based on some simple JSON input
            Example: filters = {"Path": 29, "Row": 29, "Sensor": "ETM+" }
        TODO: Add support for AND/OR/BETWEEN searches
        """
        fields = cls.datasetfields(apiKey=api_key, datasetName=dataset)
        k = 'additionalCriteria'
        criteria = {k: {"filterType": "and", "childFilters": []}}
        for look_for, compare in filters.items():
            field_matches = [f for f in fields if look_for in f['name']]
            if len(field_matches) > 1:
                message(['Search "%s" not unique. Found:' % look_for]
                        + ['* %s' % f['name'] for f in field_matches], stop=True)
            elif len(field_matches) < 1:
                message(['Search "%s" failed. Available:' % look_for]
                        + ['* %s' % f['name'] for f in fields], stop=True)

            field_id = int(field_matches[0]['fieldId'])
            field_name = field_matches[0]['name']
            selections = field_matches[0].get('valueList')
            mapping = {str(s['name']):str(s['value']) for s in selections}
            if not isinstance(compare, (list, dict)):
                if mapping and compare not in mapping.values():
                    message(['"%s" invalid value not found: %s' % (field_name, compare)]
                            + ['* %s: %s' % (k, v) for k, v in mapping.items()],
                            stop=True)
                search = {"filterType": "value", "fieldId": field_id, "value": compare}
                criteria[k]['childFilters'].append(search)
        return criteria

    @staticmethod
    def temporalCriteria(temporal):
        dates = temporal.split(',')
        sd, ed = dates if len(dates) == 2 else dates * 2
        return {"temporalFilter":{"dateField":"search_date","startDate":sd,"endDate":ed}}


def build_command_line_arguments():
    description = ('Search and download data (skip those already downloaded)')
    parser = ArgumentParser(description=description, add_help=False)
    parser.add_argument('--help', action='help', help='show this help message and exit')
    parser.add_argument('-d', '--directory', type=str, dest='directory', required=True, metavar='PATH',
                        help='Relative path to download all data')
    parser.add_argument('-u', '--username', type=str, dest='username', default=None, metavar='STR',
                        help='ERS Username (with full M2M download access)')
    parser.add_argument('-t', '--threads', type=int, dest='threads', default=40, metavar='INT',
                        help='Number of parallel download threads [Default: 40]')
    parser.add_argument('-b', '--batch', type=int, dest='batch', default=1000, metavar='INT',
                        help='Batch size iteration of URLs to receive [Default: 1000]')
    parser.add_argument('-m', '--max', type=int, dest='N', default=50000, metavar='INT',
                        help='Maximum number of search results to return [Default: 50000]')
    parser.add_argument('--dataset', type=str, dest='dataset', default='ARD_TILE', metavar='STR',
                        help='EE Catalog dataset [Default: ARD_TILE]')
    parser.add_argument('--products', type=str, dest='products', default='STANDARD', metavar='STR',
                        help='Comma-delimited products to download [Default: STANDARD]')
    parser.add_argument('--temporal', type=str, dest='temporal', default=None, metavar='STR',
                        help='Search Date Acquired (YYYY-MM-DD or YYYY-MM-DD,YYYY-MM-DD)')
    parser.add_argument('--maxcloudcover', type=int, dest='maxcloudcover', default=80, metavar='INT',
                        help='max cloud cover')
    parser.add_argument('--fields', type=json.loads, dest='fields', default=None, metavar='JSON',
                        help='Filter results based on dataset-specific metadata fields')
    args = parser.parse_args()
    return args


def download_url(x):
    fileurl, directory = x[0], x[1]
    head = requests.head(fileurl, allow_redirects=True, timeout=3000)
    filename = head.headers['Content-Disposition'].split('filename=')[-1]
    filename = filename[1:-1]
    local_fname = os.path.join(directory, filename)
    if os.path.exists(local_fname):
        message('Already exists: %s \n' % local_fname)
        return

    file_size = None
    if 'Content-Length' in head.headers:
        file_size = int(head.headers['Content-Length'])
    bytes_recv = 0
    if os.path.exists(local_fname + '.part'):
        bytes_recv = os.path.getsize(local_fname + '.part')

    message("Downloading %s ... \n" % local_fname)
    resume_header = {'Range': 'bytes=%d-' % bytes_recv}
    sock = requests.get(fileurl, headers=resume_header, timeout=3000,
                        stream=True, verify=False, allow_redirects=True)

    start = time.time()
    f = open(local_fname + '.part', 'ab')
    bytes_in_mb = 1024*1024
    for block in sock.iter_content(chunk_size=bytes_in_mb):
        if block:
            f.write(block)
            bytes_recv += len(block)
    f.close()
    ns = time.time() - start
    mb = bytes_recv/float(bytes_in_mb)
    message("%s (%3.2f (MB) in %3.2f (s), or  %3.2f (MB/s)) \n" % (filename, mb, ns, mb/ns))

    if bytes_recv >= file_size:
        os.rename(local_fname + '.part', local_fname)


def download_url_wrapper(x):
    try:
        download_url(x)
    except Exception as e:
        message('\n\n *** Failed download %s: %s \n' % (x, str(e)))


def chunkify(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def read_credentials(config_path, section='default'):
    config = configparser.ConfigParser()
    config.read(config_path)
    cfg_info = dict()
    for opt in config.options(section):
        cfg_info[opt] = config.get(section, opt)
    return cfg_info


def credentials(username=None):
    if username is None:
        cfgpath = os.getenv('M2M_DOWNLOAD_CREDENTIALS_FILE')
        cfgsection = os.getenv('M2M_DOWNLOAD_CREDENTIALS_PROFILE', 'default')
        if cfgpath:
            return read_credentials(os.path.expanduser(cfgpath), cfgsection)
        else:
            return {'username': input('ERS Username: ')}
    else:
        return {'username': username}


def download_executor(api_key, dataset, entities, products, directory, logger):
    product_avail = EarthExplorer.downloadoptions(apiKey=api_key, datasetName=dataset, entityIds=entities)
    product_avail = set(p.get('productcode') or p.get('downloadCode') for x in product_avail for p in x['downloadOptions'])
    valid_prods = list(set(products.split(',')) & product_avail)
    if len(valid_prods) < 1:
        logger.warning(['"%s" products not available. Choose from:' % products] + ['* %s' % m for m in
                                                                                   list(product_avail)])

    results = EarthExplorer.download(apiKey=api_key, datasetName=dataset,
                                     products=products.split(','), entityIds=entities)

    urls = [(r['url'], directory) for r in results]
    urls = [u for u in urls if all(u)]
    if urls:
        for url in urls:
            try:
                download_url(url)
            except Exception as e:
                logger.warning('Failed download (%s) %s: %s' % (entities, url, str(e)))
            else:
                logger.info('Downloading succeeded (%s): %s' % (entities, url))


def download_m2m(directory, username=None, products='STANDARD', dataset='ARD_TILE',
                    N=50000, temporal=None, batch=1000, threads=1, maxcloudcover=80, fields=None):
    """
    Search for and download Landsat Level-2 products to local directory
        Args:
            directory: Relative path to local directory (will be created)
            username: ERS Username (with full M2M download access) [Optional]
            dataset: EarthExplorer Catalog datasetName [Default: ARD_TILE]
            N: Maximum number of search results to return
            products: Comma-delmited list of download products [Default: STANDARD]
            temporal: Search Date image acquired [ Format: %Y-%m-%d or %Y-%m-%d,%Y-%m-%d ]
            batch: How many URLs to request before working on downloads
            threads: Number of download threads to launch in parallel
            max
            fields: JSON dataset-specific metadata fields (see #additionalCriteria)
    """
    # username = 'xiuchengyang'
    # dataset = 'ARD_TILE'
    # N = 50000
    api_key = EarthExplorer.login(**credentials(username))
    # temporal = "2000-01-01,2020-12-31"
    # fields = {"Grid Region": "CU", "Horizontal": 11, "Vertical": 9}
    # directory = u'/Users/coloury/Landsat_test'
    # threads = 4
    # products = 'SR'

    log_path = '%s/download.log' % (directory)
    if os.path.exists(log_path):
        os.remove(log_path)

    logging.basicConfig(filename=log_path, filemode='w',
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('Downloading starts')

    datasets = EarthExplorer.datasets(apiKey=api_key, datasetName=dataset, publicOnly=False)
    matches = [m['datasetName'] for m in datasets]
    if len(matches) > 1 and not any([m == dataset for m in matches]):
        message(['Multiple dataset matches found, please select only 1: ']
                + ['* [%s]: %s' % (m['datasetName'], m['datasetFullName']) for m in datasets], stop=True)

    search = dict(apiKey=api_key, datasetName=dataset, maxResults=N)
    if fields:
        search.update(EarthExplorer.additionalCriteriaValues(api_key, dataset, fields))
    if temporal:
        search.update(EarthExplorer.temporalCriteria(temporal=temporal))

    search['maxCloudCover'] = maxcloudcover
    results = EarthExplorer.search(**search)
    n_results = results['totalHits']
    product_ids = results['results']

    message('Total search results: %d \n' % n_results)
    logger.info('Total search results: %d' % n_results)
    if len(product_ids) < 1:
        logger.error('No valid products returned')
        return

    if not os.path.exists(directory):
        os.makedirs(directory)

    # current users only allowed sending 1 request
    download_pool = FixedThreadPoolExecutor(threads)
    for pids in product_ids:
        entities = pids['entityId']
        download_pool.submit(download_executor, api_key, dataset, entities, products, directory, logger)
    download_pool.drain()
    download_pool.close()

if __name__ == '__main__':
    download_m2m(**vars(build_command_line_arguments()))
