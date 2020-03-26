import io
import fastavro


# taken from
# https://github.com/lsst-dm/sample-avro-alert/blob/master/python/lsst/alert/packet/schema.py
def resolve_schema_definition(to_resolve, seen_names=None):
    """Fully resolve complex types within a schema definition.
    That is, if this schema is defined in terms of complex types,
    substitute the definitions of those types into the returned copy.
    Parameters
    ----------
    schema : `list`
        The output of `fastavro.schema.load_schema`.
    Returns
    -------
    resolved_schema : `dict`
        The fully-resolved schema definition.
    Notes
    -----
    The schema is resolved in terms of the types which have been parsed
    and stored by fastavro (ie, are found in
    `fastavro.schema._schema.SCHEMA_DEFS`).
    The resolved schemas are supplied with full names and no namespace
    (ie, names of the form ``full.namespace.name``, rather than a
    namespace of ``full.namespace`` and a name of ``name``).
    """
    schema_defs = fastavro.schema._schema.SCHEMA_DEFS

    # Names of records, enums, and fixeds can only be used once in the
    # expanded schema. We'll re-use, rather than re-defining, names we have
    # previously seen.
    seen_names = seen_names or set()

    if isinstance(to_resolve, dict):
        # Is this a record, enum, or fixed that we've already seen?
        # If so, we return its name as a string and do not resolve further.
        if to_resolve['type'] in ('record', 'enum', 'fixed'):
            if to_resolve['name'] in seen_names:
                return to_resolve['name']
            else:
                seen_names.add(to_resolve['name'])
        output = {}
        for k, v in to_resolve.items():
            if k == "__fastavro_parsed":
                continue
            elif isinstance(v, list) or isinstance(v, dict):
                output[k] = resolve_schema_definition(v, seen_names)
            elif v in schema_defs and k != "name":
                output[k] = resolve_schema_definition(schema_defs[v],
                                                      seen_names)
            else:
                output[k] = v
    elif isinstance(to_resolve, list):
        output = []
        for v in to_resolve:
            if isinstance(v, list) or isinstance(v, dict):
                output.append(resolve_schema_definition(v, seen_names))
            elif v in schema_defs:
                output.append(resolve_schema_definition(schema_defs[v],
                                                        seen_names))
            else:
                output.append(v)
    else:
        raise Exception("Failed to parse.")

    return output

# the reset are taken from
# https://github.com/lsst-dm/sample-avro-alert/pull/5/commits/d6cfb400da80d768424c047f3436481146bf66fc
def load_schema(filename=None):
    """Load an Avro schema, potentially spread over muliple files.
    Parameters
    ----------
    filename : `str`, optional
        Path to the schema root. Will recursively load referenced schemas,
        assuming they can be found; otherwise, will raise. If `None` (the
        default), will load the latest schema defined in this package.
    Returns
    -------
    schema : `dict`
        Parsed schema information.
    Todo
    ----
    Should take a `version` argument (instead of? as well as?) a filename, and
    return the corresponding schema.
    """
    # if filename is None:
    #     filename = os.path.join(get_schema_root(), "latest", "ztf.alert.avsc")
    return fastavro.schema.load_schema(filename)

def resolve_schema(schema, root_name='ztf.alert'):
    """Expand nested types within a schema.
    That is, if one type is given in terms of some other type, substitute the
    definition of the second type into the definition of the first.
    Parameters
    ----------
    schema : `list` of `dict`
        Schema as returned by `~ztf.alert.load_schema`. Each type definition
        is described by a separate element in the list.
    root_name : `str`
        Name of the root element of the resulting schema. The contituents of
        this are what will be expanded.
    Output
    ------
    expanded_schema : `dict`
        A single dictionary describing the expanded schema.
    """
    def expand_types(input_data, data_types):
        """Recursively substitute `data_types` into `input_data`.
        """
        if isinstance(input_data, dict):
            output = {}
            for k, v in input_data.items():
                if k == "__fastavro_parsed":
                    continue
                elif isinstance(v, list) or isinstance(v, dict):
                    output[k] = expand_types(v, data_types)
                elif v in data_types.keys():
                    output[k] = data_types[v]
                else:
                    output[k] = v
        elif isinstance(input_data, list):
            output = []
            for v in input_data:
                if isinstance(v, list) or isinstance(v, dict):
                    output.append(expand_types(v, data_types))
                elif v in data_types.keys():
                    output.append(data_types[v])
                else:
                    output.append(v)
        else:
            raise Exception("Failed to parse.")

        return output

    schema_types = {entry['name'] : entry for entry in schema}
    schema_root = schema_types.pop('ztf.alert')
    return expand_types(schema_root, schema_types)

def write_avro_data(data, schema):
    """Create an Avro representation of data following a given schema.
    Parameters
    ----------
    data : `dict`
        The data to be serialized to Avro.
    schema : `dict`
        The schema according to which the data will be written.
    Returns
    -------
    avro_data : `bytes`
        An Avro serialization of the input data.
    """
    bytes_io = io.BytesIO()
    fastavro.schemaless_writer(bytes_io, schema, data)
    return bytes_io.getvalue()
