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

import apache_beam as beam
import custommods.beam_helpers as bhelp

# gcp resources
PROJECTID = 'ardent-cycling-243415'
dataflow_job_name = 'salt2-fits'
beam_bucket = 'ardent-cycling-243415_dataflow-test'
input_bq_table = 'ztf_alerts.alerts'
output_bq_table = 'ztf_alerts.salt2'

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

def salt2fit(alert):
    """ Performs a Salt2 fit on alert history.

    Args:
        alert (dict): dictionary of alert data from ZTF

    Returns:
        salt2_fit (dict): output of Salt2 fit, formatted for upload to BQ
    """
    import sncosmo
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
    result['cov_names'] = result['vparam_names']
    flatres = dict(sncosmo.flatten_result(result))


    # param_dict = {result.param_names[i]: result.parameters[i] for i in range(len(result.param_names))}
    return {'candid': candid,
            'ndof': result.ndof
            }
output_schema = 'candid:INTEGER, ndof:INTEGER'

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
