# ---------------------------------------------------------------------------
# |  
# |  LinuxEnvironmentImpl.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/08/2015 02:16:41 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import os
import sys
import textwrap

from ...Shell import Environment, Raw

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class LinuxEnvironmentImpl(Environment):
    ScriptExtension                         = ".sh"
    ExecutableExtension                     = ""
    AllArgumentsScriptVariable              = '"$@"'
    EnvironmentVariableDelimiter            = ':'
    HasCaseSensitiveFileSystem              = True
    TempDirectories                         = [ "/tmp", ]
    
    IsLinux                                 = True
    
    # ---------------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ---------------------------------------------------------------------------
    def __init__(self):
        self._user_directory = os.path.expanduser("~")
        
    # ---------------------------------------------------------------------------
    @property
    def UserDirectory(self):
        return self._user_directory
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def CreateInstallBinaryCommand(install_filename, binary_filename):
        install_location = open(install_filename).read().strip()

        return Raw(textwrap.dedent(
            """\
            echo "Extracting '{binary}' to '{install}'..."

            if [ -d "{install}" ];
            then
                rm -r "{install}"
            fi

            mkdir -p "{install}"
            pushd "{install}" > /dev/null

            tar -zxvf "{binary}"

            if [ -d "lib" ];
            then
                echo "Modifying '/etc/ld.so.conf.d'..."
                echo "{install}/lib" > "/etc/ld.so.conf.d/{decorated_install}.conf"
                ldconfig
            fi
            popd > /dev/null
            """).format( binary=binary_filename,
                         install=install_location,
                         decorated_install=(install_location[len(os.path.sep):] if install_location.startswith(os.path.sep) else install_location).replace(os.path.sep, '-'),
                       ))

    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateCommentCommand(value):
        return "# {}".format(value)
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateMessageCommand(value):
        replacement_chars = [ ( '$', r'\$' ),
                              ( '"', r'\"' ),
                            ]
                            
        output = []
        
        for line in value.split('\n'):
            if not line.strip():
                output.append('echo ""')
            else:
                for old_char, new_char in replacement_chars:
                    link = line.replace(old_char, new_char)
                    
                output.append('echo "{}"'.format(line))
                
        return '\n'.join(output)
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateCallCommand(command_line):
        return ". {}".format(command_line)
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateExecuteCommand(command_line):
        return command_line
        
    # ---------------------------------------------------------------------------
    def _GenerateSymbolicLinkCommand(self, link_filename, link_source, is_dir):
        return 'ln -fs{dir_flag} "{source}" "{link}"\nchmod a+x "{link}"'.format( link=link_filename,
                                                                                  source=link_source,
                                                                                  dir_flag='d' if is_dir else '',
                                                                                )
                                                                                
    # ---------------------------------------------------------------------------
    @classmethod
    def _GenerateSetCommand(cls, name, values, preserve_original):
        return "export {name}={values}{preserve}".format( name=name,
                                                          values=cls.EnvironmentVariableDelimiter.join(values),
                                                          preserve=":${}".format(name) if preserve_original else '',
                                                        )
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateExitCommand(pause_on_success, pause_on_error, return_code):
        return textwrap.dedent(
            """\
            {success}
            {error}
            return {result}
            """).format( success=textwrap.dedent(
                                    """\
                                    if [ $? -eq 0 ]; 
                                    then 
                                        read -p "Press [Enter] to continue" 
                                    fi
                                    """) if pause_on_success else '',
                         error=textwrap.dedent(
                                    """\
                                    if [ $? -ne 0 ]; 
                                    then 
                                        read -p "Press [Enter] to continue" 
                                    fi
                                    """) if pause_on_error else '',
                         result=return_code or 0,
                       )
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateExitOnErrorCommand(return_code):
        return textwrap.dedent(
            """\
            error_code=$?
            if [ $error_code -ne 0 ]; 
            then 
                return $error_code
            fi
            """)
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateEchoOffCommand():
        return ""
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateSetCommandPromptCommand(prompt):
        return r'PS1="({}) `id -nu`@`hostname -s`:\w$ "'.format(prompt)
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateRemoveFileCommand(filename):
        return 'rm "{}"'.format(filename)
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateCopyFileCommand(source, dest):
        return 'cp "{source}" "{dest}"'.format( source=source,
                                                dest=dest,
                                              )
        