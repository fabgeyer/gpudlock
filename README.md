# Distributed GPU lock

**gpudlock** is a small python library to share Nvidia GPUs between multiple processes.
The library performs the following steps:

1. Probes the system with `nvidia-smi` to know the current usage of GPUs;
2. Iterates through the unused GPUs and locks one using a distributed lock.

The distributed lock mechanism is based on [redis](http://redis.io/topics/distlock) using the [redlock-py](https://github.com/SPSCommerce/redlock-py) library.


## Library installation

```
$ sudo apt install redis-server
$ pip install --upgrade https://github.com/fabgeyer/gpudlock/archive/master.tar.gz
```


## Library usage

Directly in python:

```python
from gpudlock import select_gpu

def main():
	...
	try:
		select_gpu()
	except:
		print("Failed to allocate GPU")
	...
```

In a bash script:

```bash
#!/bin/sh

export CUDA_VISIBLE_DEVICES=`gpudlock --random`
```
