#!/bin/bash
# ---------------------------------------------------------------------------
# |
# |  ActivateEnvironment.sh
# |
# |  David Brownell (db@DavidBrownell.com)
# |      11/11/2015
# |
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
set +v
should_continue=1
changed_dir=0

# Get the distro name and use it to differentiate between functionality
distro_name=`uname -a | tr "[:upper:]" "[:lower:]"`

if [[ $distro_name == *el5* ]];
then
    is_rhel5=1
else
    is_rhel5=0
fi

# Ensure that this script is being invoked via source (as it modifies the current 
# environment)
if [ ${0##*/} = ActivateEnvironment.sh ];
then
    echo
    echo "This script activates a console for development according to information"
    echo "specific to the repository."
    echo
    echo "Because this process makes changes to environment variables, it must be run within"
    echo "the current context. To do this, please run the script as follows:"
    echo
    echo "    . ./ActivateEnvironment.sh"
    echo
    echo

    should_continue=0
fi

# Move the the dir that contains this script, regardless of where we are invoked from. Note that
# this code doesn't work on RHEL5 when sourced, as BASH_SOURCE is not defined as expected. It works
# on other distros and when not sourced, but there are problems with that particular combo.
#
# On RHEL5, the script must be invoked from the repo root.
#
if [ $should_continue = 1 ] && [ $is_rhel5 = 0 ];
then
    GetCurrentDir()
    {
        current_dir="${BASH_SOURCE[0]}";
        if [ -h "${SCRIPT_PATH}" ] 
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
    pushd $current_dir > /dev/null
    changed_dir=1
fi

# Get the python executable and the fullpath to the source repository tools.
# This information is required to bootstrap the environment activation process.
if [ ! -e `pwd`/Generated/Linux/EnvironmentBootstrap.data ]
then
    echo
    echo "ERROR: It appears that SetupEnvironment.sh has not been run for this environment."
    echo "       Please run SetupEnvironment.sh and run this script again."
    echo
    echo "       [`pwd`/Generated/Linux/EnvironmentBootstrap.data was not found]"
    echo
    
    should_continue=0
fi

if [ $should_continue = 1 ]
then
    # Parse the bootstrap info, extracting the python binary and common code root
    while read line; 
    do
        if [[ $line == python_binary* ]] 
        then
            export PYTHON_BINARY=`readlink -f ${line#python_binary=}`
        elif [[ $line == fundamental_repo* ]]
        then
            export DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=`readlink -f ${line#fundamental_repo=}`
        elif [[ $line == is_tool_repo* ]]
        then
            is_tool_repo=${line#is_tool_repo=}
        elif [[ $line == is_configurable* ]]
        then
            is_configurable=${line#is_configurable=}
        fi
    done < "`pwd`/Generated/Linux/EnvironmentBootstrap.data"
fi

export PYTHON_PATH=$DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL

# List configurations if requested
if [ "$1" == "ListConfigurations" ];
then
    shift 1

    $PYTHON_BINARY -m SourceRepositoryTools.Impl.ActivateEnvironment ListConfigurations "`pwd`" $@
    should_continue=0
fi

# Indicate if this is a tool repository if requested
if [ "$1" == "IsToolRepository" ];
then
    shift 1

    $PYTHON_BINARY -m SourceRepositoryTools.Impl.ActivateEnvironment IsToolRepository "`pwd`" $@
    should_continue=0
fi

# Only allow one activated environment at a time (unless we are activating a tool repository).
if [ $should_continue = 1 ]
then
    if [[ "$is_tool_repo" != "1" && "$DEVELOPMENT_ENVIRONMENT_REPOSITORY" != "" && "$DEVELOPMENT_ENVIRONMENT_REPOSITORY" != "`pwd`" ]]
    then
        echo ""
        echo "ERROR: Only one environment can be activated at a time, and it appears as"
        echo "       if one is already active. Please open a new console window and run"
        echo "       this script again."
        echo ""
        echo "       [DEVELOPMENT_ENVIRONMENT_REPOSITORY is already defined as \"$DEVELOPMENT_ENVIRONMENT_REPOSITORY\"]"
        echo ""
        
        should_continue=0
    fi
fi

# A tool repository can't be activated in isolation
if [ $should_continue = 1 ]
then
    if [[ "$is_tool_repo" == "1" && "$DEVELOPMENT_ENVIRONMENT_REPOSITORY_ACTIVATED_FLAG" != "1" ]]
    then
        echo ""
        echo "ERROR: A tool repository cannot be activated in isolation. Activate another repository before"
        echo "       activating this one."
        echo ""

        should_continue=0
    fi
fi

# If we are working with a repository that requires a configuration name, extract the value. If
# the value doesn't exist, display an error message.
# 
# NOTE THAT THE FOLLOWING CODE WILL NEED TO CHANGE IF THE ARGUMENTS TO ActivateEnvironment.py INCREASE
# BEYOND THE NUMBER CURRENTLY SUPPORTED.
# 
# Note that this code was created to match the code in ActivateEnvironment.cmd, which requires a 
# hacky workaround (see comments in ActivateEnvironment.cmd). This workaround may not be necessary
# here, but I am erroring on the side of consistency because I really hate making changes to these
# foundational files.

if [ $should_continue = 1 ];
then
    if [ "$is_configurable" == "1" ];
    then
        if [ "$1" == "" ];
        then
            echo ""
            echo "ERROR: This environment is a configurable environment, which means that it"
            echo "       can be activated in a variety of different configurations. Please" 
            echo "       run this script again with a configuration name provided on the"
            echo "       command line."
            echo ""
            echo "       Available configuration names are:"
            $PYTHON_BINARY -m SourceRepositoryTools.Impl.ActivateEnvironment ListConfigurations "`pwd`" indented
            echo ""

            should_continue=0
        fi
        
        if [ "$DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION" != "" ]
        then
            if [ "$DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION" != "$1" ]
            then
                echo ""
                echo "ERROR: The environment was previously activated with a different configuration."
                echo "       Please open a new window and reactivate the environment with the new"
                echo "       configuration."
                echo ""
                echo "       ['$DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION' != '$1']"
                echo ""

                should_continue=0
            fi
        fi

        export _ACTIVATE_ENVIRONMENT_CLA=$@
    else
        export _ACTIVATE_ENVIRONMENT_CLA=None $@
    fi
fi

if [ $should_continue = 1 ];
then
    # Create a temporary command file that contains the output of the setup scripts. This is necessary to
    # work around differences between the 64-bit command prompt and the 32-bit python version currently in
    # use.
    temp_script_name=`mktemp`
    rm $temp_script_name

    should_continue=0

    # Generate...
    $PYTHON_BINARY -m SourceRepositoryTools.Impl.ActivateEnvironment Activate "$temp_script_name" "`pwd`" $_ACTIVATE_ENVIRONMENT_CLA
    script_generation_error=$?
    if [ -f $temp_script_name ]; 
    then
        chmod u+x $temp_script_name
        
        # Invoke...
        . $temp_script_name
        script_execution_error=$?
        
        if [ $script_generation_error != 0 ];
        then
            echo ""
            echo "ERROR: Errors were encountered and the environment has not been successfully"
            echo "       activated for development."
            echo ""
            echo "       [$DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL/SourceRepositoryTools/Impl/ActivateEnvironment.py failed]"
            echo ""
        elif [ $script_execution_error != 0 ];
        then
            echo ""
            echo "ERROR: Errors were encountered and the environment has not been successfully"
            echo "       activated for development."
            echo ""
            echo "       [$temp_script_name failed]"
            echo ""
        else
            should_continue=1
        fi
    fi
fi

export _ACTIVATE_ENVIRONMENT_CLA=
export PYTHON_PATH=

if [ $changed_dir = 1 ];
then        
    popd > /dev/null
fi

if [ $should_continue = 1 ];
then
    echo ""
    echo ""
    echo "The environment has been activated and is ready for development."
    echo ""
    echo ""

    return 0
else
    return -1
fi