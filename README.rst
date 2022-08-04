.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

.. image:: https://travis-ci.org/collective/collective.xkey.svg?branch=master
    :target: https://travis-ci.org/collective/collective.xkey

.. image:: https://coveralls.io/repos/github/collective/collective.xkey/badge.svg?branch=master
    :target: https://coveralls.io/github/collective/collective.xkey?branch=master
    :alt: Coveralls

.. image:: https://img.shields.io/pypi/v/collective.xkey.svg
    :target: https://pypi.python.org/pypi/collective.xkey/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/status/collective.xkey.svg
    :target: https://pypi.python.org/pypi/collective.xkey
    :alt: Egg Status

.. image:: https://img.shields.io/pypi/pyversions/collective.xkey.svg?style=plastic   :alt: Supported - Python Versions

.. image:: https://img.shields.io/pypi/l/collective.xkey.svg
    :target: https://pypi.python.org/pypi/collective.xkey/
    :alt: License


===============
collective.xkey
===============

.. note:: This add-on is now deprecated. All improvements here have been merged into collective.purgebyid. You may use that add-on instead.

Use Varnish's `xkey module <https://github.com/varnish/varnish-modules>`_ for tag-based cache invalidation in Plone.

This add-on is heavily inspired by and built upon `collective.purgebyid <https://github.com/collective/collective.purgebyid>`_ (major credit goes to its contributors), but it is more adapted to xkey's specific requirements.
It uses tags in the same manner, but instead of banning objects with tags, it purges them with the efficient xkey implementation.
Doing so lowers the memory consumption and improves the performance of Varnish.

The default implementation covers basic use-cases, but it can be extended for your needs.

What is Varnish' xkey module?
-----------------------------

Traditionally, Varnish uses the URL as the hash key for purging, but with the xkey module there comes a secondary hash for doing so.
Cached objects being tagged can be specifically purged for a more targeted cache control.

To have xkey working, it is mandatory so provide a special HTTP header called "Xkey" which contains all the tags (separated by white-space).
This is already provided by this add-on.

Lastly, a small addition in the Varnish configuration file is needed (see "Installation").

What does collective.xkey do?
-----------------------------

Imagine that you have two documents containing several images.

One document exposes this header:

.. code-block:: bash

    $ curl -s -I -X GET http://localhost:8080/Plone/my-pets

    HTTP/1.1 200 OK
    ...
    Xkey: 10a91397b7e74b8fb449a212147da89d ebbec6674baa4b2e9acdc1d8706c973e 943f8ea1a2f7400ebef9cd4b9cdc7692

Inspecting the header reveals all the UUIDs of objects involved for rendering the HTML:

* 10a91397b7e74b8fb449a212147da89d (the document itself)
* ebbec6674baa4b2e9acdc1d8706c973e (image of a cute kitty)
* 943f8ea1a2f7400ebef9cd4b9cdc7692 (image of an equally cute puppy)

A second document exposes:

.. code-block:: bash

    $ curl -s -I -X GET http://localhost:8080/Plone/my-pets/my-cat-pixie

    HTTP/1.1 200 OK
    ...
    Xkey: 5540249e9aa84020856454b001737775 ebbec6674baa4b2e9acdc1d8706c973e

Now, after updating the image (with UUID ebbe5c...), all URLs that use this image are purged in Varnish.
This does include of course all variants of the URLs of these two documents (potentially with query parameters like ``utm_campaign`` and such) and every scale of the updated image as well.

How does it work? How to extend it?
-----------------------------------

During the publishing process all involved IDs (UUIDs and custom IDs) are collected (by subscribing to IPubAfterTraversal).

Important are the adapters for IInvolvedIDs, which are responsible for collecting IDs for their given context.
The base implementation looks for the UUIDs, but may be specialized for your custom content types.

Apart from the adapter approach, there is the inline approach. You may call the following methods from collective.xkey.utils:

* mark_involved_objects(request, objs, stoponfirst=False)
* mark_involved(request, single_id)

Whereas the first method uses internally the adapters for IInvolvedIDs for the given objects, the second one allows setting any arbitrary IDs.
These methods combined might be used in your views, whenever a certain object or part is being rendered.

Additionally, there is a utility browser view "mark_involved", that can be used in your template as follows:

.. code-block:: xml

    <tal:image tal:define="image python:context.get_image()" tal:condition="python: image">

        <tal:mark-involved tal:define="involved image/@@mark_involved" />
        <!-- put image rendering here -->

    </tal:image>

Alternatively, you can again set arbitrary IDs:

.. code-block:: xml

    <tal:mark-involved tal:define="involved context/@@mark_involved/my_custom_id" />

After having collected all IDs a ITransform adapter puts the expected Xkey header in the HTTP response header.

When Plone sends a purge request to the configured Cache Proxy, it sends additionally a specialized request for handling objects with tags.

Installation
------------

The installation is two-fold. On the **Plone** side, you need to install collective.xkey by adding it to your buildout::

    [buildout]

    ...

    eggs =
        collective.xkey


and then running ``bin/buildout``. Upon running up your instance, you may see the new header. No need to install this add-on for your Plone site.

On the **Varnish** side, you need to update the configuration file (e.g. ``/etc/varnish/default.vcl``)::

    # This a configuration file for varnish.
    # See the vcl(7) man page for details on VCL syntax and semantics.
    #
    vcl 4.0;

    ...
    import xkey;

    sub vcl_recv {
        ...
        if (req.method == "PURGE") {
            # Not from an allowed IP? Then die with an error.
            if (!client.ip ~ purge) {
                return (synth(405, "This IP is not allowed to send PURGE requests."));
            }
            if (req.url ~ ".*\/@@purgebyxkey\/") {
                set req.http.xkey = regsub(req.url, ".*\/@@purgebyxkey\/", "");
                set req.http.n-gone = xkey.purge(req.http.xkey);
                return (synth(200, "Invalidated "+req.http.n-gone+" objects"));
            }
            return(purge);
        }
        ...
    }

    sub vcl_deliver {
        ...
        # hide xkey headers in payload, comment out for debugging
        unset resp.http.xkey;
        ...
    }

.. note::

    Please note the limitations for the HTTP response header sizes in the various places of your infrastructure. For Apache, nginx and Varnish it varies from 4K to 8K and might be configured individually.


Contribute
----------

- Issue Tracker: https://github.com/collective/collective.xkey/issues
- Source Code: https://github.com/collective/collective.xkey


Support
-------

If you are having issues, please let us know.


License
-------

The project is licensed under the GPLv2.
