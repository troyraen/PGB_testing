`FileNotFoundError: [Errno 2] No such file or directory: '/root/.astropy/cache/sncosmo/models/salt2/salt2-4/salt2_template_0.dat' [while running 'fitSalt2-ptransform-3934']`

This file appears to be used in the instantiation of
`model = sncosmo.Model(source='salt2')`

See [sncosmo.SALT2Source](https://sncosmo.readthedocs.io/en/stable/api/sncosmo.SALT2Source.html)

Best guess is that this happens occasionally when workers get reassigned/reconfigured and can't find the file, though it seems like Dataflow should be more fault-tolerant than that.
