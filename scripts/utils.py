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

################################################################################
# SYSTEM IMPORT
################################################################################
import subprocess
import socket
import time
import sys
import os

################################################################################
# LOCAL IMPORT
################################################################################
import parser
import pp

################################################################################
# GLOBALS
################################################################################
TIMESTR       = time.strftime("%Y%m%d-%H%M%S")
RESULT_TAG_HEADER  = '#TBSLAS-HEADER: '
RESULT_TAG         = '#TBSLAS-RESULT: '
MPI_TOTAL_NUM_PORCESSES = 1
OMP_NUM_THREADS = 1

################################################################################
# ENVIRONMENT VARIABLES
################################################################################
try:
    TBSLAS_DIR = os.environ['TBSLAS_DIR']
except KeyError as e:
    print "Environment variable {0} is not set.".format(e)
    sys.exit()

################################################################################
# DIRECTORIES
################################################################################
TBSLAS_EXAMPLES_DIR      = os.path.join(TBSLAS_DIR, "examples/")
TBSLAS_EXAMPLES_BIN_DIR  = os.path.join(TBSLAS_EXAMPLES_DIR, "bin/")
# TBSLAS_RESULT_DIR_PREFIX = ''

################################################################################
# EXECUTION COMMAND
################################################################################
SCRIPT_ID       = sys.argv[0].replace('.py', '').replace('./','')

def parse_args():
    USAGE = 'USAGE: ./python PROGRAM <mpi-num-processes> <omp-num-threads> <num-steps=5>'
    print sys.argv
    if len(sys.argv) < 3:
        print USAGE
        sys.exit()
    if len(sys.argv) >= 3:
        MPI_TOTAL_NUM_PORCESSES = int(sys.argv[1])
        OMP_NUM_THREADS = int(sys.argv[2])

def get_output_prefix(num_proces):
    return SCRIPT_ID+'-np'+str(num_proces).zfill(5)+'-'+TIMESTR

def get_result_dir_prefix():
    hostname      = socket.gethostname()
    output_prefix = get_output_prefix(MPI_TOTAL_NUM_PORCESSES)
    RESULT_DIR = os.environ['PWD']
    if 'stampede' in hostname:
        RESULT_DIR = os.environ['SCRATCH']
    elif 'maverick' in hostname:
        RESULT_DIR = os.environ['WORK']
    print "STORING OUTPUT IN: " + RESULT_DIR
    return os.path.join(RESULT_DIR, output_prefix)

def compile_code():
    PWD = os.environ['PWD']
    os.chdir(TBSLAS_EXAMPLES_DIR)
    # execute command
    cmd = ['make','-j']
    p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        sys.stdout.write(line)
    os.chdir(PWD)

def determine_command_prefix(mpi_num_procs):
    hostname      = socket.gethostname()
    if 'stampede' in hostname:
        return ['ibrun', '-np', str(mpi_num_procs), 'tacc_affinity']
    elif 'maverick' in hostname:
        return ['ibrun', '-np', str(mpi_num_procs), 'tacc_affinity']
    else:
        return ['mpirun', '-np', str(mpi_num_procs)]

def analyse_command_output(output, \
                           file_dt, file_pr, file_out, file_pp, \
                           PRINT_RSLT_HEADER, PRINT_PRFL_HEADER):
    for line in output:
        file_out.write(line)
        # CATCH RESULTS HEADER
        if line.startswith(RESULT_TAG_HEADER) and PRINT_RSLT_HEADER:
            li = line.replace(RESULT_TAG_HEADER, '')
            file_dt.write(li)
            sys.stdout.write(li)
        # CATCH RESULTS DATA
        if line.startswith(RESULT_TAG):
            li = line.replace(RESULT_TAG, '')
            file_dt.write(li)
            sys.stdout.write(li)

    # PARSE PROFILE OUTPUT
    mydoc = parser.pdoc(output)
    mydoc.print_me(file_pr)
    pp.post_process_profile_data(mydoc, file_pp, PRINT_PRFL_HEADER);

def execute_commands(cmds, id):
    id = SCRIPT_ID+'-'+id
    sys.stdout.write("##############################\n")
    sys.stdout.write("# "+id+"\n")
    sys.stdout.write("##############################\n")
    PRINT_RSLT_HEADER = True
    PRINT_PRFL_HEADER = True

    # open output files
    TBSLAS_RESULT_DIR_PREFIX = get_result_dir_prefix()
    if not os.path.exists(TBSLAS_RESULT_DIR_PREFIX):
        os.makedirs(TBSLAS_RESULT_DIR_PREFIX)
    file_dt = open(os.path.join(TBSLAS_RESULT_DIR_PREFIX, id+'.data'), 'w')
    file_pr = open(os.path.join(TBSLAS_RESULT_DIR_PREFIX, id+'.profile'), 'w')
    file_pp = open(os.path.join(TBSLAS_RESULT_DIR_PREFIX, id+'.profile.pp'), 'w')

    # output current git revision
    revision = subprocess.check_output(["git", "describe"])
    file_dt.write('# REVISION: ' + revision)
    file_pr.write('# REVISION: ' + revision)
    file_pp.write('# REVISION: ' + revision)

    # execute generated commands
    for counter, cmd in cmds.iteritems():
        out_dir_name = \
          os.path.join(TBSLAS_RESULT_DIR_PREFIX,'{0}-cmd{1:03}'.format(id,counter))
        out_file_name = out_dir_name+'.out'
        file_out = open(out_file_name, 'w')
        os.environ['TBSLAS_RESULT_DIR'] = out_dir_name
        os.makedirs(out_dir_name)

        # output command
        cmd_msg = '# CMD: ' +  ' '.join(cmd) + '\n'

        sys.stdout.write('# ============================================================================================================================================\n')
        sys.stdout.write(cmd_msg)

        file_out.write('# ============================================================================================================================================\n')
        file_out.write(cmd_msg)

        file_dt.write('# ============================================================================================================================================\n')
        file_dt.write(cmd_msg)

        file_pr.write('# ============================================================================================================================================\n')
        file_pr.write(cmd_msg)

        file_pp.write('# ============================================================================================================================================\n')
        file_pp.write (cmd_msg)

        # execute command
        p = subprocess.Popen(cmd,                    \
                             shell=False,            \
                             stdout=subprocess.PIPE, \
                             stderr=subprocess.STDOUT)

        # analyse command
        analyse_command_output(p.stdout.readlines(),                \
                               file_dt, file_pr, file_out, file_pp, \
                               PRINT_RSLT_HEADER, PRINT_PRFL_HEADER)
        PRINT_RSLT_HEADER = False
        PRINT_PRFL_HEADER = False

        # flush output
        file_dt.flush()
        file_pr.flush()
        file_pp.flush()
        file_out.close()
    file_dt.close()
    file_pr.close()
    file_pp.close()
