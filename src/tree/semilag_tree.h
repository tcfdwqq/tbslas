// *************************************************************************
// Copyright (C) 2014 by Arash Bakhtiari
// You may not use this file except in compliance with the License.
// You obtain a copy of the License in the LICENSE file.

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// *************************************************************************

#ifndef SRC_TREE_SEMILAG_TREE_H_
#define SRC_TREE_SEMILAG_TREE_H_

#include <vector>
#include <string>

#include <profile.hpp>

#include "semilag/semilag.h"
#include "tree/node_field_functor.h"
#include "tree/utils_tree.h"
#include "utils/common.h"
#include "utils/reporter.h"
#include "utils/cheb.h"

namespace tbslas {

template <class TreeType>
void SolveSemilagTree(TreeType& tvel_curr,
                      TreeType& tree_curr,
                      TreeType& tree_next,
                      const int timestep,
                      const typename TreeType::Real_t dt,
                      int num_rk_step = 1) {
  assert(false); // don't know what this function does, should be deprecated.
  typedef typename TreeType::Node_t NodeType;
  typedef typename TreeType::Real_t RealType;
  tbslas::SimConfig* sim_config = tbslas::SimConfigSingleton::Instance();

  // pvfmm::Profile::Tic("SemilagTree", &sim_config->comm, false,5);
  ////////////////////////////////////////////////////////////////////////
  // (1) collect the starting positions of the backward traj computation
  ////////////////////////////////////////////////////////////////////////
  // get the tree parameters from current tree
  NodeType* n_curr = tree_curr.PostorderFirst();
  while (n_curr != NULL) {
    if(!n_curr->IsGhost() && n_curr->IsLeaf())
      break;
    n_curr = tree_curr.PostorderNxt(n_curr);
  }
  int data_dof = n_curr->DataDOF();
  int cheb_deg = n_curr->ChebDeg();
  int sdim     = tree_curr.Dim();
  int num_points_per_node = (cheb_deg+1)*(cheb_deg+1)*(cheb_deg+1);

  std::vector<RealType> points_pos_all_nodes;
  tbslas::CollectChebTreeGridPoints(tree_next, points_pos_all_nodes);

  ////////////////////////////////////////////////////////////////////////
  // (2) solve semi-Lagrangian
  ////////////////////////////////////////////////////////////////////////
  int num_points_local_nodes = points_pos_all_nodes.size()/sdim;
  std::vector<RealType> points_val_local_nodes(num_points_local_nodes*data_dof);
  tbslas::SolveSemilagRK2(tbslas::NodeFieldFunctor<RealType,TreeType>(&tvel_curr),
                          tbslas::NodeFieldFunctor<RealType,TreeType>(&tree_curr),
                          points_pos_all_nodes,
                          sdim,
                          timestep,
                          dt,
                          num_rk_step,
                          points_val_local_nodes);

  ////////////////////////////////////////////////////////////////////////
  // (3) set the computed values
  ////////////////////////////////////////////////////////////////////////
  NodeType* n_next = tree_next.PostorderFirst();
  while (n_next != NULL) {
    if(!n_next->IsGhost() && n_next->IsLeaf()) break;
    n_next = tree_next.PostorderNxt(n_next);
  }

  int tree_next_node_counter = 0;
  while (n_next != NULL) {
    if (n_next->IsLeaf() && !n_next->IsGhost()) {
      pvfmm::cheb_approx<RealType, RealType>(
          &points_val_local_nodes[tree_next_node_counter*num_points_per_node*data_dof],
          cheb_deg,
          data_dof,
          &(n_next->ChebData()[0])
                                             );
      tree_next_node_counter++;
    }
    n_next = tree_next.PostorderNxt(n_next);
  }
  // pvfmm::Profile::Toc();
}

template <class TreeType>
void SolveSemilagInSitu(TreeType& tvel_curr,
                        TreeType& tree_curr,
                        const int timestep,
                        const typename TreeType::Real_t dt,
                        int num_rk_step = 1,
                        bool adaptive = true) {
  typedef typename TreeType::Node_t NodeType;
  typedef typename TreeType::Real_t RealType;
  tbslas::SimConfig* sim_config = tbslas::SimConfigSingleton::Instance();

  // pvfmm::Profile::Tic("SemilagTree", &sim_config->comm, false,5);
  ////////////////////////////////////////////////////////////////////////
  // (1) collect the starting positions of the backward traj computation
  ////////////////////////////////////////////////////////////////////////
  // get the tree parameters from current tree
  NodeType* n_curr = tree_curr.PostorderFirst();
  while (n_curr != NULL) {
    if(!n_curr->IsGhost() && n_curr->IsLeaf())
      break;
    n_curr = tree_curr.PostorderNxt(n_curr);
  }
  int data_dof = n_curr->DataDOF();
  int cheb_deg = n_curr->ChebDeg();
  int sdim     = tree_curr.Dim();
  int num_points_per_node; //= (cheb_deg+1)*(cheb_deg+1)*(cheb_deg+1);
  long Ncoeff=(cheb_deg+1)*(cheb_deg+2)*(cheb_deg+3)/6;
  static pvfmm::Matrix<RealType> M;
  { // Compute interpolation matrix
    std::vector<RealType> coord=new_nodes<RealType>(cheb_deg,3);
    if(M.Dim(0)!=coord.size()/3 || M.Dim(1)!=Ncoeff){
      for(int i=0;i<coord.size();i++) coord[i]=coord[i]*2.0-1.0;
      M.ReInit(coord.size()/3,Ncoeff);
      M.SetZero();
      std::vector<RealType> buff((cheb_deg+1)*(cheb_deg+1+3*2));
      for(long i=0;i<M.Dim(0);i++){
        pvfmm::cheb_eval(cheb_deg, &coord[i*3], &M[i][0], &buff[0]);
      }
      M=M.pinv().Transpose();
    }
    num_points_per_node=coord.size()/3;
  }


  std::vector<RealType> points_pos_all_nodes;
  tbslas::CollectChebTreeGridPoints(tree_curr, points_pos_all_nodes);

  ////////////////////////////////////////////////////////////////////////
  // (2) solve semi-Lagrangian
  ////////////////////////////////////////////////////////////////////////
  int num_points_local_nodes = points_pos_all_nodes.size()/sdim;
  std::vector<RealType> points_val_local_nodes(num_points_local_nodes*data_dof);
  tbslas::SolveSemilagRK2(tbslas::NodeFieldFunctor<RealType,TreeType>(&tvel_curr),
                          tbslas::NodeFieldFunctor<RealType,TreeType>(&tree_curr),
                          points_pos_all_nodes,
                          sdim,
                          timestep,
                          dt,
                          num_rk_step,
                          points_val_local_nodes);

  ////////////////////////////////////////////////////////////////////////
  // (3) set the computed values
  ////////////////////////////////////////////////////////////////////////
  NodeType* n_next = tree_curr.PostorderFirst();
  while (n_next != NULL) {
    if(!n_next->IsGhost() && n_next->IsLeaf()) break;
    n_next = tree_curr.PostorderNxt(n_next);
  }
  std::vector<NodeType*> nodes;
  while (n_next != NULL) {
    if (n_next->IsLeaf() && !n_next->IsGhost()) nodes.push_back(n_next);
    n_next = tree_curr.PostorderNxt(n_next);
  }

  int omp_p=omp_get_max_threads();
  pvfmm::Matrix<RealType> Mvalue(points_val_local_nodes.size()/num_points_per_node,num_points_per_node,&points_val_local_nodes[0],false);
  pvfmm::Matrix<RealType> Mcoeff(points_val_local_nodes.size()/num_points_per_node,Ncoeff);
  #pragma omp parallel for schedule(static)
  for(int pid=0;pid<omp_p;pid++){
    long a=(pid+0)*nodes.size()/omp_p;
    long b=(pid+1)*nodes.size()/omp_p;
    pvfmm::Matrix<RealType> Mi((b-a)*data_dof, Mvalue.Dim(1), &Mvalue[a*data_dof][0], false);
    pvfmm::Matrix<RealType> Mo((b-a)*data_dof, Mcoeff.Dim(1), &Mcoeff[a*data_dof][0], false);
    pvfmm::Matrix<RealType>::GEMM(Mo, Mi, M);
    for(long j=0;j<b-a;j++){
      memcpy(&(nodes[a+j]->ChebData()[0]), &Mo[j*data_dof][0], Ncoeff*data_dof*sizeof(RealType));
    }
  }

  //int tree_next_node_counter = 0;
  //while (n_next != NULL) {
  //  if (n_next->IsLeaf() && !n_next->IsGhost()) {
  //    // convert the function values at scaled points
  //    // to function values at first kind chebyshev point
  //    tbslas::NewPt2ChebPt<RealType>(
  //        &points_val_local_nodes[tree_next_node_counter*num_points_per_node*data_dof],
  //        cheb_deg, data_dof);
  //    pvfmm::cheb_approx<RealType, RealType>(
  //        &points_val_local_nodes[tree_next_node_counter*num_points_per_node*data_dof],
  //        cheb_deg,
  //        data_dof,
  //        &(n_next->ChebData()[0]));
  //    tree_next_node_counter++;
  //  }
  //  n_next = tree_curr.PostorderNxt(n_next);
  //}
  // pvfmm::Profile::Toc();
}

}  // namespace tbslas

#endif  // SRC_TREE_SEMILAG_TREE_H_
