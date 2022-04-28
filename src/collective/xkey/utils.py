# -*- coding: utf-8 -*-
import logging

from collective.xkey.interfaces import IInvolvedIDs
from zope.annotation.interfaces import IAnnotations
from Products.Five.browser import BrowserView
from zope.publisher.interfaces import IPublishTraverse
from zope.interface import implementer
from zope.traversing.interfaces import ITraversable

KEY = "collective.xkey.involved"
logger = logging.getLogger("collective.xkey")


def mark_involved_objects(request, objs, stoponfirst=False):
    """Retrieve the involved ids by the given objects. Objects might be
    ordinary strings, Plone content objects having UID attributes, IUUID.

    :param request: request
    :param objs: list
    :type objs: object
    :param stoponfirst: True only the first object that respond to below rules will be marked as involved.
    :type stoponfirst: bool, optional
    """
    for obj in objs:
        ids = IInvolvedIDs(obj, None)
        if ids:
            for single_id in ids:
                mark_involved(request, single_id)
            if stoponfirst:
                break


def mark_involved(request, single_id):
    """Mark an id as being involved for this request.

    :param request: _description_
    :type request: _type_
    :param single_id: _description_
    :type single_id: _type_
    """
    logger.debug("mark request %r with %s" % (request, single_id))
    annotations = IAnnotations(request)
    if annotations.get(KEY, None):
        annotations[KEY].add(single_id)
    else:
        annotations[KEY] = set([single_id])


def get_involved_ids(request):
    """Get all registered involved ids from the request

    :param request: request
    :return: set of involved ids
    :rtype: set
    """
    annotations = IAnnotations(request)
    return annotations.get(KEY, set())


@implementer(ITraversable)
@implementer(IPublishTraverse)
class MarkInvolvedView(BrowserView):
    """Useful utility view to mark IDs in page templates.

    In offers two ways for using it:

    1. marking objects (with UUID)

        <tal:mark-involved tal:define="involved image/@@mark_involved" />

    2. marking arbitrary IDs

        <tal:mark-involved tal:define="involved context/@@mark_involved/0b05ba53734965c6e48bdcd2c7c7e41f" />
    """

    def __init__(self, context, request):
        super(MarkInvolvedView, self).__init__(context, request)
        self.uuid = ""

    def __call__(self):
        """Mark an ID as beinged involved for delivering the current request"""
        if self.uuid:
            mark_involved(self.request, self.uuid)
        else:
            mark_involved_objects(
                self.request,
                [
                    self.context,
                ],
            )

    def publishTraverse(self, request, uuid):
        """Set uuid by traversing the path segment"""
        self.uuid = uuid
        return self

    def traverse(self, name, furtherPath):
        """Set uuid by traversing the path segment"""
        self.uuid = name
        return self
