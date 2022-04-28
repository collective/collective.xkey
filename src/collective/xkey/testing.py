# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import collective.xkey


class CollectiveXkeyLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=collective.xkey)

    def setUpPloneSite(self, portal):
        portal["portal_workflow"].setDefaultChain("simple_publication_workflow")


COLLECTIVE_XKEY_FIXTURE = CollectiveXkeyLayer()


COLLECTIVE_XKEY_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_XKEY_FIXTURE,),
    name="CollectiveXkeyLayer:IntegrationTesting",
)


COLLECTIVE_XKEY_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_XKEY_FIXTURE,),
    name="CollectiveXkeyLayer:FunctionalTesting",
)


COLLECTIVE_XKEY_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        COLLECTIVE_XKEY_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name="CollectiveXkeyLayer:AcceptanceTesting",
)
