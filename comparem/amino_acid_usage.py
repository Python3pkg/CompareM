###############################################################################
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program. If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

__author__ = 'Donovan Parks'
__copyright__ = 'Copyright 2014'
__credits__ = ['Donovan Parks']
__license__ = 'GPL3'
__maintainer__ = 'Donovan Parks'
__email__ = 'donovan.parks@gmail.com'

import logging
import ntpath
from collections import defaultdict

from comparem.seq_io import SeqIO
from comparem.parallel import Parallel


class AminoAcidUsage(object):
    """Calculate amino acid usage over a set of genomes."""

    def __init__(self):
        """Initialization."""
        self.logger = logging.getLogger()

        # class variables used by consumer function
        # in a producer/consumer multiprocessing
        # framework
        self.genome_aa_usage = dict()
        self.aa_set = set()

    def amino_acid_usage(self, seqs):
        """ Calculate amino acid usage within sequences.

        Parameters
        ----------
        seqs : dict[seq_id] -> seq
            Sequences indexed by sequence id.

        Returns
        -------
        dict : dict[aa] -> count
            Occurrence of each amino acid.
        """
        aa_usage = defaultdict(int)

        for _seqId, seq in seqs.iteritems():
            for aa in seq:
                if aa != '*':
                    aa = aa.upper()
                    aa_usage[aa] += 1

        return aa_usage

    def _producer(self, gene_file):
        """Calculates amino acid usage of a genome.

        This function is intended to be used as a producer
        within a producer/consumer multiprocessing framework.
        It calculates the amino acid usage for a single genome
        and returns the results for consumption by the
        consumer function.

        Parameters
        ----------
        gene_file : str
            Fasta file containing amino acid sequences.

        Returns
        -------
        str
           Unique identifier of genome.
        dict : dict[aa] -> count
            Occurrence of each amino acid.
        """

        genome_id = ntpath.basename(gene_file)
        genome_id = genome_id[0:genome_id.rfind('.')]

        seq_io = SeqIO()
        seqs = seq_io.read_fasta(gene_file)
        aa_usage = self.amino_acid_usage(seqs)

        return [genome_id, aa_usage]

    def _consumer(self, data):
        """Consume results from producer processes.

        This function is intended to be used as a
        consumer within a producer/consumer multiprocessing
        framework. It stores the amino acid usage for each
        genome into a dictionary and determines the set
        of amino acids observed over all genomes.

         Parameters
        ----------
        data : list -> [genome_id, aa_usage]
            Unique id of a genome followed by a dictionary
            indicating its amino acid usage.
        """
        genome_id, aa_usage = data

        self.aa_set.update(aa_usage.keys())
        self.genome_aa_usage[genome_id] = aa_usage

    def run(self, gene_files, cpus):
        """Calculate amino acid usage over a set of genomes.

        Parameters
        ----------
        gene_files : list
            Fasta files containing called genes.
        cpus : int
            Number of cpus to use.

        Returns
        -------
        dict of dict : dict[genome_id][aa] -> count
           Amino acid usage of each genome.
        set
           Set with all identified amino acids.
        """

        self.logger.info('  Calculating amino acid usage for each genome:')

        parallel = Parallel()
        parallel.run(self._producer, self._consumer, gene_files, cpus)

        return self.genome_aa_usage, self.aa_set