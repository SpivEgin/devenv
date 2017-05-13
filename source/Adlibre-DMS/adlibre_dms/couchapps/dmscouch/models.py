"""Module: DMS CouchDB Documents manager

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from datetime import datetime
from django.conf import settings
from couchdbkit.ext.django.schema import Document
from couchdbkit.ext.django.schema import StringProperty
from couchdbkit.ext.django.schema import DateTimeProperty
from couchdbkit.ext.django.schema import ListProperty
from couchdbkit.ext.django.schema import DictProperty
from adlibre.date_converter import str_date_to_couch


class CouchDocument(Document):
    """Main CouchDB document format model

    Usually a representation of DMS Document() stored in CouchDB"""
    id = StringProperty()
    metadata_doc_type_rule_id = StringProperty(default="")
    metadata_user_id = StringProperty(default="")
    metadata_user_name = StringProperty(default="")
    metadata_created_date = DateTimeProperty(default=datetime.utcnow())
    metadata_description = StringProperty(default="")
    tags = ListProperty(default=[])
    mdt_indexes = DictProperty(default={})
    search_keywords = ListProperty(default=[])
    revisions = DictProperty(default={})
    index_revisions = DictProperty(default={})

    class Meta:
        app_label = "dmscouch"

    def populate_from_dms(self, user, document):
        """Populates CouchDB Document fields from DMS Document object.

        @param user: django internal User() object instance
        @param document: DMS Document() instance"""
        # Setting document ID, based on filename. Using stripped (pure docrule regex readable) filename if possible.
        if document.get_code():
            self.id = document.get_code()
            self._doc['_id'] = self.id
        self.metadata_doc_type_rule_id = str(document.docrule.pk)
        # setting provided user name/id
        if "metadata_user_name" in document.db_info and "metadata_user_id" in document.db_info:
            self.metadata_user_name = document.db_info["metadata_user_name"]
            self.metadata_user_id = document.db_info["metadata_user_id"]
        else:
            self.set_user_name_for_couch(user)
        self.set_doc_date(document)
        # adding description if exists
        if "description" in document.db_info:
            self.metadata_description = document.db_info["description"]
        else:
            self.metadata_description = ""
        self.tags = document.tags
        # populating secondary indexes
        if document.db_info:
            db_info = document.db_info
            # trying to cleanup irrelevant fields if exist...
            # (Bug #829 Files Secondary indexes contain username and user PK)
            del_keys = []
            for key in db_info:
                if key in [
                    "date",
                    "description",
                    "metadata_user_name",
                    "metadata_user_id",
                    "mdt_indexes",
                    "metadata_created_date",
                    "metadata_doc_type_rule_id",
                    "tags",
                ]:
                    del_keys.append(key)
            for key in del_keys:
                del db_info[key]
            self.mdt_indexes = db_info
        self.search_keywords = []  # TODO: not implemented yet
        self.revisions = document.get_file_revisions_data()
        if document.index_revisions:
            self.index_revisions = document.index_revisions

    def populate_into_dms(self, document):
        """Updates DMS Document object with CouchDB fields data.

        @param document: DMS Document() instance"""
        document.set_file_revisions_data(self.revisions)
        if self.tags:
            document.tags = self.tags
        document.code = self.id
        document.db_info = self.construct_db_info()
        if 'index_revisions' in self:
            document.index_revisions = self.index_revisions
        if 'deleted' in self:
            if self['deleted'] == 'deleted':
                document.marked_deleted = True
        return document

    def construct_db_info(self, db_info=None):
        """Method to populate additional database info from CouchDB into DMS Document object.

        @param db_info: a set of CouchDB metadata info, extracted from CouchDB document"""
        if not db_info:
            db_info = {}
        db_info["description"] = self.metadata_description
        db_info["tags"] = self.tags
        db_info["metadata_doc_type_rule_id"] = self.metadata_doc_type_rule_id
        db_info["metadata_user_id"] = self.metadata_user_id
        db_info["metadata_user_name"] = self.metadata_user_name
        db_info["metadata_created_date"] = self.metadata_created_date
        db_info["mdt_indexes"] = self.mdt_indexes
        return db_info

    def construct_index_revision_dict(self, old_couchdoc_id=False):
        """Constructs current indexes revision and export into result dict

        @param old_couchdoc_id: either to include or not old document name into metadata list
            mus contain old couchdoc name"""
        current_index_data = {
            'metadata_created_date':   self.metadata_created_date,
            'metadata_description':    self.metadata_description,
            'metadata_user_id':        self.metadata_user_id,
            'metadata_user_name':      self.metadata_user_name,
            'mdt_indexes':    self.mdt_indexes,
        }
        if old_couchdoc_id:
            current_index_data['metadata_old_id'] = old_couchdoc_id
        return current_index_data

    def set_doc_date(self, document):
        """Unifies DB storage of date object received from document.

        @param document: DMS Document() instance"""
        doc_date = None
        # trying to get date from db_info dict first
        if 'date' in document.db_info:
            doc_date = datetime.strptime(str(document.db_info["date"]), settings.DATE_FORMAT)
        if not doc_date and document.revision:
            # Setting document current revision metadata date, except not exists using now() instead.
            revision = unicode(document.revision)
            if revision in document.file_revision_data:
                rev_dict = document.file_revision_data[revision]
                if 'created_date' in rev_dict[revision]:
                    tmp_date = rev_dict[revision][u'created_date']
                    doc_date = datetime.strptime(tmp_date, "%Y-%m-%d %H:%M:%S")
        if not doc_date:
            doc_date = datetime.utcnow()
        self.metadata_created_date = doc_date

    def update_indexes_revision(self, document):
        """Updates CouchDB document with new revision of indexing data.

        @param document: DMS Document() instance

        Old indexing data is stored in revision. E.g.:
        Document only created:

            couchdoc.index_revisions = None

        Document updated once:

            couchdoc.index_revisions = { '1': { ... }, }

        Document updated again and farther:

            couchdoc.index_revisions = {
                '1': { ... },
                '2': { ... },
                ...
            }

        This method handles storing of indexing data changes (old one's) are stored into revisions.
        New data are populated into couchdoc thus making them current.
        """
        if document.new_indexes:
            # Creating clean self.mdt_indexes
            secondary_indexes = {}
            for secondary_index_name, secondary_index_value in document.new_indexes.iteritems():
                if not secondary_index_name in ['description', 'metadata_user_name', 'metadata_user_id',]:
                    # Converting date format to couch if secondary index is DMS date type
                    try:
                        datetime.strptime(secondary_index_value, settings.DATE_FORMAT)
                        secondary_indexes[secondary_index_name] = str_date_to_couch(secondary_index_value)
                    except ValueError:
                        secondary_indexes[secondary_index_name] = secondary_index_value
                        pass
            # Only for update without docrule change (it makes it's own indexes backup)
            if not document.old_docrule:
                # Storing current index data into new revision
                if not 'index_revisions' in self:
                    # Creating index_revisions initial data dictionary.
                    self.index_revisions = {'1': self.construct_index_revision_dict(), }
                else:
                    # Appending new document indexes revision to revisions dict
                    new_revision = self.index_revisions.__len__() + 1
                    self.index_revisions[new_revision] = self.construct_index_revision_dict()
            # Populating self with new provided data
            self.mdt_indexes = secondary_indexes
            # Making desc and user data optional, taking them from current user
            if 'description' in document.new_indexes:
                self.metadata_description = document.new_indexes['description']
            else:
                self.metadata_description = 'N/A'
            if 'metadata_user_id' in document.new_indexes:
                self.metadata_user_id = document.new_indexes['metadata_user_id']
            else:
                self.metadata_user_id = unicode(document.user.id)
            if 'metadata_user_name' in document.new_indexes:
                self.metadata_user_id = document.new_indexes['metadata_user_name']
            else:
                self.metadata_user_name = document.user.username
        return document

    def update_file_revisions_metadata(self, document):
        """ Stores files revision data into CouchDB from DMS document object

        @param document: DMS Document() instance

        E.g.: Before this function:
            couchdoc.revisions = { '1': { ... }, }

        After:
            couchdoc.revisions = { '1': { ... }, '2': { ... }, }
        (Loaded from a Document() object)
        """
        self.revisions = document.get_file_revisions_data()

    def migrate_metadata_for_docrule(self, document, old_couchdoc):
        """Moving a CouchDB document into another file

        @param document: DMS Document() instance
        @param old_couchdoc: CouchDocument instance"""
        if not old_couchdoc.index_revisions:
            # Creating index_revisions initial data dictionary.
            self.index_revisions = {'1': old_couchdoc.construct_index_revision_dict(old_couchdoc.id), }
        else:
            self.index_revisions = old_couchdoc.index_revisions
            # Appending new document indexes revision to revisions dict
            new_revision = self.index_revisions.__len__() + 1
            self.index_revisions[str(new_revision)] = old_couchdoc.construct_index_revision_dict(old_couchdoc.id)
        self.revisions = document.get_file_revisions_data()
        self.metadata_description = old_couchdoc.metadata_description
        if document.user:
            self.set_user_name_for_couch(document.user)
        else:
            self.metadata_user_id = old_couchdoc.metadata_user_id
            self.metadata_user_name = old_couchdoc.metadata_user_name
        self.metadata_description = old_couchdoc.metadata_description
        self.metadata_created_date = old_couchdoc.metadata_created_date
        self.search_keywords = old_couchdoc.search_keywords
        self.tags = old_couchdoc.tags
        self.metadata_doc_type_rule_id = str(document.docrule.pk)
        self.id = document.get_filename()

    def set_user_name_for_couch(self, user):
        """ user name/id from Django user

        @param user: django internal User() object instance"""
        self.metadata_user_id = str(user.pk)
        if user.first_name:
            self.metadata_user_name = user.first_name + u' ' + user.last_name
        else:
            self.metadata_user_name = user.username
