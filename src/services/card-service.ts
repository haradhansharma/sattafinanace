import type { Card } from '../types';
import { mockCards } from '../mock-data/cards';
// import { apiBridge } from './api-bridge'; // Uncomment when backend ready

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

export const cardService = {
  async getCards(): Promise<Card[]> {
    await delay(50);
    // TODO: Replace with: return apiBridge.get('/cards');
    return [...mockCards];
  },

  async getCardById(id: string): Promise<Card | undefined> {
    await delay(30);
    // TODO: Replace with: return apiBridge.get(`/cards/${id}`);
    return mockCards.find(c => c.id === id);
  },

  async createCard(data: Omit<Card, 'id' | 'createdAt' | 'updatedAt'>): Promise<Card> {
    await delay(50);
    // TODO: Replace with: return apiBridge.post('/cards', data);
    return {
      ...data,
      id: `card_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  },

  async updateCard(id: string, data: Partial<Card>): Promise<Card> {
    await delay(50);
    // TODO: Replace with: return apiBridge.put(`/cards/${id}`, data);
    const card = mockCards.find(c => c.id === id);
    if (!card) throw new Error('Card not found');
    return { ...card, ...data, updatedAt: new Date().toISOString() };
  },

  async deleteCard(id: string): Promise<void> {
    await delay(50);
    // TODO: Replace with: return apiBridge.delete(`/cards/${id}`);
    console.log(`Deleted card ${id}`);
  },
};
