# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""
from zope.interface import Interface


class IInvolvedIDs(Interface):
    """Adapter to find uid involved for the context.

    the adapter returns a list of ids (basestring)
    """
