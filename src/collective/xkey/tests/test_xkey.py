# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from collective.xkey.interfaces import IInvolvedIDs
from collective.xkey.testing import COLLECTIVE_XKEY_FUNCTIONAL_TESTING  # noqa: E501
from collective.xkey.utils import mark_involved
from collective.xkey.utils import mark_involved_objects
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.testing.z2 import Browser
from plone.uuid.interfaces import IUUID
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import adapter
from zope.component import getGlobalSiteManager
from zope.component import provideAdapter
from zope.globalrequest import setRequest
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserView
from zope.publisher.interfaces.browser import IHTTPRequest

import transaction
import unittest


class MarkerInterface(Interface):
    """Some marker interface"""


class TestHeaders(unittest.TestCase):
    """Test that collective.xkey provides the right headers."""

    layer = COLLECTIVE_XKEY_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        setRequest(self.portal.REQUEST)
        setRoles(self.portal, TEST_USER_ID, ("Manager",))

    def test_xkey_header_published(self):
        """Test if the headers are published."""
        setRoles(self.portal, TEST_USER_ID, ("Manager",))
        document = api.content.create(title="Document", id="document", type="Document", container=self.portal)
        api.content.transition(document, to_state="published")
        transaction.commit()
        browser = Browser(self.app)
        browser.open(document.absolute_url())
        self.assertTrue("xkey" in browser.headers)
        uuid = IUUID(document)
        self.assertIn(uuid, browser.headers["xkey"])

    def test_involved_adapter(self):
        """Test if the headers are published."""
        setRoles(self.portal, TEST_USER_ID, ("Manager",))
        document = api.content.create(title="Document", id="document", type="Document", container=self.portal)
        api.content.transition(document, to_state="published")
        alsoProvides(document, MarkerInterface)
        transaction.commit()

        # prepare a dummy adapter
        @adapter(MarkerInterface)
        @implementer(IInvolvedIDs)
        def document_adapter(obj):
            uuid = IUUID(obj)
            return [uuid, "custom-tag-from-adapter"]

        provideAdapter(document_adapter)

        browser = Browser(self.app)
        browser.open(document.absolute_url())
        self.assertTrue("xkey" in browser.headers)
        xkey_header = browser.headers["xkey"]
        self.assertIn(IUUID(document), xkey_header)
        self.assertIn("custom-tag-from-adapter", xkey_header)

        # cleanup
        gsm = getGlobalSiteManager()
        gsm.unregisterAdapter(
            factory=document_adapter,
            provided=IInvolvedIDs,
        )

    def test_util_methods(self):
        """Test the util methods."""
        document = api.content.create(title="Document", id="document", type="Document", container=self.portal)
        api.content.transition(document, to_state="published")
        # create a bunch of auxiliary objects
        auxiliary_document = api.content.create(
            title="Auxiliary document", id="auxiliary-document", type="Document", container=self.portal
        )
        api.content.transition(auxiliary_document, to_state="published")
        auxiliary_document2 = api.content.create(
            title="Auxiliary document", id="auxiliary-document2", type="Document", container=self.portal
        )
        api.content.transition(auxiliary_document2, to_state="published")

        transaction.commit()

        # prepare a specialized view
        @adapter(Interface, IHTTPRequest)
        class CustomDocumentView(BrowserView):
            index = ViewPageTemplateFile("document_with_dependencies.pt")

            def __call__(self):
                self.auxiliary_document = self.context.aq_parent["auxiliary-document"]
                self.auxiliary_document2 = self.context.aq_parent["auxiliary-document2"]

                mark_involved_objects(
                    self.request,
                    [
                        self.auxiliary_document,
                    ],
                )
                mark_involved(self.request, "custom-tag-from-view")

                return self.index()

        provideAdapter(
            CustomDocumentView,
            adapts=(Interface, IHTTPRequest),
            provides=IBrowserView,
            name="special-view",
        )

        browser = Browser(self.app)
        browser.open(document.absolute_url() + "/@@special-view")

        self.assertTrue("xkey" in browser.headers)
        xkey_header = browser.headers["xkey"]
        self.assertIn(IUUID(document), xkey_header)
        self.assertIn(IUUID(auxiliary_document), xkey_header)
        self.assertIn(IUUID(auxiliary_document2), xkey_header)
        self.assertIn("custom-tag-from-view", xkey_header)
        self.assertIn("custom-tag-from-template", xkey_header)

        # cleanup
        gsm = getGlobalSiteManager()
        gsm.unregisterAdapter(
            factory=CustomDocumentView,
            provided=IBrowserView,
        )
