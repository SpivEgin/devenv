"""
Module: DMS Metadata Template Manager

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging
from mdtcouch.models import MetaDataTemplate
from couchdbkit.exceptions import ResourceConflict

log = logging.getLogger('dms.mdtcouch.mdt_manager')


class MetaDataTemplateManager(object):
    """Main DMS manager for operating with Metadata Templates.

    Uses only CouchDB storage implementation for now.
    """
    def __init__(self):
        self.mdt = {}
        self.docrule_id = None
        self.delete = False

    def get_mdts_for_docrule(self, docrule_id):
        """
        Method to construct response with MDT's for docrule provided.
        Returns dict of MDT's for docrule_id provided/or False to indicate failure in operation.
        """
        log.debug('Getting MDT-s for document type rule: %s' % docrule_id)
        mdts_list = {}
        self.docrule_id = docrule_id
        # Validating
        if self.mdt_read_call_valid():
            # Getting MDT's from DB
            mdts_view = MetaDataTemplate.view('mdtcouch/docrule', key=docrule_id, include_docs=True)
            # Constructing MDT's response dict
            id = 1
            for row in mdts_view:
                mdts_list[str(id)] = row._doc
                # cleaning up _id and _rev from response to unify response
                mdts_list[str(id)]["mdt_id"] = mdts_list[str(id)]['_id']
                del mdts_list[str(id)]['_id']
                del mdts_list[str(id)]['_rev']
                id+=1
            return mdts_list
        else:
            log.error('Got no mdts for docrule: %s' % docrule_id)
            return False

    def get_mdts_by_name(self, names_list):
        """ """
        log.debug('Getting MDT-s named: %s' % names_list)
        mdts_list = {}
        # Getting MDT's from DB
        if names_list:
            mdts_view = MetaDataTemplate.view('mdtcouch/all', keys=names_list, include_docs=True)
        else:
            mdts_view = None
        # Constructing MDT's response dict
        if mdts_view:
            id = 1
            for row in mdts_view:
                mdts_list[str(id)] = row._doc
                # cleaning up _id and _rev from response to unify response
                mdts_list[str(id)]["mdt_id"] = mdts_list[str(id)]['_id']
                del mdts_list[str(id)]['_id']
                del mdts_list[str(id)]['_rev']
                id+=1
            return mdts_list
        else:
            log.error('Got no MDT-s from CouchDB named: %s' % names_list)
            return False

    def get_all_mdts(self):
        """ """
        log.debug('Getting all MDT-s.')
        mdts_list = {}
        # Getting MDT's from DB
        mdts_view = MetaDataTemplate.view('mdtcouch/docrules_list', classes={None: MetaDataTemplate})
        if mdts_view:
            # Constructing MDT's response dict
            id = 1
            for row in mdts_view:
                mdts_list[str(id)] = row._doc
                # cleaning up _id and _rev from response to unify response
                mdts_list[str(id)]["mdt_id"] = mdts_list[str(id)]['_id']
                del mdts_list[str(id)]['_id']
                del mdts_list[str(id)]['_rev']
                id += 1
            return mdts_list
        else:
            log.error('Got no MDT-s from CouchDB.')
            return False

    def store(self, mdt_data):
        """
        Method to store MDT into DB. Uses JSON provided.
        Example MDT:
        {
            "_id": "mymdt",
            "docrule_id": ["1", "2"],
            "description": "description of this metadata template",
            "fields": {
               "1": {
                   "type": "integer",
                   "field_name": "Employee ID",
                   "description": "Unique (Staff) ID of the person associated with the document"
               },
               "2": {
                   "type": "string",
                   "length": 60,
                   "field_name": "Employee Name",
                   "description": "Name of the person associated with the document"
               },
            },
            "parallel": {
               "1": [ "1", "2"],
            }
        }

        """
        mdt = MetaDataTemplate()
        if self.validate_mdt(mdt_data):
            mdt.populate_from_DMS(mdt_data)
            try:
                mdt.save()
                log.debug('MetaDataTemplateManager.store added mdt with _id: %s' % mdt._id)
                return {"status": "ok", "mdt_id": "%s" % mdt._id}
            except ResourceConflict, e:
                log.error('MetaDataTemplateManager.store ResourceConflict error: %s' % e)
                pass
        else:
            log.error('MetaDataTemplateManager.store MDT provided did not validate')
        return False

    def delete_mdt(self, mdt_id):
        log.info('delete_mdt %s' % mdt_id)
        try:
            mdt = MetaDataTemplate.get(docid=mdt_id)
            mdt.delete()
        except Exception, e:
            log.error("%s template with _id: %s" % (e, mdt_id))
            return False
        return True

    def get_restricted_keys_names(self, mdts):
        """ Checking MDTs provided for locked indexes
        @param mdts is a list of MDT's for analysis
        @return 2 lists of field names locked for adding indexes and admin ability to add new indexes.
        """
        admin_locked_keys = []
        locked_keys = []
        # Checking mdts configuration for keys (fields) that have restriction in adding new indexes
        if mdts:
            for mdt in mdts:
                for field_id, field in mdts[mdt]["fields"].iteritems():
                    if "create_new_indexes" in field.iterkeys():
                        if field["create_new_indexes"]=="open":
                            # normal fileld
                            pass
                        elif field["create_new_indexes"]=="admincreate":
                            # Only admin list adding
                            admin_locked_keys.append(field["field_name"])
                        elif field["create_new_indexes"]=="locked":
                            # None has ability to add new indexes
                            locked_keys.append(field["field_name"])
        log.debug("Document has keys available for edit for admin only: %s and locked for adding: %s" %
                  (admin_locked_keys, locked_keys))
        return admin_locked_keys, locked_keys

    def validate_mdt(self, mdt):
        # TODO: uploading MDT validation sequence here
        return True

    def mdt_read_call_valid(self):
        """
        Simple type validation of docrule_id provided.
        """
        if not self.docrule_id:
            return False
        try:
            int(self.docrule_id)
            str(self.docrule_id)
            return True
        except Exception, e:  # FIXME
            log.error(e)
            return False
