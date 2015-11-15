#!/bin/bash
# ---------------------------------------------------------------------------
# |
# |  SetupEnvironment.sh
# |
# |  David Brownell (db@DavidBrownell.com)
# |      9/13/2011
# |
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2011-15.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
set +v
error_bit=0

if [ "$DEVELOPMENT_ENVIRONMENT_ROOT" = "" ];
then
    echo
    echo "ERROR: Please run ActivateEnvironment.sh within the Common repository before"
    echo "       running this script."
    echo

    error_bit=1
fi

if [ $error_bit == 0 ];
then
    GetCurrentDir()
    {
        current_dir="${BASH_SOURCE[0]}";
        if [ -h "${SCRIPT_PATH}" ];
        then
            while [ -h "${SCRIPT_PATH}" ] 
            do 
                SCRIPT_PATH=`readlink "${SCRIPT_PATH}"`; 
            done
        fi
        pushd . > /dev/null
        cd `dirname ${current_dir}` > /dev/null
        current_dir=`pwd`;
        popd  > /dev/null
    }

    GetCurrentDir

    . $DEVELOPMENT_ENVIRONMENT_ROOT/SourceRepositoryTools/SourceRepositoryToolsImpl/SetupEnvironment.sh $current_dir "$@"
fi
