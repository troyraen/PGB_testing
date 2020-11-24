# -*- coding: utf-8 -*-
# +----------------+
# |                |
# | Read BigQuery  |
# |                |
# +-------+--------+
#         |
#         v
# +-------+--------+
# |                |
# | Modify Element |
# |                |
# +----------------+
#         |
#         v
# +-------+--------+
# |                |
# | Write BigQuery |
# |                |
# +----------------+

# from tempfile import SpooledTemporaryFile
import apache_beam as beam
# from apache_beam.io.localfilesystem import LocalFileSystem
# from apache_beam.options.pipeline_options import PipelineOptions
# from google.cloud import logging as cloud_logging
# from google.cloud import storage

import custommods.beam_helpers as bhelp

# lfs = LocalFileSystem(PipelineOptions())  # instantiate classes
# lfs.mkdirs('plotlc_temp')

# logging_client = cloud_logging.Client()
# log_name = 'salt2-dataflow'
# logger = logging_client.logger(log_name)

# gcp resources
PROJECTID = 'ardent-cycling-243415'
dataflow_job_name = 'salt2-fits2'
beam_bucket = 'ardent-cycling-243415_dataflow-test'
input_bq_table = 'ztf_alerts.alerts'
output_bq_table = 'ztf_alerts.salt2'

# storage_client = storage.Client()
# bucket = storage_client.get_bucket(beam_bucket)

# beam options
options = beam.options.pipeline_options.PipelineOptions()
gcloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
gcloud_options.job_name = dataflow_job_name
gcloud_options.project = PROJECTID
gcloud_options.staging_location = f'gs://{beam_bucket}/staging'
gcloud_options.temp_location = f'gs://{beam_bucket}/temp'
worker_options = options.view_as(beam.options.pipeline_options.WorkerOptions)
worker_options.disk_size_gb = 50
worker_options.max_num_workers = 6
# worker_options.num_workers = 2
# worker_options.machine_type = 'n1-standard-8'
options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'
# output_schema must match salt2fit() return
# output_schema = 'candid:INTEGER, success:INTEGER, ncall:INTEGER, chisq:FLOAT, ndof:INTEGER, z:FLOAT, z_err:FLOAT, t0:FLOAT, t0_err:FLOAT, x0:FLOAT, x0_err:FLOAT, x1:FLOAT, x1_err:FLOAT, c:FLOAT, c_err:FLOAT, z_z_cov:FLOAT, z_t0_cov:FLOAT, z_x0_cov:FLOAT, z_x1_cov:FLOAT, z_c_cov:FLOAT, t0_z_cov:FLOAT, t0_t0_cov:FLOAT, t0_x0_cov:FLOAT, t0_x1_cov:FLOAT, t0_c_cov:FLOAT, x0_z_cov:FLOAT, x0_t0_cov:FLOAT, x0_x0_cov:FLOAT, x0_x1_cov:FLOAT, x0_c_cov:FLOAT, x1_z_cov:FLOAT, x1_t0_cov:FLOAT, x1_x0_cov:FLOAT, x1_x1_cov:FLOAT, x1_c_cov:FLOAT, c_z_cov:FLOAT, c_t0_cov:FLOAT, c_x0_cov:FLOAT, c_x1_cov:FLOAT, c_c_cov:FLOAT'

def modify_data1(element):
    # beam.Map
    # element = {u'corpus_date': 0, u'corpus': u'sonnets', u'word': u'LVII', u'word_count': 1}

    corpus_upper = element['publisher'].upper()
    word_len = len(element['objectId'])

    return {'publisher': corpus_upper,
            'objectId_len': word_len
            }

def salt2fit(alert):
    """ Performs a Salt2 fit on alert history.

    Args:
        alert (dict): dictionary of alert data from ZTF

    Returns:
        salt2_fit (dict): output of Salt2 fit, formatted for upload to BQ
    """
    import sncosmo
    from sncosmo.fitting import DataQualityError
    import custommods.beam_helpers as bhelp

    candid = alert['candid']

    # extract epochs from alert
    epoch_dict = bhelp.extract_epochs(alert)
    # format epoch data for salt2
    epoch_tbl = bhelp.format_for_salt2(epoch_dict)

    # fit with salt2
    model = sncosmo.Model(source='salt2')
    result, fitted_model = sncosmo.fit_lc(epoch_tbl, model,
                            ['z', 't0', 'x0', 'x1', 'c'],  # parameters of model to vary
                            bounds={'z':(0.01, 0.2)},  # https://arxiv.org/pdf/2009.01242.pdf
    )
    # result['cov_names'] = result['vparam_names']
    # flatres = dict(sncosmo.flatten_result(result))

    # try:
    #     result, fitted_model = sncosmo.fit_lc(epoch_tbl, model,
    #                             ['z', 't0', 'x0', 'x1', 'c'],  # parameters of model to vary
    #                             bounds={'z':(0.01, 0.2)},  # https://arxiv.org/pdf/2009.01242.pdf
    #     )
    # except DataQualityError as e:
    #     raise
    #     # msg = f'Candidate ID: {candid}; sncosmo.fitting.DataQualityError: {e}'
    #     # logger.log_text(msg, severity='INFO')

    #     # # dummy data for BQ, should probably be handled at beam level
    #     # oslist = output_schema.split(',')
    #     # cols = [c.strip().split(':')[0] for c in oslist]
    #     # tmap = {'INTEGER':-1, 'FLOAT':-1.0}
    #     # data = [tmap[t.strip().split(':')[1]] for t in oslist]
    #     # flatres = dict(zip(cols,data))
    #     # del flatres['candid']
    # else:
    #     # collect real results
    #     # cov_names depreciated in favor of vparam_names, but flatten_result() requires it
    #     result['cov_names'] = result['vparam_names']
    #     flatres = dict(sncosmo.flatten_result(result))

    #     # filename = f'{candid}.png'
    #     # lfs.create(f'plotlc_temp/{filename}')

    #     # # plot the lightcurve and save in bucket
    #     # with SpooledTemporaryFile(max_size=100000, mode='w') as temp_file:
    #     #     gcs_filename = f'{candid}.png'
    #     #     sncosmo.plot_lc(epoch_tbl, model=fitted_model, errors=result.errors, fname=temp_file)
    #     #     blob = bucket.get_blob(f'sncosmo/plot_lc/{gcs_filename}')


    param_dict = {result.param_names[i]: result.parameters[i] for i in range(len(result.param_names))}
    return {'candid': candid,
            'chisq': result.chisq,
            'ndof': result.ndof,
            **param_dict
            }
output_schema = 'candid:INTEGER, chisq:FLOAT, ndof:INTEGER, z:FLOAT, t0:FLOAT, x0:FLOAT, x1:FLOAT, c:FLOAT'  

p4 = beam.Pipeline(options=options)

query = f'SELECT * FROM {PROJECTID}.{input_bq_table} LIMIT 100'

(p4 | 'Read alert BQ' >> beam.io.Read(beam.io.ReadFromBigQuery(project=PROJECTID,
        use_standard_sql=True, query=query))
    | 'Filter exgal trans' >> beam.Filter(bhelp.is_transient)
    | 'Salt2 fit' >> beam.Map(salt2fit)
    | 'Write to BQ' >> beam.io.Write(beam.io.WriteToBigQuery(output_bq_table,
        schema=output_schema,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE))
 )

p4.run()  # .wait_until_finish()
