import numpy as np
from scipy.linalg import inv
from js.data.plyParse import PlyParse
import mayavi.mlab as mlab
import os.path, re
import subprocess as subp
from js.geometry.rotations import Quaternion
from js.utils.plot.colors import colorScheme
import argparse, sys
from helpers import *

def EvalError(q_gt, t_gt, q, t):
  err_a = q_gt.angleTo(q)*180./np.pi
  err_t = np.sqrt(((t_gt-t)**2).sum())
  return err_a, err_t

cfgNYU = {"name":"nyu", "lambdaS3": [60, 70, 80], "lambdaR3": 0.3}

cfg = cfgNYU

loadCached = True
stopToShow = True
showUntransformed = False
applyBB = True
applyEGI = False
applyMM = False
applyICP = True
loadGlobalsolutionforICP = True
useSurfaceNormalsInICP = True

#if cfg["name"] == "nyu":

parser = argparse.ArgumentParser(description = 'randomly sample two renders and align them')
parser.add_argument('-i','--input',
    default="../data/bunny_rnd/bun_zipper.ply", \
    help='path to input pointcloud .ply file')
parser.add_argument('-o','--output',
    default="./", \
    help='path to output .json results file')
parser.add_argument('-p','--prefix',
    default="out", \
    help='prefix for temp files')
parser.add_argument('-a','--angle', default=30., help='magnitude of random angle')
parser.add_argument('-t','--translation', default=1., help='magnitude of random translation')
parser.add_argument('-m','--minOverlap', default=70., help='min overlap between sampled point clouds')
cmdArgs = parser.parse_args()

resultsPath = cmdArgs.output + "/" + os.path.splitext(os.path.split(cmdArgs.input)[1])[0]
outputPath = "./" + cmdArgs.prefix
nameA = cmdArgs.prefix+"_A"
nameB = cmdArgs.prefix+"_B"
transformationPathBB = '{}_{}_BB.csv'.format(nameA, nameB)
transformationPathBBICP = '{}_{}_BB_ICP.csv'.format(nameA, nameB)
transformationPathICP = '{}_{}_ICP.csv'.format(nameA, nameB)
transformationPathEGI = '{}_{}_EGI.csv'.format(nameA, nameB)
transformationPathMM = '{}_{}_MM.csv'.format(nameA, nameB)
transformationPathMMICP = '{}_{}_MM_ICP.csv'.format(nameA, nameB)

runBB = True
runBBICP = True
runMM = True
runMMICP = True
runICP = True

args = ['../build/bin/renderPcFromPc',
    '-i ' + cmdArgs.input,
    '-o ' + outputPath,
    '-a {}'.format(cmdArgs.angle), 
    '-t {}'.format(cmdArgs.translation), 
    '-m {}'.format(cmdArgs.minOverlap), 
    ]
print " ".join(args)
if subp.call(" ".join(args), shell=True) == 0:
  scanApath = outputPath+"_A_angle_{}_translation_{}.ply".format(\
      int(cmdArgs.angle), int(cmdArgs.translation))
  scanBpath = outputPath+"_B_angle_{}_translation_{}.ply".format(\
      int(cmdArgs.angle), int(cmdArgs.translation))
  # load gt
  gtPath = outputPath+"_angle_{}_translation_{}_TrueTransformation.csv".format(\
      int(cmdArgs.angle), int(cmdArgs.translation))
  q_gt, t_gt, overlap = LoadTransformationAndOverlap(gtPath)
  results = {"GT":{"q":q_gt.q.tolist(), "t":t_gt.tolist(),
    "overlap":overlap}, "version":"1.1"}
  if runBB:
    q,t = RunBB(cfg, scanApath, scanBpath, transformationPathBB)
    err_a, err_t = EvalError(q_gt, t_gt, q, t)
    print "BB: {} deg {} m".format(err_a, err_t)
    results["BB"] = {"err_a":err_a, "err_t":err_t, "q":q.q.tolist(), "t":t.tolist()}

  if runBBICP:
    q,t = RunICP(scanApath, scanBpath, transformationPathBBICP,
        useSurfaceNormalsInICP, transformationPathBB)
    err_a, err_t = EvalError(q_gt, t_gt, q, t)
    print "BB+ICP: {} deg {} m".format(err_a, err_t)
    results["BB+ICP"] = {"err_a":err_a, "err_t":err_t, "q":q.q.tolist(), "t":t.tolist()}

  if runMM:
    q,t = RunMM(scanApath, scanBpath, transformationPathMM)
    err_a, err_t = EvalError(q_gt, t_gt, q, t)
    print "MM: {} deg {} m".format(err_a, err_t)
    results["MM"] = {"err_a":err_a, "err_t":err_t, "q":q.q.tolist(), "t":t.tolist()}

  if runMMICP:
    q,t = RunICP(scanApath, scanBpath, transformationPathMMICP,
        useSurfaceNormalsInICP, transformationPathMM)
    err_a, err_t = EvalError(q_gt, t_gt, q, t)
    print "MM+ICP: {} deg {} m".format(err_a, err_t)
    results["MM+ICP"] = {"err_a":err_a, "err_t":err_t, "q":q.q.tolist(), "t":t.tolist()}

  if runICP:
    q,t = RunICP(scanApath, scanBpath, transformationPathICP,
        useSurfaceNormalsInICP)
    err_a, err_t = EvalError(q_gt, t_gt, q, t)
    print "ICP: {} deg {} m".format(err_a, err_t)
    results["ICP"] = {"err_a":err_a, "err_t":err_t, "q":q.q.tolist(), "t":t.tolist()}

  import json, time
#  print results
#  import ipdb
#  ipdb.set_trace()
  stamp = "{}".format(int(np.floor(time.time()*1e3)))
  json.dump(results, open(resultsPath+"_"+stamp+'_results.json','w'))
  print "done"

  sys.exit(0)
sys.exit(1)