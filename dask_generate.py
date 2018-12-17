import glob
#from DeepForest import config
from DeepForest import Generate,config
from dask import compute, delayed

import subprocess
import socket

import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

def find_csvs():
    """
    Find training csvs on path
    """
    DeepForest_config = config.load_config("train")
    data_paths = glob.glob(DeepForest_config['training_csvs']+"/*.csv")
    
    return data_paths

def run_local(data_paths):
    """
    Run training processes on local laptop
    """
    
    #Local threading/processes, set scheduler.
    values = [delayed(Generate.run)(x) for x in data_paths]
    
    #Compute tiles    
    results = compute(*values, scheduler='processes')    
    
    return results
    
### HiperGator ####

#Start juypter notebook to watch
def start_tunnel():
    """
    Start a juypter session and ssh tunnel to view task progress
    """
    host = socket.gethostname()        
    proc = subprocess.Popen(['jupyter', 'lab', '--notebook-dir', '/home/b.weinstein/logs/', '--ip', host, '--no-browser'])
    print("To tunnel into dask dashboard:")
    print("ssh -N -L 8888:%s:8888 -l b.weinstein hpg2.rc.ufl.edu" % (host))
    
def run_HPC(data_paths):
        
    #################
    # Setup dask cluster
    #################
    
    from dask_jobqueue import SLURMCluster
    from dask.distributed import Client
    from dask import delayed
    
    #job args
    extra_args=[
        "--error=/home/b.weinstein/logs/dask-worker.err",
        "--account=ewhite",
        "--output=/home/b.weinstein/logs/dask-worker.out"
    ]
    
    cluster = SLURMCluster(processes=1,queue='hpg2-compute',cores=1, memory='8GB', walltime='48:00:00',job_extra=extra_args,local_directory="/home/b.weinstein/logs/")
    
    print(cluster.job_script())
    cluster.scale(2)
    
    dask_client = Client(cluster)
        
    #Start dask dashboard? Not clear yet.
    dask_client.run_on_scheduler(start_tunnel)    
    
    # Local threading/processes, set scheduler.
    values = [delayed(Generate.run)(x) for x in data_paths]
    
    #Compute tiles    
    results = compute(*values, scheduler='processes')    
    return results

if __name__ == "__main__":
    
    #Local Debugging
    data_paths=find_csvs()[:2]

    print("{s} csv files found for training".format(s=len(data_paths)))
    
    #run_local(data_paths)
    
    #On Hypergator
    run_HPC(data_paths)
    