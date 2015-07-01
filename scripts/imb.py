#!/bin/env python

#*************************************************************************
#Copyright (C) 2015 by Arash Bakhtiari
#You may not use this file except in compliance with the License.
#You obtain a copy of the License in the LICENSE file.

#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.
#*************************************************************************
import os
import subprocess
import math
import sys
from collections import OrderedDict
from utils import *

def generate_command_args(de_init, de_factor, \
                          dt_init, dt_factor, \
                          tn_init, tn_factor, \
                          test_init, test_factor, \
                              num_steps):
    EXEC = os.path.join(TBSLAS_EXAMPLES_BIN_DIR, "advection")
    de_list = [de_init+cnt*de_factor                  for cnt in range(0, num_steps)]
    dt_list = [dt_init*math.pow(dt_factor,float(cnt)) for cnt in range(0,TOL_NUM_STEPS)]
    tn_list = [tn_init*math.pow(tn_factor,float(cnt)) for cnt in range(0,TOL_NUM_STEPS)]
    test_list = [test_init+cnt*test_factor            for cnt in range(0,TOL_NUM_STEPS)]

    # generate a dictionary data type of commands
    cmd_args = OrderedDict()
    cmd_id = 1;
    for counter in range(0,num_steps):
        ARGS    = ['-N'   , str(8**math.ceil(math.log(MPI_NUM_PROCESS,8))),   \
                   '-tol' , str(1e-10),                                       \
                   '-q'   , str(5),                                           \
                   '-d'   , str(de_list[counter]),                            \
                   '-dt'  , str(dt_list[counter]),                            \
                   '-tn'  , str(tn_list[counter]),                            \
                   '-test', str(test_list[counter]),                          \
                   '-vs'  , str(1),                               \
                   '-cubic',str(1),                               \
                   '-cuf'  ,str(8),                               \
                   '-omp' , str(OMP_NUM_THREADS)]
        cmd_args[cmd_id] = [EXEC] + ARGS
        cmd_id = cmd_id + 1
    return cmd_args

################################################################################
# MAIN
################################################################################
if __name__ == '__main__':
    prepare_environment(OUTPUT_PREFIX)
    TOL_NUM_STEPS = 3
    if len(sys.argv) >= 4:
        TOL_NUM_STEPS   = int(sys.argv[3])
    # T_END = 1.0
    # ############################################################################
    # # TEST 1: TEMPORAL ERROR
    # ############################################################################
    de_factor = 2
    de_init   = 5
    # tl_factor = 1#0.1
    # tl_init   = 1e-5
    dt_factor = 1#0.5
    dt_init   = 0.25
    tn_factor = 1.0#/dt_factor
    tn_init   = 5#T_END/dt_init
    test_init = 4
    test_factor = 0;
    cmd_args = generate_command_args(de_init, de_factor, \
                                     dt_init, dt_factor, \
                                     tn_init, tn_factor, \
                                     test_init, test_factor, \
                                     1)
    execute_commands(cmd_args, 'table1')

    # ############################################################################
    # # TEST 2
    # ############################################################################
    de_factor = 2
    de_init   = 5
    # tl_factor = 1#0.1
    # tl_init   = 1e-5
    dt_factor = 1#0.5
    dt_init   = 0.25
    tn_factor = 1.0#/dt_factor
    tn_init   = 5#T_END/dt_init
    test_init = 5
    test_factor = 0;
    cmd_args = generate_command_args(de_init, de_factor, \
                                     dt_init, dt_factor, \
                                     tn_init, tn_factor, \
                                     test_init, test_factor, \
                                     TOL_NUM_STEPS)
    execute_commands(cmd_args, 'table2')

    # ############################################################################
    # # TEST 3
    # ############################################################################
    de_factor = 2
    de_init   = 5
    # tl_factor = 1#0.1
    # tl_init   = 1e-5
    dt_factor = 1#0.5
    dt_init   = 0.25
    tn_factor = 1.0#/dt_factor
    tn_init   = 5#T_END/dt_init
    test_init = 6
    test_factor = 0;
    cmd_args = generate_command_args(de_init, de_factor, \
                                     dt_init, dt_factor, \
                                     tn_init, tn_factor, \
                                     test_init, test_factor, \
                                     TOL_NUM_STEPS)
    execute_commands(cmd_args, 'table3')