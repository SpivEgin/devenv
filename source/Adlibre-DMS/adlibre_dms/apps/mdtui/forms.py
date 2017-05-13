"""
Module: MDTUI forms

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash

Dynamic form that allows the user to change and then verify the data that was parsed
Built based on code of Django Snippet: Dynamic Django form.
http://djangosnippets.org/snippets/714/
"""

from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
import datetime

from forms_representator import setFormFields
from forms_representator import setFormData
from adlibre.date_converter import date_standardized

CUSTOM_ERRORS = {
    'NUMBER': 'Must be Number. (example "123456")',
    'DATE': 'Must be in valid Date format. (example "%s")' % date_standardized('2012-12-30'),
    'UPPER': 'This field should be uppercase.'
}


class DocumentUploadForm(forms.Form):
    file = forms.FileField()


class BarcodePrintedForm(forms.Form):
    printed = forms.CharField(required=True,widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(BarcodePrintedForm, self).__init__(*args, **kwargs)
        self.fields['printed'].initial = 'printed'

    def clean_printed(self):
        printed = self.cleaned_data.get('printed')
        if not printed == 'printed':
            raise forms.ValidationError("Form not validated")
        return printed


class DocumentIndexForm(forms.Form):
    """
    Form for posting document indexes.

    Has dynamic initialization abilities.
    """
    description = forms.CharField(max_length=100, label="Description", help_text="Brief Document Description")

    def __init__(self, *args, **kwargs):
        super(DocumentIndexForm, self).__init__(*args, **kwargs)

    def setFields(self, kwds):
        setFormFields(self, kwds)

    def setData(self, kwds):
        setFormData(self, kwds)

    def populateFormSecondary(self, kwds):
        data = {}
        if kwds:
            keys = [k for k in kwds.iterkeys()]
            if keys:
                for key in keys:
                    for field in self.fields:
                        if 'field_name' in self.fields[field].__dict__:
                            if key==self.fields[field].__dict__['field_name']:
                                data[field] = kwds[key]
                                self.data[field] = kwds[key]
                                try:
                                    int_value = int(kwds[key])
                                    self.fields[field].initial = int_value
                                    self.initial[field] = int_value
                                except ValueError:
                                    try:
                                        dt = datetime.datetime.strptime(kwds[key], settings.DATE_FORMAT)
                                        self.fields[field].initial = dt
                                        self.initial[field] = dt
                                    except ValueError:
                                        try:
                                            self.fields[field].initial = kwds[key]
                                            self.initial[field] = kwds[key]
                                        except ValueError:
                                            pass
                # Form description populated on non search requests
                if 'description' in keys:
                    self.fields['description'].initial = kwds['description']
                    self.base_fields['description'].initial = kwds['description']

    def validation_ok(self):
        """
        Form validation sequence overridden here.
        Does check if field is entered (basic fields validation)
        Does Type validation for the proper data entry.
        E.g. if user enters ABC instead of 123 or date in wrong format.
        Char fields are only checked if entered at all.
        """
        # TODO: refactor this part to be used only for indexing
        for field in self.fields:
            cur_field = self.fields[field]
            # Simple if field entered validation
            try:
                # Validate only if those keys exist e.g in search usage there is no description field
                try:
                    # Trimming whitespaces on all fields
                    self.data[unicode(field)] = self.data[unicode(field)].strip(' \t\n\r')
                    cur_field.validate(self.data[unicode(field)])
                except ValidationError, e:
                    # appending error to form errors
                    self.errors[field] = e
                    self._errors[field] = e
            except KeyError:
                pass

            # Wrong type validation
            try:
                # Validate only if those keys exist
                if cur_field.__class__.__name__ == "IntegerField":
                    try:
                        int(self.data[unicode(field)])
                    except ValueError:
                        # appending error to form errors
                        if self.data[unicode(field)]:
                            # Wrong data entered adding type error
                            e = ValidationError(CUSTOM_ERRORS['NUMBER'])
                            self.errors[field] = e
                            self._errors[field] = e
                        pass
                if cur_field.__class__.__name__ == "DateField":
                    try:
                        datetime.datetime.strptime(self.data[unicode(field)], settings.DATE_FORMAT)
                    except ValueError:
                        # appending error to form errors
                        if self.data[unicode(field)]:
                            # Wrong data entered adding type error
                            e = ValidationError(CUSTOM_ERRORS['DATE'])
                            self.errors[field] = e
                            self._errors[field] = e
                        pass
            except KeyError:
                pass
        if self.errors:
            return False
        return True


class EditDocumentIndexForm(forms.Form):
    """
    Form for editing document indexes.
    Has dynamic initialization abilities.
    """
    description = forms.CharField(max_length=100, label="Description", help_text="Brief Document Description")

    def __init__(self, *args, **kwargs):
        super(EditDocumentIndexForm, self).__init__(*args, **kwargs)

    def setFields(self, kwds):
        setFormFields(self, kwds)

    def setData(self, kwds):
        setFormData(self, kwds)
        if 'description' in kwds:
            self.base_fields['description'].initial = kwds['description']

    def validation_ok(self):
        """
        Form validation sequence overridden here.
        Does check if field is entered (basic fields validation)
        Does Type validation for the proper data entry.
        E.g. if user enters ABC instead of 123 or date in wrong format.
        Char fields are only checked if entered at all.
        """
        # TODO: test validation if it is working or not... (garmoncheg @ #794 Edit metadata)
        for field in self.fields:
            cur_field = self.fields[field]
            # Simple if field entered validation
            try:
                # Validate only if those keys exist e.g in search usage there is no description field
                try:
                    # Trimming whitespaces on all fields
                    self.data[unicode(field)] = self.data[unicode(field)].strip(' \t\n\r')
                    cur_field.validate(self.data[unicode(field)])
                except ValidationError, e:
                    # appending error to form errors
                    self.errors[field] = e
                    self._errors[field] = e
            except KeyError:
                pass

            # Wrong type validation
            try:
                # Validate only if those keys exist
                if cur_field.__class__.__name__ == "IntegerField":
                    try:
                        int(self.data[unicode(field)])
                    except ValueError:
                        # appending error to form errors
                        if self.data[unicode(field)]:
                            # Wrong data entered adding type error
                            e = ValidationError(CUSTOM_ERRORS['NUMBER'])
                            self.errors[field] = e
                            self._errors[field] = e
                        pass
                if cur_field.__class__.__name__ == "DateField":
                    try:
                        datetime.datetime.strptime(self.data[unicode(field)], settings.DATE_FORMAT)
                    except ValueError:
                        # appending error to form errors
                        if self.data[unicode(field)]:
                            # Wrong data entered adding type error
                            e = ValidationError(CUSTOM_ERRORS['DATE'])
                            self.errors[field] = e
                            self._errors[field] = e
                        pass
            except KeyError:
                pass
        if self.errors:
            return False
        return True


class DocumentSearchOptionsForm(forms.Form):
    """
    Form for searching documents by indexes.

    Has dynamic initialization abilities.
    """
    date = forms.DateField(label="Indexing Date From", help_text="Date of the document added")
    end_date = forms.DateField(required=False, label="Indexing Date To", help_text="Final possible document date")
    export_results = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(DocumentSearchOptionsForm, self).__init__(*args, **kwargs)

    def setFields(self, kwds):
        setFormFields(self, kwds)

    def setData(self, kwds):
        setFormData(self, kwds)

    def validation_ok(self):
        for field in self.fields:
            cur_field = self.fields[field]
            # Wrong type validation
            try:
                # Validate only if those keys exist
                if cur_field.__class__.__name__ == "IntegerField":
                    try:
                        int(self.data[unicode(field)])
                    except ValueError:
                        # appending error to form errors
                        if self.data[unicode(field)]:
                            # Wrong data entered adding type error
                            e = ValidationError(CUSTOM_ERRORS['NUMBER'])
                            self.errors[field] = e
                            self._errors[field] = e
                        pass
                if cur_field.__class__.__name__ == "DateField":
                    try:
                        datetime.datetime.strptime(self.data[unicode(field)], settings.DATE_FORMAT)
                    except ValueError:
                        # appending error to form errors
                        if self.data[unicode(field)]:
                            # Wrong data entered adding type error
                            e = ValidationError(CUSTOM_ERRORS['DATE'])
                            self.errors[field] = e
                            self._errors[field] = e
                        pass
            except KeyError:
                pass
        if self.errors:
            return False
        return True

