"""
http://djangosnippets.org/snippets/678/

Upload progress handler using cache framework

Setup: place the UploadProgressCachedHandler anywhere you like on the python path, and add to your settings.py:

from django.conf import global_settings
FILE_UPLOAD_HANDLERS = ('path.to.UploadProgressCachedHandler', ) + global_settings.FILE_UPLOAD_HANDLERS

Set up the upload_progress view in any of your apps along with a corresponding entry in your urlconf.

Here's some javascript example code to make the ajax requests and display the progress meter: http://www.djangosnippets.org/snippets/679/
"""

import logging
from django.core.cache import get_cache
from django.core.files.uploadhandler import FileUploadHandler

log = logging.getLogger('adlibre.upload_handler')
cache_data_for = 320
cache = get_cache('default')


from django.core.files.uploadhandler import TemporaryFileUploadHandler
#from django.core.cache import cache
#from django.conf import settings



#class UploadProgressCachedHandler(TemporaryFileUploadHandler):
#    """
#    Tracks progress for file uploads.
#    The http post request must contain a query parameter, 'X-Progress-ID',
#    which should contain a unique string to identify the upload to be tracked.
#    """
#
#    def __init__(self, request=None):
#        super(UploadProgressCachedHandler, self).__init__(request)
#        self.progress_id = None
#        self.cache_key = None
#        self.logger = logging.getLogger('adlibre.upload_handler.UploadProgressCachedHandler')
#
#    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
#        self.content_length = content_length
#        if 'X-Progress-ID' in self.request.GET:
#            self.progress_id = self.request.GET['X-Progress-ID']
#        if self.progress_id:
#            self.cache_key = "%s_%s" % (self.request.META['REMOTE_ADDR'], self.progress_id )
#            cache.set(self.cache_key, {
#                'state': 'uploading',
#                'size': self.content_length,
#                'received': 0
#            })
#            self.logger.debug('Initialized cache with %s %s' % (self.cache_key, cache.get(self.cache_key)))
#        else:
#            self.logger.warn("No progress ID.")
#
#    def new_file(self, field_name, file_name, content_type, content_length, charset=None):
#        self.logger.debug("Field_name %s file_name %s" % (field_name, file_name))
#
#    def receive_data_chunk(self, raw_data, start):
#        if self.cache_key:
#            data = cache.get(self.cache_key)
#            if data:
#                data['received'] += self.chunk_size
#                cache.set(self.cache_key, data)
#                self.logger.debug('Updated cache with %s %s' % (self.cache_key, data))
#        return raw_data
#
#    def file_complete(self, file_size):
#        pass
#
#    def upload_complete(self):
#        self.logger.debug('Upload complete for %s' % self.cache_key)
#        if self.cache_key:
#            data = cache.get(self.cache_key)
#            if data:
#                # upload is 'done'.
#                data['state'] = 'done'
#                cache.set(self.cache_key, data)
#                self.logger.debug('Updated cache with %s %s' % (self.cache_key, data))

class UploadProgressCachedHandler(FileUploadHandler):
    """
    Tracks progress for file uploads.
    The http post request must contain a header or query parameter, 'X-Progress-ID'
    which should contain a unique string to identify the upload to be tracked.
    """

    def __init__(self, request=None):
        super(UploadProgressCachedHandler, self).__init__(request)
        log.debug('UploadProgressCachedHandler init() called.')
        self.progress_id = None
        self.cache_key = None

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        self.content_length = content_length
        log.debug('handle_raw_input called with: input_data: %s content_length: %s boundary: %s encoding: %s META: %s' %
            (input_data, content_length, boundary, encoding, META))
        if 'X-Progress-ID' in self.request.GET :
            self.progress_id = self.request.GET['X-Progress-ID']
        elif 'X-Progress-ID' in self.request.META:
            self.progress_id = self.request.META['X-Progress-ID']
        if self.progress_id:
            self.cache_key = "%s" % self.progress_id
            cache.set(self.cache_key, {
                'length': self.content_length,
                'uploaded' : 0
            }, cache_data_for)
            # TODO Remove thid debug info
            try:
                data = cache.get(self.cache_key)
                log.debug('handle_raw_input set up cache_variable: %s' % data)
            except: pass

    def new_file(self, field_name, file_name, content_type, content_length, charset=None):
        pass

    def receive_data_chunk(self, raw_data, start):
        log.debug('receive_data_chunk called with: raw_data: %s, start: %s' % (raw_data, start) )
        if self.cache_key:
            data = cache.get(self.cache_key)
            data['uploaded'] += self.chunk_size
            cache.set(self.cache_key, data, cache_data_for)
            log.debug('receive_data_chunk updated data in cache: cache_key: %s, data: %s' % (self.cache_key, data) )
        return raw_data

    def file_complete(self, file_size):
        pass

    def upload_complete(self):
        if self.cache_key:
            cache.delete(self.cache_key)