#!/usr/bin/env python
# coding: utf-8

############## PART 1: IMPORT STATEMENTS ##############

import pandas as pd
import numpy as np
from CAML_generic_automl_classes import process_glycans, checkValidity, fill, makeComplement


############## PART 2: CONSTRAINT HELPER FUNCTIONS ##############

def clean_constraints(constraint_seq, sequence_type):
    """cleans exact sequences in constraints to conform with other rules
    Parameters
    ----------
    constraint_seq : str (if nucleic_acid or protein; else list of strs for glycans) representing exact sequence match
    sequence_type : str, either 'nucleic_acid', 'peptide', or 'glycan'

    Returns
    -------
    constraint_seq : cleaned constraint sequence
    """

    seqs = [constraint_seq]
    if sequence_type == 'glycan':
        seqs = process_glycans(seqs)
        
    # fix Us to Ts in nucleic acids
    if sequence_type == 'nucleic_acid':
        seqs = [s.replace("U", "T") for s in seqs]

    checkValidity(seqs, sequence_type)

    # fill gaps
    seqs = [fill(seq, sequence_type) for seq in seqs]

    return(seqs[0])

def enforce_bio_constraints(seq, bio_constraints):
    """cleans exact sequences in constraints to conform with other rules
    Parameters
    ----------
    seq : str (if nucleic_acid or protein; else list of strs for glycans) representing input sequence string
    bio_constraints : list of constraint tuples generated by read_bio_constraints, with each tuple containing the following information
        constraint type, exact_seq, start_position, end_position, comp_start, comp_end
    
    Returns
    -------
    seq : str (if nucleic_acid or protein; else list of strs for glycans) representing sequence satisfying constraints
    """

    if bio_constraints:
        for idx, (constraint_type, exact_seq, start, end, comp_start, comp_end) in enumerate(bio_constraints, 1):   
            if constraint_type == "exact_sequence":
                assert start <= len(seq) and start >= 0, "Start position outside of possible sequence positions in constraint {}".format(idx)
                assert end <= len(seq) and end >= 0, "End position outside of possible sequence positions in constraint {}".format(idx)
                assert start <= end, "End position before start position in constraint {}".format(idx)
                seq = seq[:start-1] + exact_seq + seq[end:]
            if constraint_type == "reverse_complement":
                assert comp_start <= len(seq) and comp_start >= 0, "Complement start position outside of possible sequence positions in constraint {}".format(idx)
                assert comp_end <= len(seq) and comp_end >= 0, "Complement end position outside of possible sequence positions in constraint {}".format(idx)
                assert comp_start <= comp_end, "Complement end position before complement start position in constraint {}".format(idx)
                rev_comp = makeComplement(seq[start-1:end], rev = True)
                seq = seq[:comp_start-1] + rev_comp + seq[comp_end:]

    return seq

def read_bio_constraints(file_path, alph, sequence_type):
    """read in file with constraint files
    note: column headers must be exactly: constraint_type, exact_seq, start_position, end_position, comp_start, comp_end
    Parameters
    ----------
    file_path : str representing path to .csv, .xls, or .xlsx file containing constraints
    alph : list representation of alphabet

    Returns
    -------
    b_constraints : list of constraint tuples generated by read_bio_constraints, with each tuple containing the following information
        constraint type, exact_seq, start_position, end_position, comp_start, comp_end
        """

    if not file_path:
        return None
    b_constraints = []
    if '.csv' in file_path:
        df = pd.read_csv(file_path, sep = ',')
    elif '.xls' in file_path:
        df = pd.read_excel(file_path)
    elif '.xlsx' in file_path:
        df = pd.read_excel(file_path, engine='openpyxl')
    if df.empty:
        return None
    for col in ['start_position', 'end_position', 'comp_start', 'comp_end']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].replace(np.nan, 0, regex=True)
        df[col] = df[col].astype(int)

    for i in range(df.shape[0]):
        b_constraints.append((df['constraint_type'][i],df['exact_seq'][i],df['start_position'][i],df['end_position'][i],df['comp_start'][i],df['comp_end'][i]))
    for idx, constraint in enumerate(b_constraints, 1):
        assert constraint[0] == 'exact_sequence' or constraint[0] == 'reverse_complement', 'Constraint type must be "exact_sequence" or "reverse_complement" in constraint {}.'.format(idx)
        if constraint[0] == 'exact_sequence':
            new_constr = clean_constraints(constraint[1], sequence_type)
            constraint = (constraint[0], new_constr, constraint[2], constraint[3], constraint[4], constraint[5])
            b_constraints[idx-1] = constraint
            for nt in constraint[1]:    
                assert nt in alph, 'Exact sequence has illegal character "{0}" in constraint {1}.'.format(nt, idx)
            assert constraint[3] - constraint[2] + 1 == len(constraint[1]), 'Positions do not match exact sequence length in constraint {}.'.format(idx)
        if constraint[0] == 'reverse_complement': 
            assert constraint[5] - constraint[4] == constraint [3] - constraint[2], 'Lengths of complementary regions do not match in constraint {}.'.format(idx) 
        if constraint[0] == 'reverse_complement': 
            assert constraint[4] - constraint [3] >=0, 'Start of second region occurs before the end of the first region, please correct constraint {}.'.format(idx)
    
    return b_constraints

############## END OF FILE ##############