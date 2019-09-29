'''
Basic Evolutionary framework (primarily scaffolding) to be used
for experimenting with simple problems and concepts
'''
from typing import List, Optional, Tuple


class Genotype:
    pass


class Phenotype:
    pass


class EvolutionRunner:

    def decode_genes(self, genes: List[Genotype]) -> List[Phenotype]:
        pass

    def evaluate_fitness(self, cohort: Phenotype) -> float:
        pass

    def select_next_generation(self, scored_cohort: List[Tuple[Phenotype, float]]) -> List[Genotype]:
        pass

    def evolution_loop(self: 'EvolutionRunner',
                       gene_pool: List[Genotype], *,
                       stop_at_fitness_limit: bool,
                       stop_at_iteration_limit: bool,
                       fitness_limit: float,
                       iteration_limit: int
                       ) -> None:
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
