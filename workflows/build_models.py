"""Builds the community models."""

from os import makedirs
from os.path import isfile
import micom
from micom import Community
import pandas as pd
from micom.workflows import workflow

micom.logger.file_logger("micom.log")
logger = micom.logger.logger
try:
    max_procs = snakemake.threads
except NameError:
    max_procs = 20

makedirs("data/models", exist_ok=True)

taxonomy = pd.read_csv("data/genera.csv").query("relative > 1e-3")
taxonomy["file"] = taxonomy.file.apply(
    lambda ids: ["data/agora/" + i for i in ids.split("|")]
)
taxonomy["name"] = taxonomy.genus
assert not taxonomy.name.str.contains(" ").any()
taxonomy = taxonomy.rename(columns={"name": "id", "reads": "abundance"})

diet = pd.read_csv("data/western_diet.csv")
diet.index = diet.reaction = diet.reaction.str.replace("_e", "_m")
diet = diet.flux * diet.dilution


def build_and_save(args):
    s, tax = args
    filename = "data/models/" + s + ".pickle"
    if isfile(filename):
        return
    com = Community(tax, id=s, progress=False)
    ex_ids = [r.id for r in com.exchanges]
    logger.info(
        "%d/%d import reactions found in model.",
        diet.index.isin(ex_ids).sum(),
        len(diet),
    )
    com.medium = diet[diet.index.isin(ex_ids)]
    com.to_pickle(filename)


samples = taxonomy.samples.unique()
args = [(s, taxonomy[taxonomy.samples == s]) for s in samples]
workflow(build_and_save, args, max_procs)
