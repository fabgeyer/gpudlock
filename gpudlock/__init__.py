#!/usr/bin/env python

import os
import sys
import random
import platform
import subprocess
from redlock import Redlock


def hide_gpu():
    """Sets the CUDA_VISIBLE_DEVICES environment variable to empty
    """
    os.environ['CUDA_VISIBLE_DEVICES'] = ''


def select_gpu(redis_conf=None, timeout=10000, shuffle=True):
    """Sets the CUDA_VISIBLE_DEVICES environment variable

    :param redis_conf: Redis configuration passed to redlock-py
    :param timeout: Timeout of the lock in milliseconds, default 10000
    :param shuffle: Shuffles the available GPU list, default True
    """
    if len(os.environ.get('CUDA_VISIBLE_DEVICES', 'unset')) == 0:
        # Environment variable empty
        return ""

    gpu_status = str(subprocess.check_output(['nvidia-smi', 'pmon', '-c', '1']))
    # Example of expected result from nvidia-smi:
    #   # gpu        pid  type    sm   mem   enc   dec   command
    #   # Idx          #   C/G     %     %     %     %   name
    #       0      25729     C    94    57     0     0   python
    #       1          -     -     -     -     -     -   -
    gpu_status = map(lambda x: x.split(), gpu_status.split("\n")[2:-1])

    # Check if the GPU is not already used by the current process
    pid = os.getpid()
    gpu_pids = map(lambda x: x[:2], gpu_status)
    for gpu, p in gpu_pids:
        if p == '-':
            continue
        if pid == int(p):
            return int(gpu)

    gpu_status = filter(lambda x: x[7] == '-', gpu_status)
    if shuffle:
        # Suffle GPUs list
        random.shuffle(gpu_status)

    if redis_conf is None:
        redis_conf = {'unix_socket_path': '/var/run/redis/redis-server.sock'}
    dlm = Redlock([redis_conf])

    if len(gpu_status) > 0:
        for gpu_ in gpu_status:
            gpu = gpu_[0]
            gpu_lock = dlm.lock("{}:gpu{}".format(platform.node(), gpu), timeout)
            if gpu_lock != False:
                os.environ['CUDA_VISIBLE_DEVICES'] = gpu
                return int(gpu)

    raise Exception("No GPU available!")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--random', action='store_true')
    parser.add_argument('--timeout', type=int, default=10000, help='Lock timeout (in milliseconds)')
    args = parser.parse_args()
    try:
        print(select_gpu(**vars(args)))
    except:
        print("Failed to lock GPU")
        sys.exit(1)


if __name__ == "__main__":
    main()
