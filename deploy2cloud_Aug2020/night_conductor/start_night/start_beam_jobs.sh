#! /bin/bash
# Starts the Beam/Dataflow job(s) and waits for status = RUNNING

brokerdir=$1
bucket=$2
cd ${brokerdir}

# copy the broker's Beam directory from GCS and cd in
gsutil cp -r gs://${bucket}/beam .
cd beam
beamdir=$(pwd)

# copy beam_helpers modules to job dirs
mkdir -p ztf_bq_sink/beam_helpers
cp beam_helpers/__init__.py beam_helpers/data_utils.py ztf_bq_sink/beam_helpers/.
cp -r beam_helpers ztf_value_added/.

# set configs
source jobs.config ${beamdir}

# start the ztf-value_added job
cd ztf_value_added
timeout 3 \
    python3 beam_ztf_value_added.py \
            --experiments use_runner_v2 \
            --setup_file ${setup_file_valadd} \
            --runner ${runner} \
            --region ${region} \
            --project ${PROJECTID} \
            --job_name ${dataflow_job_name_valadd} \
            --max_num_workers ${max_num_workers_valadd} \
            --staging_location ${staging_location} \
            --temp_location ${temp_location} \
            --PROJECTID ${PROJECTID} \
            --source_PS_ztf ${source_PS_ztf} \
            --sink_BQ_salt2 ${sink_BQ_salt2} \
            --sink_PS_exgalTrans ${sink_PS_exgalTrans} \
            --sink_PS_salt2 ${sink_PS_salt2} \
            --streaming

# Start the ztf -> BQ job
cd ${beamdir} && cd ztf_bq_sink
python3 beam_ztf_bq_sink.py \
            --experiments use_runner_v2 \
            --setup_file ${setup_file_bqsink} \
            --runner ${runner} \
            --region ${region} \
            --project ${PROJECTID} \
            --job_name ${dataflow_job_name_bqsink} \
            --max_num_workers ${max_num_workers_bqsink} \
            --staging_location ${staging_location} \
            --temp_location ${temp_location} \
            --PROJECTID ${PROJECTID} \
            --source_PS_ztf ${source_PS_ztf} \
            --sink_BQ_originalAlert ${sink_BQ_originalAlert} \
            --streaming
