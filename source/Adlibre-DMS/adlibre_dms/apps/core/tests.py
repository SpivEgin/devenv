"""
Module: DMS Core tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""

# TODO: for this file
# 1. Fix hash codes plugin operation and make sure in tests they are working Bug #624

# 2. Method Document().get_filename() returns code this is wrong. Must return filename with extension,
# e.g. ADL-0001.pdf instead of ADL-0001

# 3. CouchDB plugin modifies workflow. Should not do that. Bug #1069

import os
import datetime
import zlib
import hashlib
import json

from couchdbkit import Server

from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.core.files.uploadedfile import UploadedFile

from adlibre.dms.base_test import DMSTestCase

from document_processor import DocumentProcessor
from core.models import DocTags
from core.models import CoreConfiguration
from core.models import DocumentTypeRule


class CoreTestCase(DMSTestCase):
    """Data for testing Core specific workflows"""
    fixtures = ['initial_datas.json', 'djangoplugins.json', 'dms_plugins.json', 'core.json', ]

    def __init__(self, *args, **kwargs):
        """Per test suite initialisation"""
        super(CoreTestCase, self).__init__(*args, **kwargs)

        self.couchdb_name = 'dmscouch_test'

        self.admin_user = User.objects.filter(is_superuser=True)[0]

        self.fs_metadata_ext = 'json'

        self.this_test_docs = ['ADL-0003']

        self.doc1 = {
            'description': u'Additional Secondary Indexes Data for file ADL-1111',
            'date': u'15/05/2013',
            u'Friends ID': u'123456',
            u'Friends Name': u'Yuri',
            u'Required Date': u'15/05/2013',
            u'Employee ID': u'11111',
            u'Employee Name': u'Yuri',
            u'Additional': u'Something more',
        }

    def _get_fixtures_file(self, code, extension='pdf'):
        """Opens a file from DMS fixtures directory"""
        path = os.path.join(self.test_document_files_dir, code + '.' + extension)
        result_file = open(path, 'r')
        result_file.seek(0)
        return result_file

    def _chek_documents_dir(self, filename, docrule, code=False, check_exists=True):
        """Tests DMS documents folder (Local Storage) for existing of given file there

        @filename should be like 'ADL-0001.json' or 'ADL-0002'
        @docrule is an instance of document's DocumentTypeRule()
        @check_exists is a task to test if this file exists in file system
        @code is a certain code specified for this filename (need in case it is impossible to get from @filename)
        """
        docs_dir = settings.DOCUMENT_ROOT
        file_path_list = docrule.split(filename)
        check_path = os.path.join(docs_dir, str(docrule.pk))
        if not code:
            # Obtaining code from filename
            file_path_list[-1] = filename.split('.')[0]
        else:
            file_path_list[-1] = code
        for item in file_path_list:
            check_path = os.path.join(check_path, item)
        check_path = os.path.join(check_path, filename)
        if check_exists:
            if not os.path.isfile(check_path):
                raise AssertionError('No such file: %s' % check_path)
        return check_path

    def _check_files_equal(self, fixtures_file, dms_file, compressed=True, check=True):
        """Tests if 2 given file objects are equal. Taking compression into account

        @param fixtures_file: is open file instance
        @param dms_file: is open file instance
        @param compressed: is a switch to compress @fixtures_file before comparing hashes
        @param check: is a switch to really compare hash codes

        @return: fixtures hash code and a hash code of a checked file from dms
        """
        def get_hash(document, method='md5', salt=settings.SECRET_KEY):
            """Helper to get a hash for a document

            @param document: hashed object
            @param method: type of hashing
            @param salt: is a secret phrase to hash an object
            """
            h = hashlib.new(method)
            h.update(document)
            h.update(salt)
            return h.hexdigest()
        if compressed:
            f_file = zlib.compress(fixtures_file.read())
            fixt_hashcode = get_hash(f_file)
        else:
            fixt_hashcode = get_hash(fixtures_file.read())
        dms_string = dms_file.read()
        dms_hashcode = get_hash(dms_string)
        if check:
            self.assertEqual(fixt_hashcode, dms_hashcode)
        return fixt_hashcode, dms_hashcode

    def _remove_file(self, code, extension='pdf', check_couchdb=True, check_revision_1=True):
        """Removes a file from DMS

        @code is an assigned object code
        """
        processor = DocumentProcessor()
        doc = processor.read(code, {'user': self.admin_user})
        processor = DocumentProcessor()
        processor.delete(code, {'user': self.admin_user})
        if processor.errors:
            raise AssertionError('Removing document error: %s' % processor.errors)
        if check_revision_1:
            r1 = code + '_r1.' + extension
            check_path = self._chek_documents_dir(r1, doc.get_docrule(), code=code, check_exists=False)
            if os.path.isfile(check_path):
                raise AssertionError('File: %s has not been actually removed' % code)
        rev_data = code + '.' + self.fs_metadata_ext
        check_metadata_path2 = self._chek_documents_dir(rev_data, doc.get_docrule(), code=code, check_exists=False)
        if os.path.isfile(check_metadata_path2):
            raise AssertionError('File: %s has not been actually removed' % check_metadata_path2)
        if check_couchdb:
            couchfile = self._open_couchdoc(self.couchdb_name, code)
            if couchfile:
                print couchfile
                print 'CouchDB file contents: \n'
                for key, value in couchfile.iteritems():
                    print '%s: %s' % (key, value)
                all_couchdocs = self._list_couch_docs(self.couchdb_name)
                print all_couchdocs
                raise AssertionError('CouchDB document has not been removed: %s' % code)

    def _check_file_revisions_dict(self, file_rev_data, file_code, check_rev_2=True, mimetype='application/pdf'):
        """Checking file_revisions_data dictionary for proper configuration and indexes in proper places

        @param file_rev_data: dict of file indexes with revision data. e.g. doc.get_file_revisions_data()
        @param file_code: is a code name of the file for the revisions data being checked
        @param check_rev_2: is a switch to check for revision 2 exists in there
        @param mimetype: is ability to specify custom mimetype for checking
        @return:
        """
        extension = 'pdf'
        if mimetype != 'application/pdf':
            if mimetype == 'image/jpeg':
                extension = 'jpg'
            else:
                raise AssertionError('unsupported mimetype')
        if not '1' in file_rev_data.keys():
            raise AssertionError('No revision data for revision 1 generated by manager')
        if check_rev_2:
            if '2' in file_rev_data.keys():
                raise AssertionError('Should not contain revision 2 at this stage of testing')
        rev1 = file_rev_data['1']
        self.assertIn('compression_type', rev1)
        self.assertEqual(rev1['compression_type'], 'GZIP')
        self.assertIn('created_date', rev1)
        try:
            datetime.datetime.strptime(rev1['created_date'], settings.DATETIME_FORMAT)
        except Exception, e:
            raise AssertionError('Revision 1 datetime is wrong with error: %s' % e)
        self.assertIn('mimetype', rev1)
        self.assertEqual(rev1['mimetype'], mimetype)
        self.assertIn('name', rev1)
        self.assertEqual(rev1['name'], file_code + '_r1.' + extension)
        self.assertIn('revision', rev1)
        self.assertEqual(rev1['revision'], 1)

    def _open_couchdoc(self, db_name, code, view_name='_all_docs'):
        """Open given document in a given CouchDB database

        @param: db_name is a couchdb name to look in for doc
        @param: code is a CouchDB document _id
        @param: view_name is a non default (_all_docs) name of CouchDB view to look for code
        """
        first_doc = {}
        server = Server()
        db = server.get_or_create_db(db_name)
        r = db.view(
            view_name,
            key=code,
            include_docs=True,
        )
        for row in r:
            first_doc = row['doc']
        return first_doc

    def _get_thumbnail_dir(self, code, docrule):
        """Create a thumbnail path for given document code.
        @param code: should be like 'ADL-0001' or 'ADL-0002'
        @param docrule: is an instance of document's DocumentTypeRule()
        @return: thumbnails path for current code
        """
        docs_dir = settings.DOCUMENT_ROOT
        file_path_list = docrule.split(code)
        docrule_id = str(docrule.pk)
        check_path = os.path.join(docs_dir, docrule_id)
        for item in file_path_list:
            check_path = os.path.join(check_path, item)
        return os.path.join(check_path, 'thumbnails_storage')

    def _chek_thumbnails_created(self, code, docrule, check_exists=True):
        """Tests DMS documents folder (Local Storage) for existing of given file there

        @code should be like 'ADL-0001' or 'ADL-0002'
        @docrule is an instance of document's DocumentTypeRule()
        @check_exists is a task to test if this file exists in file system
        """
        p = self._get_thumbnail_dir(code, docrule)
        thumbnail_check_path = os.path.join(p, code) + '.pdf.png'
        if check_exists:
            if not os.path.isfile(thumbnail_check_path):
                raise AssertionError('No such file: %s' % thumbnail_check_path)
            tmp_path = thumbnail_check_path.split('.png')[0]
            if os.path.isfile(tmp_path):
                raise AssertionError('Temporary file leftover thumbnail creation: %s' % tmp_path)
        return thumbnail_check_path

    def _check_dms_object_empty(self, doc):
        """Checks a DMS object for empty parameters (core integrity of the empty document object)"""
        # TODO: this is wrong. Code should store "ADL-0010", not file_name
        self.assertEqual(doc.code, None)
        self.assertEqual(doc.db_info, {})
        self.assertEqual(doc.current_file_revision_data, {})
        self.assertEqual(doc.file_obj, None)
        self.assertEqual(doc.file_revision_data, None)
        self.assertEqual(doc.full_filename, None)
        self.assertEqual(doc.fullpath, None)
        self.assertEqual(doc.hashcode, None)
        self.assertEqual(doc.index_revisions, {})
        self.assertEqual(doc.marked_deleted, False)
        self.assertEqual(doc.mimetype, None)
        self.assertEqual(doc.new_indexes, {})
        self.assertEqual(doc.old_docrule, None)
        self.assertEqual(doc.old_name_code, None)
        self.assertEqual(doc.options, {})
        self.assertEqual(doc.remove_tag_string, '')
        self.assertEqual(doc.requested_extension, None)
        self.assertEqual(doc.revision, None)
        self.assertEqual(doc.tag_string, '')
        self.assertEqual(doc.tags, [])
        self.assertEqual(doc.thumbnail, None)
        self.assertEqual(doc.user, self.admin_user)


class DocumentProcessorTest(CoreTestCase):
    """Test for core.DocumentProcessor() and it's workflow"""

    def setUp(self):
        """Per test initialization"""
        self.processor = DocumentProcessor()

    def test_00_initial_one_time_setup(self):
        """Populating data into test space"""
        pass

    def test_01_basic_create(self):
        """Create workflow with bulk file feeding,
        e.g. upload file without any additional data, named according to DMS rules.
        Should be file ADL-0001.pdf

        Tests it creates ADL-0001.json
        Tests it creates ADL-0001_r1.pdf
        Tests it does not create revision 2 or related files.
        Tests if file is compressed and stored into proper place with hashes
        Tests document created in CouchDB
        """
        print 'listing couchdocs for BEFORE tests to make sure we are clean'
        docs = self._list_couch_docs(self.couchdb_name)
        if docs:
            raise AssertionError('CouchDB is not clean for tests. Contains docs: %s' % [d for d in docs])
        file_code = self.documents_pdf[0]
        test_file = self._get_fixtures_file(file_code)
        doc = self.processor.create(test_file, {'user': self.admin_user})
        # Processor has no errors
        if self.processor.errors:
            raise AssertionError([e for e in self.processor.errors])
        # Proper name
        self.assertEqual(doc.get_filename(), file_code + '.pdf')
        # Proper docrule
        self.assertEqual(doc.get_docrule().pk, 2)
        # Proper revision data generated and has all the indexes required
        file_rev_data = doc.get_file_revisions_data()
        # TODO: check this with '_check_file_revisions_dict' method after fixing a bug with dict keys type (Bug #1091)
        if not 1 in file_rev_data.keys():
            raise AssertionError('No revision data for revision 1 generated by manager')
        if 2 in file_rev_data.keys():
            raise AssertionError('Should not contain revision 2 at this stage of testing')
        rev1 = file_rev_data[1]
        self.assertIn('compression_type', rev1)
        self.assertEqual(rev1['compression_type'], 'GZIP')
        self.assertIn('created_date', rev1)
        try:
            datetime.datetime.strptime(rev1['created_date'], settings.DATETIME_FORMAT)
        except Exception, e:
            raise AssertionError('Revision 1 datetime is wrong with error: %s' % e)
        self.assertIn('mimetype', rev1)
        self.assertEqual(rev1['mimetype'], 'application/pdf')
        self.assertIn('name', rev1)
        self.assertEqual(rev1['name'], file_code + '_r1.pdf')
        self.assertIn('revision', rev1)
        self.assertEqual(rev1['revision'], 1)
        # Files created
        json_path = self._chek_documents_dir(file_code + '.' + self.fs_metadata_ext, doc.get_docrule())
        path1 = self._chek_documents_dir(file_code + '_r1.pdf', doc.get_docrule(), code=file_code)
        path = self._chek_documents_dir(file_code + '_r2.pdf', doc.get_docrule(), code=file_code, check_exists=False)
        if os.path.isfile(path):
            raise AssertionError('Revision 2 file should be absent')
        # Proper files in proper places with proper data
        self._check_files_equal(self._get_fixtures_file(file_code), open(path1, 'r'))
        hcode1, hcode2 = self._check_files_equal(self._get_fixtures_file(file_code), open(json_path, 'r'), check=False)
        if hcode1 == hcode2:
            raise AssertionError('Wrong data stored into json file.')
        # Couchdb doc created properly
        couchdoc = self._open_couchdoc(self.couchdb_name, file_code)
        self.assertEqual(couchdoc['id'], file_code)
        self.assertEqual(couchdoc['metadata_doc_type_rule_id'], '2')

    def test_02_create_existing_code(self):
        """Feeding existing file again and checking for errors and actions

        e.g. Create file ADL-0001 with file ADL-0001 already existing in system form previous tests
        """
        file_code = self.documents_pdf[0]
        test_file = self._get_fixtures_file(file_code)
        doc = self.processor.create(test_file, {'user': self.admin_user})
        if self.processor.errors:
            self.assertIn('409', str(self.processor.errors[0]))
        else:
            raise AssertionError('Processor does not indicate about "create" of existing file.')
        path = self._chek_documents_dir(file_code + '_r2.pdf', doc.get_docrule(), code=file_code, check_exists=False)
        if os.path.isfile(path):
            raise AssertionError('Revision 2 file should be absent')
        json_path = self._chek_documents_dir(file_code + '.' + self.fs_metadata_ext, doc.get_docrule())
        json_data = open(json_path).read()
        rev_data = json.loads(json_data)
        if '2' in rev_data.iterkeys() or 2 in rev_data.iterkeys():
            raise AssertionError('Revisions integrity broken. Revision 2 metadata created, but it should not be so.')

    def test_03_create_new_code(self):
        """Creating new code uploading the same file (rename file upon creation)

        e.g. Uploading a file ADL-0001.pdf with forcing code ADL-0002 assignment.
        """
        file_code = self.documents_pdf[1]
        filename = self.documents_pdf[0]
        test_file = self._get_fixtures_file(filename)
        doc = self.processor.create(test_file, {'user': self.admin_user, 'barcode': file_code})
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        # Only revision 1 and metadata present
        json_path = self._chek_documents_dir(file_code + '.' + self.fs_metadata_ext, doc.get_docrule())
        path1 = self._chek_documents_dir(file_code + '_r1.pdf', doc.get_docrule(), code=file_code)
        path2 = self._chek_documents_dir(file_code + '_r2.pdf', doc.get_docrule(), code=file_code, check_exists=False)
        if os.path.isfile(path2):
            raise AssertionError('Revision 2 file should be absent')
        # Proper files in proper places with proper data
        self._check_files_equal(self._get_fixtures_file(filename), open(path1, 'r'))
        hcode1, hcode2 = self._check_files_equal(self._get_fixtures_file(filename), open(json_path, 'r'), check=False)
        if hcode1 == hcode2:
            raise AssertionError('Wrong data stored into json file.')
        # Couchdb doc created properly
        couchdoc = self._open_couchdoc(self.couchdb_name, file_code)
        self.assertEqual(couchdoc['id'], file_code)
        self.assertEqual(couchdoc['metadata_doc_type_rule_id'], '2')

    def test_04_create_file_with_indexes(self):
        """Create a file with certain code and secondary indexes specified

        e.g. Using a given 'index_info' dict in MUI

        Also:
        Refs #1069 CouchDB plugin modifies provided data when storing indexes
        original dict index_info is fed to processor and is modified during lifetime.
        This should not happen. (Fixed for now).
        """
        file_code = self.documents_pdf[2]
        filename = self.documents_pdf[0]
        tests_file = self._get_fixtures_file(filename)
        index_info = self.doc1
        options = {
            'user': self.admin_user,
            'barcode': file_code,
            'index_info': index_info,
        }
        doc = self.processor.create(tests_file, options)
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        self._chek_documents_dir(file_code + '.' + self.fs_metadata_ext, doc.get_docrule())
        self._chek_documents_dir(file_code + '_r1.pdf', doc.get_docrule(), code=file_code)
        # CouchDB doc created properly
        couchdoc = self._open_couchdoc(self.couchdb_name, file_code)
        self.assertEqual(couchdoc['id'], file_code)
        self.assertEqual(couchdoc['metadata_doc_type_rule_id'], '2')
        if couchdoc['index_revisions']:
            raise AssertionError('File should not contain index revisions at this stage.')
        if not couchdoc['metadata_description'] == index_info['description']:
            raise AssertionError('description metadata broken')
        if not '1' in couchdoc['revisions']:
            raise AssertionError('File indexing data not stored to CouchDB')
        for index in index_info.iterkeys():
            if not index in couchdoc['mdt_indexes'] and not index in ['description', 'date']:
                raise AssertionError('Secondary index absent: %s' % index)

    def test_05_create_0_revisions_file(self):
        """Create a file storing only metadata and 0 file revisions

        This creation should produce CpuchDB document without storing any files,
        but reserving this code, indicating this file exists.
        """
        file_code = self.documents_pdf[3]
        index_info = self.doc1
        options = {
            'user': self.admin_user,
            'barcode': file_code,
            'index_info': index_info,
            'only_metadata': True,
        }
        doc = self.processor.create(None, options)
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        filename1 = ''.join([file_code, '.', self.fs_metadata_ext])
        filename2 = ''.join([file_code, '_r1.pdf'])
        json_path = self._chek_documents_dir(filename1, doc.get_docrule(), check_exists=False)
        rev1_path = self._chek_documents_dir(filename2, doc.get_docrule(), code=file_code, check_exists=False)
        if os.path.isfile(json_path) or os.path.isfile(rev1_path):
            raise AssertionError('Directory should not contain files on creating 0 revisions file')
        # CouchDB doc created properly
        couch_doc = self._open_couchdoc(self.couchdb_name, file_code)
        self.assertEqual(couch_doc['id'], file_code)
        self.assertEqual(couch_doc['metadata_doc_type_rule_id'], '2')

    def test_06_create_document_without_security_permission(self):
        """Create a file request for user that is not in security group"""
        file_code = self.documents_pdf[4]
        tests_file = self._get_fixtures_file(file_code)
        user = User.objects.create_user(username='someone')
        doc = self.processor.create(tests_file, {'user': user, 'barcode': file_code})
        if not self.processor.errors:
            raise AssertionError('Processor should fail creating file for user not in security group')
        filename1 = ''.join([file_code, '.', self.fs_metadata_ext])
        filename2 = ''.join([file_code, '_r1.pdf'])
        json_path = self._chek_documents_dir(filename1, doc.get_docrule(), check_exists=False)
        rev1_path = self._chek_documents_dir(filename2, doc.get_docrule(), code=file_code, check_exists=False)
        if os.path.isfile(json_path) or os.path.isfile(rev1_path):
            raise AssertionError('Directory should not contain files on creating code without security permission')
        # CouchDB doc is not created
        couch_doc = self._open_couchdoc(self.couchdb_name, file_code)
        if couch_doc:
            raise AssertionError('CouchDB should not contain document: %s' % file_code)

    def test_07_create_by_user_in_security_group(self):
        """Create a file for user that is in security group"""
        user_login = 'some_user'
        user_pass = 'something'
        # give user a group 'security' (permission)
        user = User.objects.create_user(username=user_login, password=user_pass)
        group = Group.objects.get(name='security')
        group.user_set.add(user)
        # Upload a doc again
        file_code = self.documents_pdf[4]
        tests_file = self._get_fixtures_file(file_code)
        doc = self.processor.create(tests_file, {'user': user, 'barcode': file_code})
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        # Only revision 1 and metadata present
        self._chek_documents_dir(file_code + '.' + self.fs_metadata_ext, doc.get_docrule())
        self._chek_documents_dir(file_code + '_r1.pdf', doc.get_docrule(), code=file_code)
        path2 = self._chek_documents_dir(file_code + '_r2.pdf', doc.get_docrule(), code=file_code, check_exists=False)
        if os.path.isfile(path2):
            raise AssertionError('Revision 2 file should be absent')
        # CouchDB doc created properly
        couch_doc = self._open_couchdoc(self.couchdb_name, file_code)
        self.assertEqual(couch_doc['id'], file_code)
        self.assertEqual(couch_doc['metadata_doc_type_rule_id'], '2')

    def test_08_no_code_creation_and_uncategorized_off(self):
        """Create a code that has no Document Type Rule set"""
        # Disabling uncategorized support to test behaviour
        config = CoreConfiguration.objects.all()[0]
        config.delete()
        file_code = self.no_docrule_files[0]
        tests_file = self._get_fixtures_file(file_code, extension='jpg')
        doc = self.processor.create(tests_file, {'user': self.admin_user})
        if doc is not None:
            raise AssertionError('Assume we have to return None not a doc instance in case of creation no docrule file')
        if not self.processor.errors:
            raise AssertionError('Processor should contain errors')
        if self.processor.errors != [u'No document type rule found for file Z50141104.jpg']:
            raise AssertionError('Processor errors are wrong.')

    def test_09_no_code_creation_with_barcode_set(self):
        """Create a code that has no Document Type Rule set"""
        # Disabling uncategorized support to test behaviour
        config = CoreConfiguration.objects.all()[0]
        config.delete()
        file_code = self.no_docrule_files[0]
        tests_file = self._get_fixtures_file(file_code, extension='jpg')
        doc = self.processor.create(tests_file, {'user': self.admin_user, 'barcode': file_code})
        if doc is not None:
            raise AssertionError('Assume we have to return None not a doc instance in case of creation no docrule file')
        if not self.processor.errors:
            raise AssertionError('Processor should contain errors')

    def test_10_create_jpg(self):
        """Create a JPG file"""
        file_code = self.documents_jpg[2]
        test_file = self._get_fixtures_file(file_code, extension='jpg')
        doc = self.processor.create(test_file, {'user': self.admin_user})
        # Processor has no errors
        if self.processor.errors:
            raise AssertionError(self.processor.errors[0])
        # Proper name
        self.assertEqual(doc.get_filename(), file_code + '.jpg')
        # Proper docrule
        self.assertEqual(doc.get_docrule().pk, 9)
        # Proper revision data generated and has all the indexes required
        file_rev_data = doc.get_file_revisions_data()
        # TODO: check this with '_check_file_revisions_dict' method after fixing a bug with dict keys type (Bug #1091)
        if not 1 in file_rev_data:
            raise AssertionError('No revision data for revision 1 generated by manager')
        if 2 in file_rev_data:
            raise AssertionError('Should not contain revision 2 at this stage of testing')
        rev1 = file_rev_data[1]
        self.assertIn('compression_type', rev1)
        self.assertEqual(rev1['compression_type'], 'GZIP')
        self.assertIn('created_date', rev1)
        try:
            datetime.datetime.strptime(rev1['created_date'], settings.DATETIME_FORMAT)
        except Exception, e:
            raise AssertionError('Revision 1 datetime is wrong with error: %s' % e)
        self.assertIn('mimetype', rev1)
        self.assertEqual(rev1['mimetype'], 'image/jpeg')
        self.assertIn('name', rev1)
        self.assertEqual(rev1['name'], file_code + '_r1.jpg')
        self.assertIn('revision', rev1)
        self.assertEqual(rev1['revision'], 1)
        # Files created
        json_path = self._chek_documents_dir(file_code + '.' + self.fs_metadata_ext, doc.get_docrule())
        path1 = self._chek_documents_dir(file_code + '_r1.jpg', doc.get_docrule(), code=file_code)
        path = self._chek_documents_dir(file_code + '_r2.jpg', doc.get_docrule(), code=file_code, check_exists=False)
        if os.path.isfile(path):
            raise AssertionError('Revision 2 file should be absent')
        # Proper files in proper places with proper data
        self._check_files_equal(self._get_fixtures_file(file_code, extension='jpg'), open(path1, 'r'))
        file_2 = self._get_fixtures_file(file_code, extension='jpg')
        hash_code1, hash_code2 = self._check_files_equal(file_2, open(json_path, 'r'), check=False)
        if hash_code1 == hash_code2:
            raise AssertionError('Wrong data stored into json file.')
        # CouchDB doc created properly
        couch_doc = self._open_couchdoc(self.couchdb_name, file_code)
        self.assertEqual(couch_doc['id'], file_code)
        self.assertEqual(couch_doc['metadata_doc_type_rule_id'], '9')

    def test_11_create_tags(self):
        """Create a document with Tags. Stored into SQL DB"""
        tag_string = 'some_tag'
        file_code = self.documents_hash[0][0]
        test_file = self._get_fixtures_file(file_code)
        doc = self.processor.create(test_file, {'user': self.admin_user, 'tag_string': tag_string})
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        self._chek_documents_dir(file_code + '.' + self.fs_metadata_ext, doc.get_docrule())
        self._chek_documents_dir(file_code + '_r1.pdf', doc.get_docrule(), code=file_code)
        self.assertEqual(doc.get_tag_string(), tag_string)
        # Deleting doc and checking tags deleted too.
        self._remove_file(file_code)
        try:
            DocTags.objects.get(name=file_code)
            raise AssertionError('Tags for document %s should be deleted' % file_code)
        except ObjectDoesNotExist:
            pass

    def test_12_create_with_hash_code(self):
        """Creating a file with new code with hash code validation for provided file"""
        # TODO: logic here is broken somewhere. I should fix it.
        # @dms_stored_hashcode should not be different
        # FIXME: Hash code logic is really broken
        file_code = self.documents_hash[1][0]
        hcode = self.documents_hash[1][1]
        dms_stored_hashcode = '479610f78adc3aa7d30ea1e9fb166761'
        test_file = self._get_fixtures_file(file_code)
        doc = self.processor.create(test_file, {'user': self.admin_user, 'hashcode': hcode})
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        if not 'hashcode' in doc.get_file_revisions_data()[1]:
            raise AssertionError('Hash code is not present')
        f = self.processor.read(file_code, {'user': self.admin_user, 'hashcode': hcode})
        self.assertEqual(doc.get_file_revisions_data()[1]['hashcode'], dms_stored_hashcode)
        self.assertEqual(f.get_hashcode(), hcode)
        json_path = self._chek_documents_dir(file_code + '.' + self.fs_metadata_ext, doc.get_docrule())
        self._chek_documents_dir(file_code + '_r1.pdf', doc.get_docrule(), code=file_code)
        json_file = json.load(open(json_path))
        self.assertIn('hashcode', json_file['1'])
        self.assertEqual(json_file['1']['hashcode'], dms_stored_hashcode)

    def test_13_basic_read(self):
        """Read a document from DMS. Without additional data and secondary indexes"""
        file_code = self.documents_pdf[0]
        doc = self.processor.read(file_code, {'user': self.admin_user})
        if self.processor.errors:
            raise AssertionError('Errors on reading a code: %s' % [e for e in self.processor.errors])

        # Docrule OK
        self.assertEqual(doc.docrule.__class__.__name__, 'DocumentTypeRule')
        self.assertEqual(doc.docrule.title, 'Adlibre Invoices')
        self.assertEqual(doc.mimetype, 'application/pdf')

        # Proper revision data generated and has all the indexes required
        file_rev_data = doc.get_file_revisions_data()
        self._check_file_revisions_dict(file_rev_data, file_code)

        # Latest file revision object attached
        file_string = doc.get_file_obj().read()
        self.assertIn(self.pdf_file_contains, file_string)

        # Indexes dict OK
        db_info = doc.get_db_info()
        check_keys = [
            'description',
            'mdt_indexes',
            'tags',
            'metadata_doc_type_rule_id',
            'metadata_user_name',
            'metadata_created_date',
            'metadata_user_id',
        ]
        for key in check_keys:
            if not key in db_info:
                raise AssertionError('db_info dict Should contain key: %s' % key)
        self.assertEqual(db_info['metadata_user_name'], self.username)
        self.assertEqual(db_info['metadata_user_id'], '1')
        self.assertEqual(db_info['metadata_doc_type_rule_id'], '2')
        if db_info['metadata_created_date'].__class__.__name__ != 'datetime':
            raise AssertionError('db_info date should be datetime instead of: %s' % db_info['metadata_created_date'])

        # File names and path's
        # TODO: this is wrong. Must return filename with extension (Bug #1092)
        self.assertEqual(doc.get_filename(), file_code)
        self.assertEqual(doc.code, file_code)
        doc_rev1_name = file_code + '_r1.pdf'
        doc_rev1_path = self._chek_documents_dir(doc_rev1_name, doc.get_docrule(), code=file_code, check_exists=False)
        self.assertEqual(doc_rev1_path, doc.fullpath)

    def test_14_read_no_docrule(self):
        """Attempt to read a file without document type for it """
        # Disabling uncategorized support to test behaviour
        config = CoreConfiguration.objects.all()[0]
        config.delete()
        file_code = self.no_docrule_files[0]
        doc = self.processor.read(file_code, {'user': self.admin_user})
        if not self.processor.errors:
            raise AssertionError('DocumentProcessor instance should warn about document type rule does not exist')
        error = 'No document type rule found for file %s' % file_code
        self.assertEqual(self.processor.errors[0], error)
        if len(self.processor.errors) > 1:
            warn = self.processor.errors[2]
            raise AssertionError('DocumentProcessor should have only one warning about no docrule, instead: %s' % warn)
        if doc.docrule:
            raise AssertionError('Should not contain DocumentTypeRule: %s' % doc.get_docrule())
        if doc.get_file_revisions_data():
            raise AssertionError('Should not contain File revisions data: %s' % doc.get_file_revisions_data())
        if doc.get_db_info():
            raise AssertionError('Should not contain db_info: %s' % doc.get_db_info())

    def test_15_read_only_metadata(self):
        """Read a workflow 'only_metadata' to know only indexes and file indexes, without actual file retrieval"""
        file_code = self.documents_pdf[0]
        doc = self.processor.read(file_code, {'user': self.admin_user, 'only_metadata': True})
        if self.processor.errors:
            raise AssertionError('Errors on reading a code flag only_metadata: %s' % [e for e in self.processor.errors])
        if doc.get_file_obj():
            raise AssertionError('Read only_metadata should not contain file object')
        # Proper revision data generated and has all the indexes required
        file_rev_data = doc.get_file_revisions_data()
        if not '1' in file_rev_data.keys():
            raise AssertionError('No revision data for revision 1 generated by manager')
        if '2' in file_rev_data.keys():
            raise AssertionError('Should not contain revision 2 at this stage of testing')
        # File revisions data retrieved and proper
        file_rev_data = doc.get_file_revisions_data()
        self._check_file_revisions_dict(file_rev_data, file_code)

    def test_16_read_security_group(self):
        """Read file with user that is not in security group and add it there and read again"""
        file_code = self.documents_pdf[0]
        user = User.objects.create_user(username='someone')
        doc = self.processor.read(file_code, {'user': user, 'only_metadata': True})
        if not self.processor.errors:
            raise AssertionError('Processor should not work without errors')
        if not doc.docrule:
            raise AssertionError('Should contain Document Type Rule')
        if doc.current_file_revision_data:
            raise AssertionError('current_file_revision_data Should be empty: %s' % doc.current_file_revision_data)
        if doc.db_info:
            raise AssertionError('db_info Should be empty: %s' % doc.db_info)
        if doc.get_file_obj():
            raise AssertionError('file_obj Should be empty')

        # adding to a security group and processing
        group = Group.objects.get(name='security')
        group.user_set.add(user)

        doc = self.processor.read(file_code, {'user': user, 'only_metadata': True})
        if not self.processor.errors:
            raise AssertionError('Processor should not work without errors')
        if not doc.get_file_revisions_data():
            raise AssertionError("Processor should read the file's indexes")

    def test_17_read_not_existing(self):
        """Read code for document with code not existing in system"""
        inexisting_code = 'ADL-0010'
        doc = self.processor.read(inexisting_code, {'user': self.admin_user})
        if not self.processor.errors:
            raise AssertionError('DocumentProcessor should contain errors about file absent!')
        else:
            error = self.processor.errors[0]
            if not error.code == 404 or not self.processor.errors.__len__() == 1:
                raise AssertionError('DocumentProcessor returned wrong error.')
            self.assertEqual(error.parameter, 'No such document: %s' % inexisting_code)
        self._check_dms_object_empty(doc)
        self.assertEqual(doc.file_name, inexisting_code)
        # Docrule Recognized
        self.assertEqual(doc.docrule.__class__.__name__, 'DocumentTypeRule')
        self.assertEqual(doc.docrule.title, 'Adlibre Invoices')

    def test_18_read_not_existing_uncategorized(self):
        """Read code for document with code not existing in system and being uncategorized code"""
        inexisting_code = 'UNC-0010'
        doc = self.processor.read(inexisting_code, {'user': self.admin_user})
        if not self.processor.errors:
            raise AssertionError('DocumentProcessor should contain errors about file absent!')
        else:
            error = self.processor.errors[0]
            if not error.code == 404 or not self.processor.errors.__len__() == 1:
                raise AssertionError('DocumentProcessor returned wrong error.')
            self.assertEqual(error.parameter, 'No such document: %s' % inexisting_code)
        self._check_dms_object_empty(doc)
        self.assertEqual(doc.file_name, inexisting_code)
        # Docrule Recognized
        self.assertEqual(doc.docrule.__class__.__name__, 'DocumentTypeRule')
        self.assertEqual(doc.docrule.title, 'No doccode')

    def test_19_read_not_existing_no_rule(self):
        """Reading a code with not existing code and no docrule assigned.

        Checks for Uncategorized document type assigned properly and nothing worng returned"""
        inexisting_code = 'abracadabra'
        doc = self.processor.read(inexisting_code, {'user': self.admin_user})
        if not self.processor.errors:
            raise AssertionError('DocumentProcessor should contain errors about file absent!')
        else:
            error = self.processor.errors[0]
            if not error.code == 404 or not self.processor.errors.__len__() == 1:
                raise AssertionError('DocumentProcessor returned wrong error.')
            self.assertEqual(error.parameter, 'No such document: %s' % inexisting_code)
        self._check_dms_object_empty(doc)
        self.assertEqual(doc.file_name, inexisting_code)
        # Docrule Recognized
        self.assertEqual(doc.docrule.__class__.__name__, 'DocumentTypeRule')
        self.assertEqual(doc.docrule.title, 'No doccode')
        # DocRule sequence last not incremented
        self.assertEqual(doc.docrule.sequence_last, 0)

    def test_20_read_0_file_revisions(self):
        # TODO: develop
        pass

    def test_21_read_not_existing_only_metadata(self):
        # TODO: develop
        # TODO: fix bugs in this. Only_metadata call response contains lots of trash info. We should fix that and test
        pass

    def test_22_read_not_existing_with_extension(self):
        # TODO: develop
        pass

    def test_23_read_with_secondary_indexes(self):
        # TODO: develop
        pass

    def test_24_read_marked_deleted(self):
        # TODO: develop
        pass

    def test_25_create_revision_for_existing_code(self):
        """Updates a code with new file revision"""
        # TODO: develop
        pass

    def test_26_update_document_type_with_indexes_pdf(self):
        """Update existing code with new document type and new indexes in one call (For AUI usage)

        Refs #1349 CORE: zlib decompress issue with moved JPEG file (from AUI indexing)
        Refs #1353 CORE: Logic with revisions bug on update()
        """
        target_code = 'CCC-0001'
        options = {
            'new_name': None,
            'new_type': u'8',
            'extension': None,
            'remove_tag_string': None,
            'tag_string': None,
            'user': self.admin_user,
            'new_indexes': {
                u'Employee': u'tdyjetyj',
                u'Chosen Field': u'choice one',
                u'Tests Uppercase Field': u'ghmte'
            },
            'update_file': None,
        }
        code = self.uncategorized_codes[0]
        file_code = self.documents_pdf[0]
        test_file = self._get_fixtures_file(file_code)
        doc = self.processor.create(test_file, {'user': self.admin_user, 'barcode': code})
        if self.processor.errors:
            raise AssertionError('DocumentProcessor failed to create uncategorized file: %s' % code)
        self._chek_documents_dir(code + '_r1.pdf', doc.get_docrule(), code=code)

        doc = self.processor.update(code, options)
        if self.processor.errors:
            raise AssertionError('DocumentProcessor did not move document: %s, from uncategorized with indexes' % code)
        old_doc_path = self._chek_documents_dir(code, doc.get_docrule(), code=code, check_exists=False)
        if os.path.isfile(old_doc_path + '_r1.pdf'):
            raise AssertionError('DocumentProcessor left document: %s' % old_doc_path + '_r1.pdf')
        if os.path.isfile(old_doc_path + '.json'):
            raise AssertionError('DocumentProcessor left metadata indexes: %s' % old_doc_path + '.json')
        path1 = self._chek_documents_dir(target_code + '_r1.pdf', doc.get_docrule(), code=target_code)
        self._chek_documents_dir(target_code + '.json', doc.get_docrule(), code=target_code)

        # Proper files in proper places with proper data
        self._check_files_equal(self._get_fixtures_file(file_code), open(path1, 'r'))
        # CouchDB doc created properly
        couch_doc = self._open_couchdoc(self.couchdb_name, target_code)
        self.assertEqual(couch_doc['id'], target_code)
        self.assertEqual(couch_doc['metadata_doc_type_rule_id'], '8')
        self.assertEqual(couch_doc['mdt_indexes'], options['new_indexes'])
        if not u'1' in couch_doc['revisions'].iterkeys():
            raise AssertionError('File revisions metadata not present in CouchDB')
        if not u'compression_type' in couch_doc['revisions']['1'].iterkeys():
            raise AssertionError('Compression file metadata did not pass to CouchDB')

        self.assertEqual(doc.db_info['mdt_indexes'], options['new_indexes'])  # Indexing data present
        self.assertEqual(doc.code, target_code)
        self.assertEqual(doc.get_docrule().pk, 8)
        self.assertEqual(doc.file_obj, None)
        self.assertIn('1', doc.file_revision_data.iterkeys())
        self.assertIn('compression_type', doc.file_revision_data['1'].iterkeys())

        self.processor.delete(target_code, {'user': self.admin_user})
        if self.processor.errors:
            raise AssertionError('DocumentProcessor failed to remove file: %s' % target_code)

    def test_27_update_document_type_with_indexes_right_compression_jpeg(self):
        """Refs #1349 zlib decompress issue with moved JPEG file (from AUI indexing)"""
        # import time
        # time.sleep(20000)
        # TODO: develop this
        pass

    def test_28_thumbnail_read(self):
        """Thumbnail appearing in the destination folder without leaving temporary file and returned to caller"""
        code = self.documents_pdf[0]
        doc = self.processor.read(code, options={'user': self.admin_user, 'thumbnail': True})
        if self.processor.errors:
            raise AssertionError('DocumentProcessor failed to create a thumbnail for file: %s' % code)
        if not doc.thumbnail:
            raise AssertionError('thumbnail for code: %s is not present in manager run result')
        self._chek_thumbnails_created(code, doc.get_docrule())

    def test_29_thumbnail_for_uncategorized(self):
        """Upload an uncategorized PDF file and generate a thumbnail for it"""
        # making current code - UNC-0003
        dr = CoreConfiguration.objects.filter()[0].uncategorized
        dr.sequence_last = 2
        dr.save()
        code = self.uncategorized_codes[2]
        test_file = self._get_fixtures_file(self.documents_pdf[0])
        doc = self.processor.create(test_file, {'user': self.admin_user, 'barcode': code})
        if self.processor.errors:
            raise AssertionError('Can not create uncategorized document with errors creating document: %s %s'
                                 % (code, self.processor.errors))
        # Original filename is there in revision data
        self.assertEqual(doc.file_revision_data[1]['uncategorized_filename'], 'ADL-0001.pdf')
        self.assertEqual(doc.full_filename, 'UNC-0003.pdf')
        doc = self.processor.read(code, options={'user': self.admin_user, 'thumbnail': True})
        if self.processor.errors or not doc.thumbnail:
            raise AssertionError('DocumentProcessor errors for reading a thumbnail %s' % self.processor.errors)
        # Another usecase here to check for whole code thumbnail. Rather then code + extension
        thumb_path = self._chek_thumbnails_created(code, dr, check_exists=False)
        paths = os.path.split(thumb_path)
        thumb_path = os.path.join(paths[0], code) + '.png'
        if not os.path.isfile(thumb_path):
            raise AssertionError('Thumbnail have not been generated: %s' % thumb_path)

    def test_30_thumbnail_deletion(self):
        """Thumbnail deleted on changing this document or deleting this document"""
        code = self.this_test_docs[0]
        file_code = self.documents_pdf[0]
        test_file = self._get_fixtures_file(file_code)
        # Creating a document
        self.processor.create(test_file, {'user': self.admin_user, 'barcode': code})
        if self.processor.errors:
            raise AssertionError('Can not check thumbnail deletion because of errors creating document: %s %s'
                                 % (file_code, self.processor.errors))
        # Touch (reading) thumbnail
        doc = self.processor.read(code, options={'user': self.admin_user, 'thumbnail': True})
        docrule = doc.get_docrule()  # For future checks
        if self.processor.errors or not doc.thumbnail:
            raise AssertionError('DocumentProcessor errors for reading a thumbnail %s' % self.processor.errors)
        # Deletion of document and deletion of thumbnail
        self.processor.delete(code, options={'user': self.admin_user})
        if self.processor.errors:
            raise AssertionError('DocumentProcessor code delete errors: %s' % self.processor.errors)
        thumb_path = self._chek_thumbnails_created(code, docrule, check_exists=False)
        if os.path.isfile(thumb_path):
            raise AssertionError('Thumbnail have not been deleted: %s' % thumb_path)

    def test_31_thumbnail_update(self):
        """Thumbnail removed on document update. e.g. new file added or type changed"""
        code = self.this_test_docs[0]
        file_code = self.documents_pdf[0]
        indexes = {
            u'Employee': u'dgtjtj',
            u'Chosen Field': u'choice one',
            u'Tests Uppercase Field': u'tyjtyjtet'
        }
        test_file = self._get_fixtures_file(file_code)
        # Creating a document
        self.processor.create(test_file, {'user': self.admin_user, 'barcode': code})
        if self.processor.errors:
            raise AssertionError('Can not check thumbnail update because of errors creating document: %s %s'
                                 % (code, self.processor.errors))
        # Touch (reading) thumbnail
        doc = self.processor.read(code, options={'user': self.admin_user, 'thumbnail': True})
        docrule = doc.get_docrule()  # For farther checks of thumbnail left
        if self.processor.errors or not doc.thumbnail:
            raise AssertionError('DocumentProcessor errors for reading a thumbnail %s' % self.processor.errors)
        self.processor.update(code, options={'user': self.admin_user, 'new_type': u'8', 'new_indexes': indexes})
        if self.processor.errors:
            raise AssertionError('DocumentProcessor code update errors: %s' % self.processor.errors)
        # Returning back document for tests consistency
        self.processor.create(test_file, {'user': self.admin_user, 'barcode': code})
        thumb_path = self._chek_thumbnails_created(code, docrule, check_exists=False)
        if os.path.isfile(thumb_path):
            raise AssertionError('Thumbnail have not been deleted: %s' % thumb_path)

    def test_32_upload_first_revision_after_0_revisions_indexing(self):
        """Refs #1211: Indexes Missed at production

        This issue occurred after uploading file revisions to existing 0 revisions documents
        with "only indexes" set
        """

        code = 'CCC-0002'
        file_code = self.documents_pdf[0]
        indexes = {
            u'Employee': u'rthrthrhtw',
            u'Chosen Field': u'choice two',
            u'Tests Uppercase Field': u'rgeqrghqeg rgewg'
        }
        # Creating a document
        self.processor.create(None, {'user': self.admin_user, 'barcode': code, 'index_info': indexes})
        if self.processor.errors:
            raise AssertionError('Can not create document: %s %s'
                                 % (code, self.processor.errors))

        # Trying to create document file revision 1 again
        test_file = self._get_fixtures_file(file_code)
        ufile = UploadedFile(test_file, code + '.pdf', content_type='application/pdf')

        self.processor.create(ufile, {'user': self.admin_user, 'barcode': code})
        if not self.processor.errors:
            raise AssertionError('Created document: %s for existing code with indexes only present.' % code)
        else:
            if self.processor.errors.__len__() > 1:
                raise AssertionError(
                    'Created document: %s for existing code with indexes only present. MORE THEN 1 EXCEPTION RISED.'
                    % code)
            error1 = self.processor.errors[0]
            if not error1.__class__.__name__ == 'DmsException' and not error1.code == 409:
                raise AssertionError("Create existing code rises wrong Exception")
            # Cleanup processor errors for farther interactions
            self.processor.errors = []
        # Updating a document with revision 1 (First file revision)
        test_file = self._get_fixtures_file(file_code)
        ufile = UploadedFile(test_file, code + '.pdf', content_type='application/pdf')
        self.processor.update(code, {'user': self.admin_user, 'update_file': ufile})
        if self.processor.errors:
            raise AssertionError('Can not update document: %s with file revision 1: %s'
                                 % (code, self.processor.errors))
        doc = self.processor.read(code, options={'user': self.admin_user})
        if not '1' in doc.file_revision_data:
            raise AssertionError('Document file revisions absent')
        if not doc.db_info['mdt_indexes']:
            raise AssertionError('Document mdt_indexes deleted')
        if not doc.get_file_obj():
            raise AssertionError('Document has no file instance')

    def test_33_store_uncategorized(self):
        """Creates an uncategorized Document

        Current implementation should take an uncategorized file name into account,
        with storing it in the revision metadata ([code].json file in a document folder).

        Should be stored in an uncategorized folder, set in admin.
        This uncategorized testing should be done.

        Also feature should not work in case uncategorized document type is not set.
        E.g. Uncategorized document type is not selected in CoreConfiguration instance.
        """
        dest_name = self.uncategorized_codes[0]
        file_code, extension = os.path.splitext(self.uncategorized_files[0])
        extension = 'jpg'
        test_file = self._get_fixtures_file(file_code, extension=extension)
        doc = self.processor.create(test_file, {'user': self.admin_user})
        # Processor has no errors
        if self.processor.errors:
            raise AssertionError([e for e in self.processor.errors])
        # Proper name
        self.assertEqual(doc.get_filename(), dest_name + '.' + extension)
        # Proper docrule
        self.assertEqual(doc.get_docrule().pk, self.rule_uncategorized)
        # Proper revision data generated and has all the indexes required
        file_rev_data = doc.get_file_revisions_data()
        if not 1 in file_rev_data.keys():
            raise AssertionError('No revision data for revision 1 generated by manager')
        if 2 in file_rev_data.keys():
            raise AssertionError('Should not contain revision 2 at this stage of testing')
        rev1 = file_rev_data[1]
        self.assertIn('created_date', rev1)
        try:
            datetime.datetime.strptime(rev1['created_date'], settings.DATETIME_FORMAT)
        except Exception, e:
            raise AssertionError('Revision 1 datetime is wrong with error: %s' % e)
        self.assertIn('mimetype', rev1)
        self.assertEqual(rev1['mimetype'], 'image/jpeg')
        self.assertIn('name', rev1)
        self.assertEqual(rev1['name'], dest_name + '_r1.' + extension)
        self.assertIn('uncategorized_filename', rev1)
        self.assertEqual(rev1['uncategorized_filename'], file_code + '.' + extension)
        self.assertIn('revision', rev1)
        self.assertEqual(rev1['revision'], 1)
        # Files created
        self._chek_documents_dir(dest_name + '.' + self.fs_metadata_ext, doc.get_docrule())
        self._chek_documents_dir(dest_name + '_r1.' + extension, doc.get_docrule(), code=dest_name)
        path = self._chek_documents_dir(
            dest_name + '_r2.' + extension,
            doc.get_docrule(),
            code=file_code,
            check_exists=False
        )
        if os.path.isfile(path):
            raise AssertionError('Revision 2 file should be absent')
        path2 = self._chek_documents_dir(
            file_code + '.' + extension,
            doc.get_docrule(),
            code=file_code,
            check_exists=False
        )
        if os.path.isfile(path2):
            raise AssertionError('Original Uncategorizsed file name should be absent')

    def test_34_store_uncategorized_with_barcode(self):
        """Creates an uncategorized Document

        with Uncategorized barcode specified"""
        # Making last Uncategorized file UNC-0001 (not absent)
        config = CoreConfiguration.objects.all()[0]
        config.uncategorized.sequence_last += 1
        config.uncategorized.save()
        dest_name = self.uncategorized_codes[1]
        file_code, extension = os.path.splitext(self.documents_pdf[3])  # should not exist in DMS at this stage
        extension = 'pdf'
        test_file = self._get_fixtures_file(file_code, extension=extension)
        doc = self.processor.create(test_file, {'user': self.admin_user, 'barcode': 'some_fancy_filename'})
        # Processor has no errors
        if self.processor.errors:
            raise AssertionError([e for e in self.processor.errors])
        # Proper name
        self.assertEqual(doc.get_filename(), dest_name + '.' + extension)
        # Proper docrule
        self.assertEqual(doc.get_docrule().pk, self.rule_uncategorized)
        # Proper revision data generated and has all the indexes required
        file_rev_data = doc.get_file_revisions_data()
        if not 1 in file_rev_data.keys():
            raise AssertionError('No revision data for revision 1 generated by manager')
        if 2 in file_rev_data.keys():
            raise AssertionError('Should not contain revision 2 at this stage of testing')
        rev1 = file_rev_data[1]
        self.assertIn('created_date', rev1)
        try:
            datetime.datetime.strptime(rev1['created_date'], settings.DATETIME_FORMAT)
        except Exception, e:
            raise AssertionError('Revision 1 datetime is wrong with error: %s' % e)
        self.assertIn('mimetype', rev1)
        self.assertEqual(rev1['mimetype'], 'application/pdf')
        self.assertIn('name', rev1)
        self.assertEqual(rev1['name'], dest_name + '_r1.' + extension)
        self.assertIn('uncategorized_filename', rev1)
        self.assertEqual(rev1['uncategorized_filename'], file_code + '.' + extension)
        self.assertIn('revision', rev1)
        self.assertEqual(rev1['revision'], 1)
        # Files created
        self._chek_documents_dir(dest_name + '.' + self.fs_metadata_ext, doc.get_docrule())
        self._chek_documents_dir(dest_name + '_r1.' + extension, doc.get_docrule(), code=dest_name)
        path = self._chek_documents_dir(
            dest_name + '_r2.' + extension,
            doc.get_docrule(),
            code=file_code,
            check_exists=False
        )
        if os.path.isfile(path):
            raise AssertionError('Revision 2 file should be absent')
        path2 = self._chek_documents_dir(
            file_code + '.' + extension,
            doc.get_docrule(),
            code=file_code,
            check_exists=False
        )
        if os.path.isfile(path2):
            raise AssertionError('Original Uncategorizsed file name should be absent')

    def test_35_thumbnail_for_image(self):
        """Thumbnail generated for JPEG image document"""
        code = self.uncategorized_codes[0]  # Should be image (jpeg)
        doc = self.processor.read(code, options={'user': self.admin_user, 'thumbnail': True})
        if self.processor.errors or not doc.thumbnail:
            raise AssertionError('DocumentProcessor errors for reading a thumbnail %s' % self.processor.errors)
        # Another usecase here to check for whole code thumbnail. Rather then code + extension
        thumb_path = self._chek_thumbnails_created(code, doc.get_docrule(), check_exists=False)
        paths = os.path.split(thumb_path)
        thumb_path = os.path.join(paths[0], code) + '.png'
        if not os.path.isfile(thumb_path):
            raise AssertionError('Thumbnail have not been generated: %s' % thumb_path)

    def test_36_thumbnail_for_multiple_revisions_document(self):
        """Thumbnail generated for LAST JPEG image of the multiple revisions document

        adds revisions to the document by uploading another image after another image.
        check previous image does not equal to the new generated one."""
        code = self.uncategorized_codes[0]  # Should be image (jpeg)
        doc = self.processor.read(code, options={'user': self.admin_user, 'thumbnail': True})
        if self.processor.errors or not doc.thumbnail:
            raise AssertionError('DocumentProcessor errors for reading a thumbnail %s' % self.processor.errors)
        # Another usecase here to check for whole code thumbnail. Rather then code + extension
        thumbnail_1 = doc.thumbnail
        ext = 'jpg'
        new_file = self.fixtures_files[18]
        filename, extension = os.path.splitext(new_file)
        test_file = self._get_fixtures_file(filename, extension=ext)
        f = UploadedFile(test_file, test_file.name, content_type='image/jpeg')
        doc = self.processor.update(code + extension, options={'user': self.admin_user, 'update_file': f})
        if self.processor.errors:
            raise AssertionError('DocumentProcessor errors updateing athumbnails code: %s' % self.processor.errors)
        doc_file_revisions = doc.get_file_revisions_data()
        if not 2 in doc_file_revisions.iterkeys():
            raise AssertionError('New revision of a file is not present in metadata')
        if 3 in doc_file_revisions.iterkeys() or '3' in doc_file_revisions.iterkeys():
            raise AssertionError('File contains wrong metadata')
        self._chek_documents_dir(code + '_r2.' + ext, doc.get_docrule(), code=code)
        path = self._chek_documents_dir(
            code + '_r3.' + ext,
            doc.get_docrule(),
            code=code,
            check_exists=False
        )
        if os.path.isfile(path):
            raise AssertionError('Revision 3 file should be absent')
        # Check thumbnails absent after update
        thumb_path = self._chek_thumbnails_created(code, doc.get_docrule(), check_exists=False)
        paths = os.path.split(thumb_path)
        thumb_path = os.path.join(paths[0], code) + '.png'
        if os.path.isfile(thumb_path):
            raise AssertionError('Thumbnail have left over after update of a file: %s' % thumb_path)
        doc = self.processor.read(code, options={'user': self.admin_user, 'thumbnail': True})
        if self.processor.errors or not doc.thumbnail:
            raise AssertionError('DocumentProcessor errors for reading a thumbnail %s' % self.processor.errors)
        self.assertNotEqual(doc.thumbnail, thumbnail_1)

    def test_zz_cleanup(self):
        """Cleaning alll the docs and data that are touched or used in those tests"""
        for code in self.documents_pdf:
            self._remove_file(code)
        for code in [self.documents_hash[1][0], ]:
            self._remove_file(code)
        for code in [self.documents_jpg[2], ]:
            self._remove_file(code, extension='jpg')
        for code in ['CCC-0001', 'CCC-0002']:
            self._remove_file(code)
        for code in self.uncategorized_codes:
            self._remove_file(code)


class DocCodeModelTest(TestCase):
    """DocCode Model Tests"""
    fixtures = ['initial_datas.json', 'djangoplugins.json', 'dms_plugins.json', 'core.json', ]

    def setUp(self):
        """Populate test database with model instances."""
        # DocCodeModelTest Test Data
        self.MODELS = [DocumentTypeRule, ]

        self.generated_barcodes = (
            #(docode_id, result)
            (10, 'UNC-1001'),
            (2, 'ADL-1001'),
            (3, False),
            (4, False),
            (5, False),
            (6, False),
            (7, 'BBB-1001'),
            (8, 'CCC-1001'),
        )

    def tearDown(self):
        """Depopulate created model instances from test database."""
        for model in self.MODELS:
            for obj in model.objects.all():
                obj.delete()

    def test_generate_document_barcode(self):
        """This is a test for barcode generation."""

        for docrule_id, result in self.generated_barcodes:
            obj = DocumentTypeRule.objects.get(pk=docrule_id)
            obj.set_last_document_number(1000)
            self.assertEquals(obj.allocate_barcode(), result)
            self.assertEquals(obj.get_last_document_number(), 1001)

