// Server-side in-memory singleton store for assessment records
const globalStore: Map<string, any> = (global as any).__assessmentsStore || new Map<string, any>();
if (!(global as any).__assessmentsStore) {
  (global as any).__assessmentsStore = globalStore;
}

export function saveAssessment(id: string, data: any) {
  globalStore.set(id, data);
}

export function getAssessment(id: string) {
  return globalStore.get(id);
}
