"""
Module: API Unit Tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
"""
import json
import os
import tempfile

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import encode_multipart

from dms_plugins.models import DoccodePluginMapping
from dms_plugins.workers.validators.hashcode import HashCodeWorker

from adlibre.dms.base_test import DMSTestCase
from core.models import CoreConfiguration
from core.models import DocumentTypeRuleManager

# TODO: Test self.rules, self.rules_missing, self.documents_missing
# TODO: Test with and without correct permissions.


class APITest(DMSTestCase):
    def setUp(self):
        """Local test variables, that may override DMSTestCase"""
        self.documents_pdf_this_test = ["ADL-1985", 'ADL-1984', 'ADL-1983']
        self.adlibre_invoices_rule_id = self.rules[0]
        self.test_tag = 'test_tag'
        self.hworker = HashCodeWorker(method=self.hash_method)
        self.doc1_dict = {
            'date': '2012/03/06',
            'description': 'Test Document Number 1',
            'Employee ID': '123456',
            'Required Date': '2012/03/07',
            'Employee Name': 'Iurii Garmash',
            'Friends ID': '123',
            'Friends Name': 'Andrew',
            'Additional': 'Something for 1',
        }

    def test_00_setup(self):
        """Load Test Data required by this test"""
        self.loadTestData()

    def test_01_api_list_files(self):
        """Testing file listing for different API calls"""
        docrule = self.rule_uncategorized  # Uncategorized
        url = reverse('api_file_list', kwargs={'id_rule': docrule})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)  # unauthorised not fetched
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertContains(response, 'No doccode')
        self.assertContains(response, 'thumb_url')
        self.assertContains(response, '/api/thumbnail/UNC-0001')
        self.assertContains(response, '/api/new_file/UNC-0001')
        self.assertNotContains(response, '/api/thumbnail/UNC-0002')
        url = reverse('api_file_list', kwargs={'id_rule': 100})  # Not existing rule
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_02_api_file(self):
        """Uses abcde333 document to test file upload with code. Retrieves file afterwards"""
        self.client.login(username=self.username, password=self.password)
        doc = self.documents_hash[0][0]
        hash_code = self.documents_hash[0][1]
        # Upload a document with code
        self._upload_file(doc, code=self.documents_codes[0])
        # Download doc
        revision = 1
        url = reverse('api_file', kwargs={
            'code': self.documents_codes[0],
            'suggested_format': 'pdf'}) + '?r=%s&h=%s' % (revision, hash_code)
        response = self.client.get(url)
        self.assertContains(response, self.documents_pdf_test_string, status_code=200)

    def test_03_api_file_jpeg(self):
        """ Testing upload of JPG file into DMS api"""
        self.client.login(username=self.username, password=self.password)
        code = self.jpg_codes[0]
        doc_name = self.documents_jpg[2]
        response = self._upload_file(doc_name, suggested_format='jpg', check_response=False, code=code)
        self.assertEqual(response.status_code, 201)

    def test_04_api_no_docrule_upload(self):
        """
        Testing upload of file with no document type assigned returns a proper response

        Refs #946 Bug: API piston bug when uploading barcode with error (no document type rule)
        """
        # Name 'Z50141104' is set like so to be loaded in the end of all files.
        self._upload_file(self.no_docrule_files[0], suggested_format='jpg')
        # removing support of uncategorized and testing we are failing gracefully
        config = CoreConfiguration.objects.all()[0]
        config.delete()
        response = self._upload_file(self.no_docrule_files[0], suggested_format='jpg', check_response=False)
        self.assertEqual(response.status_code, 400)

    def test_05_upload_files(self):
        """Upload files through API uses 1 file and exact code specified"""
        for f in self.documents_pdf_this_test:
            response = self._upload_file(self.documents_pdf[0], code=f)
            self.assertEqual(response.status_code, 201)

    def test_06_api_create_existing_file(self):
        """Create an existing file. We should not allow that due to CRUD architecture"""
        for f in self.documents_pdf:
            response = self._upload_file(f, check_response=False)
            self.assertEqual(response.status_code, 400)

    def test_07_get_rev_count(self):
        """Uploading new revision of the document and checking it exists"""
        for f in self.documents_pdf:
            url = reverse('api_revision_count', kwargs={'document': f})
            self.client.login(username=self.username, password=self.password)
            response = self.client.get(url)
            if not response.content.isdigit():
                raise self.failureException('Invalid response: %s' % response.content)
            # We now have only one revision of the file that was uploaded on self.setUp()
            self.assertEqual(response.content, "1")
            # Uploading file for revision 2 and checking revision count
            self._update_code(f)
            response = self.client.get(url)
            if not response.content.isdigit():
                raise self.failureException('Invalid response: %s' % response.content)
            self.assertEqual(response.content, "2")

    def test_08_get_bad_rev_count(self):
        """Wrong revision number request"""
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_revision_count', kwargs={'document': 'sdfdsds42333333333333333333333333432423'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_09_api_wrong_code_shows_not_exists(self):
        """ Fixed Bug #785 MUI: View invalid filename causes exception"""
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_file', args={"code": 'mas00000280.pdf'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_10_api_rule_detail(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_rules_detail', kwargs={'id_rule': 3})
        response = self.client.get(url)
        self.assertContains(response, 'Test PDFs')

    def test_11_api_rules(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_rules')
        response = self.client.get(url)
        self.assertContains(response, 'Test PDFs')

    def test_12_api_plugins(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_plugins')
        response = self.client.get(url)
        self.assertContains(response, 'dms_plugins.workers.storage.local.LocalStoragePlugin')

    def test_13_api_files_list(self):
        """Refs #1434 TEST: API file list url

        Added response JSON parsing check to existing files list test"""
        fixed_codes = [
            u'ADL-0001',
            u'ADL-0002',
            u'ADL-1111',
            u'ADL-1234',
            u'ADL-1983',
            u'ADL-1984',
            u'ADL-1985',
            u'ADL-2222',
        ]
        self.client.login(username=self.username, password=self.password)
        dman = DocumentTypeRuleManager()
        docrule = dman.get_docrule_by_name('Adlibre Invoices')
        mapping = DoccodePluginMapping.objects.get(doccode=docrule.get_id())
        url = reverse("api_file_list", kwargs={'id_rule': mapping.pk})
        response = self.client.get(url)
        data = json.loads(response.content)
        current_files_list = [d['name'] for d in data]
        for code in fixed_codes:
            if not code in current_files_list:
                raise AssertionError('File code absent in list! Code: %s' % code)

    def test_14_api_fileinfo(self):
        """
            Sometimes file revision data can be corrupt due to plugins misconfiguration or improper file storage.
            Tests this bug with file info data:
            {
                "1": {
                         "mimetype": "application/pdf",
                         "revision": 1,
                         "compression_type": "GZIP",
                         "name": "ADL-0001_r1.pdf",
                         "created_date": "2013-02-20 05:06:41"
                     },
                "2": {
                        "created_date": "2013-02-20 05:07:38",
                        "name": "ADL-0001_r2.pdf",
                        "revision": 2
                }
            }
        """
        def check_proper_json_format(data, rev_count, f, extension='pdf'):
            data = json.loads(data)
            if not 'document_name' in data or data['document_name'] != f:
                raise self.failureException('Invalid response: %s' % data)
            for rev_num in range(1, rev_count):
                md = data['metadata'][str(rev_num)]
                # Check each revision has compression and mimetype for each file.
                # (Important for integrity of update sequence)
                if not 'mimetype' in md or not 'compression_type' in md:
                    raise self.failureException('Invalid response for file revision: %s' % md)
                name_with_revision = f + '_r' + str(rev_num) + '.' + extension
                if not md['name'] == name_with_revision:
                    raise self.failureException('Improper stored filename in file revision: %s' % md)

        self.client.login(username=self.username, password=self.password)
        for f_name in self.documents_pdf:
            url = reverse('api_file_info', kwargs={'code': f_name})
            response = self.client.get(url)
            r_data = json.loads(response.content)
            check_proper_json_format(r_data, 2, f_name)

    def test_15_read_api_file_content(self):
        """"Comparing file content to actual file, that was uploaded, using hash from our DMS hash plugin"""
        file_name = self.documents_pdf[0]
        extension = 'pdf'

        self.client.login(username=self.username, password=self.password)
        url = reverse('api_file', kwargs={'code': file_name, 'suggested_format': extension})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Comparing response to actual file using hash codes
        resp_h = self.hworker.get_hash(response.content, self.hash_method)
        file_h = self._get_hash_for_file(file_name)
        if not resp_h == file_h:
            raise self.failureException('Wrong file content returned by DMS: %s' % resp_h)

    def test_16_complex_revisions_check__file_after_revision_update(self):
        """Upload another file revision and test it is a proper revision.

        (E.g. check file content for file ADL-0002 in a code ADL-0001, uploading a file ADL-0002)
        (After: Check it has not affected retrieving ability of earlier revisions)
        """
        extension = 'pdf'
        first_file_name = self.documents_pdf[0]
        second_file_name = self.documents_pdf[1]
        # Updating code of file #1 with revision from file #2
        self._update_code(second_file_name, first_file_name)
        url = reverse('api_file', kwargs={'code': first_file_name, 'suggested_format': extension})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        resp_h = self.hworker.get_hash(response.content, self.hash_method)
        file_h = self._get_hash_for_file(second_file_name)
        if not resp_h == file_h:
            raise self.failureException('Wrong file content returned by DMS (hash): %s' % resp_h)

        rev_url = url + '?r=%s' % 1
        response = self.client.get(rev_url)
        resp_h = self.hworker.get_hash(response.content, self.hash_method)
        file_h = self._get_hash_for_file(first_file_name)
        if not resp_h == file_h:
            raise self.failureException('Wrong file content returned by DMS for previous revision (hash) : %s' % resp_h)

    def _get_hash_for_file(self, filename, extension='pdf'):
        """helper for test 14 and 15 to calculate a hash for file from fixtures"""
        file_path = os.path.join(self.test_document_files_dir, filename + '.' + extension)
        f = open(file_path, 'r')
        file_h = self.hworker.get_hash(f.read(), self.hash_method)
        f.close()
        return file_h

    def test_17_file_storage_structure(self):
        """File really exists in a directory it should.

        For document ADL-0001.pdf and all of it's revisions at a current state"""
        file_directory = os.path.join(settings.DOCUMENT_ROOT, '2', 'ADL', '0001', 'ADL-0001')
        file_list = []
        for dirname, dirnames, filenames in os.walk(file_directory):
            for filename in filenames:
                file_list.append(filename)
            if dirnames:
                raise self.failureException('System integrity broken, should not contain directories. contains: %s'
                                            % dirnames)
        required_list = ['ADL-0001.json', 'ADL-0001_r1.pdf', 'ADL-0001_r2.pdf', 'ADL-0001_r3.pdf']
        for fname in file_list:
            if not fname in required_list:
                raise self.failureException('System integrity broken, file: %s absent' % fname)

    def test_18_api_tags(self):
        """ Adds a tag to a file and then deletes it"""
        self.client.login(username=self.username, password=self.password)
        for filename in [self.documents_pdf[0], self.documents_jpg[0]]:
            # Remove tag
            url = reverse('api_file', kwargs={'code': filename})
            data = {'filename': filename, 'remove_tag_string': self.test_tag}
            content = encode_multipart('BoUnDaRyStRiNg', data)
            response = self.client.put(url, content, content_type='multipart/form-data; boundary=BoUnDaRyStRiNg')
            self.assertEqual(response.status_code, 200)
            # Check that we don't have tag
            url = reverse('api_file_info', kwargs={'code': filename})
            response = self.client.get(url)
            self.assertNotContains(response, self.test_tag, status_code=200)
            # Set tags
            url = reverse('api_file', kwargs={'code': filename})
            data = {'filename': filename, 'tag_string': self.test_tag}
            content = encode_multipart('BoUnDaRyStRiNg', data)
            response = self.client.put(url, content, content_type='multipart/form-data; boundary=BoUnDaRyStRiNg')
            self.assertEqual(response.status_code, 200)
            # Check that we have tag
            url = reverse('api_file_info', kwargs={'code': filename})
            response = self.client.get(url)
            self.assertContains(response, self.test_tag, status_code=200)
            # Get all tags for rule, check our tag
            url = reverse('api_tags', kwargs={'id_rule': self.adlibre_invoices_rule_id})
            response = self.client.get(url)
            self.assertContains(response, self.test_tag, status_code=200)

    def test_19_api_read_file_revisions(self):
        """Refs #968 API returns revision independent filename"""
        self.client.login(username=self.username, password=self.password)
        doc_url = reverse('api_file', kwargs={'code': self.documents_pdf[0], 'suggested_format': 'pdf'})
        # Download doc without certain revision
        test_filename = 'filename=ADL-0001.pdf'
        response = self.client.get(doc_url)
        # File name in response contains only code
        self.assertEqual(response._headers['content-disposition'][1], test_filename)
        self.assertEqual(response.status_code, 200)

        # Download doc with revision
        r = 2
        test_filename_with_revision = 'filename=ADL-0001_r%s.pdf' % r
        url_2 = doc_url + '?r=%s' % r
        response = self.client.get(url_2)
        # File name in response contains revision
        self.assertEqual(response._headers['content-disposition'][1], test_filename_with_revision)
        self.assertEqual(response.status_code, 200)

    def test_20_delete_documents(self):
        delete_doc = self.documents_pdf_this_test[0]
        remain_doc = self.documents_pdf_this_test[1]
        self._delete_documents(delete_doc, remain_doc)

    def _delete_documents(self, delete_doc, remain_doc, suggested_format='pdf'):
        self.client.login(username=self.username, password=self.password)
        # Delete one
        url = reverse('api_file', kwargs={'code': delete_doc, 'suggested_format': suggested_format})
        response = self.client.delete(url)
        self.assertContains(response, '', status_code=204)
        # Check the other still exists
        url = reverse('api_file', kwargs={'code': remain_doc, 'suggested_format': suggested_format})
        response = self.client.get(url)
        self.assertContains(response, '', status_code=200)

    def test_21_deprecated_api_handler(self):
        """Old handler that creates or updates existing document"""
        self.client.login(username=self.username, password=self.password)
        file_name = self.documents_pdf_this_test[1]
        suggested_format = 'pdf'
        url = reverse('api_file_deprecated', kwargs={'code': file_name, 'suggested_format': suggested_format})
        rev_count_url = reverse('api_revision_count', kwargs={'document': file_name})
        before_rev = self.client.get(rev_count_url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        t, data = self._get_tests_file(self.documents_pdf[0], file_name, suggested_format)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, file_name)
        after_rev = self.client.get(rev_count_url)
        self.assertGreater(int(after_rev.content), int(before_rev.content), 'Revision Count mismatch')

    def test_22_deprecated_file_handler_no_doc_type_upload(self):
        """Refs #1203 Deprecated file handler upload bug with no document type rule"""
        self.client.login(username=self.username, password=self.password)
        file_name = 'Some-File-0001'
        suggested_format = 'pdf'
        url = reverse('api_file_deprecated', kwargs={'code': file_name, 'suggested_format': suggested_format})
        t, data = self._get_tests_file(self.documents_pdf[0], file_name, suggested_format)
        response = self.client.post(url, data)
        self.assertContains(response, self.uncategorized_codes[0])

    def test_23_rules_api_hook(self):
        """Refs #1436 TEST: Rules handler

        Checking rules API hook provides rules in JSON parsed format
        and all the doc types present there"""
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_rules')
        response = self.client.get(url)
        parsed_data = json.loads(response.content)
        rule_names_parsed = [r['doccode'] for r in parsed_data]
        docrules = DoccodePluginMapping.objects.all()
        for docrule in docrules:
            if not docrule.name in rule_names_parsed:
                raise AssertionError('Docrule is not present in API response!')

    def test_24_mdt_handler(self):
        """Refs #1435 TEST: MDT handler"""
        mdt_name = 'mdt1.json'
        mdt_id = 'mytesttemplate'
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_mdt')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        mdt_path = os.path.join(self.test_document_files_dir, '..', 'mdts_json', mdt_name)
        data = {'mdt': str(open(mdt_path, 'r').read())}
        response = self.client.post(url, data)
        if response.status_code == 409:
            raise AssertionError('MDT for tests exists')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"ok"')
        self.assertContains(response, '"mdt_id"')
        self.assertContains(response, mdt_id)
        ok_resp_data = json.loads(response.content)
        if not 'status' in ok_resp_data.iterkeys():
            raise AssertionError('MDT POST wrong parsed result data.')
        # Retrieving MDT that was posted via API
        response = self.client.get(url, {'docrule_id': "100000"})
        self.assertEqual(response.status_code, 200)
        got_mdts = json.loads(response.content)
        if not '1' in got_mdts.iterkeys():
            raise AssertionError('no MDT returned')
        self.assertEqual(mdt_id, got_mdts['1']['mdt_id'])
        # Deleting mdt that exists in the API
        content = encode_multipart('BoUnDaRyStRiNg', {'mdt_id': mdt_id})
        response = self.client.delete(url, content, content_type='multipart/form-data; boundary=BoUnDaRyStRiNg')
        self.assertEqual(response.status_code, 204)
        # Checking now for mdt presence
        response = self.client.get(url, {'docrule_id': "100000"})
        self.assertEqual(response.status_code, 404)

    def test_25_version(self):
        """Refs #1446 TEST: Coverage of Version API handler"""
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_version')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, settings.PRODUCT_VERSION)

    def test_26_api_docs(self):
        """Refs #1471 /api/ url documentation"""
        url = reverse('api_main')
        response = self.client.get(url)
        self.assertContains(response, 'api_rules_detail')

    def test_27_api_empty_file_call(self):
        """Get an empty file call response. File size is 0 (Should return error)"""
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_file_deprecated', kwargs={'code': self.documents_codes[0]})
        response = self.client.post(url, {'file': tempfile.TemporaryFile()})
        self.assertEqual(response.status_code, 400)

    def test_28_api_empty_call(self):
        """Get an empty call response. Empty == does nothing. (Should return error)"""
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_file_deprecated', kwargs={'code': self.documents_codes[0]})
        response = self.client.post(url, {'file': ''})
        self.assertEqual(response.status_code, 400)

    def test_29_api_post_document_index_data(self):
        """Put document's couchdb indexes via API call"""
        self.client.login(username=self.username, password=self.password)
        content = encode_multipart('BoUnDaRyStRiNg', {'indexing_data': json.dumps(self.doc1_dict)})
        doc_url = reverse('api_file', kwargs={'code': self.documents_pdf[0], 'suggested_format': 'pdf'})
        response = self.client.put(doc_url, content, content_type='multipart/form-data; boundary=BoUnDaRyStRiNg')
        self.assertEqual(response.status_code, 200)

    def test_30_api_get_document_indexes(self):
        """Get document indexes from CouchDB"""
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_file_info', kwargs={'code': self.documents_pdf[0]}) + '?indexing_data=1'
        response = self.client.get(url)
        r_data = json.loads(json.loads(response.content))
        if not "indexing_data" in r_data:
            raise AssertionError("No indexing data in %s" % r_data)
        indexing_data = r_data['indexing_data']
        if not 'description' in indexing_data:
            raise AssertionError('No "description" field in indexing_data')
        for key, value in indexing_data.iteritems():
            if not key in self.doc1_dict.iterkeys():
                raise AssertionError('Key "%s" not present in indexing_data: %s' % (key, indexing_data))
            if not indexing_data[key] in self.doc1_dict.itervalues():
                raise AssertionError('Value "%s" not present in indexing_data' % value)

    def test_zz_cleanup(self):
        """Test Cleanup"""
        self.cleanAll()
        # Doc #0 should be already deleted in delete test
        self.cleanUp([self.documents_pdf_this_test[1], self.documents_pdf_this_test[2]])
        self.cleanUp(self.documents_codes)
        self.cleanUp(self.jpg_codes)
