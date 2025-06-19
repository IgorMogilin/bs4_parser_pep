from pathlib import Path


BASE_DIR = Path(__file__).parent
MAIN_DOC_URL = 'https://docs.python.org/3/'
PEP8_DOC_URL = 'https://peps.python.org/'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
MAX_BYTES_LOGFILE = 1_048_576
LOG_BACKUP_COUNT = 5
OUTPUT_TABLE = 'pretty'
OUTPUT_FILE = 'file'
LOGS_DIR = 'logs'
DOWNLOADS_DIR = 'downloads'
RESULTS_DIR = 'results'
