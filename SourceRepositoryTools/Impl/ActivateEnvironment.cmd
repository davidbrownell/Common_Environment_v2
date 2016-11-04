@REM ---------------------------------------------------------------------------
@REM |
@REM |  ActivateEnvironment.cmd
@REM |
@REM |  David Brownell (db@DavidBrownell.com)
@REM |      8/11/2015
@REM |
@REM ---------------------------------------------------------------------------
@REM |
@REM |  Copyright David Brownell 2015-16.
@REM |        
@REM |  Distributed under the Boost Software License, Version 1.0.
@REM |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |
@REM ---------------------------------------------------------------------------
@echo off

pushd %~dp0

REM Enusure that this command prompt has been launched from an elevated command prompt.
REM This is necessary, as some activities only function when they are able to create sympolic
REM links, which requires elevated privelidges.
REM
REM This technique is based on information found at:
REM     https://stackoverflow.com/questions/4051883/batch-script-how-to-check-for-admin-rights#11995662
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    @echo.
    @echo ERROR: This script must be run from an elevated command prompt.
    @echo.
    @echo        [Admin privelidges required]
    @echo.
    
    goto end
)

REM Get the python executable and the fullpath to the source repository tools.
REM This information is required to bootstrap the environment activation process.
if not exist "%~dp0Generated\Windows\EnvironmentBootstrap.data" (
    @echo.
    @echo ERROR: It appears that SetupEnvironment.cmd has not been run for this environment.
    @echo        Please run SetupEnvironment.cmd and run this script again.
    @echo. 
    @echo        [%~dp0Generated\Windows\EnvironmentBootstrap.data was not found]
    @echo.

    goto end
)

set _ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL=%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%

REM Parse the bootstrap info, extracting the python binary and fundamental root
for /f "tokens=1,2 delims==" %%a in (%~dp0Generated\Windows\EnvironmentBootstrap.data) do (
    if "%%a"=="python_binary" set PYTHON_BINARY=%%~fb
    if "%%a"=="fundamental_development_root" set DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=%%~fb
    if "%%a"=="is_tool_repository" set _ACTIVATE_ENVIRONMENT_IS_TOOL_REPOSITORY=%%b
    if "%%a"=="is_configurable_repository" set _ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY=%%b
)

REM List configurations if requested
if "%1" == "ListConfigurations" (
    %PYTHON_BINARY% "%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\SourceRepositoryTools\Impl\ActivateEnvironment.py" ListConfigurations %~dp0 standard
    goto end
)

REM Indicate if this is a tool repository if requested
if "%1" == "IsToolRepository" (
    %PYTHON_BINARY% "%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\SourceRepositoryTools\Impl\ActivateEnvironment.py" IsToolRepository %~dp0
    goto end
)

REM Only allow one activated environment at a time (unless we are activating a tool repository).
if "%_ACTIVATE_ENVIRONMENT_IS_TOOL_REPOSITORY%" NEQ "1" if "%DEVELOPMENT_ENVIRONMENT_REPOSITORY%" NEQ "" if "%DEVELOPMENT_ENVIRONMENT_REPOSITORY%\" NEQ "%~dp0" (
    @echo.
    @echo ERROR: Only one environment can be activated at a time, and it appears as
    @echo        if one is already active. Please open a new console window and run
    @echo        this script again.
    @echo.
    @echo        [DEVELOPMENT_ENVIRONMENT_REPOSITORY is already defined as "%DEVELOPMENT_ENVIRONMENT_REPOSITORY%"]
    @echo.

    goto end
)

REM If we are working with a repository that requires a configuration name, extract the value. If
REM the value doesn't exist, display an error message.
REM 
REM NOTE THAT THE FOLLOWING CODE WILL NEED TO CHANGE IF THE ARGUMENTS TO ActivateEnvironment.py INCREASE
REM BEYOND THE NUMBER CURRENTLY SUPPORTED.
REM 
REM Note that all of this is required because the "shift" command doesn't modify %*

if "%_ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY%" NEQ "0" (
    if "%1" == "" (
        @echo.
        @echo ERROR: This environment is a configurable environment, which means that it
        @echo        can be activated in a variety of different configurations. Please 
        @echo        run this script again with a configuration name provided on the 
        @echo        command line.
        @echo.
        @echo        Available configuration names are:
        %PYTHON_BINARY% "%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\SourceRepositoryTools\Impl\ActivateEnvironment.py" ListConfigurations %~dp0 indented
        @echo.

        goto reset_and_end
    )

    if "%DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION%" NEQ "" (
        if "%DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION%" NEQ "%1" (
            @echo.
            @echo ERROR: The environment was previously activated with a different configuration.
            @echo        Please open a new window and reactive the environment with the new 
            @echo        configuration.
            @echo.
            @echo        ["%DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION%" != "%1"]
            @echo.

            goto reset_and_end
        )
    )

    set _ACTIVATE_ENVIRONMENT_CLA1=%1
    set _ACTIVATE_ENVIRONMENT_CLA2=%2
    set _ACTIVATE_ENVIRONMENT_CLA3=%3
    set _ACTIVATE_ENVIRONMENT_CLA4=%4
    set _ACTIVATE_ENVIRONMENT_CLA5=%5

    goto cla_args_set
)

set _ACTIVATE_ENVIRONMENT_CLA1=None
set _ACTIVATE_ENVIRONMENT_CLA2=%1
set _ACTIVATE_ENVIRONMENT_CLA3=%2
set _ACTIVATE_ENVIRONMENT_CLA4=%3
set _ACTIVATE_ENVIRONMENT_CLA5=%4

:cla_args_set

REM Create a temporary command file that contains the output of the setup scripts. This is necessary to
REM work around differences between the 64-bit command prompt and the 32-bit python version currently in
REM use.
call :create_temp_script_name

REM Generate...
%PYTHON_BINARY% "%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\SourceRepositoryTools\Impl\ActivateEnvironment.py" Activate "%_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%" %~dp0 %_ACTIVATE_ENVIRONMENT_CLA1% %_ACTIVATE_ENVIRONMENT_CLA2% %_ACTIVATE_ENVIRONMENT_CLA3% %_ACTIVATE_ENVIRONMENT_CLA4% %_ACTIVATE_ENVIRONMENT_CLA5%
set _ACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL=%ERRORLEVEL%

REM Invoke...
call %_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%
set _ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL=%ERRORLEVEL%

REM Process errors...
if %_ACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL% NEQ 0 (
    @echo.
    @echo ERROR: Errors were encountered and the environment has not been successfully
    @echo        activated for development.
    @echo.
    @echo        [%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\SourceRepositoryTools\Impl\ActivateEnvironment.py failed]
    @echo.

    goto reset_and_end
)

if %_ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL% NEQ 0 (
    @echo.
    @echo ERROR: Errors were encountered and the environment has not been successfully
    @echo        activated for development.
    @echo.
    @echo        [%_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME% failed]
    @echo.

    goto reset_and_end
)

REM Cleanup...
del "%_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%"

:complete
@echo.
@echo.
@echo The environment has been activated and is ready for development.
@echo.
@echo.
goto end

@REM ---------------------------------------------------------------------------
:create_temp_script_name
setlocal EnableDelayedExpansion
set _filename=%~dp0\ActivateEnvironment-!RANDOM!-!Time:~6,5!.cmd
endlocal & set _ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME=%_filename%

if exist "%_ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME%" goto :create_temp_script_name
goto :EOF
@REM ---------------------------------------------------------------------------

:reset_and_end
set DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=

:end
set _ACTIVATE_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL=
set _ACTIVATE_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL=
set _ACTIVATE_ENVIRONMENT_CLA5=
set _ACTIVATE_ENVIRONMENT_CLA4=
set _ACTIVATE_ENVIRONMENT_CLA3=
set _ACTIVATE_ENVIRONMENT_CLA2=
set _ACTIVATE_ENVIRONMENT_CLA1=
set _ACTIVATE_ENVIRONMENT_TEMP_SCRIPT_NAME=
set _ACTIVATE_ENVIRONMENT_IS_CONFIGURABLE_REPOSITORY=
set _ACTIVATE_ENVIRONMENT_IS_TOOL_REPOSITORY=
set _ACTIVATE_ENVIRONMENT_PREVIOUS_FUNDAMENTAL=

popd
