import os
import uuid
import time
import gc
from django.conf import settings
from couchbase import (
    Couchbase,
    OBS_FOUND,
    OBS_LOGICALLY_DELETED,
    OBS_MASK,
    OBS_NOTFOUND,
    OBS_PERSISTED)
from couchbase.connection import LOCKMODE_WAIT
from couchbase.views.params import Query
from couchbase.exceptions import (
    NotFoundError,
    TimeoutError,
    ConnectError,
    BucketNotFoundError,
    KeyExistsError,
    TemporaryFailError,
    NetworkError
)


class ConnectionPool(object):
    instance = None
    instance_uuid = None

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance_uuid = uuid.uuid4()
            cls.instance = cls(cls.instance_uuid)
        return cls.instance

    def __init__(self, instance_uuid=None):
        ## enforce singleton
        if instance_uuid != self.instance_uuid:
            raise RuntimeError('singleton class, use get_instance()')

        ## keys are (bucket, host), values are connection arguments dict
        self.pool = {}

    @staticmethod
    def __connect(**connect_kwargs):
        cbconn = Couchbase.connect(**connect_kwargs)
        conn = {}
        conn['cb'] = cbconn
        conn['pid'] = os.getpid()
        conn['connect_kwargs'] = connect_kwargs
        return conn

    def __connect_manager(self, host, bucket):
        conn_kwargs = {}
        conn_kwargs['bucket'] = bucket
        conn_kwargs['host'] = host
        conn_kwargs['lockmode'] = LOCKMODE_WAIT
        conn_kwargs['timeout'] = 15.0  # seconds
        try:
            conn = self.__connect(**conn_kwargs)
        except BucketNotFoundError:
            raise RuntimeError("Bucket '{}' is missing.".format(bucket))

        return conn

    def connection(self, host, bucket, refresh=False):
        assert bucket and isinstance(bucket, (str, unicode))
        assert host and isinstance(host, (list, tuple, str, unicode))
        conn_key = '{}.{}'.format(bucket, host)
        conn = self.pool.get(conn_key)
        if conn is None:
            conn = self.pool[conn_key] = self.__connect_manager(host, bucket)
        elif refresh or os.getpid() != conn['pid']:  # new connection if child process of fork()
            time.sleep(0.5)
            conn['cb']._close()
            conn = None
            gc.collect()
            time.sleep(0.5)
            conn = self.pool[conn_key] = self.__connect_manager(host, bucket)
        return conn['cb']


import re
import time
import random
from django.conf import settings

from declara_ds.docstore.connection_pool import (
    Query,
    NotFoundError,
    KeyExistsError,
    STRING_RANGE_END,
    TemporaryFailError,
    TimeoutError,
    ConnectError,
    NetworkError,
    OBS_FOUND,
    OBS_LOGICALLY_DELETED,
    OBS_MASK,
    OBS_NOTFOUND,
    OBS_PERSISTED
)

from couchbase.exceptions import (
    ClientTemporaryFailError
)

from declara_ds.docstore.admin import CouchbaseManager
from declara_ds.docstore.conf import (
    VIEW_MAP,
    HOST_BUCKET_DEFAULT,
    HOST_BUCKET_FROM_TYPE,
)

MtlTemporaryFailError = TemporaryFailError
MtlConnectError = ConnectError
MtlNetworkError = NetworkError
MtlTimeoutError = TimeoutError


## regular express to match <type>.<id> or <id> style document keys
MULTITENANT_DOC_KEY_REGEX = re.compile(r'^([\w\d\-]+)\.([\w\d]+)\.(.+)$')
UID_REGEX = re.compile(r'^([\w\d]+)\.(.+)$')
DOC_TYPE_REGEX = re.compile(r'^[\w\d]+$')


def id_from_uid(uid):
    mo = UID_REGEX.match(uid)
    return mo.group(2)


def id_from_uid_iter(uid_iter):
    for uid in uid_iter:
        mo = UID_REGEX.match(uid)
        yield mo.group(2)


def mtl_version_conflict_retry(attempts=3, sleep_interval_sec=(0.005, 0.25)):
    """
    Decorator that catches version conflict errors when setting a document
    with an explicit version (catches MtlKeyExists exception), and will
    retry the function several times.

    Proper use of this decorator requires you have you get your
    document, make the modifications, and set it within the body of this
    function.
    """
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            i = 0
            while i < attempts:
                try:
                    return f(*args, **kwargs)
                except MtlKeyExists:
                    i += 1
                    if i > attempts:
                        raise
                if i > 1:
                    time.sleep(random.uniform(*sleep_interval_sec))
        return wrapped_f
    return wrap



class MtlConnection(object):

    @classmethod
    def connection(cls):
        """
        Make a connection for the current settings.CUSTOMER_ID.
        @return:
        """
        return cls(settings.CUSTOMER_ID)

    def __init__(self, tenant_id):
        """
        Makes a new connection for the given tenant_id.
        This constructor throws a security exception if this doesn't match
        settings.CUSTOMER_ID in production mode.

        @param tenant_id: tenant ID
        """
        test_or_debug = settings.DEBUG or settings.TESTING
        if (test_or_debug is False) and (settings.CUSTOMER_ID != tenant_id):
            raise MtlTenantAccessViolation('settings.CUSTOMER_ID!=tenant_id not allowed with DEBUG=False')
        self.tenant_id = tenant_id

    @staticmethod
    def __cb(doc_type, refresh=False):
        """
        Get a Couchbase connection from the connection pool.
        @param doc_type: the document type needed
        @returns
        """
        cb = CouchbaseManager.get_connection_for_doc_type(doc_type, refresh=refresh)
        return cb

    def __parse_doc_id(self, doc_id):
        """
        Parses the full multitenant doucment ID: <tenant_id>.<doc_type>.<id>,
        performs a security check on the tenant_id, and returns the 2-tuple
        (doc_type, id).
        @param doc_id: the full multitenant document ID
        @return: 2-tuple (doc_type, id)
        """
        m = MULTITENANT_DOC_KEY_REGEX.match(doc_id)
        if m is None:
            raise MtlIntegrityError('invalid doucment key=%s' % doc_id)
        tenant_id, doc_type, _id = m.groups()
        if tenant_id != self.tenant_id:
            raise MtlTenantAccessViolation('tenant=%d attempted access of doc_id=%s' % (self.tenant_id, doc_id))
        return doc_type, _id

    def __make_doc_id(self, doc_type, _id):
        """
        Returns the full multitenant doucment ID: <tenant_id>.<doc_type>.<id>
        @param doc_type: the document type
        @param _id: the document ID
        @return: full document ID string for key storage
        """
        doc_id = '%s.%s.%s' % (self.tenant_id, doc_type, _id)
        if len(doc_id) > 4096:
            raise MtlKeyError('key too long=%s' % doc_id)
        return doc_id

    @staticmethod
    def __parse_doc_type_id(uid, doc_type_required=True):
        """
        Normalizes multiple ways of specifing a document ID.
        @param uid: "type.id" OR (type, id)
        @return: 2-tuple of (doc_type, doc_id), if doc_type is None, then no explicit doc_type was specified
        """
        if isinstance(uid, (tuple, list)):
            try:
                doc_type, _id = uid
            except ValueError:
                raise MtlKeyError(uid)
            if DOC_TYPE_REGEX.match(doc_type) is None:
                raise MtlKeyError(uid)

        elif isinstance(uid, (str, unicode)):
            m = UID_REGEX.match(uid)
            if m is None:
                raise MtlKeyError(uid)
            doc_type = m.group(1)
            _id = m.group(2)

        return doc_type, _id

    def __store_prepare(self, doc_type_id, doc):
        """
        Helper function for document storage API functions.
        @param doc_type_id: "type.id", (type, id), "id"
        @param doc: MUST have type field, must be set to type from above
        @return: 2-tuple of (doc_type, doc_id)
        """
        ## parse multiple forms of doc_type_id
        doc_type, _id = self.__parse_doc_type_id(doc_type_id, False)

        ## add managed document fields: id, type
        ## agree on what the doc_type is
        doc_type_from_doc = doc.get('type')
        if doc_type_from_doc is not None:
            if DOC_TYPE_REGEX.match(doc_type_from_doc) is None:
                raise MtlTypeError()

        if doc_type is not None:
            if doc_type_from_doc is not None:
                if doc_type != doc_type_from_doc:
                    raise MtlTypeError('doc type specified in key does not match type in document')
            else:
                doc['type'] = doc_type
        else:
            doc_type = doc_type_from_doc

        ## at this point doc_type should be set, if not, no type was specified
        if doc_type is None:
            raise MtlTypeError()

        ## note: ID stored in document is actually uid==guid in this code: <type>.<id>
        uid = '%s.%s' % (doc_type, _id)
        doc['uid'] = uid
        doc['tid'] = self.tenant_id

        ## set document id
        doc_id = self.__make_doc_id(doc_type, _id)

        return doc_type, doc_id

    def __mtlvalue_from_cbvalue(self, cbvalue):
        """
        Converts a Couchbase stored document result value to a Mtl version.
        @param cbvalue: Couchbase result Value instance
        @return: MtlValue instance
        """
        kwargs = {}

        #print({k: getattr(cbvalue, k) for k in dir(cbvalue) if not k.startswith('_')})

        if getattr(cbvalue, 'docid', None):
            doc_type, _id = self.__parse_doc_id(cbvalue.docid)
            kwargs['docid'] = '%s.%s' % (doc_type, _id)

        if getattr(cbvalue, 'doc', None) is not None:
            kwargs['doc'] = cbvalue.doc

        kwargs['value'] = cbvalue.value

        if hasattr(cbvalue, 'success'):
            kwargs['success'] = cbvalue.success

        if hasattr(cbvalue, 'cas'):
            kwargs['cas'] = cbvalue.cas

        ## when the cbvalue has a key its the result of a view function
        if getattr(cbvalue, 'key', None):

            ## a key that is a single string comes from a get() call,
            ## not a view, and is the full document key
            if isinstance(cbvalue.key, (str, unicode)):
                doc_type, _id = self.__parse_doc_id(cbvalue.key)
                ## set key to document uid
                kwargs['key'] = '%s.%s' % (doc_type, _id)

            ## this is from a view, all views should be composite keys because
            ## by convention is it the tenant_id
            elif isinstance(cbvalue.key, (list, tuple)):
                ## remove first item from compound key, by convention is it the tenant_id
                kwargs['key'] = cbvalue.key[1:]

        mtlvalue = MtlValue(**kwargs)
        return mtlvalue

    def __delegate_cb_call_with_update(self, func_name, doc_type_id, doc, **kwargs):
        doc_type, doc_id = self.__store_prepare(doc_type_id, doc)
        try:
            try:
                cbresult = getattr(self.__cb(doc_type), func_name)(doc_id, doc, **kwargs)
            except (ConnectError, NetworkError, TemporaryFailError, ClientTemporaryFailError) as e:
                cbresult = getattr(self.__cb(doc_type, refresh=True), func_name)(doc_id, doc, **kwargs)
        except KeyExistsError:
            raise MtlKeyExists()
        except NotFoundError:
            raise MtlNotFound()
        return self.__mtlvalue_from_cbvalue(cbresult)

    def set(self, doc_type_id, doc, **kwargs):
        """
        Store a document.
        @param id: "type.id", (type, id), "id"
        @param doc: MUST have type field, must be set to type from above
        """
        return self.__delegate_cb_call_with_update('set', doc_type_id, doc, **kwargs)

    def replace(self, doc_type_id, doc, **kwargs):
        """
        Replace a document.  Only stores if the document exists.
        @param id: "type.id", (type, id), "id"
        @param doc: MUST have type field, must be set to type from above
        """
        return self.__delegate_cb_call_with_update('replace', doc_type_id, doc, **kwargs)

    def add(self, doc_type_id, doc, **kwargs):
        """
        Add a document.  Only stores if the document does not exist.
        @param id: "type.id", (type, id), "id"
        @param doc: MUST have type field, must be set to type from above
        """
        return self.__delegate_cb_call_with_update('add', doc_type_id, doc, **kwargs)

    def __delegate_cb_call(self, func_name, doc_type_id, **kwargs):
        doc_type, _id = self.__parse_doc_type_id(doc_type_id)
        doc_id = self.__make_doc_id(doc_type, _id)
        try:
            try:
                cbresult = getattr(self.__cb(doc_type), func_name)(doc_id, **kwargs)
            except (ConnectError, NetworkError, TemporaryFailError, ClientTemporaryFailError) as e:
                cbresult = getattr(self.__cb(doc_type, refresh=True), func_name)(doc_id, **kwargs)
        except NotFoundError:
            raise MtlNotFound(doc_type_id)
        return self.__mtlvalue_from_cbvalue(cbresult)

    def endure(self, doc_type_id, **kwargs):
        return self.__delegate_cb_call('endure', doc_type_id, **kwargs)

    def get(self, doc_type_id, **kwargs):
        """
        Retrieve a document.
        @param doc_type_id: "type.id", (type, id)
        """
        return self.__delegate_cb_call('get', doc_type_id, **kwargs)

    def observe(self, doc_type_id):
        """
        Observes a document.
        @param doc_type_id: "type.id", (type, id)
        """
        return self.__delegate_cb_call('observe', doc_type_id)

    def delete(self, doc_type_id, **kwargs):
        """
        Delete a document.
        @param doc_type_id: "type.id", (type, id)
        """
        return self.__delegate_cb_call('delete', doc_type_id, **kwargs)


    def query(self, doc_type, mtl_view, **kwargs):
        """
        Query a view function.  Returns an iterator over the index entries.
        For this to work, all view functions must emit compound keys and the first
        key component must be the doucment tenant ID (tid field in doc).
        @type doc_type: type of document
        @type mtl_view: str
        @type kwargs: dict
        """
        try:
            view_conf = VIEW_MAP[mtl_view]
        except KeyError:
            raise MtlViewNotFound(mtl_view)

        design_doc, view = view_conf['view']

        ## TODO: check the view_conf to make sure the view applies to this type

        if kwargs.has_key('mapkey_single'):
            mapkey_single = kwargs['mapkey_single']
            mapkey_single.insert(0, self.tenant_id)
        elif not kwargs.has_key('mapkey_range'):
            kwargs['mapkey_range'] = [[self.tenant_id, STRING_RANGE_END], [self.tenant_id]]
        else:
            rstart, rend = kwargs['mapkey_range']
            rstart.insert(0, self.tenant_id)
            rend.insert(0, self.tenant_id)

        if kwargs.get('reduce', False):
            if kwargs.has_key('group_level'):
                kwargs['group_level'] += 1
            else:
                kwargs['group_level'] = 1

        count = 0
        try:
            query = self.__cb(doc_type).query(design_doc, view, **kwargs)
            for cbvalue in query:
                mtlvalue = self.__mtlvalue_from_cbvalue(cbvalue)
                count += 1
                yield mtlvalue
        except (ConnectError, NetworkError, TemporaryFailError, ClientTemporaryFailError) as e:
            # network error happens in step 'for cbvalue in query:'
            query = self.__cb(doc_type, refresh=True).query(design_doc, view, **kwargs)
            from itertools import islice
            for cbvalue in islice(query, count, None):
                mtlvalue = self.__mtlvalue_from_cbvalue(cbvalue)
                yield mtlvalue


class MtlValue(object):
    __slots__ = ['count', 'doc', 'docid', 'index', 'key', 'value', 'success', 'cas']

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MtlException(Exception):
    pass


class MtlTypeError(Exception):
    pass


class MtlTenantAccessViolation(Exception):
    pass


class MtlIntegrityError(Exception):
    pass


class MtlKeyError(Exception):
    pass


class MtlNotFound(Exception):
    pass


class MtlKeyExists(Exception):
    pass


class MtlViewNotFound(Exception):
    pass