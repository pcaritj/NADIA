import yaml
import pathlib
import numpy as np
import time
import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants
import tqdm

config = yaml.load(open('test_config.yaml'))

results = SoapySDR.Device.enumerate()
for result in results: print(result)

buffer = np.empty(
    int(float(config['sample_rate_hz'])*float(config['observation_secs'])), 
    np.complex64)

path = pathlib.Path(config['data_dir']).mkdir(parents=True, exist_ok=True) 
path = pathlib.Path(config['data_dir'])

args = dict(driver=config['driver'])
sdr = SoapySDR.Device(args)

with open(path.joinpath('params.yaml'), 'w') as outfile:
    yaml.dump(config, outfile, default_flow_style=False)



start = time.time()
interval = "0"
intervals = []

rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)

for i in tqdm.tqdm(range(0,100)):

    sdr.setFrequency(SOAPY_SDR_RX, 0, float(config['center_freq_hz']))
    sdr.setSampleRate(SOAPY_SDR_RX, 0, float(config['sample_rate_hz']))
    sdr.setGain(SOAPY_SDR_RX, 0, int(config['gain']))
    
    sdr.activateStream(rxStream) #start streaming
    sr = sdr.readStream(rxStream, [buffer], len(buffer))

    np.savez_compressed(path.joinpath(interval), buffer)

    sdr.setFrequency(SOAPY_SDR_RX, 0, float(config['blank_freqs_hz'][0]))
    sdr.setSampleRate(SOAPY_SDR_RX, 0, float(config['sample_rate_hz']))
    sdr.setGain(SOAPY_SDR_RX, 0, int(config['gain']))
    
    sdr.activateStream(rxStream) #start streaming
    sr = sdr.readStream(rxStream, [buffer], len(buffer))
    np.savez_compressed(path.joinpath(interval+"_blank"), buffer)

    with open(path.joinpath("intervals"), "a") as f:
        f.write(interval +"\n")
    time.sleep(config['observe_every_secs'])
    interval = str(time.time()-start)