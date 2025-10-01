'use client';
import { useEffect, useState } from 'react';

export interface InventoryItem {
  part_number?: string;
  description: string;
  expected: number;
  scanned: number;
}

export interface InventoryState {
  [sapArticle: string]: InventoryItem;
}

export function useInventoryStream(projectId: string, category: string) {
  const [inventory, setInventory] = useState<InventoryState>({});

  useEffect(() => {
    if (!projectId || !category) return;

    const es = new EventSource(`https://isa-nged.onrender.com/api/sse/${encodeURIComponent(projectId)}/${encodeURIComponent(category)}`);

    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        // Create a new object reference to ensure React triggers a re-render
        setInventory({ ...data });
      } catch (e) {
        console.error('Failed to parse SSE data:', e);
      }
    };

    es.onerror = () => {
      console.error('EventSource failed.');
      // Opcional: implementar lógica de reconexión aquí
    };

    return () => {
      es.close();
    };
  }, [projectId, category]);

  return { inventory, setInventory };
}
