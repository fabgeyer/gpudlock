#!/usr/bin/env python

import os
import sys
import random
import platform
import subprocess
from redlock import Redlock


class GPUAvailabilityException(Exception):
    pass


def hide_gpu():
    """Sets the CUDA_VISIBLE_DEVICES environment variable to empty
    """
    os.environ['CUDA_VISIBLE_DEVICES'] = ''


def select_gpu(redis_conf=None, timeout=10000, shuffle=True, set_environ=True):
    """Sets the CUDA_VISIBLE_DEVICES environment variable

    :param redis_conf: Redis configuration passed to redlock-py
    :param timeout: Timeout of the lock in milliseconds, default 10000
    :param shuffle: Shuffles the available GPU list, default True
    """
    if len(os.environ.get('CUDA_VISIBLE_DEVICES', 'unset')) == 0:
        # Environment variable empty
        return "", None

    gpu_status = subprocess.check_output(['nvidia-smi', 'pmon', '-c', '1'])
    # Example of expected result from nvidia-smi:
    #   # gpu        pid  type    sm   mem   enc   dec   command
    #   # Idx          #   C/G     %     %     %     %   name
    #       0      25729     C    94    57     0     0   python
    #       1          -     -     -     -     -     -   -
    gpu_status = list(map(lambda x: x.split(), gpu_status.splitlines()[2:]))

    # Check if the GPU is not already used by the current process
    pid = os.getpid()
    gpu_pids = list(map(lambda x: x[:2], gpu_status))
    for gpu, p in gpu_pids:
        if p.isdigit() and pid == int(p):
            return int(gpu), None

    gpu_status = list(filter(lambda x: not x[1].isdigit(), gpu_status))
    if shuffle:
        # Suffle GPUs list
        random.shuffle(gpu_status)

    if redis_conf is None:
        redis_conf = {'unix_socket_path': '/var/run/redis/redis-server.sock'}
    dlm = Redlock([redis_conf])

    if len(gpu_status) > 0:
        for gpu_ in gpu_status:
            gpu = int(gpu_[0])
            gpu_lock = dlm.lock("{}:gpu{}".format(platform.node(), gpu), timeout)
            if gpu_lock != False:
                if set_environ:
                    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu)

                def unlock():
                    return dlm.unlock(gpu_lock)

                return int(gpu), unlock

    raise GPUAvailabilityException("No GPU available!")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--shuffle', action='store_true')
    parser.add_argument('--timeout', type=int, default=10000, help='Lock timeout (in milliseconds)')
    args = parser.parse_args()
    try:
        gpuid, unlock = select_gpu(**vars(args))
        print(gpuid)
    except GPUAvailabilityException:
        print("Failed to lock GPU")
        sys.exit(1)


if __name__ == "__main__":
    main()
