@REM ---------------------------------------------------------------------------
@REM |
@REM |  SetupEnvironment.cmd
@REM |
@REM |  David Brownell (db@DavidBrownell.com)
@REM |      8/08/2015
@REM |
@REM ---------------------------------------------------------------------------
@REM |
@REM |  Copyright David Brownell 2015-18.
@REM |        
@REM |  Distributed under the Boost Software License, Version 1.0.
@REM |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |
@REM ---------------------------------------------------------------------------
@echo off

pushd %1

REM The following environment variables must be set prior to invoking this batch file:
REM - DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL
REM - PYTHON_BINARY

REM Create a temporary command file that contains the output of the setup scripts. This is necessary to
REM work around differences between the 64-bit command prompt and the 32-bit python version currently in
REM use.
call :create_temp_script_name

REM Generate...
set PYTHONPATH=%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%
%PYTHON_BINARY% -m SourceRepositoryTools.Impl.SetupEnvironment "%_SETUP_ENVIRONMENT_TEMP_SCRIPT_NAME%" %*
set PYTHONPATH=

set _SETUP_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL=%ERRORLEVEL%

REM Invoke...
call %_SETUP_ENVIRONMENT_TEMP_SCRIPT_NAME%
set _SETUP_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL=%ERRORLEVEL%

REM Process errors...
if %_SETUP_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL% NEQ 0 (
    @echo.
    @echo ERROR: Errors were encountered and the environment has not been successfully setup for development.
    @echo.
    @echo        [%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\SourceRepositoryTools\Impl\SetupEnvironment.py failed]
    @echo.
    
    goto error_end
)

if %_SETUP_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL% NEQ 0 (
    @echo.
    @echo ERROR: Errors were encountered and the environment has not been successfully setup for development.
    @echo.
    @echo        [%_SETUP_ENVIRONMENT_TEMP_SCRIPT_NAME% failed]
    @echo.
    
    goto error_end
)

REM Cleanup...
del "%_SETUP_ENVIRONMENT_TEMP_SCRIPT_NAME%"

:complete
@echo The environment has been setup for development. Please run ActivateEnvironment.cmd 
@echo within a new console window to begin development within this environment.
@echo.
@echo.

set _SETUP_ENVIRONMENT_ERROR_LEVEL=0
goto end

:error_end
set _SETUP_ENVIRONMENT_ERROR_LEVEL=-1
goto end

@REM ---------------------------------------------------------------------------
:create_temp_script_name
setlocal EnableDelayedExpansion
set _filename=%~dp0\SetupEnvironment-!RANDOM!-!Time:~6,5!.cmd
endlocal & set _SETUP_ENVIRONMENT_TEMP_SCRIPT_NAME=%_filename%

if exist "%_SETUP_ENVIRONMENT_TEMP_SCRIPT_NAME%" goto :create_temp_script_name
goto :EOF
@REM ---------------------------------------------------------------------------

:end
set _SETUP_ENVIRONMENT_TEMP_SCRIPT_NAME=
set _SETUP_ENVIRONMENT_SCRIPT_GENERATION_ERROR_LEVEL=
set _SETUP_ENVIRONMENT_SCRIPT_EXECUTION_ERROR_LEVEL=

popd

exit /B %_SETUP_ENVIRONMENT_ERROR_LEVEL%
