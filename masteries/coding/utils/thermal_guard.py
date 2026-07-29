import subprocess
import time
import torch
import gc


def assert_safe_thermals(max_temp=78, cooldown_seconds=180):
    """
    Monitors GPU temperature and memory using nvidia-smi.
    If GPU temperature exceeds max_temp, forces a cooldown.
    Raises RuntimeError if temperature exceeds safety limit after cooldown.
    """
    try:
        # Run nvidia-smi
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu,memory.used",
                "--format=csv,noheader,nounits",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        # Parse output (assuming single GPU for simplicity)
        output = result.stdout.strip().split("\n")[0]
        temp_str, mem_str = output.split(", ")
        temp = int(temp_str)
        mem = int(mem_str)

        if temp > max_temp:
            print(
                f"\n[THERMAL GUARD] Warning: GPU temperature is {temp}C (Threshold: {max_temp}C)."
            )
            print("[THERMAL GUARD] Forcing memory cleanup and cooling down...")

            # Clean up memory
            gc.collect()
            torch.cuda.empty_cache()

            # Sleep to let GPU cool
            time.sleep(cooldown_seconds)

            # Re-check temperature
            result_after = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            temp_after = int(result_after.stdout.strip().split("\n")[0])
            if temp_after > 83:
                raise RuntimeError(
                    f"THERMAL ABORT: GPU overheating ({temp_after}C after cooldown)"
                )
            else:
                print(
                    f"[THERMAL GUARD] Cooldown successful. GPU temperature is now {temp_after}C."
                )

        return temp, mem

    except FileNotFoundError:
        print("[THERMAL GUARD] nvidia-smi not found. Skipping thermal checks.")
        return -1, -1
    except subprocess.CalledProcessError as e:
        print(f"[THERMAL GUARD] Failed to run nvidia-smi: {e}")
        return -1, -1
