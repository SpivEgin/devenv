"""
Module: DMS Browser Django Unit Tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import magic

from django.conf import settings
from django.core.urlresolvers import reverse

from adlibre.dms.base_test import DMSTestCase
from core.models import CoreConfiguration
from django.contrib.auth.models import User


class ViewTest(DMSTestCase):
    """Adlibre Browser Views and functionality test case

    Test data is provided by DMSTestCase
    """

    # TODO: Add test to upload files with no docrule.
    # TODO: Add test to upload files with wrong mime type.

    def test_00_setup(self):
        # Load Test Data
        self.loadTestData()

    def test_zz_cleanup(self):
        """Test Cleanup (Executed after all tests"""
        self.cleanAll()

    def test_AUI_support(self):
        """Support of database setting for AUI"""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('home'))
        # AUI uncategorized PK present in AUI call URL
        conf = CoreConfiguration.objects.filter()[0]
        self.assertContains(response, '&uncategorized_id=%s' % conf.uncategorized.pk)
        self.assertContains(response, conf.aui_url)

    def browser_upload_file(self, filename):
        url = reverse('upload')
        self.client.login(username=self.username, password=self.password)
        # Do upload
        data = {'file': open(filename, 'r')}
        response = self.client.post(url, data)
        return response

    def test_upload_files(self):
        for doc_set, ext in [(self.documents_pdf, 'pdf'), (self.documents_txt, 'txt'), (self.documents_tif, 'tif')]:
            for f in doc_set:
                response = self.browser_upload_file(settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.' + ext)
                self.assertContains(response, 'File has been uploaded')

    def test_upload_files_hash(self):
        for f in self.documents_hash:
            response = self.browser_upload_file(settings.FIXTURE_DIRS[0] + '/testdata/' + f[0] + '.pdf')
            self.assertContains(response, 'File has been uploaded')

    # TODO: expand this to get documents with specific revisions.
    def test_get_document(self):
        # Test security group required
        for d in self.documents_pdf:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, "You're not in security group", status_code=403)
        self.client.login(username=self.username, password=self.password)
        # Check mime type
        mime = magic.Magic(mime=True)
        for d in self.documents_pdf:
            url = '/get/' + d
            response = self.client.get(url)
            mimetype = mime.from_buffer(response.content)
            self.assertEquals(mimetype, 'application/pdf')
        for d in self.documents_pdf:
            url = '/get/' + d + '?extension=pdf'
            response = self.client.get(url)
            mimetype = mime.from_buffer(response.content)
            self.assertEquals(mimetype, 'application/pdf')
        # Check 404 on missing documents
        for d in self.documents_missing:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, 'No such document', status_code=404)

    def test_get_document_hash(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_hash:
            url = '/get/%s?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, self.pdf_file_contains)

        for d in self.documents_hash:
            url = '/get/%s.pdf?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, self.pdf_file_contains)

        for d in self.documents_hash:
            url = '/get/%s.pdf?hashcode=%s&extension=txt' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, self.pdf_file_contains)

        # TODO: fix this it will break...
        for d in self.documents_missing_hash:
            url = '/get/%s?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, 'Hashcode did not validate', status_code=500)

    def test_versions_view(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_pdf:
            url = '/revision/' + d
            response = self.client.get(url)
            self.assertContains(response, 'Revision of')

    def test_documents_view(self):
        self.client.login(username=self.username, password=self.password)
        for r in self.rules:
            url = '/files/' + str(r) + '/'
            response = self.client.get(url)
            self.assertContains(response, 'Documents for')
        for r in self.rules_missing:
            url = '/files/' + str(r) + '/'
            response = self.client.get(url)
            self.assertContains(response, '', status_code=404)

    def test_displays_all_required_documents(self):
        """
        Documents found by browser app and rendered properly by API.

        Backend provides all proper data for browser 'view documents list for docrule' section.
        """
        self.client.login(username=self.username, password=self.password)
        for rule_id in ['2', '7']:
            url = reverse('files_document', kwargs={'id_rule': rule_id})
            data = {"finish": "15",
                    "order": "created_date",
                    "start": "0"
                    }
            response = self.client.post(url, data)
            if rule_id == '2':
                self._check_docs_exist(
                    response,
                    self.documents_pdf,
                    [self.documents_missing, self.documents_tif, self.documents_txt]
                )
            if rule_id == '7':
                self._check_docs_exist(
                    response,
                    self.documents_pdf2,
                    [self.documents_pdf, self.documents_missing, self.documents_tif, self.documents_txt]
                )

    def _check_docs_exist(self, response, exist, not_exist_list_of_lists):
        """Helper to check for documents names present/absent in response"""
        for doc_name in exist:
            self.assertContains(response, doc_name)
        for not_exist_list in not_exist_list_of_lists:
            for doc_name in not_exist_list:
                self.assertNotContains(response, doc_name)


class SettingsTest(DMSTestCase):

    def test_settings_view(self):
        url = '/settings/'
        # un-authenticated request
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre DMS')
        self.assertContains(response, 'Log in |')
        # authenticated
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertContains(response, 'Settings')

    def test_plugins_view(self):
        url = '/settings/plugins'
        # un-authenticated request
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre DMS')
        self.assertContains(response, 'Log in |')
        # authenticated
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertContains(response, 'Plugins')


class MiscViewTest(DMSTestCase):

    def test_index_view(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre DMS')


class ConversionTest(DMSTestCase):

    def test_00_setup(self):
        # Load Test Data
        self.loadTestData()

    def test_tif2pdf_conversion(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_tif:
            url = reverse('get_file', kwargs={'code': d, 'suggested_format': 'pdf'})
            response = self.client.get(url)
            self.assertContains(response, '')

    def test_txt2pdf_conversion(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_txt:
            url = reverse('get_file', kwargs={'code': d, 'suggested_format': 'pdf'})
            response = self.client.get(url)
            self.assertContains(response, '')

    def test_pdf2txt_conversion(self):
        self.client.login(username=self.username, password=self.password)
        # FIXME: real pdf to txt conversion not tested here. Do we really need it?
        for d in self.documents_pdf:
            url = reverse('get_file', kwargs={'code': d, 'suggested_format': 'txt'})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_zz_cleanup(self):
        """Test Cleanup"""
        self.cleanAll()


class RegistrationTest(DMSTestCase):
    """Testing django registration forms and password renewal"""

    def setUp(self):
        # Creating a special registration user
        self.registration_email = 'another@hostname.com'
        self.registration_username = 'RegistrationTest'
        registration_user = User(username=self.registration_username)
        registration_user.email = self.registration_email
        registration_user.save()
        self.registration_user = registration_user

    def test_01_registration_openes(self):
        url = reverse('pwd_reset')
        response = self.client.get(url)
        self.assertContains(response, 'id_email')
        self.assertContains(response, 'Enter your e-mail address below')
        self.assertNotContains(response, 'Admin')  # Django admin template not used

    def test_02_registration_confirmation(self):
        url = reverse('pwd_reset')
        retrieve_url = 'http://127.0.0.1:8000/user/password/reset/NA-3rd-a49dd5e53146caf72ddb/'
        post_data = {'email': self.registration_user.email}
        response = self.client.post(url, post_data)
        exp_url = reverse('django.contrib.auth.views.password_reset_done')
        self.assertRedirects(response, exp_url)
        response = self.client.get(exp_url)
        self.assertContains(response, 'Instructions Emailed')
        response = self.client.get(retrieve_url)
        self.assertContains(response, 'Password reset unsuccessful')

    # TODO: make check of full password reset with intercepting token.
