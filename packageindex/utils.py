# -*- coding: utf-8 -*-
## Copyright (C) 2008 Ingeniweb

## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; see the file COPYING. If not, write to the
## Free Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
import urllib2
import urlparse
from setuptools.package_index import PackageIndex as BasePackageIndex
from setuptools.package_index import (
    egg_info_for_url,
    safe_name,
    safe_version,
    to_filename,
    HREF,
    htmldecode,
    find_external_links,
    PYPI_MD5,
    )

from pkg_resources import Requirement

class PackageIndexScraper(BasePackageIndex):
    """
    """

    def can_add(self, dist):
        """Overrides PackageIndex.can_add method to remove filter on python
    major version: we want packages for all versions, all platforms
        """
        return True

    def process_index(self, url, page):
        """Process the contents of a PyPI page
        Override: don't lowercase package name
        """
        def scan(link):
            # Process a URL to see if it's for a package page
            if link.startswith(self.index_url):
                parts = map(
                    urllib2.unquote, link[len(self.index_url):].split('/')
                )
                if len(parts)==2 and '#' not in parts[1]:
                    # it's a package page, sanitize and index it
                    pkg = safe_name(parts[0])
                    ver = safe_version(parts[1])
                    # changed "pkg.lower()" to "pkg"
                    self.package_pages.setdefault(pkg, {})[link] = True
                    return to_filename(pkg), to_filename(ver)
            return None, None

        # process an index page into the package-page index
        for match in HREF.finditer(page):
            scan( urlparse.urljoin(url, htmldecode(match.group(1))) )

        pkg, ver = scan(url)   # ensure this page is in the page index
        if pkg:
            # process individual package page
            for new_url in find_external_links(url, page):
                # Process the found URL
                base, frag = egg_info_for_url(new_url)
                if base.endswith('.py') and not frag:
                    if ver:
                        new_url+='#egg=%s-%s' % (pkg,ver)
                    else:
                        self.need_version_info(url)
                self.scan_url(new_url)

            return PYPI_MD5.sub(
                lambda m: '<a href="%s#md5=%s">%s</a>' % m.group(1,3,2), page
            )
        else:
            return ""   # no sense double-scanning non-package pages
    
    def get_package_downloads(self, package_name):
        requirement = Requirement.parse(package_name)
        self.find_packages(requirement)
        downloads = list()
        dists = self[package_name]
        if not dists:
            # We already have a cached index page and there are no dists.
            # Pypi is probably down, so we keep our existing one.
            return downloads
        
        for dist in dists:
            if getattr(dist, "module_path", None) is not None:
                # this is a module installed in system
                continue
            filename, md5 = egg_info_for_url(dist.location)
            downloads.append({'filename': filename, 
                              'md5': md5.split('=',1)[-1],
                              'location': dist.location.split('#')[0],})
        return downloads

