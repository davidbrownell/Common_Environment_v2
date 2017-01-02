# ---------------------------------------------------------------------------
# |  
# |  CreateSmtpMailer.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  11/29/2015 01:16:48 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys
import textwrap

from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Shell
from CommonEnvironment.SmtpMailer import SmtpMailer

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
@CommandLine.EntryPoint()
@CommandLine.FunctionConstraints( configuration_name=CommandLine.StringTypeInfo(),
                                  host=CommandLine.StringTypeInfo(),
                                  username=CommandLine.StringTypeInfo(arity='?'),
                                  password=CommandLine.StringTypeInfo(arity='?'),
                                  port=CommandLine.IntTypeInfo(min=1),
                                  from_name=CommandLine.StringTypeInfo(arity='?'),
                                  from_email=CommandLine.StringTypeInfo(arity='?'),
                                  output_stream=None,
                                )
def Create( configuration_name,
            host,
            username=None,
            password=None,
            port=25,
            from_name=None,
            from_email=None,
            ssl=False,
            output_stream=sys.stdout,
          ):
    if not from_name and not from_email:
        raise CommandLine.UsageException("'from_name' or 'from_email' must be provided")
        
    SmtpMailer( host,
                username=username,
                password=password,
                port=port,
                from_name=from_name,
                from_email=from_email,
                ssl=ssl,
              ).Save(configuration_name)
              
    output_stream.write("'{}' has been created.\n".format(configuration_name))
          
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint()
@CommandLine.FunctionConstraints( output_stream=None,
                                )
def List( output_stream=sys.stdout,
        ):
    output_stream.write(textwrap.dedent(
        """\
        
        Available configurations:
        {}
        """).format( '\n'.join([ "    - {}".format(name) for name in SmtpMailer.GetConfigurations() ]),
                   ))
    
# ---------------------------------------------------------------------------
@CommandLine.EntryPoint()
@CommandLine.FunctionConstraints( configuration_name=CommandLine.StringTypeInfo(),
                                  to=CommandLine.StringTypeInfo(arity='+'),
                                  output_stream=None,
                                )
def Verify( configuration_name,
            to,
            output_stream=sys.stdout,
          ):
    mailer = SmtpMailer.Load(configuration_name)
    
    mailer.SendMessage( to,
                        "SmtpMailer Verification",
                        "This is a test message to ensure that the configuration '{}' is working as expected.".format(configuration_name),
                      )
                      

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
