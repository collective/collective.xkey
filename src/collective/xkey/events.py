# -*- coding: utf-8 -*-
import logging

from ZODB.POSException import ConflictError
from ZPublisher.interfaces import IPubAfterTraversal
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from plone.transformchain.interfaces import ITransform

from collective.xkey.utils import mark_involved_objects
from collective.xkey.utils import get_involved_ids


logger = logging.getLogger("collective.xkey")


@implementer(ITransform)
@adapter(Interface, Interface)
class MutatorTransform(object):
    """Transformation using plone.transformchain.
    This is registered at order 11000, i.e. "late". A typical transform

    chain order may include:
    * lxml transforms (e.g. plone.app.blocks, collectivexdv) => 8000-8999
    * gzip => 10000
    * mark ids involved => 11000
    * caching => 12000

    This transformer is uncommon in that it doesn't actually change the
    response body. Instead, we look up caching operations which can modify
    response headers and perform other caching functions.
    """

    order = 11000

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def transformUnicode(self, result, encoding):
        self.mutate()
        return None

    def transformBytes(self, result, encoding):
        self.mutate()
        return None

    def transformIterable(self, result, encoding):
        self.mutate()
        return None

    def mutate(self):
        request = self.request
        involved = get_involved_ids(request)
        if involved:
            request.response.setHeader("Xkey", " ".join(involved))


@adapter(IPubAfterTraversal)
def handle_request_after_traversal(event):
    """handle "IPubAfterTraversal"."""
    try:
        # XXX: stoponfirst=True to get the IUUDs of the first parent
        mark_involved_objects(event.request, event.request.get("PARENTS", []), stoponfirst=True)
        published = event.request.get("PUBLISHED", None)
        if published:
            context = getattr(published, "context", None)
            if context:
                mark_involved_objects(
                    event.request,
                    [
                        context,
                    ],
                )
    except ConflictError:
        raise
    except:
        logger.exception("Swallowed exception in IPubAfterTraversal event handler")
