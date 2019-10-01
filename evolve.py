'''
Basic Evolutionary framework (primarily scaffolding) to be used
for experimenting with simple problems and concepts
'''
import random
from typing import List, Optional, Tuple

GENERATION_SIZE: int = 20
MUTATION_RATE: float = 0.07


class Genotype:
    """
    Implements a basic genotype with a vector of genes as its genome.
    Can be inherited from and overriden to create more exciting Genotypes.
    """

    genes: List[float]

    def __init__(self, genes):
        self.genes = genes

    def clone(self):
        """
        Simply returns a new Genotype with the same genome.
        Can be overriden if the class is inherited with some other
        representation of the genome.
        """
        return Genotype(self.genes)

    def mutate(self, ranges: List[float], probability: float = 0.05) -> 'Genotype':
        # Define the default value with a check because it is not allowed in the function signature
        if ranges is None:
            ranges = [1.0 for gene in self.genes]
        if len(ranges) != len(self.genes):
            raise ValueError('ranges must be a vector with one range per gene in the genome')

        # Return a value in the range (-max_amplitude, max_amplitude)
        def difference_with_max_amplitude(max_amplitude: float) -> float:
            return -max_amplitude + random.random() * 2.0 * max_amplitude

        mutated_genes = [gene for gene in self.genes]
        for gene_index in range(0, len(self.genes)):
            if random.random() <= probability:
                mutated_genes[gene_index] += difference_with_max_amplitude(ranges[gene_index])

        return Genotype(mutated_genes)

    def procreate(self, other: 'Genotype', preference: float = 0.5):
        """
        Returns a new Genotype from mating self with another.
        Two default strategies are implemented: average and give_and_take.
        They can be chosen betweem, or this function can be entirely overriden.
        """
        if len(other.genes) != len(self.genes):
            raise ValueError('Genotypes must have same number of genes')
        return self.average_mating(other, preference)

    def average_mating(self, other: 'Genotype', preference: float = 0.5):
        """
        Averages the genes of the two individuals' genes at every position.
        Uses a weighted average, skewed towards self
        """
        child_genes = [gene for gene in self.genes]
        scaling_factor: float = (1.0 - preference)
        for gene_index in range(0, len(self.genes)):
            difference: float = other.genes[gene_index] - self.genes[gene_index]
            child_genes[gene_index] += scaling_factor * difference

        return Genotype(child_genes)

    def give_and_take_mating(self, other: 'Genotype', preference: float = 0.5):
        """
        Chooses each gene on random from the two parents.
        Is biased towards self with the preference weight
        """
        child_genes = [gene for gene in self.genes]
        for gene_index in range(0, len(self.genes)):
            if random.random() <= preference:
                child_genes[gene_index] = other.genes[gene_index]

        return Genotype(child_genes)


class Phenotype:

    genome: Genotype


class EvolutionRunner:

    def decode_genes(self, genes: List[Genotype]) -> List[Phenotype]:
        raise NotImplementedError('You need to implement some problem-specific way to interpret genes')

    def evaluate_fitness(self, cohort: Phenotype) -> float:
        raise NotImplementedError('You need to implement some problem-specific fitness evaluation')

    def translate_fitness_to_probability(self, fitness: float) -> float:
        """
        Does not translate fitness, but simply uses a linear scale where.
        Can be overridden to create more exciting probability functions, e.g. sigmoids or cutoffs.
        """
        return fitness

    def select_next_generation(self,
                               scored_cohort: List[Tuple[Phenotype, float]],
                               clone_weight: float = 1.0,
                               mutate_weight: float = 1.0,
                               mate_weight: float = 1.0
                               ) -> List[Genotype]:
        """
        implements a basic roulette selection mechanism, can be overridden to
        create more exciting selection mechanisms
        """
        def get_genome_from_scored_tuple(scored_phenotype: Tuple[Phenotype, float]) -> Genotype:
            return scored_phenotype[0].genome

        cummulative_scale: List[Tuple[float, Genotype]] = []
        probability_sum: float = 0.0
        for individual, fitness in scored_cohort:
            probability_sum += self.translate_fitness_to_probability(fitness)
            cummulative_scale += [(probability_sum, individual.genome)]

        def get_genome_by_roulette_value(roulette_value: float) -> Genotype:
            for upper_limit_for_selection, genome in cummulative_scale:
                if roulette_value <= upper_limit_for_selection:
                    return genome
            raise ValueError('roulette value is higher than highest limit in cummulative_scale')

        weight_sum: float = clone_weight + mutate_weight + mate_weight

        def create_child():
            roulette_value_for_selection_method: float = random.random() * weight_sum
            roulette_value_for_child_selection: float = random.random() * probability_sum
            genome = get_genome_by_roulette_value(roulette_value_for_child_selection)
            if roulette_value_for_selection_method <= clone_weight:
                return genome.clone()
            elif roulette_value_for_selection_method <= clone_weight + mutate_weight:
                return genome.mutate()
            else:
                roulette_value_for_partner_selection = random.random() * probability_sum
                partner_genome = get_genome_by_roulette_value(roulette_value_for_partner_selection)
                return genome.procreate(partner_genome)

        next_generation = [create_child() for i in range(0, GENERATION_SIZE)]
        return next_generation

    def evolution_loop(self: 'EvolutionRunner',
                       gene_pool: List[Genotype], *,
                       stop_at_fitness_limit: bool,
                       stop_at_iteration_limit: bool,
                       fitness_limit: float,
                       iteration_limit: int
                       ) -> None:
        """
        Runs an evolution process until either fitness limit or iteration limit is reached,
        based on what stop-criterin is selected.
        Uses functions on self to progress through the generations, and each of the functtions
        can be overridden to tweak the approach.
        """
        if stop_at_fitness_limit and fitness_limit is None:
            raise ValueError("fitness_limit is not supplied, despite stop_at_fitness_limit=True")
        if stop_at_iteration_limit and iteration_limit is None:
            raise ValueError("iteration_limit is not supplied, despite stop_at_iteration_limit=True")

        current_iteration: int = 0
        current_fitness: float = float("-inf")
        best_individual: Optional[Phenotype] = None

        while ((current_iteration < iteration_limit or not stop_at_iteration_limit)
               and (current_fitness < fitness_limit or not stop_at_fitness_limit)):
            cohort: List[Phenotype] = self.decode_genes(gene_pool)
            scored_cohort: List[Tuple[Phenotype, float]] = []
            generation_fitness: float = float("-inf")
            generation_leader: Optional[Phenotype] = None

            for individual in cohort:
                fitness = self.evaluate_fitness(individual)
                if fitness > generation_fitness:
                    generation_fitness = fitness
                    generation_leader = individual
                    if fitness > current_fitness:
                        current_fitness = fitness
                        best_individual = individual
                scored_cohort += [(individual, fitness)]

            gene_pool = self.select_next_generation(scored_cohort)
            current_iteration += 1

            print('This generation: ', generation_fitness, 'for phenotype ', generation_leader)
            print('Best individual: ', current_fitness, 'for phenotype ', best_individual)
