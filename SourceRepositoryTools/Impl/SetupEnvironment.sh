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
set +v 
error_bit=0

pushd $1 > /dev/null

# The following environment variables must be set prior to invoking this file:
#   - DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL
#   - PYTHON_BINARY

# Create a temporary command file that contains the output of the setup script.
if [ $error_bit = 0 ];
then
    # Create a temporary command file that contains the output of the setup scripts. This is necessary to
    # work around differences between the 64-bit command prompt and the 32-bit python version currently in
    # use.
    temp_script_name=`mktemp`

    # Generate
    $PYTHON_BINARY $DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL/SourceRepositoryTools/Impl/SetupEnvironment.py $temp_script_name "$@"
    script_generation_error=$?
    chmod u+x $temp_script_name
    
    # Invoke
    $temp_script_name
    script_execution_error=$?
    
    if [ $script_generation_error != 0 ];
    then
        echo
        echo ERROR: Errors were encountered and the environment has not been successfully
        echo        setup for development.
        echo
        echo        [$DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL/SourceRepositoryTools/Impl/SetupEnvironment.py failed]
        echo
        
        error_bit=1
    fi
    
    if [ $script_execution_error != 0 ];
    then
        echo
        echo ERROR: Errors were encountered and the environment has not been successfully
        echo        setup for development.
        echo
        echo        [$temp_script_name failed]
        echo
    
        error_bit=1
    fi
    
    if [ $error_bit = 0 ];
    then
        echo
        echo
        echo The environment has been setup for development. Please run ActivateEnvironment.cmd 
        echo within a new console window to begin development within this environment.
        echo
        echo
    fi
fi

popd > /dev/null

