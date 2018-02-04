import yaml
import pathlib
import numpy as np
import time
import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants
import tqdm
import shutil
import pysftp
import datetime
import os

def getserial():
  # Extract serial from cpuinfo file
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    cpuserial = "ERROR000000000"

  return cpuserial

config = yaml.load(open('test_config.yaml'))

results = SoapySDR.Device.enumerate()
for result in results: print(result)

buffer = np.empty(
    int(float(config['sample_rate_hz'])*float(config['observation_secs'])), 
    np.complex64)


path = pathlib.Path(config['data_dir'])

args = dict(driver=config['driver'])
sdr = SoapySDR.Device(args)





start = None
interval = "0"
intervals = []

rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)

observation_id = None

while True:
    if start is None or time.time()-start > config['upload_every_secs']:

        if start is not None:
            # Zip, upload, and clear results

            # ZIP
            zip_filename = observation_id+'.zip'
            shutil.make_archive(observation_id, 'zip', path)
            print ("Uploading %s to %s" % (zip_filename, config['upload_uri']))
            #UPLOAD
            with pysftp.Connection(config['upload_uri'], 
                username=config['upload_username'], 
                password=config['upload_password']) as sftp:
                with sftp.cd(config['upload_path']):
                    sftp.put(zip_filename) 
            # DELETE
            shutil.rmtree(path)
            if os.path.isfile(zip_filename):
                os.unlink(zip_filename)

        pathlib.Path(path).mkdir(parents=True, exist_ok=True)

        start = time.time()
        observation_id = getserial()+"_"+str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f"))
        with open(path.joinpath('params.yaml'), 'w') as outfile:
            yaml.dump(config, outfile, default_flow_style=False)



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