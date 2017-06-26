@REM ---------------------------------------------------------------------------
@REM |
@REM |  SetupEnvironment.cmd
@REM |
@REM |  David Brownell (db@DavidBrownell.com)
@REM |      8/08/2015
@REM |
@REM ---------------------------------------------------------------------------
@REM |
@REM |  Copyright David Brownell 2015-17.
@REM |        
@REM |  Distributed under the Boost Software License, Version 1.0.
@REM |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |
@REM ---------------------------------------------------------------------------
@echo off

@REM Common_Environment BEGIN

@REM This is a one-time customization that is required because this is the most fundamental repository
@REM and a dependency of all other libraries. Sections in this file delimited by "Common_Environment"
@REM should not be duplicated in other SetupEnvironment.cmd files.
@REM 
@REM *** Python is hard-coded; this file will need to be updated should the python version change ***

set DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=%~dp0
set PYTHON_BINARY=%~dp0Tools\Python\v3.6.0\Windows\python.exe
@REM Common_Environment END

if "%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%"=="" (
    echo.
    echo ERROR: Please run ActivateEnvironment.cmd within a repository before running this script
    echo.
    goto end
)

call %DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\SourceRepositoryTools\Impl\SetupEnvironment.cmd %~dp0 %*

@REM Common_Environment BEGIN
set PYTHON_BINARY=
set DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=
@REM Common_Environment END

:end