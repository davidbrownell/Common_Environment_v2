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
# |  Copyright David Brownell 2015.
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
fi
