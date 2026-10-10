import sys, os, json
SCR = sys.argv[1]
sys.path.insert(0, os.path.join(SCR, "dl_pycge", "pycge-master"))
os.environ["PATH"] = os.path.join(SCR, r"dl_ipopt\ipopt\Ipopt-3.14.20-win64-msvs2022-md\bin") + os.pathsep + os.environ["PATH"]
from pyomo.environ import value
from pycge.examples.stdcge_model_def import StdModelDef
from pycge.pycge import PyCGE
cge = PyCGE(StdModelDef())
cge.model_data(os.path.join(SCR, "dl_pycge", "pycge-master", "pycge", "data", "stdcge_data_dir"))
cge.model_instance("pf", "LAB")            # same numeraire as stdcge.gms
# Walras: with the numeraire fixed one equation is redundant; Ipopt needs a square system, so set aside the
# balance of payments and check afterwards that it still holds.
cge.base.eqepsilon.deactivate()
cge.model_calibrate("ipopt")
cge.model_sim()
cge.sim.eqepsilon.deactivate()
for i in ("BRD", "MLK"): cge.model_modify_sim("taum", i, 0)
cge.model_solve("ipopt")
def grab(m):
    out = {}
    for v in m.component_objects(ctype=__import__("pyomo.environ", fromlist=["Var"]).Var):
        for idx in v:
            out[f"{v.name}[{idx}]" if idx is not None else v.name] = value(v[idx])
    return out
bop = lambda m: value(sum(m.pWe[i]*m.E[i] for i in m.i) + m.Sf - sum(m.pWm[i]*m.M[i] for i in m.i))
res = {"bop_residual_base": bop(cge.base), "bop_residual_sim": bop(cge.sim), "solver_base": str(cge.base_results.solver.termination_condition), "solver_sim": str(cge.sim_results.solver.termination_condition),
       "base": grab(cge.base), "sim": grab(cge.sim)}
json.dump(res, open(os.path.join(SCR, "hosoe", "pycge_results.json"), "w"), indent=1)
print("BOP residual base/sim:", res["bop_residual_base"], res["bop_residual_sim"]); print(res["solver_base"], res["solver_sim"], len(res["base"]), "variables")
