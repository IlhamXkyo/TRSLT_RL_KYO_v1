import pyaudiowpatch as pyaudio
import time

p = pyaudio.PyAudio()
try:
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = p.get_device_info_by_index(wasapi_info['defaultOutputDevice'])
    loopback_dev = None
    for dev in p.get_loopback_device_info_generator():
        if default_speakers['name'] in dev['name']:
            loopback_dev = dev
            break
    print("Found Loopback:", loopback_dev['name'])
    
    count = [0]
    def callback(in_data, frame_count, time_info, status):
        count[0] += 1
        return (None, pyaudio.paContinue)

    stream = p.open(
        format=pyaudio.paInt16,
        channels=loopback_dev['maxInputChannels'],
        rate=int(loopback_dev['defaultSampleRate']),
        input=True,
        input_device_index=loopback_dev['index'],
        stream_callback=callback
    )
    stream.start_stream()
    time.sleep(1)
    stream.stop_stream()
    stream.close()
    print("Success! Chunks received:", count[0])
except Exception as e:
    print("Error:", e)
finally:
    p.terminate()
