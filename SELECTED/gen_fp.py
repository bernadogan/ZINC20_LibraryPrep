#!/usr/bin/env python

import sys

import h5py
import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdMolDescriptors as rdmd
from tqdm import tqdm
from functools import wraps
from time import time
from itertools import islice

def timing(f):
    """
    Decorator to measure execution time, adapted from
    # https://medium.com/pythonhive/python-decorator-to-measure-the-execution-time-of-methods-fa04cb6bb36d
    # https://codereview.stackexchange.com/questions/169870/decorator-to-measure-execution-time-of-a-function
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        print(f.__name__, f"Elapsed time: {end - start:.2f} sec")
        return result

    return wrapper


@timing
def make_np_array(lst, dtype=np.float32):
    """
    Convert a list to a numpy array
    :param lst: input list
    :param dtype: data type
    :return: output array
    """
    return np.array(lst, dtype=dtype)


@timing
def save_data(fp_array, smiles_list, name_list, outfile_name):
    """
    Write the fingerprints to an hdf5 file
    :param fp_array: numpy array with fingerprints
    :param smiles_list: list of SMILES
    :param name_list: list of molecule names
    :param outfile_name: output file name
    :return: None
    """
    h5f = h5py.File(outfile_name, 'w')
    dt = h5py.special_dtype(vlen=bytes)
    h5f.create_dataset('fp_list', data=fp_array)
    h5f.create_dataset('smiles_list', (len(smiles_list), 1), dt, smiles_list)
    h5f.create_dataset('name_list', (len(name_list), 1), dt, name_list)
    h5f.close()


@timing
def generate_fingerprints(infile_name):
    """
    Generate fingerprints from an input file, currently generates a 256 bit morgan fingerprint
    :param infile_name: input file name
    :return: lists with fingerprints, SMILES, and molecule names
    """
    ifs = open(infile_name)
    fp_list = []
    smiles_list = []
    name_list = []
    for line in tqdm(islice(ifs, 1, None)):
        toks = line.strip().split(" ")
        if len(toks) >= 2:
            smiles = toks[0]
            name = toks[1]
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                fp = rdmd.GetMorganFingerprintAsBitVect(mol, 3, 1024)
                arr = np.zeros((1,))
                DataStructs.ConvertToNumpyArray(fp, arr)
                fp_list.append(arr)
                smiles_list.append(smiles.encode("ascii", "ignore"))
                name_list.append(name.encode("ascii", "ignore"))
    return fp_list, smiles_list, name_list


@timing
def main(input_smiles_file, output_fp_file):
    """
    Generate fingerprints and write to an hdf5 file
    :return:
    """
    fp_list, smiles_list, name_list = generate_fingerprints(input_smiles_file)
    outfile_name = output_fp_file
    fp_array = make_np_array(fp_list)
    save_data(fp_array, smiles_list, name_list, outfile_name)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} infile.smi outfile.h5")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
