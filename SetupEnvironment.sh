#!/bin/bash
# ---------------------------------------------------------------------------
# |
# |  SetupEnvironment.sh
# |
# |  David Brownell (db@DavidBrownell.com)
# |      8/08/2015
# |
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-17.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Run as:
# |     sudo -E ./SetupEnvironment.sh
# |
# ---------------------------------------------------------------------------

set +v
error_bit=0

if [ $error_bit = 0 ];
then
    # Common_Environment BEGIN
    
    # This is a one-time customization that is required because this is the most fundamental repository
    # and a dependency of all other libraries. Sections in this file delimited by "Common_Environment"
    # should not be duplicated in other SetupEnvironment.cmd files.
    # 
    # *** Python is hard-coded; this file will need to be updated should the python version change ***
    export DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL="$(cd "$(dirname "$0")" && pwd)"
    export PYTHON_BINARY=/usr/bin/python
    
    $PYTHON_BINARY $DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL/SourceRepositoryTools/Impl/SetupEnvironment_LinuxPreinstall.py
    error_bit=$?
    if [ $error_bit != 0 ];
    then
        echo
        echo "ERROR: Linux preinstall activities were not successfully completed."
        echo
    fi
    # Common_Environment END
    
    if [ "$DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL" = "" ];
    then
        echo
        echo "ERROR: Please run ActivateEnvironment.sh within a repository before running this script."
        echo
        error_bit=1
    fi
    
    if [ $error_bit = 0 ];
    then
        GetCurrentDir()
        {
            current_dir="${BASH_SOURCE[0]}";
            
            while [ -h "${SCRIPT_PATH}" ];
            do
                SCRIPT_PATH=`readlink "${SCRIPT_PATH}"`;
            done
            
            pushd . > /dev/null
            cd `dirname ${current_dir}` > /dev/null
            current_dir=`pwd`
            popd > /dev/null
        }
        
        GetCurrentDir
        
        . $DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL/SourceRepositoryTools/Impl/SetupEnvironment.sh $current_dir "$@"
    fi
    
    # Common_Environment BEGIN
    export PYTHON_BINARY=
    export DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=
    # Common_Environment END
fi
