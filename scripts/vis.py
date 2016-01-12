#*************************************************************************
# Copyright (C) 2015 by Arash Bakhtiari
# You may not use this file except in compliance with the License.
# You obtain a copy of the License in the LICENSE file.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#*************************************************************************

#*************************************************************************
# In order to run this script, you should do the following in advance:
#
#         1- Make sure you have VisIt package on your machine; for LRZ Linux cluster,
#         one should load the VisIt module:
#
#                         >>> module load visit
#
#         2- run the script on the machine by invoking visit
#
#                         >>> visit -cli -nowin -s vis.py -i<vtk-files-dir>
#
#
#         IMPORTANT NOTE: make sure you are using the proper system on which Xlib is
#         accessible by VisIt; this means you need to run the code on special nodes;
#         namely Render Nodes. For instace, for linux cluster in LRZ one should should
#         use the following command on the remote visualization nodes:
#
#                         >>> rvglrun visit -cli -nowin -s vis.py -i<vtk-files-dir>
#
#         For more information, please refer to the LRZ user manual web-page:
#
#                 https://www.lrz.de/services/v2c_en/remote_visualisation_en/super_muc_users_en/
#*************************************************************************

############################################################################
# IMPORT SYSTEM LIBRARIES
############################################################################
import time
import sys
import os

############################################################################
# IMPORT LOCAL LIBRARIES
############################################################################
from visit import *

from vis_plot_utils import *
from vis_plot_slice import *
from vis_plot_porous import *

############################################################################
# INPUT ARGUMENTS
############################################################################
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-i', dest='input_dir', action='store')
args, unknown = parser.parse_known_args()

############################################################################
# SET THE TIME STRING
############################################################################
TIMESTR = time.strftime("%Y%m%d-%H%M%S")

############################################################################
# DATABASES
############################################################################
VTK_DIR   = args.input_dir
IMAGE_DIR = VTK_DIR+"/images-"+TIMESTR
os.makedirs(IMAGE_DIR)

CON_VTK_FILES = VTK_DIR+"/"+"conc_T*_P.pvtu database"
RHO_VTK_FILES = VTK_DIR+"/"+"stokes_rho_0_.pvtu"
VEL_VTK_FILES = VTK_DIR+"/"+"stokes_vel_0_.pvtu"

############################################################################
# VISUALIZATION SCENARIOS
############################################################################
def vis_slice(vtk_files, output_dir):
    OpenDatabase(vtk_files)
    draw_slice()
    save_images(output_dir)

def vis_porous(rho_vtk_files, vel_vtk_files, conc_vtk_files, output_dir):
    OpenDatabase(rho_vtk_files, 0)
    draw_porous_media_IV()
    cut_porous_media()

    OpenDatabase(vel_vtk_files, 1)
    ActivateDatabase(vel_vtk_files)
    draw_porous_velocity()

    OpenDatabase(conc_vtk_files, 2)
    ActivateDatabase(conc_vtk_files)
    draw_concentration_field()

    set_view()
    save_images(output_dir)

############################################################################
# MAIN
############################################################################
if __name__ == '__main__':

    ########################################################################
    # PLOTS
    ########################################################################
    vis_slice(CON_VTK_FILES, IMAGE_DIR)
    #vis_porous(RHO_VTK_FILES, VEL_VTK_FILES, CON_VTK_FILES, IMAGE_DIR)
    sys.exit()