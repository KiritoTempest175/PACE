import subprocess
import time

MAX_TEMP = 83


def get_gpu_temp():
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        )
        temps = [
            int(x.strip()) for x in output.strip().split("\n") if x.strip().isdigit()
        ]
        return max(temps) if temps else 0
    except Exception as e:
        print("Could not read GPU temp:", e)
        return 0


def kill_training_script():
    print(f"CRITICAL: GPU Temp exceeded {MAX_TEMP}°C! Taking emergency action.")
    try:
        # Find train.py process and kill it
        output = subprocess.check_output(
            "wmic process where \"commandline like '%masteries/coding/training/critic/train.py%' and name='python.exe'\" get processid",
            shell=True,
            text=True,
        )
        lines = [line.strip() for line in output.split("\n") if line.strip()]
        killed = False
        for line in lines[1:]:  # skip header 'ProcessId'
            if line.isdigit():
                pid = line
                print(f"Killing Train Script PID {pid}...")
                subprocess.call(f"taskkill /F /PID {pid}", shell=True)
                killed = True

        if not killed:
            print(
                "Could not find specific train.py process. Not killing all python just in case."
            )

    except Exception as e:
        print("Error while trying to kill process:", e)


print(
    f"Starting Hardware Watchdog. Monitoring GPU Temp every 60 seconds. Max Temp: {MAX_TEMP}°C"
)
while True:
    temp = get_gpu_temp()
    print(f"Current GPU Temp: {temp}°C")
    if temp >= MAX_TEMP:
        kill_training_script()
        print("Watchdog emergency triggered. Exiting watchdog.")
        break
    time.sleep(60)
