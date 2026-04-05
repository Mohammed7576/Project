import { ASTMutator } from './ASTMutator';
import { SuccessValidator } from '../utils/SuccessValidator';

export interface Individual {
  payload: string;
  score: number;
  status: string;
}

export class IslandManager {
  private mutator = new ASTMutator();
  private validator = new SuccessValidator();
  private population: string[] = [];
  private baseSeeds: string[] = [];
  private populationSize: number;

  constructor(basePayloads: string[], populationSize = 12) {
    this.baseSeeds = basePayloads;
    this.populationSize = populationSize;
    
    if (basePayloads.length > 0) {
      this.population = this._shuffle(basePayloads).slice(0, Math.min(basePayloads.length, populationSize));
    }
  }

  public async evolveGeneration(
    sendRequest: (payload: string) => Promise<{ body: string, status: number }>,
    onIndividualResult: (ind: Individual) => void
  ): Promise<string | null> {
    if (this.population.length === 0) {
      if (this.baseSeeds.length > 0) {
        this.population = this._shuffle(this.baseSeeds).slice(0, Math.min(this.baseSeeds.length, this.populationSize));
      } else {
        return null;
      }
    }

    const scoredPopulation: Individual[] = [];

    for (const payload of this.population) {
      const response = await sendRequest(payload);
      const { score, status } = this.validator.validate(response.body, response.status);
      
      const ind = { payload, score, status };
      onIndividualResult(ind);
      scoredPopulation.push(ind);
      
      if (score >= 1.0) {
        return payload;
      }
    }

    scoredPopulation.sort((a, b) => b.score - a.score);
    const survivors = scoredPopulation.filter(p => p.score >= 0.4).map(p => p.payload);
    
    this.population = this._generateNextGen(survivors);
    return null;
  }

  private _generateNextGen(survivors: string[]): string[] {
    const nextGen: string[] = [];
    
    if (survivors.length === 0) {
      return this._shuffle(this.baseSeeds).slice(0, Math.min(this.baseSeeds.length, this.populationSize));
    }

    // Elitism
    nextGen.push(survivors[0]);
    
    while (nextGen.length < this.populationSize) {
      if (Math.random() < 0.3) {
        nextGen.push(this.baseSeeds[Math.floor(Math.random() * this.baseSeeds.length)]);
      } else {
        const parent = survivors[Math.floor(Math.random() * survivors.length)];
        const child = this.mutator.mutate(parent);
        if (!nextGen.includes(child)) {
          nextGen.push(child);
        }
      }
    }
    
    return nextGen;
  }

  private _shuffle<T>(array: T[]): T[] {
    return [...array].sort(() => Math.random() - 0.5);
  }
}
