# 11/3/20

# function call
run in jupyter notebook on Roy in conda env pgb2

```python

from confluent_kafka import Consumer, KafkaException
import os
import sys

os.environ['KRB5_CONFIG'] = './krb5.conf'
# Consumer configuration
# See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
conf = {
            'bootstrap.servers': 'public2.alerts.ztf.uw.edu:9094',
            'group.id': 'group',
            'session.timeout.ms': 6000,
            'enable.auto.commit': 'TRUE',
            'sasl.kerberos.principal': 'pitt-reader@KAFKA.SECURE',
            'sasl.kerberos.kinit.cmd': 'kinit -t "%{sasl.kerberos.keytab}" -k %{sasl.kerberos.principal}',
            'sasl.kerberos.keytab': './pitt-reader.user.keytab',
            'sasl.kerberos.service.name': 'kafka',
            'security.protocol': 'SASL_PLAINTEXT',
            'sasl.mechanisms': 'GSSAPI',
            'auto.offset.reset': 'earliest'
            }

# Create Consumer instance
# Hint: try debug='fetch' to generate some log messages
c = Consumer(conf, debug='fetch')

# Subscribe to topics
c.subscribe(['ztf_20201031_programid1'])

# Read messages from Kafka, print to stdout
i=0
try:
    while True:
        print('while True')

        msg = c.poll(timeout=5.0)
#         msg = c.consume(num_messages=1, timeout=1)
        print(msg)
#         break

        if msg is None:
            print('continue')
            continue
        if msg.error():
            print('error')
            raise KafkaException(msg.error())
        else:
            print('else')
            # Proper message
            sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' %
                             (msg.topic(), msg.partition(), msg.offset(),
                              str(msg.key())))
            print(msg.value())
            break

except KeyboardInterrupt:
        sys.stderr.write('%% Aborted by user\n')

finally:
        # Close down consumer to commit final offsets.
        c.close()

```

# notebook output
```
while True
None
continue
while True
None
continue
# continued until manually force terminate
```

# terminal output
```bash
# c.subscribe(['ztf_20201031_programid1']) produces:
%7|1604454996.048|INIT|rdkafka#consumer-1| [thrd:app]: librdkafka v1.5.0 (0x10500ff) rd
kafka#consumer-1 initialized (builtin.features gzip,snappy,ssl,sasl,regex,lz4,sasl_gssa
pi,sasl_plain,sasl_scram,plugins,sasl_oauthbearer, CC CXX OSXLD LIBDL PLUGINS ZLIB SSL
SASL_CYRUS HDRHISTOGRAM LZ4_EXT SYSLOG SNAPPY SOCKEM SASL_SCRAM SASL_OAUTHBEARER CRC32C
_HW, debug 0x400)
%7|1604454996.226|PROTOERR|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.zt
f.uw.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/bootstrap: Pr

otocol parse failure for ApiVersion v3 at 3/6 (rd_kafka_handle_ApiVersion:1945) (incorr
ect broker.version.fallback?)
%7|1604454996.226|PROTOERR|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.zt
f.uw.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/bootstrap: Ap
iArrayCnt -1 out of range
%5|1604454996.396|LIBSASL|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.ztf
.uw.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/bootstrap: GSS
API client step 1
%5|1604454996.985|LIBSASL|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.ztf
.uw.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/bootstrap: GSS
API client step 1
%5|1604454997.070|LIBSASL|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.ztf
.uw.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/bootstrap: GSS
API client step 2
# i don't think I've seen this PROTOERR before 11/3/20:
%7|1604454997.497|PROTOERR|rdkafka#consumer-1| [thrd:GroupCoordinator]: GroupCoordinato
r/0: Protocol parse failure for ApiVersion v3 at 3/6 (rd_kafka_handle_ApiVersion:1945)
(incorrect broker.version.fallback?)
%7|1604454997.497|PROTOERR|rdkafka#consumer-1| [thrd:GroupCoordinator]: GroupCoordinato
r/0: ApiArrayCnt -1 out of range
%5|1604454997.664|LIBSASL|rdkafka#consumer-1| [thrd:GroupCoordinator]: GroupCoordinator
/0: GSSAPI client step 1
%5|1604454997.789|LIBSASL|rdkafka#consumer-1| [thrd:GroupCoordinator]: GroupCoordinator
/0: GSSAPI client step 1
%5|1604454997.875|LIBSASL|rdkafka#consumer-1| [thrd:GroupCoordinator]: GroupCoordinator
/0: GSSAPI client step 2
# try statement produces:
# ... repeated, similar messages; here are the last ones before I restarted the kernel
%7|1604453408.556|FETCH|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.ztf.u
w.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/0: Fetch topic z
tf_20201031_programid1 [8] at offset 13187 (v2)
%7|1604453408.556|FETCH|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.ztf.u
w.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/0: Fetch topic z
tf_20201031_programid1 [9] at offset 13187 (v2)
%7|1604453408.556|FETCH|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.ztf.u
w.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/0: Fetch topic z

tf_20201031_programid1 [10] at offset 13187 (v2)
%7|1604453408.556|FETCH|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.ztf.u
w.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/0: Fetch topic z
tf_20201031_programid1 [11] at offset 13187 (v2)
%7|1604453408.556|FETCH|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.ztf.u
w.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/0: Fetch topic z
tf_20201031_programid1 [12] at offset 13187 (v2)
%7|1604453408.556|FETCH|rdkafka#consumer-1| [thrd:sasl_plaintext://public2.alerts.ztf.u
w.edu:9094/bootstrap]: sasl_plaintext://public2.alerts.ztf.uw.edu:9094/0: Fetch 16/16/1
6 toppar(s)
```
