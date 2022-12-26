#!/usr/bin/env python3
"""
ETL for RTL_433 json objects via syslog -> processed Dataframe -> influx

Note: depends on `rf_stream` already being running and feeding data to port 1433
    via `rtl_433 -F syslog::1433`
"""
from datetime import datetime
import json
from json import JSONDecodeError
from pathlib import Path
import socket
from typing import (
    Dict,
    Optional,
    Union
)

from kavalkilu import (
    GracefulKiller,
    HAHelper,
    Hosts
)
import pandas as pd
from pukr import get_logger


LOG_DIR = Path().home().joinpath('logs/rf')
LOG_DIR.mkdir(exist_ok=True)
logg = get_logger(log_name='rf_collect', log_dir_path=LOG_DIR, base_level='INFO')


DATA_DIR = Path().home().joinpath('data/rf')
DATA_DIR.mkdir(exist_ok=True)
unknown_devs_file = DATA_DIR.joinpath(f'unknown_devs_{datetime.today():%F}.csv')

UDP_IP = Hosts().get_ip_from_host('altserv')
UDP_PORT = 1433

hass = HAHelper()
killer = GracefulKiller()

# device id to device-specific data mapping
mappings: Dict[int, Dict[str, Union[str, Optional[int]]]]
mappings = {
    3092: {'name': 'rf_mgm_tba'},
    5252: {'name': 'rf_elu_tba'},
    8416: {'name': 'rf_rdu_lne'},
    9459: {'name': 'rf_kok_kyt'},
    9533: {'name': 'rf_knt_tba'},
    10246: {'name': 'rf_kok_uks'},
    12476: {'name': 'rf_swc_tba'},
    13455: {'name': 'rf_unk_uk1'},
    14539: {'name': 'rf_kok_kkp'},
    15227: {'name': 'rf_rdu_ida'}
}

# Map the names of the variables from the various sensors to what's acceptable in the db
possible_measurements = {
    'temperature_C': {'suffix': 'temp', 'data_class': 'temperature'},
    'humidity': {'suffix': 'hum', 'data_class': 'humidity'}
}


def parse_syslog(ln: bytes) -> str:
    """Try to extract the payload from a syslog line."""
    ln = ln.decode("ascii")  # also UTF-8 if BOM
    if ln.startswith("<"):
        # fields should be "<PRI>VER", timestamp, hostname, command, pid, mid, sdata, payload
        fields = ln.split(None, 7)
        ln = fields[-1]
    return ln


logg.debug('Establishing socket...')
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.bind((UDP_IP, UDP_PORT))

unknown_devs_df = pd.DataFrame()
last_dt = datetime.now().date()     # For reporting daily unknown devices
start_s = int(datetime.now().timestamp())
interval_s = 60     # Update values every minute

logg.debug('Beginning loop!')
while not killer.kill_now:
    line, _addr = sock.recvfrom(1024)
    # Convert line from bytes to str, prep for conversion into dict
    line = parse_syslog(line)
    data = None
    try:
        data = json.loads(line)
    except JSONDecodeError as e:
        logg.error(e, f'Unable to parse this object. Skipping. \n {line}')
        continue

    if "model" not in data:
        # Exclude anything that doesn't contain a device 'model' key
        logg.info('Skipping, missed "model" key: '
                  f'{json.dumps(data, indent=2)}')
        unknown_devs_df = pd.concat([unknown_devs_df, pd.DataFrame(data, index=[0])])
        continue

    # Begin processing the data
    if data is not None:
        # Begin extraction process
        dev_id = data.get('id')
        rcv_time = data.get('time')
        dev_model = data.get('model')
        logg.debug(f'Receiving from device: {dev_model} ({dev_id})')
        if dev_id in mappings.keys():
            # Device is known sensor... record data
            dev_dict = mappings[dev_id]
            name = dev_dict['name']
            last_update = dev_dict.get('last_update', start_s)
            logg.debug(f'Device identified. Name: {name}.')
            for measurement_name, detail_dict in possible_measurements.items():
                if datetime.now().timestamp() - last_update > interval_s:
                    logg.debug('Interval lapsed. Sending measurements to HASS...')
                    hass.set_state(
                        device_name=f'sensor.{name}_{detail_dict["suffix"]}',
                        data={'state': data[measurement_name]},
                        data_class=detail_dict['data_class']
                    )
                    mappings[dev_id]['last_update'] = int(datetime.now().timestamp())
        else:
            logg.info(f'Unknown device found: {dev_model}: ({dev_id})\n'
                      f'{json.dumps(data, indent=2)}')
            unknown_devs_df = pd.concat([unknown_devs_df, pd.DataFrame(data, index=[0])])

    if last_dt != datetime.now().date() and unknown_devs_df.shape[0] > 0:
        # Report on found unknown devices
        logg.debug(f'Saving {unknown_devs_df.shape[0]} unknown devs to file...')
        unknown_devs_df.to_csv(unknown_devs_file, index=False, sep=';', mode='a')
        logg.debug('Resetting unknown device df.')
        unknown_devs_df = pd.DataFrame()
        unknown_devs_file = DATA_DIR.joinpath(f'unknown_devs_{datetime.today():%F}.csv')
        last_dt = datetime.now().date()


logg.debug('Collection ended.')
