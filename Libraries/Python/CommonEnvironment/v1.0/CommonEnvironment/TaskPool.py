# ---------------------------------------------------------------------------
# |  
# |  TaskPool.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  09/05/2015 09:50:45 PM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-16.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import datetime
import multiprocessing
import os
import sys
import threading
import textwrap
import time
import traceback

from StringIO import StringIO

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Package
from CommonEnvironment.QuickObject import QuickObject
from CommonEnvironment.StreamDecorator import StreamDecorator

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# |
# |  Public Types
# |
# ---------------------------------------------------------------------------
class Task(object):
    def __init__( self,
                  name,                     # "Foo"
                  action_description,       # "Building Foo"
                  functor,                  # def Functor(task_index, output_stream) -> None or str or (result, str)
                ):
        assert name
        assert action_description
        assert functor

        self.Name                           = name
        self.ActionDescription              = action_description
        self.Functor                        = functor

        # Working data
        self.output                         = ''
        self.result                         = 0
        self.time_delta_string              = ''

# ---------------------------------------------------------------------------
# |
# |  Public Methods
# |
# ---------------------------------------------------------------------------
def Execute( tasks,
             num_concurrent_tasks=multiprocessing.cpu_count(),
             output_stream=sys.stdout,
             verbose=False,
             silent=False,
           ):
    assert tasks
    assert num_concurrent_tasks

    output_stream = StreamDecorator(None if silent else output_stream)
    
    # ---------------------------------------------------------------------------
    class Executor(object):
        # ---------------------------------------------------------------------------
        def __init__( self,
                      num_tasks,
                      is_multithreaded,
                    ):
            self._done_lock                 = threading.Lock()

            self._num_invocations           = 0
            self._ticks                     = 0

            self._remaining                 = num_tasks
            self._num_tasks                 = num_tasks
            self._is_multithreaded          = is_multithreaded

        # ---------------------------------------------------------------------------
        @property
        def NumTasks(self):
            return self._num_tasks

        # ---------------------------------------------------------------------------
        def Execute( self,
                     task,
                     task_index,
                     output_stream,
                   ):
            assert task
            assert output_stream

            start_time = time.time()
            
            # ---------------------------------------------------------------------------
            def GeneratePrefix():
                return "[{index:<{adjust}} of {total}]: ".format( adjust=len(str(self._num_tasks)),
                                                                  index=task_index + 1,
                                                                  total=self._num_tasks,
                                                                )

            # ---------------------------------------------------------------------------
            def DoneStatement():
                with self._done_lock:
                    # Get the num remaining
                    self._remaining -= 1
                    remaining = self._remaining

                    # Get the num of invocations
                    self._num_invocations += 1
                    num_invocations = self._num_invocations

                    # Get the time remaining
                    self._ticks += (time.time() - start_time)
                    ticks = self._ticks

                # ---------------------------------------------------------------------------
                def TimeEstimate(modifier):
                    return str(datetime.timedelta(seconds=(((float(ticks) / num_invocations) * modifier) / num_concurrent_tasks)))

                # ---------------------------------------------------------------------------
                
                output_stream.write("{prefix}DONE! ({result:<4} {time:>16}) [{remaining} left, ETA ~{eta}, Total ~{total}]\n".format( prefix=GeneratePrefix() if self._is_multithreaded else '',
                                                                                                                                      result="{},".format(task.result),
                                                                                                                                      time=task.time_delta_string,
                                                                                                                                      remaining=remaining,
                                                                                                                                      eta=TimeEstimate(remaining),
                                                                                                                                      total=TimeEstimate(self._num_tasks),
                                                                                                                                    ))

            # ---------------------------------------------------------------------------
            
            output_stream.write("{0:<107}".format("{}{}...".format(GeneratePrefix(), task.ActionDescription)))
            with CallOnExit(DoneStatement):
                sink = StringIO()

                try:
                    result = task.Functor(task_index, sink)

                    if result == None:
                        task.result = 0

                    elif isinstance(result, str):
                        task.result = 0
                        sink.write(result)

                    elif isinstance(result, tuple):
                        task.result = result[0]
                        sink.write(result[1])

                    else:
                        task.result = result

                except:
                    sink.write(traceback.format_exc())
                    task.result = -1

                task.output = sink.getvalue()
                task.time_delta_string = datetime.timedelta(seconds=(time.time() - start_time))

    # ---------------------------------------------------------------------------
    class ThreadSafeStreamDecorator(object):
        # ---------------------------------------------------------------------------
        def __init__( self,
                      thread_info,
                      core_index,
                      num_cores,
                      task_index,
                    ):
            self._thread_info               = thread_info
            self._core_index                = core_index
            self._num_cores                 = num_cores
            self._task_index                = task_index

        # ---------------------------------------------------------------------------
        def write(self, content):
            with self._thread_info.output_lock:
                output_stream.write("[Core {0:>{1}}] {2}".format( self._core_index, 
                                                                  len(str(self._num_cores - 1)),
                                                                  content,
                                                                ))

                if content and content[-1] != '\n':
                    output_stream.write("\n")

        # ---------------------------------------------------------------------------
        def flush(self):
            with self._thread_info.output_lock:
                output_stream.flush()

    # ---------------------------------------------------------------------------
    def InternalThreadProc(thread_info, core_index):
        while True:
            with thread_info.index_lock:
                if thread_info.current_index == thread_info.executor.NumTasks:
                    return

                task_index = thread_info.current_index
                thread_info.current_index += 1

            thread_info.executor.Execute( thread_info.tasks[task_index],
                                          task_index,
                                          ThreadSafeStreamDecorator( thread_info, 
                                                                     core_index, 
                                                                     num_concurrent_tasks,
                                                                     task_index,
                                                                   ),
                                        )

    # ---------------------------------------------------------------------------
    
    num_concurrent_tasks = min(num_concurrent_tasks, len(tasks))
    executor = Executor(len(tasks), num_concurrent_tasks != 1)

    with output_stream.DoneManager( line_prefix='',
                                    done_prefix="\nTask pool ",
                                  ) as si:
        if num_concurrent_tasks == 1:
            for index, task in enumerate(tasks):
                executor.Execute(task, index, si.stream)
        else:
            thread_info = QuickObject( executor=executor,

                                       current_index=0,

                                       index_lock=threading.Lock(),
                                       output_lock=threading.Lock(),

                                       tasks=tasks,
                                       output_stream=si.stream,
                                     )

            # Create the threads
            threads = []

            while True:
                if len(threads) == num_concurrent_tasks:
                    break

                def ThreadProc(index=len(threads)): InternalThreadProc(thread_info, index)

                threads.append(threading.Thread(target=ThreadProc))
                threads[-1].start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

        # Calculate the final result

        # ----------------------------------------------------------------------
        def Output(stream, task):
            stream.write(textwrap.dedent(
                """\

                # ----------------------------------------------------------------------
                # |  
                # |  {name} ({result}, {time})
                # |  
                # ----------------------------------------------------------------------
                {output}

                """).format( name=task.Name,
                             result=task.result,
                             time=task.time_delta_string,
                             output=task.output,
                           ))

        # ----------------------------------------------------------------------
        
        for task in tasks:
            if task.result != 0:
                Output(output_stream, task)
                si.result = si.result or task.result

        if verbose and si.result == 0 and any(task.output for task in tasks):
            for task in tasks:
                Output(output_stream, task)

        return si.result
