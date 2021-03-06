#!/usr/bin/python
'''
Faraday Penetration Test IDE - Community Version
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

'''

import unittest
import os
import sys
sys.path.append('.')
from managers.model_managers import WorkspaceManager
from managers.mapper_manager import MapperManager
from controllers.change import ChangeController
from persistence.persistence_managers import DBTYPE, DbManager
from model.controller import ModelController

from plugins.core import PluginController
import random

from config.configuration import getInstanceConfiguration
CONF = getInstanceConfiguration()

from mockito import mock


class TestWorkspacesManagement(unittest.TestCase):

    def setUp(self):
        self.couch_uri = CONF.getCouchURI()
        # self.cdm = CouchdbManager(uri=self.couch_uri)
        wpath = os.path.expanduser("~/.faraday/persistence/" )
        # self.fsm = FSManager(wpath)
        
        self.dbManager = DbManager()
        self.mappersManager = MapperManager()
        self.changesController = ChangeController(self.mappersManager)

        self.wm = WorkspaceManager(self.dbManager, self.mappersManager,
                                    self.changesController)
        self._fs_workspaces = []
        self._couchdb_workspaces = []

    def tearDown(self):
        self.cleanCouchDatabases()
        self.cleanFSWorkspaces()
        # pass

    def new_random_workspace_name(self):
        return ("aworkspace" + "".join(random.sample(
            [chr(i) for i in range(65, 90)], 10))).lower()

    def cleanFSWorkspaces(self):
        import shutil
        basepath = os.path.expanduser("~/.faraday/persistence/")

        for d in self._fs_workspaces:
            wpath = os.path.join(basepath, d)
            if os.path.isdir(wpath):
                shutil.rmtree(wpath)

    def cleanCouchDatabases(self):
        try:
            for wname in self._couchdb_workspaces:
                self.cdm.removeWorkspace(wname)
        except Exception as e:
            print e

    def test_create_fs_workspace(self):
        """
        Verifies the creation of a filesystem workspace
        """
        wname = self.new_random_workspace_name()
        self._fs_workspaces.append(wname)
        self.wm.createWorkspace(wname, 'desc', DBTYPE.FS)

        wpath = os.path.expanduser("~/.faraday/persistence/%s" % wname)
        self.assertTrue(os.path.exists(wpath))

    def test_create_couch_workspace(self):
        """
        Verifies the creation of a couch workspace
        """
        wname = self.new_random_workspace_name()
        self._couchdb_workspaces.append(wname)
        self.wm.createWorkspace(wname, 'a desc', DBTYPE.COUCHDB)

        res_connector = self.dbManager.getConnector(wname)
        self.assertTrue(res_connector)
        self.assertEquals(res_connector.getType(), DBTYPE.COUCHDB)
        self.assertTrue(self.mappersManager.find(wname), "Workspace document not found")

        wpath = os.path.expanduser("~/.faraday/persistence/%s" % wname)
        self.assertFalse(os.path.exists(wpath))

        # self.assertEquals(WorkspaceOnCouch.__name__, self.wm.getWorkspaceType(wname))

    def test_delete_couch_workspace(self):
        """
        Verifies the deletion of a couch workspace
        """
        wname = self.new_random_workspace_name()
        self.wm.createWorkspace(wname, 'a desc', DBTYPE.COUCHDB)

        self.assertTrue(self.mappersManager.find(wname), "Workspace document not found")

        #Delete workspace
        self.wm.removeWorkspace(wname)
        self.assertIsNone(self.mappersManager.find(wname))
        self.assertFalse(self.dbManager.connectorExists(wname))

    def test_delete_fs_workspace(self):
        """
        Verifies the deletion of a filesystem workspace
        """
        wname = self.new_random_workspace_name()
        self.wm.createWorkspace(wname, 'desc', DBTYPE.FS)

        wpath = os.path.expanduser("~/.faraday/persistence/%s" % wname)
        self.assertTrue(os.path.exists(wpath))

        #Delete workspace
        self.wm.removeWorkspace(wname)
        self.assertFalse(os.path.exists(wpath))

    def test_list_workspaces(self):
        """ Lists FS workspaces and Couch workspaces """
        # First create workspaces manually 
        wnamefs = self.new_random_workspace_name()
        wnamecouch = self.new_random_workspace_name() 
        # FS
        self.wm.createWorkspace(wnamefs, 'a desc', DBTYPE.FS)
        # Couch
        self.wm.createWorkspace(wnamecouch, 'a desc', DBTYPE.COUCHDB)

        self.assertIn(wnamefs, self.wm.getWorkspacesNames(), 'FS Workspace not loaded')
        self.assertIn(wnamecouch, self.wm.getWorkspacesNames(), 'Couch Workspace not loaded')

        self.assertEquals(self.wm.getWorkspaceType(wnamecouch), 'CouchDB', 'Workspace type bad defined' )
        self.assertEquals(self.wm.getWorkspaceType(wnamefs), 'FS', 'Workspace type bad defined') 


    def test_get_workspace(self):
        """ Create a workspace, now ask for it """
        
        # When
        wname = self.new_random_workspace_name()
        workspace = self.wm.createWorkspace(wname, 'a desc', DBTYPE.FS)

        added_workspace = self.wm.openWorkspace(wname)

        # Then
        self.assertIsNotNone(workspace, 'Workspace added should not be none')
        self.assertEquals(workspace, added_workspace, 'Workspace created and added diffier')

    def _test_get_existent_couch_workspace(self): # Deprecate
        """ Create a workspace in the backend, now ask for it """
        
        # When
        wname = self.new_random_workspace_name()
        workspace = self.cdm.addWorkspace(wname)

        added_workspace = self.wm.getWorkspace(wname)

        # Then
        self.assertIsNotNone(added_workspace, 'Workspace added should not be none')

    def _test_get_existent_fs_workspace(self): # Deprecate
        """ Create a workspace in the backend, now ask for it """
        
        # When
        wname = self.new_random_workspace_name()
        workspace = self.fsm.addWorkspace(wname)
        self.wm.loadWorkspaces()

        added_workspace = self.wm.getWorkspace(wname)

        # Then
        self.assertIsNotNone(added_workspace, 'Workspace added should not be none')

    def test_get_non_existent_workspace(self):
        """ Retrieve a non existent workspace """
        
        added_workspace = self.wm.openWorkspace('inventado')

        # Then
        self.assertIsNone(added_workspace, 'Workspace added should not be none') 

    def test_set_active_workspace(self):
        ''' create a workspace through the backend, then set it as active '''

        wname = self.new_random_workspace_name()
        workspace = self.wm.createWorkspace(wname, 'desc', DBTYPE.FS)

        # when
        self.wm.setActiveWorkspace(workspace)

        self.assertEquals(workspace, self.wm.getActiveWorkspace(),
                    'Active workspace diffiers with expected workspace')

        self.assertTrue(self.wm.isActive(workspace.name),
                'Workspace is active flag not set')

    def test_remove_fs_workspace(self):
        # First
        wname = self.new_random_workspace_name()
        added_workspace = self.wm.createWorkspace(wname, 'desc', DBTYPE.FS)

        # When
        self.wm.removeWorkspace(wname) 

        # Then
        self.assertNotIn(wname, self.wm.getWorkspacesNames())
        wpath = os.path.expanduser("~/.faraday/persistence/%s" % wname)
        self.assertFalse(os.path.exists(wpath))

    def test_remove_couch_workspace(self):
        # First
        wname = self.new_random_workspace_name()
        added_workspace = self.wm.createWorkspace(wname, 'desc', DBTYPE.COUCHDB)

        # When
        self.wm.removeWorkspace(wname) 

        # Then
        self.assertNotIn(wname, self.wm.getWorkspacesNames())

    def test_remove_non_existent_workspace(self):
        # When
        self.wm.removeWorkspace('invented') 



if __name__ == '__main__':
    unittest.main()
