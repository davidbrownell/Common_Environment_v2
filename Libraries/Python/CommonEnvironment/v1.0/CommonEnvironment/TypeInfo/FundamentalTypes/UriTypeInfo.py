# ----------------------------------------------------------------------
# |  
# |  UriTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2017-06-23 07:33:14
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2017.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
import os
import sys
import textwrap

import six

from .. import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Uri(object):
    
    CREDENTIAL_DECORATORS                   = { "_BSLASH_" : '\\',
                                                "_SLASH_" : '/',
                                                "_COLON_" : ':',
                                                "_AT_" : '@',
                                              }

    # ----------------------------------------------------------------------
    @classmethod
    def FromString(cls, value):
        result = six.moves.urllib.parse.urlparse(value)

        if not (result.scheme and result.hostname):
            raise Exception("'{}' is not a valid uri".format(value))

        return cls( result.scheme,
                    result.hostname,
                    result.path,
                    query=result.query,
                    credentials=None if not (result.username and result.password) else (result.username, result.password),
                    port=result.port,
                  )

    # ----------------------------------------------------------------------
    def __init__( self,
                  scheme,
                  host,
                  path,
                  query=None,
                  credentials=None,                     # (username, password)
                  port=None,
                ):
        if not scheme:                      raise Exception("'scheme' must be valid")
        if not host:                        raise Exception("'host' must be valid")
        
        self.Scheme                         = scheme
        self.Host                           = host
        self.Path                           = path or None
        self.Query                          = six.moves.urllib.parse.parse_qs(query) if isinstance(query, six.string_types) else (query or {})
        self.Port                           = port or None

        # Python parsing functionality has problems when credentials contains backslashes, as it
        # interprets that as the beginning of the path. As a hack, replace any special tokens with
        # the proper chars when storing the actual username and password.
        self._original_credentials          = credentials

        if credentials:
            # ----------------------------------------------------------------------
            def Undecorate(s):
                s = six.moves.urllib.parse.unquote(s)

                for search, replace in six.iteritems(self.CREDENTIAL_DECORATORS):
                    s = s.replace(search, replace)

                return s

            # ----------------------------------------------------------------------

            username, password = credentials

            self.Credentials                = ( Undecorate(username), Undecorate(password) )
            
    # ----------------------------------------------------------------------
    def ToString(self):
        host = []

        if self._original_credentials:
            username, password = self._original_credentials
            assert username

            host.append(six.moves.urllib.parse.quote(username))

            if password:
                host.append(":{}".format(six.moves.urllib.parse.quote(password)))

            host.append("@")

        host.append(self.Host)

        if self.Port:
            host.append(":{}".format(self.Port))

        query = ''
        if self.Query:
            # <Too many positional arguments for function call> pylint: disable = E1121
            query = six.moves.urllib.parse.urlencode(self.Query, True)

        # <Too many positional arguments for function call> pylint: disable = E1121
        return six.moves.urllib.parse.urlunparse(( self.Scheme,
                                                   ''.join(host),
                                                   self.Path or '',
                                                   '',
                                                   query,
                                                   '',
                                                 ))

# ----------------------------------------------------------------------
class UriTypeInfo(TypeInfo):

    Uri                                     = Uri
    ExpectedType                            = Uri
    Desc                                    = "Uri"
    ConstraintsDesc                         = ''

    # ----------------------------------------------------------------------
    @property
    def PythonDefinitionString(self):
        return "UriTypeInfo({})".format(self._PythonDefinitionStringContents)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item):
        return
