# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.xkey.interfaces import IInvolvedIDs
from plone.resource.interfaces import IResourceDirectory
from plone.uuid.interfaces import IUUID
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface

import hashlib
import pkg_resources


try:
    pkg_resources.get_distribution("Products.ResourceRegistries")
    from Products.ResourceRegistries.interfaces import IResourceRegistry
except pkg_resources.DistributionNotFound:
    HAS_RESOURCEREGISTRY = False
else:
    HAS_RESOURCEREGISTRY = True


@adapter(Interface)
@implementer(IInvolvedIDs)
def content_adapter(obj):
    """return uid for context.

    * the object is a string
    * the object has a UID attribute that is a string (e.g. a catalog
      brain, AT object, ...
    * the object implements IUUID
    """
    uuid = None
    if isinstance(obj, str):
        return [obj]
    obj = aq_base(obj)
    if hasattr(obj, "UID"):
        uuid = getattr(obj, "UID")
        if callable(uuid):
            uuid = uuid()
        if not isinstance(uuid, str):
            uuid = None
    if not uuid:
        uuid = IUUID(obj, None)
    if uuid:
        return [uuid]
    else:
        return []


@adapter(IResourceDirectory)
@implementer(IInvolvedIDs)
def resource_directory_adapter(context):
    if hasattr(context, "directory"):
        # file system resources
        return [hashlib.sha1(context.directory.encode("utf-8")).hexdigest()]
    else:
        # ZODB persistent resources
        return []


if HAS_RESOURCEREGISTRY:

    @adapter(IResourceRegistry)
    @implementer(IInvolvedIDs)
    def resource_registry_adapter(context):
        """portal_javascript, portal_css, ..."""
        return []
