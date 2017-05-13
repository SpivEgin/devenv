"""
Module: DMS base tests data
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""

import os
import base64

from couchdbkit import Server

from django.conf import settings
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.client import encode_multipart

__all__ = ['DMSTestCase', 'DMSBasicAuthenticatedTestCase']


class DMSTestCase(TestCase):
    """
    Base Adlibre DMS Test Case

    Provides a standardized set of test data and ensures that each test run has a clean set of data.
    """
    fixtures = ['initial_datas.json', 'djangoplugins.json', 'dms_plugins.json', 'core.json', ]

    def __init__(self, *args, **kwargs):
        super(DMSTestCase, self).__init__(*args, **kwargs)

        # Test User Auth User
        self.username = 'admin'
        self.password = 'admin'

        # Source of documents
        self.test_document_files_dir = os.path.join(settings.FIXTURE_DIRS[0], 'testdata')

        # Test Data
        self.documents_pdf = ('ADL-0001', 'ADL-0002', 'ADL-1111', 'ADL-1234', 'ADL-2222')
        self.documents_pdf2 = ('BBB-0001', )
        self.documents_pdf_test_string = '%PDF-1.4'
        self.documents_txt = ('10001', '10006', '101',)
        self.documents_tif = ('2011-01-27-1', '2011-01-28-12',)
        self.documents_jpg = ('TST00000001', 'TST00000002', 'TST12345678')
        self.documents_missing = ('ADL-8888', 'ADL-9999',)
        self.documents_codes = ('abcde333', )
        self.jpg_codes = ('TST12345679', )
        self.no_docrule_files = ('Z50141104', )
        self.uncategorized_codes = ('UNC-0001', 'UNC-0002', 'UNC-0003')
        self.uncategorized_files = ('Z50141104.jpg', )

        self.hash_method = 'md5'
        # Documents that exist, and have valid hash
        self.documents_hash = [
            ('abcde111', 'cad121990e04dcd5631a9239b3467ee9'),
            ('abcde123', 'bc3c5035805bb8098e5c164c5e1826da'),
            ('abcde222', 'ba7e656a1288181cdcf676c0d719939e'),
        ]

        # Documents that are missing, but have correct hash
        self.documents_missing_hash = [
            ('abcde888', 'e9c84a6bcdefb9d01e7c0f9eabba5581',),
            ('abcde999', '58a38de7b3652391f888f4e971c6e12e',),
        ]

        # Documents with incorrect hashes
        self.documents_incorrect_hash = [
            # TODO: DEFINE ME
        ]

        self.rules = (2, 3, 4, 5)
        self.rule_uncategorized = 10
        self.rules_missing = (99,)

        # Used in determining if current file is PDF file by 'string' inside a file content.
        self.pdf_file_contains = '%PDF-1.4'

        # TODO: refactor tests for this
        # This list of filenames for fixtures files.
        # Upon updating a fixtures file (testdata) it should be listed here.
        # Tests in it's part must reference those strings directly, rather then filename.
        # They can not be used however for dynamic tests.
        # (Dynamic, e.g. API tests should scan directory and only reference here for strings parts to check for)
        self.fixtures_files = [
            '101.txt',
            '2011-01-27-1.tif',
            '2011-01-28-12.tif',
            '10001.txt',
            '10006.txt',
            'abcde111.pdf',
            'abcde123.pdf',
            'abcde222.pdf',
            'abcde888.pdf',
            'abcde999.pdf',
            'ADL-0001.pdf',
            'ADL-0002.pdf',
            'ADL-1111.pdf',
            'ADL-1234.pdf',
            'ADL-2222.pdf',
            'BBB-0001.pdf',
            'TST00000001.jpg',
            'TST00000002.jpg',
            'TST12345678.jpg',
            'Z50141104.jpg',
        ]

    def _upload_file(self, doc_name, suggested_format='pdf', hash_code=None, check_response=True, code=None):
        """Upload initial version of a file into DMS

        @param suggested_format - is used to set up an extension of uploaded file to search in fixtures dir
        @param hash_code - sets up a hash of an uploaded file
        @param check_response - is used to confirm file has been successfully uploaded
        @param code - is to set up a code for file (Upload this file with different name specified)
        """
        self.client.login(username=self.username, password=self.password)
        url, data = self._get_tests_file(doc_name, code, suggested_format, hash_code)
        response = self.client.post(url, data)
        if check_response:
            self.assertEqual(response.status_code, 201)
        return response

    def _update_code(self, doc_name, code=None, suggested_format='pdf', check_response=True):
        """Method to uploade an already existing document into DMS"""
        self.client.login(username=self.username, password=self.password)
        url, data = self._get_tests_file(doc_name, code, suggested_format)
        content = encode_multipart('BoUnDaRyStRiNg', data)
        response = self.client.put(url, content, content_type='multipart/form-data; boundary=BoUnDaRyStRiNg')
        if check_response:
            self.assertEqual(response.status_code, 200)
        return response

    def _get_tests_file(self, name, code, suggested_format, hashcode=None):
        """Retrieve required file from fixtures into special format for posting returning an API url and data to post"""
        file_path = os.path.join(self.test_document_files_dir, name + '.' + suggested_format)
        data = {'file': open(file_path, 'r')}
        if not code:
            code = name
        url = reverse('api_file', kwargs={'code': code, 'suggested_format': suggested_format})
        if hashcode:
            # Add hash to payload
            data['h'] = hashcode
        return url, data

    def _shelve(self, obj, name='1.html'):
        """Writes given object into a file on desktop. (For debug purposes only ;) """
        fo = False
        path = os.path.expanduser(os.path.join('~', 'Desktop', name))
        # Cleaning existing file
        try:
            with open(path):
                os.remove(path)
                pass
        except IOError:
            pass
        # Dumping object into file
        try:
            fo = open(path, 'w')
        except Exception, e:
            print e
            pass
        if fo:
            fo.writelines(obj)
            print 'file %s written' % name

    def loadTestData(self):
        """Load a copy of all our fixtures using the management command"""
        return call_command('import_documents', self.test_document_files_dir, silent=False)

    def cleanUp(self, documents, check_response=True):
        """Cleanup Helper

        @param documents: is an iterable list of documents to clean up
        @param check_response: is a switch for tests to try to test if API returned ok code"""
        self.client.login(username=self.username, password=self.password)
        for doc in documents:
            code, suggested_format = os.path.splitext(doc)
            url = reverse('api_file', kwargs={'code': code})
            data = {}
            response = self.client.delete(url, data=data)
            if response.status_code is not 204:
                print "ERROR DATA: %s, %s" % (code, response.status_code)
            if check_response:
                self.assertEqual(response.status_code, 204)

    def cleanAll(self, check_response=True):
        """Clean all of our test documents

        @param check_response: is a switch for tests to try to test if API returned ok code
        """

        # Cleaning up simple docs
        self.cleanUp(self.documents_pdf, check_response=check_response)
        self.cleanUp(self.documents_tif, check_response=check_response)
        self.cleanUp(self.documents_txt, check_response=check_response)
        self.cleanUp(self.documents_pdf2, check_response=check_response)
        self.cleanUp(self.documents_jpg, check_response=check_response)

        # Cleanup hashed dicts
        # (I'm sure there is a more elegant way to do this)
        cleanup_docs_list = []
        for doc, hashed in self.documents_hash:
            cleanup_docs_list.append(doc)
        for doc, hashed in self.documents_missing_hash:
            cleanup_docs_list.append(doc)
        self.cleanUp(cleanup_docs_list, check_response=check_response)

        # Un used file cleanup
        self.cleanUp(self.uncategorized_codes, check_response=check_response)

    def setUp(self):
        """NB This is called once for every test, not just test case before the tests are run!"""
        pass

    def tearDown(self):
        """ Cleanup
        # NB This is called once for every test, not just test case before the tests are run!
        """
        pass

    def _list_couch_docs(self,  db_name='dmscouch_test'):
        """Downloads all the documents that are currently in CouchDB now"""
        docs = {}
        server = Server()
        db = server.get_or_create_db(db_name)
        r = db.view(
            'dmscouch/all',
            include_docs=True,
        )
        for row in r:
            docs[row['doc']['_id']] = row['doc']
        return docs


class BasicAuthClient(Client):
    """Basic HTTP Authentication Client

    user for testing Piston API
    """

    def auth(self, username, password):
        """Authenticates client

        @param username: string of a username to authenticate
        @param password: string of a password to authenticate
        """
        auth = '%s:%s' % (username, password)
        auth = 'Basic %s' % base64.encodestring(auth)
        auth = auth.strip()
        self.extra = {
            'HTTP_AUTHORIZATION': auth,
        }

    # Pass auth **extra to every method
    def get(self, *args, **kwargs):
        """Transparent method

        @param args:
        @param kwargs:
        """
        return super(BasicAuthClient, self).get(*args, **self.extra)

    def post(self, *args, **kwargs):
        """Inherited method

        @param args:
        @param kwargs:
        """
        return super(BasicAuthClient, self).post(*args, **self.extra)

    def head(self, *args, **kwargs):
        """Inherited method

        @param args:
        @param kwargs:
        """
        return super(BasicAuthClient, self).head(*args, **self.extra)

    def options(self, *args, **kwargs):
        """Inherited method

        @param args:
        @param kwargs:
        """
        return super(BasicAuthClient, self).options(*args, **self.extra)

    def put(self, *args, **kwargs):
        """Inherited method

        @param args:
        @param kwargs:
        """
        return super(BasicAuthClient, self).put(*args, **self.extra)

    def delete(self, *args, **kwargs):
        """Inherited method

        @param args:
        @param kwargs:
        """
        return super(BasicAuthClient, self).delete(*args, **self.extra)


class DMSBasicAuthenticatedTestCase(DMSTestCase):
    """Basic HTTP Authentication for our API Tests"""

    client_class = BasicAuthClient

    def setUp(self, *args, **kwargs):
        """Authenticated test case

        @param args:
        @param kwargs:
        """
        super(DMSBasicAuthenticatedTestCase, self).setUp(*args, **kwargs)
        # Create Auth data
        self.client.auth(self.username, self.password)


