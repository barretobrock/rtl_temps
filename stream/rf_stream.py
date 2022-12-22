from pathlib import Path
import subprocess

from kavalkilu import Hosts
from pukr import get_logger

LOG_DIR = Path().home().joinpath('logs/rf')
LOG_DIR.mkdir(exist_ok=True)

logg = get_logger(log_name='rf_stream', log_dir_path=LOG_DIR)
serv_ip = Hosts().get_ip_from_host('altserv')
cmd = ['/usr/local/bin/rtl_433', '-F', f'syslog:{serv_ip}:1433']

logg.info(f'Sending command: {" ".join(cmd)}')
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
process_output, _ = process.communicate()
logg.debug(f'Process output: {process_output}')
