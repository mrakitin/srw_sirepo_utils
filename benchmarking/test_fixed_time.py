import os
import shutil
import time
from subprocess import STDOUT, check_output as qx

data_dir = 'data_example_10'
# timeout = 30  # seconds
timeout = 900  # seconds = 15 min
# timeout = 1800  # seconds = 30 min

try:
    shutil.rmtree(data_dir)
except:
    pass

for i in [0, 1, 4]:  # , 8, 10, 12, 16, 18, 20, 22, 24, 26, 28]:  # range(29):
    # Create the dir with the results:
    os.mkdir(data_dir)
    shutil.copy('SRWLIB_ExampleViewDataFile.bat', data_dir)
    shutil.copy('SRWLIB_ExampleViewDataFile.sh', data_dir)

    start_time = time.time()

    python_command = 'python SRWLIB_Example10.py'
    if i == 0:
        command = python_command
    else:
        command = 'mpiexec -n %i %s' % (i, python_command)

    print(command)

    try:
        # From here: http://stackoverflow.com/questions/1191374/using-module-subprocess-with-timeout
        output = qx(command, stderr=STDOUT, timeout=timeout)
    except TypeError:
        # http://stackoverflow.com/questions/23287689/how-to-make-a-subprocess-call-timeout-using-python-2-7-6
        # http://easyprocess.readthedocs.org/en/latest/
        from easyprocess import EasyProcess

        output = EasyProcess(command).call(timeout=timeout).stdout
    except:
        pass

    print('Command <%s> timed out after %i seconds' % (command, timeout))

    end_time = time.time()

    duration = end_time - start_time

    print('\nNum of processors: %2i    Duration: %.3f seconds\n' % (i, duration))
    shutil.move(data_dir, '%s_%02i_%.3f' % (data_dir, i, duration))
