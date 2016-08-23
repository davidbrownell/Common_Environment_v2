# ---------------------------------------------------------------------------
# |  
# |  WindowsEnvironment.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  08/08/2015 01:37:19 PM
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
import platform
import re
import subprocess
import sys
import textwrap

from ...Shell import Environment 

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class WindowsEnvironment(Environment):
    Name                                    = "Windows"
    CategoryName                            = "Windows"
    ScriptExtension                         = ".cmd"
    ExecutableExtension                     = ".exe"
    AllArgumentsScriptVariable              = "%*"
    EnvironmentVariableDelimiter            = ';'
    PotentialOSVersionDirectoryNames        = [ "10", "8", "7", "Vista", "2003Server", "XP", ]
    HasCaseSensitiveFileSystem              = False
    TempDirectories                         = [ os.getenv("TMP"), ]

    # ---------------------------------------------------------------------------
    def __init__(self):
        # Architecture
        self._os_architecture = "x64" if os.getenv("ProgramFiles(x86)") else "x86"
        
        # Version
        release = platform.release()
        if not release:
            # IronPython has been known to have problems with platform.release
            release = str(int(sys.getwindowsversion()[0]) + 1)
            
        potential_versions = { "8" : "10",                  # Crazy, but true
                               "2012Server" : "8",
                               "post2008Server" : "8",
                               "7" : "7",
                               "2008Server" : "7",
                               "2003Server" : "2003Server"
                             }
                            
        assert release in potential_versions, release
        self._os_version = potential_versions[release]
        
        # Directory
        from win32com.shell import shellcon, shell      # <Unable to import> pylint: disable = F0401, E0611
        import unicodedata
        
        homedir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
        homedir = unicodedata.normalize("NFKD", homedir).encode("ascii", "ignore")
        
        self._user_directory = homedir
        assert os.path.isdir(self._user_directory), self._user_directory
        
    # ---------------------------------------------------------------------------
    @property
    def OSVersion(self):
        return self._os_version
        
    # ---------------------------------------------------------------------------
    @property
    def OSArchitecture(self):
        return self._os_architecture
        
    # ---------------------------------------------------------------------------
    @property
    def UserDirectory(self):
        return self._user_directory
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def IsActive(platform_name):
        return "windows" in platform_name or platform_name == "nt"
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def IsSymLink(filename):
        # Python 2.+ doesn't support symlinks on Windows, so we have to do it manually
        import win32file
        
        file_attribute_reparse_point = 1024
        
        return os.path.exists(filename) and win32file.GetFileAttributes(filename) & file_attribute_reparse_point == file_attribute_reparse_point
        
    # ---------------------------------------------------------------------------
    def ResolveSymLink(self, filename):
        # Python 2.+ doesn't support symlinks on Windows and there doesn't seem to be
        # a way to resolve a symlink without parsing the file, and libraries mentioned
        # http://stackoverflow.com/questions/1447575/symlinks-on-windows/7924557#7924557
        # and https://github.com/sid0/ntfs seem to have problems. The only way I have found
        # to reliabaly get this info is to parse the output of 'dir' and extact the info.
        # This is horribly painful code.
        
        from StringIO import StringIO
        import cPickle as pickle

        filename = filename.replace('/', os.path.sep)

        assert self.IsSymLink(filename)

        if not hasattr(self, "_symlink_lookup"):
            self._symlink_lookup = {}                   # <Attribute defined outside __init__> pylint: disable = W0201
            self._symlink_redirection_maps = {}         # <Attribute defined outside __init__> pylint: disable = W0201

        if filename in self._symlink_lookup:
            return self._symlink_lookup[filename]

        # Are there any redirection maps that reside in the filename's path?
        path = os.path.split(filename)[0]
        while True:
            potential_map_filename = os.path.join(path, "symlink.redirection_map")
            if os.path.isfile(potential_map_filename):
                if potential_map_filename not in self._symlink_redirection_maps:
                    self._symlink_redirection_maps[potential_map_filename] = pickle.loads(open(potential_map_filename).read())

                if filename in self._symlink_redirection_maps[potential_map_filename]:
                    return self._symlink_redirection_maps[potential_map_filename][filename]

            new_path = os.path.split(path)[0]
            if new_path == path:
                break

            path = new_path

        # If here, there isn't a map filename so we have to do things the hard way.
        if os.path.isfile(filename):
            command_line = 'dir /AL "%s"' % filename
            is_match = lambda name: True
        else:
            command_line = 'dir /AL "%s"' % os.path.dirname(filename)
            is_match = lambda name: name == os.path.basename(filename)

        state = subprocess.Popen( command_line,
                                  shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                )
        sink = state.stdout.read()
        rval = state.wait() or 0
        
        assert rval == 0, sink

        regexp = re.compile(r".+<(?P<type>.+?)>\s+(?P<link>.+?)\s+\[(?P<filename>.+?)\]\s*")

        for line in sink.split('\n'):
            match = regexp.match(line)
            if match:
                link = match.group("link")
                if not is_match(link):
                    continue

                target_filename = match.group("filename")
                assert os.path.exists(target_filename), target_filename

                self._symlink_lookup[filename] = target_filename
                return target_filename

        assert False, sink
        
    # ---------------------------------------------------------------------------
    def DeleteSymLink(self, filename, command_only=True):
        assert self.IsSymLink(filename), filename
        
        command_line = '{delete} "{filename}"'.format( delete="rmdir" if os.path.isdir(filename) else "del",
                                                       filename=filename,
                                                     )
        if command_only:
            return command_line
            
        os.system(command_line)
        
    # ---------------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateCommentCommand(value):
        return "REM {}".format(value)
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateMessageCommand(value):
        replacement_chars = [ ( '%', '%%' ),
                              ( '^', '^^' ),
                              ( '&', '^&' ),
                              ( '<', '^<' ),
                              ( '>', '^>' ),
                              ( '|', '^|' ),
                              ( ',', '^,' ),
                              ( ';', '^;' ),
                              ( '(', '^(' ),
                              ( ')', '^)' ),
                              ( '[', '^[' ),
                              ( ']', '^]' ),
                              ( '"', '\"' ),
                            ]
                            
        output = []
        
        for line in value.split('\n'):
            if not line.strip():
                output.append("echo.")
            else:
                for old_char, new_char in replacement_chars:
                    line = line.replace(old_char, new_char)
                    
                output.append("echo {}".format(line))
                
        return '\n'.join(output)
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateCallCommand(command_line):
        return "call {}".format(command_line)
        
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateExecuteCommand(command_line):
        return command_line
        
    # ---------------------------------------------------------------------------
    def _GenerateSymbolicLinkCommand(self, link_filename, link_source, is_dir):
        # mklink isn't supported on 2003Server, so we have to use an alternative
        if self.OSVersion == "2003Server":
            template_string = 'if exist "{link}" ({remove} "{link}")\nfsutil hardlink create "{link}" "{dest}"'
        else:
            template_string = 'if exist "{link}" ({remove} "{link}")\nmklink{dir_flag} "{link}" "{dest}"'
            
        return template_string.format( link=link_filename,
                                       dest=link_source,
                                       dir_flag=" /D" if is_dir else '',
                                       remove="rmdir" if is_dir else "del"
                                     )
            
    # ---------------------------------------------------------------------------
    @classmethod
    def _GenerateSetCommand(cls, name, values, preserve_original):
        return "SET {name}={values}{preserve}".format( name=name,
                                                       values=cls.EnvironmentVariableDelimiter.join(values),
                                                       preserve=";%{}%".format(name) if preserve_original and os.getenv(name) else '',
                                                     )
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateExitCommand(pause_on_success, pause_on_error, return_code):
        return textwrap.dedent(
            """\
            {success}
            {error}
            exit /B {return_code}
            """).format( success="if %ERRORLEVEL% EQ 0 ( pause )" if pause_on_success else '',
                         error="if %ERRORLEVEL% NEQ 0 (pause)" if pause_on_error else '',
                         return_code=return_code or 0,
                       )
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateExitOnErrorCommand(return_code):
        return "if %ERRORLEVEL% NEQ 0 (exit /B {return_code})".format(return_code=return_code or "%ERRORLEVEL%")
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateEchoOffCommand():
        return "@echo off"
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateSetCommandPromptCommand(prompt):
        return "set PROMPT=({}) $P$G".format(prompt)
    
    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateRemoveFileCommand(filename):
        return 'del "{}"'.format(filename)
    
    # ----------------------------------------------------------------------
    @staticmethod
    def _GenerateRemoveDirectoryCommand(directory):
        return 'rmdir /S /Q "{}"'.format(directory)

    # ---------------------------------------------------------------------------
    @staticmethod
    def _GenerateCopyFileCommand(source, dest):
        return 'copy /Y "{source}" "{dest}"'.format( source=source,
                                                     dest=dest,
                                                   )
        