from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File
from pydantic import BaseModel
import asyncio, json, time, openpyxl, io, zipfile, os
from collections import defaultdict
import pandas as pd
from contextlib import asynccontextmanager
import logging

STATE_FILE = "po_state.json"
CATALOG_FILE = "product_catalog.json"

# --- State Management --- #
PRODUCT_CATALOG = {}
# PO_STATE structure: { project_id: { category: { bom: {}, inventory: {} } } }
PO_STATE = defaultdict(lambda: defaultdict(lambda: {
    'bom': {},
    'inventory': defaultdict(lambda: {'expected': 0, 'scanned': 0, 'description': ''})
}))
PO_LISTENERS = defaultdict(lambda: defaultdict(list))

def save_state():
    logging.info("Saving application state...")
    try:
        with open(STATE_FILE, "w") as f:
            serializable_state = json.loads(json.dumps(PO_STATE))
            json.dump(serializable_state, f, indent=4)
        logging.info(f"State successfully saved to {STATE_FILE}")
    except Exception as e:
        logging.error(f"Failed to save state: {e}")

def save_catalog():
    logging.info("Saving product catalog...")
    try:
        with open(CATALOG_FILE, "w") as f:
            json.dump(PRODUCT_CATALOG, f, indent=4)
        logging.info(f"Catalog successfully saved to {CATALOG_FILE}")
    except Exception as e:
        logging.error(f"Failed to save catalog: {e}")

def load_catalog():
    global PRODUCT_CATALOG
    try:
        if os.path.exists(CATALOG_FILE):
            logging.info(f"Loading catalog from {CATALOG_FILE}...")
            with open(CATALOG_FILE, "r") as f:
                PRODUCT_CATALOG = json.load(f)
            logging.info(f"Catalog loaded successfully with {len(PRODUCT_CATALOG)} items.")
        else:
            logging.info("Catalog file not found. Starting with empty catalog.")
    except Exception as e:
        logging.error(f"Failed to load catalog: {e}")
        PRODUCT_CATALOG = {}

def load_state():
    global PO_STATE
    try:
        if os.path.exists(STATE_FILE):
            logging.info(f"Loading state from {STATE_FILE}...")
            with open(STATE_FILE, "r") as f:
                loaded_projects = json.load(f)
                for project_id, categories in loaded_projects.items():
                    for category, data in categories.items():
                        inventory = defaultdict(lambda: {'expected': 0, 'scanned': 0, 'description': ''}, data.get('inventory', {}))
                        PO_STATE[project_id][category] = {
                            'bom': data.get('bom', {}),
                            'inventory': inventory
                        }
            logging.info("State loaded successfully.")
        else:
            logging.info("State file not found. Starting with a fresh state.")
    except Exception as e:
        logging.error(f"Failed to load state: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_state()
    load_catalog()
    yield
    save_state()
    save_catalog()

app = FastAPI(title="QTS Pro API", lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://localhost:19006",  # React Native web
    "exp://*",  # Expo development clients
    "*"  # For development only - restrict in production!
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---
async def notify_listeners(project_id: str, category: str):
    listeners = PO_LISTENERS.get(project_id, {}).get(category, [])
    if not listeners:
        return
    inventory_data = PO_STATE[project_id][category]['inventory']
    for queue in listeners:
        await queue.put(dict(inventory_data))

# --- API Endpoints ---
@app.get("/api/healthz")
def healthz(): 
    return {"ok": True, "ts": time.time()}

@app.post("/api/catalog/diagnose")
async def diagnose_catalog(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        df.columns = [str(col).strip().lower() for col in df.columns]

        if 'sap article' not in df.columns:
            raise HTTPException(status_code=400, detail="Excel file must contain 'SAP Article' column.")

        # Convert to string and strip whitespace
        df['sap article'] = df['sap article'].astype(str).str.strip()

        # Find empty or placeholder values
        empty_articles = df[df['sap article'].isin(['', 'nan', 'None'])]
        num_empty = len(empty_articles)

        # Find duplicates
        # Keep=False marks all duplicates, including the first occurrence
        duplicates = df[df.duplicated(subset=['sap article'], keep=False)]
        duplicate_counts = duplicates['sap article'].value_counts().to_dict()

        return {
            "status": "Diagnosis complete",
            "total_rows": len(df),
            "empty_article_rows": num_empty,
            "duplicate_articles": duplicate_counts
        }
    except Exception as e:
        logging.error(f"Failed to diagnose catalog file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to diagnose catalog file: {str(e)}")


@app.post("/api/bom/upload/{project_id}/{category}")
async def upload_bom(project_id: str, category: str, file: UploadFile = File(...)):
    logging.info(f"---")
    logging.info(f"BOM Upload for {project_id} [{category}] - File: {file.filename}")
    logging.info(f"Received file: {file.filename}")
    logging.info(f"Content-Type: {file.content_type}")

    try:
        contents = await file.read()
        logging.info(f"File size: {len(contents)} bytes")
        
        # Save for debugging if needed
        # with open(f"/tmp/debug_{file.filename}", "wb") as f:
        #     f.write(contents)

        try:
            workbook = openpyxl.load_workbook(io.BytesIO(contents))
            # Find the correct sheet, preferring one named 'BOM'
            sheet = None
            if 'BOM' in workbook.sheetnames:
                sheet = workbook['BOM']
                logging.info("Found and selected sheet named 'BOM'.")
            else:
                sheet = workbook.active
                logging.info(f"Sheet 'BOM' not found, using active sheet: {sheet.title}")

        except zipfile.BadZipFile:
            logging.error("Upload failed: File is not a valid .xlsx file.")
            return JSONResponse(status_code=400, content={"error": "Invalid file format. Please upload a valid Excel (.xlsx) file."})

        # Find the header row automatically by searching for 'SAP Article'
        header_row_index = -1
        header = []
        for i, row in enumerate(sheet.iter_rows(max_row=25)):  # Scan first 25 rows
            current_row_normalized = [str(cell.value).lower().strip() if cell.value else '' for cell in row]
            if 'sap article' in current_row_normalized:
                header_row_index = i + 1  # 1-based index for openpyxl
                header = current_row_normalized
                logging.info(f"Found header row at index {header_row_index}")
                break
        
        if header_row_index == -1:
            error_msg = "Could not find a header row containing 'SAP Article' within the first 25 rows."
            logging.error(error_msg)
            return JSONResponse(status_code=400, content={"error": error_msg})

        # Get column indices from the found header
        try:
            sap_col = header.index("sap article")
            desc_col = header.index("description")
            qty_col = header.index("quantity")
            # Part number is optional
            part_num_col = header.index("part number") if "part number" in header else -1
        except ValueError:
            missing_cols = [col for col in ["'SAP Article'", "'Description'", "'Quantity'"] if col.lower().strip("'") not in header]
            error_msg = f"Found header row, but missing required column(s): {', '.join(missing_cols)}"
            logging.error(error_msg)
            return JSONResponse(status_code=400, content={"error": error_msg})

        new_bom = {}
        logging.info("--- Starting to process BOM rows ---")
        # Start iterating from the row *after* the header row
        for i, row in enumerate(sheet.iter_rows(min_row=header_row_index + 1, values_only=True)):
            # Clean the SAP article number by converting to string and stripping whitespace
            sap_article = str(row[sap_col]).strip()
            description = str(row[desc_col])
            raw_qty = row[qty_col]
            logging.info(f"Row {i+header_row_index+1}: SAP Article='{sap_article}', Raw Quantity='{raw_qty}' (type: {type(raw_qty)}))")
            try:
                # Handle cases where quantity might be a float or a string that can be converted to float then int
                if raw_qty is None:
                    expected_qty = 0
                else:
                    expected_qty = int(float(raw_qty))
            except (ValueError, TypeError):
                logging.warning(f"Could not parse quantity for SAP Article '{sap_article}'. Value was '{raw_qty}'. Defaulting to 0.")
                expected_qty = 0
            
            if sap_article and sap_article != 'None' and expected_qty > 0:
                bom_item = {
                    "description": description,
                    "expected": expected_qty,
                    "scanned": 0
                }
                if part_num_col != -1 and row[part_num_col] is not None:
                    bom_item["part_number"] = str(row[part_num_col]).strip()
                new_bom[sap_article] = bom_item
        
        category_state = PO_STATE[project_id][category]
        category_state['bom'] = new_bom

        # Merge BOM with existing inventory for this category
        for sap_article, bom_item in new_bom.items():
            inventory_item = category_state['inventory'][sap_article]
            inventory_item['expected'] = bom_item['expected']
            # Prioritize BOM data for description and part number
            inventory_item['description'] = bom_item['description']
            if 'part_number' in bom_item:
                inventory_item['part_number'] = bom_item['part_number']

        save_state()
        
        # Notify listeners for this specific project and category
        await notify_listeners(project_id, category)

        return {"status": "BOM uploaded successfully", "project_id": project_id, "category": category, "items_loaded": len(new_bom)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to process file: {e}"})


@app.post("/api/catalog/upload")
async def upload_catalog(file: UploadFile = File(...)):
    global PRODUCT_CATALOG
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        df.columns = [str(col).strip().lower() for col in df.columns]
        
        required_columns = ['sap article', 'description']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail="Excel file must contain 'SAP Article' and 'Description' columns.")

        # Check for optional columns
        has_part_number = 'part number' in df.columns
        has_category = 'category' in df.columns

        # Ensure 'sap article' is treated as string
        # CRITICAL: Sanitize SAP Article keys to prevent type and format mismatches.
        # 1. Convert to string and strip whitespace.
        # 2. Remove trailing '.0' which pandas can add to numeric-looking strings.
        # 3. Handle any remaining non-string data gracefully.
        df['sap article'] = df['sap article'].apply(lambda x: str(x).strip().replace('.0', '') if pd.notna(x) else '')

        # Drop rows where the key is empty after sanitization
        df.dropna(subset=['sap article'], inplace=True)
        df = df[df['sap article'] != '']

        # Drop duplicates, keeping the first valid entry
        df.drop_duplicates(subset=['sap article'], keep='first', inplace=True)

        # Create catalog with description and optional part number and category
        catalog_updates = {}
        for _, row in df.iterrows():
            sap_article = row['sap article']
            catalog_entry = {
                'description': row['description']
            }
            if has_part_number and pd.notna(row['part number']):
                catalog_entry['part_number'] = str(row['part number']).strip()
            if has_category and pd.notna(row['category']):
                catalog_entry['category'] = str(row['category']).strip().upper()
            catalog_updates[sap_article] = catalog_entry

        PRODUCT_CATALOG.clear()  # Clear old catalog before updating
        PRODUCT_CATALOG.update(catalog_updates)
        save_catalog()  # Persist catalog to disk
        logging.info(f"Loaded or updated {len(catalog_updates)} items in the product catalog.")
        
        return {"status": f"{len(catalog_updates)} items loaded or updated in the catalog."}
    except Exception as e:
        logging.error(f"Failed to process catalog file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process catalog file: {str(e)}")

@app.delete("/api/catalog/clear")
async def clear_catalog():
    global PRODUCT_CATALOG
    try:
        PRODUCT_CATALOG.clear()
        save_catalog()  # Save empty catalog to disk
        logging.info("Product catalog cleared successfully.")
        return {"status": "Product catalog cleared successfully."}
    except Exception as e:
        logging.error(f"Failed to clear catalog: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear catalog: {str(e)}")

@app.get("/api/catalog/status")
async def catalog_status():
    return {
        "items_count": len(PRODUCT_CATALOG),
        "is_loaded": len(PRODUCT_CATALOG) > 0
    }

class DeleteItemPayload(BaseModel):
    project_id: str
    category: str
    sap_article: str

class UpdateQuantityPayload(BaseModel):
    project_id: str
    category: str
    sap_article: str
    new_quantity: int

class ClassifyPayload(BaseModel):
    project_id: str
    category: str
    unidentified_part_number: str
    correct_sap_article: str

class ScanPayload(BaseModel):
    project_id: str
    category: str
    part_number: str
    store_id: str
    qty: int
    device_id: str
    idempotency_key: str
    source: str

@app.post("/api/scan")
async def scan(payload: ScanPayload):
    logging.info(f"--- /api/scan endpoint hit with payload: {payload.model_dump_json()}")

    project_id = payload.project_id
    category = payload.category
    part_number_raw = payload.part_number

    # --- DEBUGGING BLOCK ---
    sap_article = str(part_number_raw).strip()
    logging.info(f"--- SCAN DEBUG ---")
    logging.info(f"Received part_number: '{sap_article}' (Type: {type(sap_article)})")
    logging.info(f"Catalog has {len(PRODUCT_CATALOG)} items.")
    # Log a few items from catalog to check keys and their types
    if len(PRODUCT_CATALOG) > 0:
        sample_key = list(PRODUCT_CATALOG.keys())[0]
        logging.info(f"Sample catalog key: '{sample_key}' (Type: {type(sample_key)})" )

    category_state = PO_STATE[project_id][category]
    inventory = category_state['inventory']
    bom = category_state['bom']

    inventory[sap_article]['scanned'] += payload.qty

    # If item is not yet identified, try to identify it.
    if inventory[sap_article].get('status') != 'IDENTIFIED':
        logging.info(f"Item '{sap_article}' is not identified. Attempting lookup.")
        catalog_entry = PRODUCT_CATALOG.get(sap_article)
        
        if catalog_entry:
            logging.info(f"SUCCESS: Found '{sap_article}' in catalog.")
            # Handle both old format (string) and new format (dict)
            if isinstance(catalog_entry, str):
                description = catalog_entry
                part_number = None
                catalog_category = None
            else:
                description = catalog_entry.get('description', 'N/A')
                part_number = catalog_entry.get('part_number')
                catalog_category = catalog_entry.get('category')

            inventory[sap_article]['description'] = description
            inventory[sap_article]['status'] = 'IDENTIFIED'

            if part_number:
                inventory[sap_article]['part_number'] = part_number

            # Auto-classify by category if available in catalog
            if catalog_category and catalog_category != category:
                logging.info(f"AUTO-CLASSIFY: Moving '{sap_article}' from '{category}' to '{catalog_category}' based on catalog")
                target_category_state = PO_STATE[project_id][catalog_category]
                target_inventory = target_category_state['inventory']
                target_inventory[sap_article] = inventory[sap_article].copy()
                del inventory[sap_article]
                category = catalog_category # Update category for SSE broadcast
        else:
            logging.warning(f"UNIDENTIFIED: '{sap_article}' not found in catalog.")
            inventory[sap_article]['description'] = 'Unidentified Item'
            inventory[sap_article]['status'] = 'UNIDENTIFIED'
            # Keep the original scanned value, as it might be a manufacturer's code
            inventory[sap_article]['scanned_part_number'] = sap_article
    # --- END DEBUGGING BLOCK ---
    
    # This block was causing a double-increment. The increment now happens unconditionally on line 381.
    # if sap_article in bom:
    #     pass

    save_state()
    await notify_listeners(project_id, category)

    # After saving, prepare a detailed response payload
    final_item_state = inventory[sap_article]
    expected_qty = final_item_state.get('expected', 0)
    scanned_qty = final_item_state.get('scanned', 0)
    status_text = ""

    # Mode-specific status logic
    is_bom_mode = project_id == 'BOM' # Assuming 'BOM' is the identifier for BOM mode

    if is_bom_mode:
        if expected_qty == 0 and scanned_qty > 0:
            status_text = "NOT_IN_BOM"
        elif scanned_qty == 0:
            status_text = "PENDING"
        elif scanned_qty < expected_qty:
            status_text = "SHORTAGE"
        elif scanned_qty == expected_qty:
            status_text = "MATCH"
        elif scanned_qty > expected_qty:
            status_text = "EXCESS"
    else:
        # For Inventory, PO, and MAC modes, use simpler statuses
        if payload.qty > 0:
            status_text = "ITEM_ADDED"
        else: # This handles the undo case
            status_text = "ITEM_UPDATED"

    response_payload = {
        "accepted": True,
        "sap_article": sap_article,
        "description": final_item_state.get('description', 'N/A'),
        "scanned_total": scanned_qty,
        "expected": expected_qty,
        "status": status_text,
        "scanned_now": payload.qty
    }

    return response_payload

@app.post("/api/classify")
async def classify_item(payload: ClassifyPayload):
    logging.info(f"--- /api/classify endpoint hit with payload: {payload.model_dump_json()}")

    project_id = payload.project_id
    category = payload.category
    unidentified_part_number = payload.unidentified_part_number
    correct_sap_article = payload.correct_sap_article

    if correct_sap_article not in PRODUCT_CATALOG:
        raise HTTPException(status_code=404, detail=f"Correct SAP Article '{correct_sap_article}' not found in product catalog.")

    category_state = PO_STATE.get(project_id, {}).get(category)
    if not category_state:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' or category '{category}' not found.")
    inventory = category_state['inventory']

    unidentified_item = inventory.get(unidentified_part_number)
    if not unidentified_item or unidentified_item.get('status') != 'UNIDENTIFIED':
        raise HTTPException(status_code=404, detail=f"Unidentified item '{unidentified_part_number}' not found in inventory.")

    catalog_entry = PRODUCT_CATALOG[correct_sap_article]
    description = catalog_entry.get('description', 'N/A')
    part_number = catalog_entry.get('part_number')

    # Merge the scanned quantity into the correct item's entry
    correct_item = inventory[correct_sap_article]
    correct_item['scanned'] += unidentified_item['scanned']
    
    # Update metadata for the correct item
    correct_item['description'] = description
    correct_item['status'] = 'IDENTIFIED'
    if part_number:
        correct_item['part_number'] = part_number

    # If the correct item is in the BOM, ensure 'expected' is set
    bom = category_state.get('bom', {})
    if correct_sap_article in bom:
        correct_item['expected'] = bom[correct_sap_article].get('expected', 0)

    # Remove the old unidentified item
    del inventory[unidentified_part_number]

    save_state()
    await notify_listeners(project_id, category)

    return {"status": f"Item {unidentified_part_number} has been re-classified as {correct_sap_article}."}

@app.post("/api/inventory/update_quantity")
async def update_scanned_quantity(payload: UpdateQuantityPayload):
    logging.info(f"--- /api/inventory/update_quantity endpoint hit with payload: {payload.model_dump_json()}")

    project_id = payload.project_id
    category = payload.category
    sap_article = payload.sap_article
    new_quantity = payload.new_quantity

    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="New quantity cannot be negative.")

    category_state = PO_STATE.get(project_id, {}).get(category)
    if not category_state:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' or category '{category}' not found.")
    
    inventory = category_state['inventory']
    if sap_article not in inventory:
        raise HTTPException(status_code=404, detail=f"SAP Article '{sap_article}' not found in inventory for this category.")

    inventory[sap_article]['scanned'] = new_quantity
    logging.info(f"Updated scanned quantity for '{sap_article}' to {new_quantity}.")

    save_state()
    await notify_listeners(project_id, category)

    return {"status": f"Scanned quantity for {sap_article} updated to {new_quantity}."}

@app.post("/api/inventory/delete_item")
async def delete_inventory_item(payload: DeleteItemPayload):
    logging.info(f"--- /api/inventory/delete_item endpoint hit with payload: {payload.model_dump_json()}")

    project_id = payload.project_id
    category = payload.category
    sap_article = payload.sap_article

    category_state = PO_STATE.get(project_id, {}).get(category)
    if not category_state:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' or category '{category}' not found.")
    
    inventory = category_state['inventory']
    if sap_article not in inventory:
        # Item might have already been deleted, which is a success case for the user.
        logging.warning(f"Attempted to delete non-existent SAP Article '{sap_article}'.")
        return {"status": f"Item {sap_article} already deleted or not found."}

    del inventory[sap_article]
    logging.info(f"Deleted SAP Article '{sap_article}' from inventory.")

    save_state()
    await notify_listeners(project_id, category)

    return {"status": f"Item {sap_article} has been deleted successfully."}


@app.post("/api/reset/{project_id}/{category}")
async def reset_inventory(project_id: str, category: str):
    # This operation is idempotent. If the state doesn't exist, it's already 'reset'.
    if project_id in PO_STATE and category in PO_STATE[project_id]:
        logging.info(f"Resetting inventory for {project_id}/{category}...")
        del PO_STATE[project_id][category]
        if not PO_STATE[project_id]: # If the project is now empty, remove it
            del PO_STATE[project_id]
        save_state()

        # Manually notify listeners with an empty dict because the state key is gone
        listeners = PO_LISTENERS.get(project_id, {}).get(category, [])
        for queue in listeners:
            await queue.put({})
        logging.info(f"Reset successful for {project_id}/{category}.")
    else:
        logging.info(f"Reset requested for {project_id}/{category}, but it does not exist. No action needed.")

    return {"status": f"Inventory for {project_id} ({category}) has been reset."}

@app.get("/api/export/{project_id}/{category}")
async def export_inventory(project_id: str, category: str):
    if project_id not in PO_STATE or category not in PO_STATE[project_id]:
        raise HTTPException(status_code=404, detail="Inventory not found.")

    inventory_data = PO_STATE[project_id][category]['inventory']
    if not inventory_data:
        raise HTTPException(status_code=404, detail="Inventory is empty.")

    # Convert inventory data to a list of dicts for pandas
    records = [
        {
            "SAP Article": article,
            "Description": data.get('description', 'N/A'),
            "Expected": data.get('expected', 0),
            "Scanned": data.get('scanned', 0)
        }
        for article, data in inventory_data.items()
    ]

    df = pd.DataFrame(records)

    # Create an in-memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventory')
    
    output.seek(0)

    headers = {
        'Content-Disposition': f'attachment; filename="inventory_{project_id}_{category}.xlsx"'
    }
    return Response(content=output.read(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

@app.get("/api/sse/{project_id}/{category}")
async def sse_stream(project_id: str, category: str, request: Request):
    queue = asyncio.Queue()
    PO_LISTENERS[project_id][category].append(queue)

    async def gen():
        try:
            initial_state = PO_STATE[project_id][category]['inventory']
            yield f"data: {json.dumps(dict(initial_state))}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                evt = await queue.get()
                yield f"data: {json.dumps(evt)}\n\n"
        finally:
            if queue in PO_LISTENERS[project_id][category]:
                PO_LISTENERS[project_id][category].remove(queue)

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(gen(), headers=headers)
