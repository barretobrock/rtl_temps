# rtl_temps
Wrapper for setting up rtl_433 system for primarily temperature collection

This project essentially runs 2 daemons who:  
 - (stream) listen for incoming transmissions on 433MHz and
 - (collect) collect information from those transmissions 

## Setup Process
### Clone the repo
```bash
git clone https://github.com/merbanan/rtl_433.git ~/extras/rtl_433/
```
### Install deps
#### Ubuntu
```bash
sudo apt install libtool libusb-1.0-0-dev librtlsdr-dev rtl-sdr build-essential autoconf cmake pkg-config
```
#### Arch/Manjaro
```bash
sudo pacman -Sy libtool libusb rx_tools rtl-sdr autoconf cmake pkg-config
```
### Installation via `cmake`
```bash
cd rtl_433/
mkdir build
cd build
cmake ..
make
make install
```

### Service Load
```bash
sh api/rf_temps/load_rf_stream_service.sh
sh api/rf_temps/load_rf_collect_service.sh
sudo systemctl start rf_stream
sudo systemctl start rf_collect
```

## Resources
- This was helpful in trying to understand the parameters: [INTEGRATION](https://triq.org/rtl_433/INTEGRATION.html)
- Actual docs on [rtl_433](https://github.com/merbanan/rtl_433#user-content-running)
- You'll need a RTL-SDR dongle that supports listening on 433MHz. For this project, I used the [Nooelec NESDR Mini USB RTL-SDR](https://www.nooelec.com/store/sdr/sdr-receivers/nesdr-mini.html)