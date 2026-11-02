// Server-side in-memory singleton store for assessment records
const globalStore: Map<string, any> = (global as any).__assessmentsStore || new Map<string, any>();
if (!(global as any).__assessmentsStore) {
  (global as any).__assessmentsStore = globalStore;
}

export function saveAssessment(id: string, data: any) {
  globalStore.set(id, {
    ...data,
    updatedAt: new Date().toISOString(),
  });
}

export function getAssessment(id: string) {
  return globalStore.get(id);
}

export function getUserAssessments(userIdOrEmail: string): any[] {
  const cleanId = (userIdOrEmail || "").trim().toLowerCase();
  const results: any[] = [];

  for (const record of globalStore.values()) {
    const rUserId = (record.userId || "").trim().toLowerCase();
    const rUserEmail = (record.userEmail || "").trim().toLowerCase();
    const rEmail = (record.user?.email || "").trim().toLowerCase();

    if (
      !cleanId ||
      rUserId === cleanId ||
      rUserEmail === cleanId ||
      rEmail === cleanId
    ) {
      results.push(record);
    }
  }

  // Sort newest first
  return results.sort((a, b) => {
    const timeA = new Date(a.createdAt || a.updatedAt || 0).getTime();
    const timeB = new Date(b.createdAt || b.updatedAt || 0).getTime();
    return timeB - timeA;
  });
}

export function deleteAssessment(id: string): boolean {
  return globalStore.delete(id);
}

export function getDemoAssessments(userEmail: string = "demo@reloop.ai"): any[] {
  return [];
}
