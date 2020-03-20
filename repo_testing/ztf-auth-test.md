# Testing that I can run the notebook `ztf-auth-test.ipynb`

See [here](https://github.com/mwvgroup/Pitt-Google-Broker/blob/master/notebooks/ztf-auth-test.ipynb) for notebook.

```bash
# create new environment
conda env create -f environment.yml -n pgb
conda activate pgb
conda install nb_conda_kernels
conda install -c conda-forge python-confluent-kafka

jupyter notebook
```

I'm able to run 3 cells, but it hangs on the 4th while trying to get an assignment.
