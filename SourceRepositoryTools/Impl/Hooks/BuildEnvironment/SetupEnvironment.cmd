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
@REM |Distributed under the Boost Software License, Version 1.0.
@REM |(See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
@REM |
@REM ---------------------------------------------------------------------------
@echo off

if "%DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%"=="" (
    echo.
    echo ERROR: Please run ActivateEnvironment.cmd within a repository before running this script
    echo.
    goto end
)

call %DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL%\SourceRepositoryTools\Impl\SetupEnvironment.cmd %~dp0 %*

:end