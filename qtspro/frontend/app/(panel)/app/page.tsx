'use client';
import React, { useState, useEffect } from 'react';
import { useInventoryStream, InventoryState, InventoryItem } from './hooks/usePOStream';

const EditableQuantityCell = ({ 
  item,
  categoryName,
  projectId,
}: {
  item: any;
  categoryName: string;
  projectId: string;
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [quantity, setQuantity] = useState(item.scanned);

  useEffect(() => {
    // Update local state if server-side value changes
    setQuantity(item.scanned);
  }, [item.scanned]);

  const handleUpdate = async () => {
    setIsEditing(false);
    const newQuantity = parseInt(quantity, 10);

    if (isNaN(newQuantity) || newQuantity < 0) {
      setQuantity(item.scanned); // Revert
      alert('Invalid quantity. Must be a non-negative number.');
      return;
    }

    if (newQuantity === item.scanned) return; // No change

    const payload = {
      project_id: projectId,
      category: categoryName,
      sap_article: item.sapArticle,
      new_quantity: newQuantity,
    };

    try {
      const response = await fetch('http://localhost:8000/api/inventory/update_quantity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const result = await response.json();
        alert(`Error: ${result.detail || 'Failed to update quantity.'}`);
        setQuantity(item.scanned); // Revert on failure
      }
      // On success, SSE will update the state, which triggers the useEffect
    } catch (error) {
      alert('Network error while updating quantity.');
      setQuantity(item.scanned); // Revert on failure
    }
  };

  if (isEditing) {
    return (
      <input
        type="number"
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        onBlur={handleUpdate}
        onKeyDown={(e) => e.key === 'Enter' && handleUpdate()}
        style={{ width: '60px', textAlign: 'center', padding: '4px', border: '1px solid #007bff', borderRadius: '4px' }}
        autoFocus
      />
    );
  }

  return (
    <div onClick={() => setIsEditing(true)} style={{ cursor: 'pointer', padding: '4px', minWidth: '60px' }}>
      {quantity}
    </div>
  );
};

const getStatus = (expected: number, scanned: number) => {
  if (expected === 0 && scanned > 0) return { text: 'NOT IN BOM', color: '#f0ad4e' };
  if (scanned === 0) return { text: 'PENDING', color: '#777' };
  if (scanned < expected) return { text: 'SHORTAGE', color: '#d9534f' };
  if (scanned === expected) return { text: 'MATCH', color: '#5cb85c' };
  if (scanned > expected) return { text: 'EXCESS', color: '#f0ad4e' };
  return { text: 'N/A', color: '#777' };
};

const BomUploader = ({ projectId, category }: { projectId: string; category: string; }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setMessage('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('Please select a file first.');
      return;
    }

    setIsUploading(true);
    setMessage(`Uploading ${file.name}...`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`http://localhost:8000/api/bom/upload/${projectId}/${category}`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setMessage(`Success: ${result.items_loaded} items loaded for PO ${result.po}.`);
      } else {
        setMessage(`Error: ${result.error}`);
      }
    } catch (error) {
      setMessage('Network error during upload.');
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px', marginTop: '2rem', backgroundColor: '#f9f9f9' }}>
            <h3>Upload BOM for: {projectId} [{category}]</h3>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={isUploading || !file} style={{ marginLeft: '1rem', padding: '0.5rem 1rem' }}>
        {isUploading ? 'Uploading...' : 'Upload'}
      </button>
      {message && <p style={{ marginTop: '1rem', fontStyle: 'italic' }}>{message}</p>}
    </div>
  );
};

const ClassificationModal = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  item 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  onConfirm: (correctSapArticle: string) => void; 
  item: any; 
}) => {
  const [correctSapArticle, setCorrectSapArticle] = useState('');

  useEffect(() => {
    if (!isOpen) {
      setCorrectSapArticle('');
    }
  }, [isOpen]);

  if (!isOpen || !item) return null;

  const handleConfirm = () => {
    if (correctSapArticle.trim()) {
      onConfirm(correctSapArticle.trim());
    } else {
      alert('Please enter the correct SAP Article.');
    }
  };

  return (
    <div style={styles.modalOverlay}>
      <div style={styles.modalContent}>
        <h2 style={{ marginTop: 0 }}>Classify Item</h2>
        <p>
          Classifying item with scanned code: <strong>{item.sapArticle}</strong>
        </p>
        <p>
          Scanned Quantity: <strong>{item.scanned}</strong>
        </p>
        <div style={{ marginTop: '1rem' }}>
          <label htmlFor="sap-input" style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>
            Enter Correct SAP Article:
          </label>
          <input
            id="sap-input"
            type="text"
            value={correctSapArticle}
            onChange={(e) => setCorrectSapArticle(e.target.value)}
            style={{ width: '100%', padding: '0.5rem', fontSize: '1rem', border: '1px solid #ccc', borderRadius: '4px' }}
            placeholder="e.g., 12345678"
          />
        </div>
        <div style={styles.modalActions}>
          <button onClick={onClose} style={styles.buttonSecondary}>Cancel</button>
          <button onClick={handleConfirm} style={styles.buttonPrimary}>Confirm Classification</button>
        </div>
      </div>
    </div>
  );
};

const ConfirmationModal = ({ isOpen, onClose, onConfirm, itemName }: { isOpen: boolean; onClose: () => void; onConfirm: () => void; itemName: string; }) => {
  if (!isOpen) return null;

  return (
    <div style={styles.modalOverlay}>
      <div style={styles.modalContent}>
        <h2 style={{ marginTop: 0 }}>Confirm Reset</h2>
                                <p style={{ margin: '1rem 0' }}>Are you sure you want to reset all data for '<strong>{itemName}</strong>'? This action cannot be undone.</p>
        <div style={styles.modalActions}>
          <button onClick={onClose} style={styles.buttonSecondary}>Cancel</button>
          <button onClick={onConfirm} style={styles.buttonDanger}>Confirm Reset</button>
        </div>
      </div>
    </div>
  );
};

const CATEGORIES = ["CCTV", "CX", "FIRE & BURG ALARM"];
const PROJECT_MODES = [
  { value: "PROJ-DEMO", label: "PO Mode" },
  { value: "Inventory", label: "Inventory Mode" },
  { value: "BOM", label: "BOM Mode" },
  { value: "MAC_REGISTRY", label: "MAC Registry" }
];

const ProjectManager = ({ 
  projectId, 
  setProjectId, 
  category, 
  setCategory, 
  onResetClick 
}: { 
  projectId: string, 
  setProjectId: (id: string) => void, 
  category: string, 
  setCategory: (cat: string) => void, 
  onResetClick: () => void 
}) => {
  const [feedbackMessage, setFeedbackMessage] = useState('');

  const handleLoad = () => {
    setFeedbackMessage(`Loaded: ${projectId} [${category}]`);
    setTimeout(() => setFeedbackMessage(''), 3000);
  };

  return (
    <div style={{ margin: '1rem 0', display: 'flex', flexDirection: 'column', gap: '1rem', border: '1px solid #ddd', padding: '1rem', borderRadius: '8px' }}>
      <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
        <label htmlFor="project-mode-select" style={{fontWeight: 'bold'}}>Mode:</label>
        <select 
          id="project-mode-select" 
          value={projectId} 
          onChange={e => setProjectId(e.target.value)} 
          style={{padding: '0.5rem', minWidth: '150px'}}
        >
          {PROJECT_MODES.map(mode => <option key={mode.value} value={mode.value}>{mode.label}</option>)}
        </select>
        <label htmlFor="category-select" style={{fontWeight: 'bold'}}>Category:</label>
        <select id="category-select" value={category} onChange={e => setCategory(e.target.value)} style={{padding: '0.5rem'}}>
          {CATEGORIES.map(cat => <option key={cat} value={cat}>{cat}</option>)}
        </select>
        <button onClick={handleLoad} style={styles.buttonPrimary}>Load</button>
      </div>
      <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
        <button onClick={onResetClick} style={styles.buttonDanger}>Reset Current</button>
        <button onClick={() => {
          if (projectId && category) {
            window.open(`http://localhost:8000/api/export/${projectId}/${category}`, '_blank');
          }
        }} style={styles.buttonSecondary}>Export to Excel</button>
        {feedbackMessage && <span style={{ marginLeft: 'auto', fontStyle: 'italic', color: '#5cb85c' }}>{feedbackMessage}</span>}
      </div>
    </div>
  );
};

export default function PanelPage() {
  const [projectId, setProjectId] = useState('BOM');
  const [category, setCategory] = useState(CATEGORIES[0]);
  const { inventory } = useInventoryStream(projectId, category);
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);
  const [isClassificationModalOpen, setIsClassificationModalOpen] = useState(false);
  const [itemToClassify, setItemToClassify] = useState<any>(null);

  const handleResetCurrent = () => {
    setIsResetModalOpen(true);
  };

  const handleDeleteItem = async (item: any) => {
    if (window.confirm(`Are you sure you want to permanently delete '${item.description}' (${item.sapArticle})? This action cannot be undone.`)) {
      const payload = {
        project_id: projectId,
        category: category,
        sap_article: item.sapArticle,
      };

      try {
        const response = await fetch('http://localhost:8000/api/inventory/delete_item', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const result = await response.json();
          alert(`Error: ${result.detail || 'Failed to delete item.'}`);
        }
        // On success, SSE will update the state and remove the item
      } catch (error) {
        alert('Network error while deleting item.');
      }
    }
  };

  const openClassificationModal = (item: any) => {
    setItemToClassify(item);
    setIsClassificationModalOpen(true);
  };

  const handleConfirmClassification = async (correctSapArticle: string) => {
    if (!itemToClassify) return;

    const payload = {
      project_id: projectId,
      category: category,
      unidentified_part_number: itemToClassify.sapArticle,
      correct_sap_article: correctSapArticle,
    };

    try {
      const response = await fetch('http://localhost:8000/api/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const result = await response.json();
      if (response.ok) {
        alert(result.status);
      } else {
        alert(`Error: ${result.detail || 'Unknown error'}`);
      }
    } catch (error) {
      alert('Network error during classification.');
    }

    setIsClassificationModalOpen(false);
    setItemToClassify(null);
  };

  const handleResetConfirm = async () => {
    if (!projectId || !category) return;

    setIsResetModalOpen(false);
    try {
      const response = await fetch(`http://localhost:8000/api/reset/${projectId}/${category}`, {
        method: 'POST',
      });

      const result = await response.json();

      if (response.ok) {
        // The UI will be cleared automatically by the SSE message from the server
        alert(result.status);
      } else {
        alert(`Error: ${result.detail || 'Unknown error'}`);
      }
    } catch (error) {
      alert('Network error during reset.');
    }
  };

  const inventoryArray = Object.entries(inventory || {}).map(([sapArticle, item]) => ({
    sapArticle,
    ...(item as InventoryItem),
  }));

  const isAuditMode = inventoryArray.some(item => item.expected > 0);

  const MacAddressTable = ({ projectId }: { projectId: string }) => {
  const { inventory } = useInventoryStream(projectId, 'SCANNED_MACS');

  const handleDeleteItem = async (item: any) => {
    if (window.confirm(`Are you sure you want to permanently delete '${item.sapArticle}'?`)) {
      const payload = {
        project_id: projectId,
        category: 'SCANNED_MACS',
        sap_article: item.sapArticle,
      };
      try {
        await fetch('http://localhost:8000/api/inventory/delete_item', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      } catch (error) {
        alert('Network error while deleting item.');
      }
    }
  };

  const macList = Object.entries(inventory || {}).map(([sapArticle, item]) => ({ sapArticle, ...(item as InventoryItem) }));

  return (
    <div style={{ marginBottom: '3rem', border: '1px solid #ddd', borderRadius: '8px', padding: '1rem' }}>
      <h2 style={{ margin: 0, color: '#333' }}>MAC Address Registry</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem' }}>
        <thead>
          <tr style={{ backgroundColor: '#f2f2f2' }}>
            <th style={styles.th}>MAC Address</th>
            <th style={styles.th}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {macList.length === 0 ? (
            <tr>
              <td colSpan={2} style={{ textAlign: 'center', padding: '1rem', fontStyle: 'italic', color: '#666' }}>
                No MAC addresses registered yet...
              </td>
            </tr>
          ) : (
            macList.map((item: any) => (
              <tr key={item.sapArticle} style={styles.tr}>
                <td style={styles.td}>{item.sapArticle}</td>
                <td style={{...styles.td, width: '100px', textAlign: 'center'}}>
                  <button onClick={() => handleDeleteItem(item)} style={styles.deleteButton} title="Delete MAC">
                    🗑️
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

const CategorySection = ({ title, inventoryArray, categoryName, isAuditMode, onClassify, onDelete, onReset, projectId }: { title: string, inventoryArray: any[], categoryName: string, isAuditMode: boolean, onClassify: (item: any) => void, onDelete: (item: any) => void, onReset: () => void, projectId: string }) => (
    <div style={{ marginBottom: '3rem', border: '1px solid #ddd', borderRadius: '8px', padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0, color: '#333' }}>{title}</h2>
      </div>
      
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: '#f2f2f2' }}>
            <th style={styles.th}>SAP Article</th>
            <th style={styles.th}>Part Number</th>
            <th style={styles.th}>Description</th>
            {isAuditMode && <th style={styles.th}>Expected</th>}
            <th style={styles.th}>Scanned</th>
            {isAuditMode && <th style={styles.th}>Status</th>}
            <th style={styles.th}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {inventoryArray.length === 0 ? (
            <tr>
              <td colSpan={isAuditMode ? 7 : 5} style={{ textAlign: 'center', padding: '1rem', fontStyle: 'italic', color: '#666' }}>
                No items scanned yet...
              </td>
            </tr>
          ) : (
            inventoryArray.map((item: any) => {
              const { sapArticle, description, expected, scanned, part_number, status: itemStatus } = item;
              const status = getStatus(expected, scanned);
              const isUnidentified = itemStatus === 'UNIDENTIFIED';
              const rowStyle = isUnidentified ? { ...styles.tr, backgroundColor: '#fffbe6' } : styles.tr;

              return (
                <tr key={sapArticle} style={rowStyle}>
                  <td style={styles.td}>{sapArticle}</td>
                  <td style={styles.td}>{part_number || 'N/A'}</td>
                  <td style={styles.td}>{description}</td>
                  {isAuditMode && <td style={{ ...styles.td, textAlign: 'center' }}>{expected}</td>}
                  <td style={{ ...styles.td, textAlign: 'center' }}>
                    <EditableQuantityCell item={item} categoryName={categoryName} projectId={projectId} />
                  </td>
                  {isAuditMode && (
                    <td style={{ ...styles.td, textAlign: 'center', color: isUnidentified ? '#f0ad4e' : status.color, fontWeight: 'bold' }}>
                      {isUnidentified ? 'UNIDENTIFIED' : status.text}
                    </td>
                  )}
                  <td style={styles.td}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {isUnidentified && (
                        <button onClick={() => onClassify(item)} style={styles.buttonPrimary}>Classify</button>
                      )}
                      <button 
                        onClick={() => onDelete(item)} 
                        style={styles.deleteButton}
                        title="Delete Item"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
      {projectId === 'BOM' && <BomUploader projectId={projectId} category={categoryName} />}
    </div>
  );

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
      <h1>Panel de Control de Inventario - Auto-Clasificación</h1>
      <ConfirmationModal 
        isOpen={isResetModalOpen} 
        onClose={() => setIsResetModalOpen(false)} 
        onConfirm={handleResetConfirm} 
        itemName={`${projectId} / ${category}`}
      />
      <ClassificationModal 
        isOpen={isClassificationModalOpen}
        onClose={() => setIsClassificationModalOpen(false)}
        onConfirm={handleConfirmClassification}
        item={itemToClassify}
      />
      <ProjectManager 
        projectId={projectId} 
        setProjectId={setProjectId} 
        category={category}
        setCategory={setCategory}
        onResetClick={handleResetCurrent} 
      />
      <p style={{ marginBottom: '2rem' }}>Modo: <strong>{projectId}</strong> - Los productos se clasifican automáticamente por categoría</p>

      {projectId === 'MAC_REGISTRY' ? (
        <MacAddressTable projectId={projectId} />
      ) : (
        <CategorySection 
          title={category} 
          inventoryArray={inventoryArray} 
          categoryName={category}
          isAuditMode={isAuditMode}
          onClassify={openClassificationModal}
          onDelete={handleDeleteItem}
          onReset={handleResetCurrent}
          projectId={projectId}
        />
      )}
      <CatalogUploader />
    </div>
  );
};

const CatalogUploader = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState('');
  const [diagnosis, setDiagnosis] = useState<any>(null);
  const [catalogStatus, setCatalogStatus] = useState<{items_count: number, is_loaded: boolean} | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setMessage('');
      setDiagnosis(null);
    }
  };

  const fetchCatalogStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/catalog/status');
      if (response.ok) {
        const status = await response.json();
        setCatalogStatus(status);
      }
    } catch (error) {
      console.error('Failed to fetch catalog status:', error);
    }
  };

  const handleProcess = async (endpoint: 'upload' | 'diagnose') => {
    if (!file) {
      setMessage('Please select a file first.');
      return;
    }

    setIsProcessing(true);
    setMessage(`Processing ${file.name}...`);
    setDiagnosis(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`http://localhost:8000/api/catalog/${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        if (endpoint === 'diagnose') {
          setDiagnosis(result);
          setMessage('Diagnosis complete.');
        } else {
          setMessage(`Success: ${result.status}`);
          fetchCatalogStatus(); // Refresh status after upload
        }
      } else {
        setMessage(`Error: ${result.detail}`);
      }
    } catch (error) {
      setMessage('Network error during processing.');
      console.error(error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClearCatalog = async () => {
    if (!window.confirm('Are you sure you want to clear the entire product catalog? This action cannot be undone.')) {
      return;
    }

    setIsProcessing(true);
    setMessage('Clearing catalog...');

    try {
      const response = await fetch('http://localhost:8000/api/catalog/clear', {
        method: 'DELETE',
      });

      const result = await response.json();

      if (response.ok) {
        setMessage(`Success: ${result.status}`);
        fetchCatalogStatus(); // Refresh status after clearing
      } else {
        setMessage(`Error: ${result.detail}`);
      }
    } catch (error) {
      setMessage('Network error during clearing.');
      console.error(error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Load catalog status on component mount
  React.useEffect(() => {
    fetchCatalogStatus();
  }, []);

  return (
    <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px', marginTop: '2rem', backgroundColor: '#f0f8ff' }}>
      <h3>Upload Product Catalog</h3>
      <p style={{fontSize: '0.9rem', color: '#555'}}>Upload an Excel file with 'SAP Article' and 'Description' columns.</p>
      <input type="file" onChange={handleFileChange} accept=".xlsx,.xls" />
      <button onClick={() => handleProcess('upload')} disabled={isProcessing || !file} style={{ marginLeft: '1rem', padding: '0.5rem 1rem' }}>
        {isProcessing ? 'Processing...' : 'Upload to Catalog'}
      </button>
      <button onClick={() => handleProcess('diagnose')} disabled={isProcessing || !file} style={{ marginLeft: '1rem', padding: '0.5rem 1rem' }}>
        {isProcessing ? 'Processing...' : 'Diagnose File'}
      </button>
      <button onClick={handleClearCatalog} disabled={isProcessing} style={{ marginLeft: '1rem', padding: '0.5rem 1rem', backgroundColor: '#d9534f', color: 'white', border: 'none', borderRadius: '4px' }}>
        {isProcessing ? 'Processing...' : 'Clear Catalog'}
      </button>
      
      {catalogStatus && (
        <div style={{ marginTop: '1rem', padding: '0.5rem', backgroundColor: catalogStatus.is_loaded ? '#d4edda' : '#f8d7da', borderRadius: '4px' }}>
          <strong>Catalog Status:</strong> {catalogStatus.is_loaded ? `${catalogStatus.items_count} items loaded (persistent)` : 'No catalog loaded'}
        </div>
      )}
      
      {message && <p style={{ marginTop: '1rem', fontStyle: 'italic' }}>{message}</p>}
      {diagnosis && (
        <div style={{marginTop: '1rem', padding: '1rem', border: '1px solid #eee', backgroundColor: 'white'}}>
          <h4>Diagnosis Report</h4>
          <p><strong>Total Rows in File:</strong> {diagnosis.total_rows}</p>
          <p><strong>Rows with Empty SAP Article:</strong> {diagnosis.empty_article_rows}</p>
          {Object.keys(diagnosis.duplicate_articles).length > 0 && (
            <div>
              <strong>Duplicate SAP Articles Found:</strong>
              <ul style={{maxHeight: '200px', overflowY: 'auto', border: '1px solid #ddd', padding: '10px'}}>
                                {Object.entries(diagnosis.duplicate_articles).map(([article, count]: [string, unknown]) => (
                                    <li key={article}>'{article}' (appears {String(count)} times)</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const styles = {
  projectSelector: {
    display: 'flex',
    justifyContent: 'center',
    gap: '1rem',
    padding: '1rem',
    borderBottom: '1px solid #eee',
  },
  th: {
    border: '1px solid #ddd',
    padding: '8px',
    textAlign: 'left' as const,
  },
  tr: {
    borderBottom: '1px solid #ddd',
  },
  td: {
    border: '1px solid #ddd',
    padding: '8px',
  },
  modalOverlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modalContent: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    minWidth: '300px',
    maxWidth: '500px',
  },
  modalActions: {
    marginTop: '1.5rem',
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '1rem',
  },
  deleteButton: {
    background: 'none',
    border: 'none',
    color: '#d9534f',
    cursor: 'pointer',
    fontSize: '1.2rem',
    marginLeft: '10px',
    padding: '5px',
  },
  buttonPrimary: {
    padding: '0.5rem 1rem',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold',
    backgroundColor: '#5cb85c',
    color: 'white',
  },
  buttonDanger: {
    padding: '0.5rem 1rem',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold',
    backgroundColor: '#d9534f',
    color: 'white',
  },
  buttonSecondary: {
    padding: '0.5rem 1rem',
    border: '1px solid #ccc',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold',
    backgroundColor: 'white',
    color: '#333',
  },
};
