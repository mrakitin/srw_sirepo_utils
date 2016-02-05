import os
import shutil
import time

data_dir = 'data_example_10'

try:
    shutil.rmtree(data_dir)
except:
    pass

for i in range(29):  # [15, 16, 17, 18, 19, 20]:  # [0, 1, 2, 4, 6, 8, 10, 12, 14]:
    # Create the dir with the results:
    os.mkdir(data_dir)

    start_time = time.time()

    python_command = 'python SRWLIB_Example10.py'
    if i == 0:
        command = python_command
    else:
        command = 'mpiexec -n %i %s' % (i, python_command)

    print(command)
    os.system(command)

    end_time = time.time()

    duration = end_time - start_time

    print('\nNum of processors: %2i    Duration: %.3f seconds\n' % (i, duration))
    shutil.move(data_dir, '%s_%02i_%.3f' % (data_dir, i, duration))
